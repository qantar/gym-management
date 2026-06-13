import { create } from "zustand"
import { persist } from "zustand/middleware"
import axios from "axios"

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"

interface User { id: number; email: string; full_name: string; role: string; branch_id: number | null }
interface AuthState {
  token: string | null; user: User | null; isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null, user: null, isAuthenticated: false,
      login: async (email, password) => {
        const form = new FormData()
        form.append("username", email); form.append("password", password)
        const { data } = await axios.post(`${BASE}/api/v1/auth/login`, form)
        const { data: user } = await axios.get(`${BASE}/api/v1/users/me`, { headers: { Authorization: `Bearer ${data.access_token}` } })
        set({ token: data.access_token, user, isAuthenticated: true })
      },
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
    }),
    { name: "gymos-auth", partialize: (s) => ({ token: s.token, user: s.user, isAuthenticated: s.isAuthenticated }) }
  )
)
