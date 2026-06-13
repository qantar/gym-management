import { useState } from "react"
import { useLocation } from "react-router-dom"

const titles: Record<string, string> = {
  "/dashboard": "Dashboard", "/members": "Members", "/billing": "Billing",
  "/crm": "CRM", "/attendance": "Attendance", "/inventory": "Inventory",
  "/staff": "Staff", "/reports": "Reports", "/branches": "Branches", "/settings": "Settings",
}

export default function Header() {
  const location = useLocation()
  const title = titles[location.pathname] || "GymOS"
  const [search, setSearch] = useState("")

  return (
    <div style={{ height: "52px", background: "#0f1117", borderBottom: "1px solid rgba(255,255,255,0.07)", display: "flex", alignItems: "center", padding: "0 20px", gap: "16px", flexShrink: 0 }}>
      <div style={{ fontSize: "12px", color: "#636882" }}>
        GymOS <span style={{ color: "#9ba3c0", margin: "0 4px" }}>/</span>
        <span style={{ color: "#f0f2ff", fontWeight: 500 }}>{title}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "6px 12px", background: "#14161f", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "6px", flex: "0 0 260px" }}>
        <span>🔍</span>
        <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search..." style={{ background: "none", border: "none", outline: "none", flex: 1, color: "#f0f2ff", fontSize: "12px", padding: 0 }} />
      </div>
      <div style={{ marginLeft: "auto", display: "flex", gap: "8px" }}>
        <button style={{ padding: "6px 12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#9ba3c0", cursor: "pointer", fontSize: "12px" }}>🏢 Al Malaz ▾</button>
        <button style={{ padding: "6px 12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#9ba3c0", cursor: "pointer", fontSize: "12px" }}>🔔</button>
        <button style={{ padding: "6px 14px", borderRadius: "6px", border: "none", background: "#6c63ff", color: "#fff", cursor: "pointer", fontSize: "12px", fontWeight: 500 }}>+ Quick Add</button>
      </div>
    </div>
  )
}
