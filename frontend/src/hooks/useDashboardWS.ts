import { useEffect, useRef, useState, useCallback } from "react"

export interface KPIData {
  active_members: number
  checkins_today: number
  in_gym_now: number
  revenue_today: string
  overdue_invoices: number
}

function buildWSUrl(branchId: number): string {
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
  const wsBase = apiUrl.replace(/^https?/, (m) => (m === "https" ? "wss" : "ws"))
  return `${wsBase}/api/v1/realtime/dashboard/${branchId}`
}

export function useDashboardWS(branchId: number) {
  const [kpis, setKpis] = useState<KPIData | null>(null)
  const [connected, setConnected] = useState(false)
  const ws = useRef<WebSocket | null>(null)
  const unmounted = useRef(false)

  const connect = useCallback(() => {
    if (unmounted.current) return
    try {
      const socket = new WebSocket(buildWSUrl(branchId))
      ws.current = socket

      socket.onopen = () => { if (!unmounted.current) setConnected(true) }

      socket.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data)
          if (msg.event === "kpi_update" && msg.data) {
            setKpis(msg.data)
          }
        } catch {}
      }

      socket.onclose = () => {
        setConnected(false)
        if (!unmounted.current) setTimeout(connect, 5000)
      }

      socket.onerror = () => socket.close()
    } catch {
      setTimeout(connect, 5000)
    }
  }, [branchId])

  useEffect(() => {
    unmounted.current = false
    connect()
    return () => {
      unmounted.current = true
      ws.current?.close()
    }
  }, [connect])

  return { kpis, connected }
}
