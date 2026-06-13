import { useState, useRef } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { useAttendanceWS } from "../hooks/useAttendanceWS"
import toast from "react-hot-toast"

const BRANCH_ID = 1

const methods = [
  { value: "qr", label: "QR Code", icon: "📱" },
  { value: "rfid", label: "RFID Card", icon: "💳" },
  { value: "pin", label: "PIN", icon: "🔢" },
  { value: "manual", label: "Manual", icon: "👤" },
]

export default function AttendancePage() {
  const [mode, setMode] = useState<"qr" | "rfid" | "pin" | "manual">("manual")
  const [input, setInput] = useState("")
  const [memberSearch, setMemberSearch] = useState("")
  const inputRef = useRef<HTMLInputElement>(null)
  const qc = useQueryClient()
  const { events, connected } = useAttendanceWS(BRANCH_ID)

  const { data: liveStats, refetch: refetchStats } = useQuery({
    queryKey: ["attendance-live", BRANCH_ID],
    queryFn: () => api.get(`/api/v1/attendance/live/${BRANCH_ID}`).then(r => r.data),
    refetchInterval: 10000,
  })

  const { data: memberResults } = useQuery({
    queryKey: ["member-search-checkin", memberSearch],
    queryFn: () => memberSearch.length > 2
      ? api.get(`/api/v1/members/?search=${memberSearch}&page_size=5`).then(r => r.data.items || [])
      : Promise.resolve([]),
    enabled: memberSearch.length > 2,
  })

  const checkin = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post("/api/v1/attendance/checkin", { branch_id: BRANCH_ID, method: mode, ...payload }).then(r => r.data),
    onSuccess: (data) => {
      toast.success("✅ Checked in successfully")
      setInput("")
      setMemberSearch("")
      refetchStats()
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Check-in failed"),
  })

  const handleCheckin = (payload: Record<string, unknown>) => checkin.mutate(payload)

  const handleInputSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    const key = mode === "qr" ? "qr_code" : mode === "rfid" ? "rfid_tag" : mode === "pin" ? "pin_code" : "member_id"
    handleCheckin({ [key]: mode === "manual" ? parseInt(input) : input })
  }

  // Live event to colour
  const eventColor = (evt: string) => ({ checkin: "#00e5a0", checkout: "#636882" }[evt] || "#9ba3c0")

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h1 style={{ fontSize: "15px", fontWeight: 600 }}>Attendance & Check-in</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: connected ? "#00e5a0" : "#ff6b6b" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: connected ? "#00e5a0" : "#ff6b6b", display: "inline-block" }} />
          {connected ? "Live feed connected" : "Reconnecting…"}
        </div>
      </div>

      {/* KPI cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px", marginBottom: "20px" }}>
        {[
          { label: "In Gym Now", value: liveStats?.in_gym_now ?? "—", color: "#00e5a0" },
          { label: "Total Today", value: liveStats?.total_today ?? "—", color: "#6c63ff" },
          { label: "Peak Hour", value: "7:00 PM", color: "#ffc107" },
          { label: "Avg Visit (min)", value: "68", color: "#4fc3f7" },
        ].map(k => (
          <div key={k.label} style={{ background: "#0f1117", border: `1px solid rgba(255,255,255,0.07)`, borderTop: `2px solid ${k.color}`, borderRadius: "10px", padding: "16px" }}>
            <div style={{ fontSize: "10px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "4px" }}>{k.label}</div>
            <div style={{ fontSize: "28px", fontWeight: 700, color: k.color }}>{k.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
        {/* ── Check-in Panel ── */}
        <div style={{ background: "#0f1117", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px" }}>
          <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "16px" }}>Check-in</div>

          {/* Method selector */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "6px", marginBottom: "16px" }}>
            {methods.map(m => (
              <button key={m.value} onClick={() => { setMode(m.value as typeof mode); setInput(""); inputRef.current?.focus() }}
                style={{ padding: "8px 4px", borderRadius: "6px", border: `1px solid ${mode === m.value ? "#6c63ff" : "rgba(255,255,255,0.07)"}`, background: mode === m.value ? "rgba(108,99,255,0.15)" : "transparent", color: mode === m.value ? "#6c63ff" : "#9ba3c0", cursor: "pointer", fontSize: "11px", fontFamily: "inherit", display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                <span style={{ fontSize: "18px" }}>{m.icon}</span>{m.label}
              </button>
            ))}
          </div>

          {/* Input form */}
          {mode !== "manual" ? (
            <form onSubmit={handleInputSubmit}>
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                placeholder={mode === "qr" ? "Scan QR code…" : mode === "rfid" ? "Tap RFID card…" : "Enter PIN…"}
                autoFocus
                type={mode === "pin" ? "password" : "text"}
                style={{ marginBottom: "12px" }}
              />
              <button type="submit" disabled={!input || checkin.isPending}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "none", background: "#6c63ff", color: "#fff", cursor: "pointer", fontSize: "13px", fontWeight: 600, fontFamily: "inherit" }}>
                {checkin.isPending ? "Processing…" : "✅ Check In"}
              </button>
            </form>
          ) : (
            <div>
              <input
                value={memberSearch}
                onChange={e => setMemberSearch(e.target.value)}
                placeholder="Search member name, ID or phone…"
                style={{ marginBottom: "8px" }}
              />
              {(memberResults || []).map((m: any) => (
                <div key={m.id}
                  onClick={() => handleCheckin({ member_id: m.id })}
                  style={{ padding: "10px 12px", background: "#14161f", borderRadius: "6px", marginBottom: "6px", cursor: "pointer", display: "flex", justifyContent: "space-between", alignItems: "center", border: "1px solid rgba(255,255,255,0.05)" }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "13px" }}>{m.first_name} {m.last_name}</div>
                    <div style={{ fontSize: "11px", color: "#636882" }}>{m.member_id} · {m.phone}</div>
                  </div>
                  <span style={{ fontSize: "10px", padding: "3px 8px", borderRadius: "4px", background: m.status === "active" ? "rgba(0,229,160,0.12)" : "rgba(255,107,107,0.12)", color: m.status === "active" ? "#00e5a0" : "#ff6b6b" }}>{m.status}</span>
                </div>
              ))}
              {memberSearch.length > 2 && (!memberResults || memberResults.length === 0) && (
                <div style={{ color: "#636882", fontSize: "12px", textAlign: "center", padding: "20px" }}>No members found</div>
              )}
            </div>
          )}

          {/* Kiosk mode card */}
          <div style={{ marginTop: "20px", padding: "16px", background: "#14161f", borderRadius: "8px", textAlign: "center" }}>
            <div style={{ fontSize: "32px", marginBottom: "8px" }}>🖥️</div>
            <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "4px" }}>Kiosk Mode</div>
            <div style={{ fontSize: "11px", color: "#636882", marginBottom: "12px" }}>Full-screen self-service terminal</div>
            <button onClick={() => toast("Kiosk mode opening...", { icon: "🖥️" })}
              style={{ padding: "6px 16px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#f0f2ff", cursor: "pointer", fontSize: "12px", fontFamily: "inherit" }}>
              Launch Kiosk
            </button>
          </div>
        </div>

        {/* ── Live Feed ── */}
        <div style={{ background: "#0f1117", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "10px", padding: "20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <div style={{ fontSize: "13px", fontWeight: 600 }}>Live Feed</div>
            <div style={{ fontSize: "11px", color: "#636882" }}>{events.length} events today</div>
          </div>

          {/* DB logs */}
          <div style={{ overflowY: "auto", maxHeight: "420px", display: "flex", flexDirection: "column", gap: "6px" }}>
            {/* WebSocket events (real-time) */}
            {events.map((e, i) => (
              <div key={i} style={{ padding: "10px 12px", background: "rgba(0,229,160,0.04)", borderLeft: `3px solid ${eventColor(e.event)}`, borderRadius: "0 6px 6px 0", animation: i === 0 ? "fadeIn 0.3s ease" : "none" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                  <span style={{ fontWeight: 600, fontSize: "12px" }}>{(e.data as any).member_name || `Member #${(e.data as any).member_id}`}</span>
                  <span style={{ fontSize: "10px", color: "#636882" }}>{new Date(e.ts).toLocaleTimeString()}</span>
                </div>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <span style={{ fontSize: "11px", color: eventColor(e.event) }}>{e.event === "checkin" ? "↗ Checked in" : "↙ Checked out"}</span>
                  <span style={{ fontSize: "10px", color: "#636882" }}>via {(e.data as any).method}</span>
                  {!(e.data as any).has_active_membership && e.event === "checkin" && (
                    <span style={{ fontSize: "10px", padding: "1px 6px", background: "rgba(255,193,7,0.12)", color: "#ffc107", borderRadius: "3px" }}>⚠ No membership</span>
                  )}
                </div>
              </div>
            ))}

            {/* DB recent logs */}
            {(liveStats?.recent_logs || []).map((l: any) => (
              <div key={l.id} style={{ padding: "10px 12px", background: "#14161f", borderLeft: "3px solid #636882", borderRadius: "0 6px 6px 0" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                  <span style={{ fontSize: "12px", color: "#9ba3c0" }}>Member #{l.member_id}</span>
                  <span style={{ fontSize: "10px", color: "#636882" }}>{new Date(l.check_in).toLocaleTimeString()}</span>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <span style={{ fontSize: "11px", color: l.check_out ? "#636882" : "#00e5a0" }}>
                    {l.check_out ? "↙ Out" : "↗ In"}
                  </span>
                  <span style={{ fontSize: "10px", color: "#636882" }}>via {l.method}</span>
                </div>
              </div>
            ))}

            {events.length === 0 && (!liveStats?.recent_logs?.length) && (
              <div style={{ textAlign: "center", color: "#636882", padding: "40px", fontSize: "12px" }}>
                Waiting for check-ins…
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`@keyframes fadeIn{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}`}</style>
    </div>
  )
}
