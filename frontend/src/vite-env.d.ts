/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Electron preload API
interface GymOSBridge {
  getVersion: () => Promise<string>
  getStore: (key: string) => Promise<unknown>
  setStore: (key: string, value: unknown) => Promise<void>
  printHTML: (html: string) => Promise<void>
  showSaveDialog: (opts: Record<string, unknown>) => Promise<{ filePath?: string }>
  minimize: () => void
  maximize: () => void
  close: () => void
  onNavigate: (cb: (route: string) => void) => void
}

declare global {
  interface Window {
    gymos?: GymOSBridge
  }
}
