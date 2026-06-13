import { useState, useRef, useEffect } from "react"
import { api } from "../lib/api"

const BRANCH_ID = 1

interface CheckinResult {
  success: boolean
  type: "success" | "warning" | "error" | "info"
  message: string
  member_name?: string
  member_id?: string
  photo_url?: string
  membership_expires?: string
  total_checkins?: number
}

export default function KioskPage() {
  const [input, setInput] = useState("")
  const [method, setMethod] = useState<"qr"|"rfid"|"pin"|"manual">("qr")
  const [result, setResult] = useState<CheckinResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({ checkins_today: 0, in_gym_now: 0 })
  const inputRef = useRef<HTMLInputElement>(null)
  const clearTimer = useRef<ReturnType<typeof setTimeout>>()

  // Fetch live stats
  const fetchStats = async () => {
    try {
      const r = await api.get(`/api/v1/kiosk/stats/${BRANCH_ID}`)
      setStats(r.data)
    } catch {}
  }

  useEffect(() => {
    fetchStats()
    const t = setInterval(fetchStats, 15000)
    return () => clearInterval(t)
  }, [])

  // Auto-focus input
  useEffect(() => { inputRef.current?.focus() }, [method])

  // Auto-clear result after 5s
  useEffect(() => {
    if (result) {
      clearTimer.current = setTimeout(() => { setResult(null); setInput(""); inputRef.current?.focus() }, 5000)
    }
    return () => clearTimeout(clearTimer.current)
  }, [result])

  const handleCheckin = async (identifier: string) => {
    if (!identifier.trim()) return
    setLoading(true)
    try {
      const r = await api.post("/api/v1/kiosk/checkin", { branch_id: BRANCH_ID, identifier: identifier.trim(), method })
      setResult(r.data)
      if (r.data.success) fetchStats()
    } catch (e: any) {
      setResult({ success: false, type: "error", message: e.response?.data?.detail || "Check-in failed" })
    } finally {
      setLoading(false)
    }
  }

  const typeColor = { success:"#00e5a0", warning:"#ffc107", error:"#ff6b6b", info:"#4fc3f7" }
  const typeIcon  = { success:"✅", warning:"⚠️", error:"❌", info:"ℹ️" }

  return (
    <div style={{
      minHeight:"calc(100vh - 100px)", display:"flex", flexDirection:"column",
      alignItems:"center", justifyContent:"center", background:"#0a0b0e",
    }}>
      {/* Header */}
      <div style={{ textAlign:"center", marginBottom:"32px" }}>
        <div style={{ fontSize:"36px", fontWeight:700, color:"#6c63ff", marginBottom:"4px" }}>GymOS</div>
        <div style={{ fontSize:"14px", color:"#636882" }}>Member Check-in Terminal</div>
        <div style={{ display:"flex", gap:"24px", justifyContent:"center", marginTop:"16px" }}>
          <div style={{ textAlign:"center" }}>
            <div style={{ fontSize:"28px", fontWeight:700, color:"#4fc3f7" }}>{stats.checkins_today}</div>
            <div style={{ fontSize:"11px", color:"#636882" }}>Today's Check-ins</div>
          </div>
          <div style={{ width:"1px", background:"rgba(255,255,255,0.1)" }} />
          <div style={{ textAlign:"center" }}>
            <div style={{ fontSize:"28px", fontWeight:700, color:"#00e5a0" }}>{stats.in_gym_now}</div>
            <div style={{ fontSize:"11px", color:"#636882" }}>In Gym Now</div>
          </div>
        </div>
      </div>

      {/* Result card */}
      {result ? (
        <div style={{
          width:"440px", padding:"32px", borderRadius:"16px", textAlign:"center",
          background: result.type === "success" ? "rgba(0,229,160,0.08)" : result.type === "warning" ? "rgba(255,193,7,0.08)" : "rgba(255,107,107,0.08)",
          border:`2px solid ${typeColor[result.type]}`,
          animation:"fadeIn 0.3s ease",
        }}>
          <div style={{ fontSize:"56px", marginBottom:"16px" }}>{typeIcon[result.type]}</div>
          {result.member_name && (
            <div style={{ fontSize:"28px", fontWeight:700, marginBottom:"8px" }}>{result.member_name}</div>
          )}
          {result.member_id && (
            <div style={{ fontSize:"13px", color:"#636882", marginBottom:"12px" }}>{result.member_id}</div>
          )}
          <div style={{ fontSize:"18px", color:typeColor[result.type], fontWeight:600, marginBottom:"16px" }}>
            {result.message}
          </div>
          {result.membership_expires && (
            <div style={{ fontSize:"12px", color:"#636882" }}>Membership expires: {result.membership_expires}</div>
          )}
          {result.total_checkins && (
            <div style={{ fontSize:"12px", color:"#636882", marginTop:"4px" }}>Visit #{result.total_checkins.toLocaleString()} 🎉</div>
          )}
          <div style={{ marginTop:"16px", height:"4px", background:`${typeColor[result.type]}33`, borderRadius:"2px", overflow:"hidden" }}>
            <div style={{ height:"4px", background:typeColor[result.type], borderRadius:"2px", animation:"shrink 5s linear forwards" }} />
          </div>
        </div>
      ) : (
        <div style={{ width:"440px" }}>
          {/* Method tabs */}
          <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"6px", marginBottom:"20px" }}>
            {(["qr","rfid","pin","manual"] as const).map(m => (
              <button key={m} onClick={() => { setMethod(m); setInput(""); inputRef.current?.focus() }}
                style={{
                  padding:"10px 6px", borderRadius:"8px", cursor:"pointer", fontSize:"12px",
                  border:`1px solid ${method===m?"#6c63ff":"rgba(255,255,255,0.1)"}`,
                  background: method===m?"rgba(108,99,255,0.15)":"transparent",
                  color: method===m?"#6c63ff":"#9ba3c0", fontFamily:"inherit",
                  display:"flex", flexDirection:"column", alignItems:"center", gap:"4px",
                }}>
                <span style={{ fontSize:"20px" }}>{ {"qr":"📱","rfid":"💳","pin":"🔢","manual":"👤"}[m] }</span>
                <span style={{ textTransform:"uppercase", letterSpacing:"0.5px" }}>{m}</span>
              </button>
            ))}
          </div>

          {/* Input */}
          <div style={{ position:"relative" }}>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleCheckin(input)}
              placeholder={
                method === "qr" ? "Scan QR code or swipe card…" :
                method === "rfid" ? "Tap RFID card…" :
                method === "pin" ? "Enter your PIN…" : "Enter member ID…"
              }
              type={method === "pin" ? "password" : "text"}
              autoFocus
              style={{
                width:"100%", padding:"16px 20px", fontSize:"16px", borderRadius:"10px",
                background:"#0f1117", border:"2px solid rgba(108,99,255,0.4)",
                color:"#f0f2ff", outline:"none", textAlign:"center", letterSpacing: method==="pin"?"6px":"normal",
              }}
              onFocus={e => (e.target as HTMLInputElement).style.borderColor = "#6c63ff"}
              onBlur={e => (e.target as HTMLInputElement).style.borderColor = "rgba(108,99,255,0.4)"}
            />
          </div>

          <button
            onClick={() => handleCheckin(input)}
            disabled={loading || !input.trim()}
            style={{
              width:"100%", marginTop:"12px", padding:"14px", borderRadius:"10px",
              fontSize:"15px", fontWeight:600, cursor:loading||!input?"not-allowed":"pointer",
              background: loading||!input ? "#1f2235" : "#6c63ff", border:"none", color:"#fff",
              fontFamily:"inherit", transition:"background 0.15s",
            }}>
            {loading ? "Processing…" : "Check In ✓"}
          </button>

          <div style={{ textAlign:"center", marginTop:"16px", fontSize:"11px", color:"#636882" }}>
            Press Enter or click Check In after scan
          </div>
        </div>
      )}

      <style>{`
        @keyframes fadeIn { from { opacity:0; transform:scale(0.95) } to { opacity:1; transform:scale(1) } }
        @keyframes shrink { from { width:100% } to { width:0% } }
      `}</style>
    </div>
  )
}
