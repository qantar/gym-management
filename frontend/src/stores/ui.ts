import { create } from "zustand"

interface UIState {
  sidebarOpen: boolean
  activePage: string
  activeBranchId: number | null
  setSidebarOpen: (open: boolean) => void
  setActivePage: (page: string) => void
  setActiveBranch: (id: number | null) => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activePage: "dashboard",
  activeBranchId: null,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActivePage: (page) => set({ activePage: page }),
  setActiveBranch: (id) => set({ activeBranchId: id }),
}))
