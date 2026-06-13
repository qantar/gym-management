import { useEffect, useRef, useState, useCallback } from "react"

export interface WSEvent {
  event: string
  data: Record<string, unknown>
  ts: string
}

function buildWSUrl(branchId: number): string {
  // Works in both browser (Vite proxy) and Electron (direct)
  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
  const wsBase = apiUrl.replace(/^https?/, (m) => (m === "https" ? "wss" : "ws"))
  return `${wsBase}/api/v1/attendance/ws/${branchId}`
}

export function useAttendanceWS(branchId: number) {
  const [events, setEvents] = useState<WSEvent[]>([])
  const [connected, setConnected] = useState(false)
  const ws = useRef<WebSocket | null>(null)
  const pingRef = useRef<ReturnType<typeof setInterval>>()
  const reconnectRef = useRef<ReturnType<typeof setTimeout>>()
  const unmounted = useRef(false)

  const connect = useCallback(() => {
    if (unmounted.current) return
    try {
      const url = buildWSUrl(branchId)
      const socket = new WebSocket(url)
      ws.current = socket

      socket.onopen = () => {
        if (unmounted.current) { socket.close(); return }
        setConnected(true)
        pingRef.current = setInterval(() => {
          if (socket.readyState === WebSocket.OPEN) socket.send("ping")
        }, 25000)
      }

      socket.onmessage = (e) => {
        try {
          const evt: WSEvent = JSON.parse(e.data)
          if (evt.event === "pong" || evt.event === "connected") return
          setEvents((prev) => [evt, ...prev].slice(0, 100))
        } catch { /* ignore malformed */ }
      }

      socket.onclose = () => {
        setConnected(false)
        clearInterval(pingRef.current)
        if (!unmounted.current) {
          reconnectRef.current = setTimeout(connect, 3000)
        }
      }

      socket.onerror = () => socket.close()
    } catch {
      // WebSocket not available (SSR / test env)
      reconnectRef.current = setTimeout(connect, 5000)
    }
  }, [branchId])

  useEffect(() => {
    unmounted.current = false
    connect()
    return () => {
      unmounted.current = true
      clearInterval(pingRef.current)
      clearTimeout(reconnectRef.current)
      ws.current?.close()
    }
  }, [connect])

  const clearEvents = useCallback(() => setEvents([]), [])

  return { events, connected, clearEvents }
}
