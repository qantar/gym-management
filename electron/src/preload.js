const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('gymos', {
  // App info
  getVersion:      ()        => ipcRenderer.invoke('get-app-version'),
  // Persistent store
  getStore:        (key)     => ipcRenderer.invoke('get-store', key),
  setStore:        (key, v)  => ipcRenderer.invoke('set-store', key, v),
  // Print
  printHTML:       (html)    => ipcRenderer.invoke('open-print-dialog', html),
  // Save dialog
  showSaveDialog:  (opts)    => ipcRenderer.invoke('show-save-dialog', opts),
  // Window controls
  minimize:        ()        => ipcRenderer.invoke('minimize'),
  maximize:        ()        => ipcRenderer.invoke('maximize'),
  close:           ()        => ipcRenderer.invoke('close'),
  // Navigation from menu
  onNavigate: (cb) => ipcRenderer.on('navigate', (_, route) => cb(route)),
})
