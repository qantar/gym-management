import axios from "axios"
import { useAuthStore } from "../stores/auth"

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" })

api.interceptors.request.use((cfg) => {
  const token = useAuthStore.getState().token
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

api.interceptors.response.use(res => res, (err) => {
  if (err.response?.status === 401) { useAuthStore.getState().logout(); window.location.href = "/login" }
  return Promise.reject(err)
})
