import { useEffect, useRef, useState, useCallback } from "react"
import { useAuthStore } from "../stores/auth"

export interface KPIData {
  active_members: number
  checkins_today: number
  in_gym_now: number
  revenue_today: string
  overdue_invoices: number
  new_members_month: number
}

function buildWSUrl(branchId: number, token: string): string {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
  const wsBase = apiUrl.replace(/^https?/, (m) => (m === "https" ? "wss" : "ws"))
  return `${wsBase}/api/v1/realtime/dashboard/${branchId}?token=${encodeURIComponent(token)}`
}

export function useDashboardWS(branchId: number) {
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [connected, setConnected] = useState(false)
  const ws = useRef<WebSocket | null>(null)
  const unmounted = useRef(false)
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>()
  const token = useAuthStore.getState().token

  const connect = useCallback(() => {
    if (unmounted.current || !token) return
    try {
      const socket = new WebSocket(buildWSUrl(branchId, token))
      ws.current = socket

      socket.onopen = () => {
        if (!unmounted.current) setConnected(true)
      }

      socket.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.event === "kpi_update" && msg.data) {
            setKpis(msg.data as KPIData)
          }
        } catch { /* ignore */ }
      }

      socket.onclose = (ev) => {
        setConnected(false)
        // Don't reconnect if auth failure
        if (!unmounted.current && ev.code !== 4001) {
          reconnectRef.current = setTimeout(connect, 5000)
        }
      }

      socket.onerror = () => socket.close()
    } catch {
      if (!unmounted.current) {
        reconnectRef.current = setTimeout(connect, 8000)
      }
    }
  }, [branchId, token])

  useEffect(() => {
    unmounted.current = false
    if (token) connect()
    return () => {
      unmounted.current = true
      clearTimeout(reconnectRef.current)
      ws.current?.close()
    }
  }, [connect, token])

  return { kpis, connected }
}
