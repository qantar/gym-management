import { useEffect, useRef, useState, useCallback } from "react"

export interface WSEvent {
  event: string
  data: Record<string, unknown>
  ts: string
}

export function useAttendanceWS(branchId: number) {
  const [events, setEvents] = useState<WSEvent[]>([])
  const [connected, setConnected] = useState(false)
  const ws = useRef<WebSocket | null>(null)
  const pingInterval = useRef<ReturnType<typeof setInterval>>()

  const connect = useCallback(() => {
    const url = `${(import.meta.env.VITE_WS_URL || "ws://localhost:8000").replace(/^http/, "ws")}/api/v1/attendance/ws/${branchId}`
    ws.current = new WebSocket(url)

    ws.current.onopen = () => {
      setConnected(true)
      pingInterval.current = setInterval(() => ws.current?.readyState === 1 && ws.current.send("ping"), 25000)
    }

    ws.current.onmessage = (e) => {
      try {
        const evt: WSEvent = JSON.parse(e.data)
        if (evt.event === "pong" || evt.event === "connected") return
        setEvents(prev => [evt, ...prev].slice(0, 100))
      } catch {}
    }

    ws.current.onclose = () => {
      setConnected(false)
      clearInterval(pingInterval.current)
      setTimeout(connect, 3000)
    }

    ws.current.onerror = () => ws.current?.close()
  }, [branchId])

  useEffect(() => {
    connect()
    return () => {
      clearInterval(pingInterval.current)
      ws.current?.close()
    }
  }, [connect])

  return { events, connected }
}
