const { app, BrowserWindow, ipcMain, shell, dialog, Menu, Tray, nativeImage } = require('electron')
const { autoUpdater } = require('electron-updater')
const Store = require('electron-store')
const path = require('path')
const { spawn, execSync } = require('child_process')
const http = require('http')
const fs = require('fs')

const store = new Store()
const isDev = process.env.ELECTRON_START_URL || !app.isPackaged
const BACKEND_PORT = 8000
const FRONTEND_PORT = 5173

let mainWindow = null
let splashWindow = null
let tray = null
let backendProcess = null
let dockerProcess = null

// ── Splash Screen ────────────────────────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 480, height: 300,
    frame: false, transparent: true, alwaysOnTop: true,
    webPreferences: { nodeIntegration: true, contextIsolation: false },
  })
  splashWindow.loadFile(path.join(__dirname, 'splash.html'))
  splashWindow.center()
}

// ── Main Window ───────────────────────────────────────────────────────────────
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440, height: 900,
    minWidth: 1200, minHeight: 700,
    show: false,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    icon: path.join(__dirname, '../assets/icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
    },
  })

  const startURL = isDev
    ? (process.env.ELECTRON_START_URL || `http://localhost:${FRONTEND_PORT}`)
    : `http://localhost:${BACKEND_PORT}/app`

  mainWindow.loadURL(startURL)

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close()
    mainWindow.show()
    mainWindow.focus()
  })

  mainWindow.on('closed', () => { mainWindow = null })

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url)
    return { action: 'deny' }
  })

  // Menu
  const menu = Menu.buildFromTemplate([
    {
      label: 'GymOS',
      submenu: [
        { label: 'About GymOS Enterprise', role: 'about' },
        { type: 'separator' },
        { label: 'Preferences', accelerator: 'CmdOrCtrl+,', click: () => mainWindow?.webContents.send('navigate', '/settings') },
        { type: 'separator' },
        { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() },
      ],
    },
    {
      label: 'View',
      submenu: [
        { label: 'Reload', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: 'Toggle DevTools', accelerator: 'CmdOrCtrl+Shift+I', role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Modules',
      submenu: [
        { label: 'Dashboard',  accelerator: 'CmdOrCtrl+1', click: () => mainWindow?.webContents.send('navigate', '/dashboard') },
        { label: 'Members',    accelerator: 'CmdOrCtrl+2', click: () => mainWindow?.webContents.send('navigate', '/members') },
        { label: 'POS',        accelerator: 'CmdOrCtrl+3', click: () => mainWindow?.webContents.send('navigate', '/pos') },
        { label: 'Attendance', accelerator: 'CmdOrCtrl+4', click: () => mainWindow?.webContents.send('navigate', '/attendance') },
        { label: 'CRM',        accelerator: 'CmdOrCtrl+5', click: () => mainWindow?.webContents.send('navigate', '/crm') },
        { label: 'Billing',    accelerator: 'CmdOrCtrl+6', click: () => mainWindow?.webContents.send('navigate', '/billing') },
      ],
    },
    {
      label: 'Help',
      submenu: [
        { label: 'API Docs', click: () => shell.openExternal(`http://localhost:${BACKEND_PORT}/api/docs`) },
        { label: 'Check for Updates', click: () => autoUpdater.checkForUpdatesAndNotify() },
      ],
    },
  ])
  Menu.setApplicationMenu(menu)
}

// ── System Tray ───────────────────────────────────────────────────────────────
function createTray() {
  const iconPath = path.join(__dirname, '../assets/tray.png')
  const icon = fs.existsSync(iconPath) ? nativeImage.createFromPath(iconPath) : nativeImage.createEmpty()
  tray = new Tray(icon)
  tray.setToolTip('GymOS Enterprise')
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open GymOS', click: () => { mainWindow?.show(); mainWindow?.focus() } },
    { label: 'Check-in Mode', click: () => mainWindow?.webContents.send('navigate', '/attendance') },
    { label: 'POS', click: () => mainWindow?.webContents.send('navigate', '/pos') },
    { type: 'separator' },
    { label: 'Quit', click: () => app.quit() },
  ]))
  tray.on('double-click', () => { mainWindow?.show(); mainWindow?.focus() })
}

// ── Backend Orchestration ──────────────────────────────────────────────────────
function sendSplashStatus(msg, pct) {
  splashWindow?.webContents.send('status', { msg, pct })
}

async function waitForPort(port, maxMs = 60000) {
  const start = Date.now()
  while (Date.now() - start < maxMs) {
    try {
      await new Promise((res, rej) => {
        const req = http.get(`http://localhost:${port}/health`, res)
        req.on('error', rej)
        req.setTimeout(1000, () => { req.destroy(); rej(new Error('timeout')) })
      })
      return true
    } catch {
      await new Promise(r => setTimeout(r, 1000))
    }
  }
  return false
}

async function startDocker() {
  sendSplashStatus('Starting Docker services…', 10)
  const composeFile = isDev
    ? path.join(__dirname, '../../docker-compose.yml')
    : path.join(process.resourcesPath, '../docker-compose.yml')

  return new Promise((resolve, reject) => {
    dockerProcess = spawn('docker', ['compose', '-f', composeFile, 'up', '-d', '--wait'], {
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    dockerProcess.stdout.on('data', d => sendSplashStatus(d.toString().trim().slice(0, 60), 30))
    dockerProcess.on('close', code => code === 0 ? resolve() : reject(new Error(`docker compose failed: ${code}`)))
  })
}

async function startBackend() {
  sendSplashStatus('Starting backend…', 60)
  const backendDir = isDev
    ? path.join(__dirname, '../../backend')
    : path.join(process.resourcesPath, 'backend')

  const python = process.platform === 'win32' ? 'python' : 'python3'
  backendProcess = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', String(BACKEND_PORT)], {
    cwd: backendDir,
    env: { ...process.env, PYTHONPATH: backendDir },
    stdio: ['ignore', 'pipe', 'pipe'],
  })
  backendProcess.stderr.on('data', d => console.log('[backend]', d.toString()))
  await waitForPort(BACKEND_PORT, 30000)
  sendSplashStatus('Backend ready', 80)
}

async function bootstrap() {
  try {
    createSplash()
    sendSplashStatus('Initializing…', 5)

    if (!isDev) {
      await startDocker()
      await startBackend()
    }

    sendSplashStatus('Launching GymOS…', 95)
    createMainWindow()
    createTray()
  } catch (err) {
    console.error('Bootstrap failed:', err)
    dialog.showErrorBox('GymOS Failed to Start', err.message)
    app.quit()
  }
}

// ── IPC Handlers ──────────────────────────────────────────────────────────────
ipcMain.handle('get-app-version', () => app.getVersion())
ipcMain.handle('get-store', (_, key) => store.get(key))
ipcMain.handle('set-store', (_, key, val) => store.set(key, val))
ipcMain.handle('open-print-dialog', async (_, html) => {
  const win = new BrowserWindow({ show: false, webPreferences: { nodeIntegration: false } })
  await win.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`)
  win.webContents.print({ silent: false, printBackground: true }, () => win.close())
})
ipcMain.handle('show-save-dialog', async (_, opts) => dialog.showSaveDialog(mainWindow, opts))
ipcMain.handle('minimize', () => mainWindow?.minimize())
ipcMain.handle('maximize', () => mainWindow?.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize())
ipcMain.handle('close', () => mainWindow?.hide())

// ── Lifecycle ─────────────────────────────────────────────────────────────────
app.whenReady().then(bootstrap)

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
app.on('activate', () => { if (!mainWindow) createMainWindow() })
app.on('before-quit', () => {
  backendProcess?.kill()
  if (!isDev) {
    try { execSync('docker compose down') } catch {}
  }
})

// Single instance lock
if (!app.requestSingleInstanceLock()) {
  app.quit()
} else {
  app.on('second-instance', () => { mainWindow?.show(); mainWindow?.focus() })
}
