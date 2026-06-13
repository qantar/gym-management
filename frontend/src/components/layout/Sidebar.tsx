import { NavLink, useNavigate } from "react-router-dom"
import { useAuthStore } from "../../stores/auth"

const navItems = [
  { path: "/dashboard", label: "Dashboard", icon: "⊡" },
  { section: "Operations" },
  { path: "/members", label: "Members", icon: "👤" },
  { path: "/attendance", label: "Attendance", icon: "✅" },
  { path: "/scheduling", label: "Scheduling", icon: "📅" },
  { path: "/pos", label: "POS", icon: "🛒" },
  { section: "Finance" },
  { path: "/billing", label: "Billing", icon: "💳" },
  { path: "/inventory", label: "Inventory", icon: "📦" },
  { path: "/payroll", label: "Payroll", icon: "💰" },
  { section: "Growth" },
  { path: "/crm", label: "CRM", icon: "🎯" },
  { path: "/marketing", label: "Marketing", icon: "📢" },
  { section: "People" },
  { path: "/staff", label: "Staff", icon: "👥" },
  { section: "Intelligence" },
  { path: "/reports", label: "Reports", icon: "📊" },
  { path: "/branches", label: "Branches", icon: "🏢" },
  { section: "System" },
  { path: "/audit", label: "Audit Log", icon: "🔍" },
  { path: "/settings", label: "Settings", icon: "⚙️" },
]

const sidebarStyle: React.CSSProperties = {
  position: "fixed", left: 0, top: 0, bottom: 0, width: "220px",
  background: "#0f1117", borderRight: "1px solid rgba(255,255,255,0.07)",
  display: "flex", flexDirection: "column", zIndex: 100,
}

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const initials = user?.full_name?.split(" ").map((n: string) => n[0]).join("").slice(0, 2) || "SA"

  return (
    <div style={sidebarStyle}>
      <div style={{ padding: "0 16px", height: "52px", display: "flex", alignItems: "center", gap: "10px", borderBottom: "1px solid rgba(255,255,255,0.07)", flexShrink: 0 }}>
        <div style={{ width: "28px", height: "28px", background: "#6c63ff", borderRadius: "6px", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "14px", color: "#fff" }}>G</div>
        <div>
          <div style={{ fontSize: "14px", fontWeight: 600 }}>GymOS</div>
          <div style={{ fontSize: "10px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.5px" }}>Enterprise</div>
        </div>
      </div>
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 0" }}>
        {navItems.map((item, i) => {
          if ("section" in item) {
            return <div key={i} style={{ padding: "12px 16px 4px", fontSize: "10px", fontWeight: 600, color: "#636882", textTransform: "uppercase", letterSpacing: "0.8px" }}>{item.section}</div>
          }
          return (
            <NavLink key={item.path} to={item.path!}
              style={({ isActive }) => ({
                display: "flex", alignItems: "center", gap: "10px",
                padding: "7px 12px", margin: "1px 8px", borderRadius: "6px",
                color: isActive ? "#6c63ff" : "#9ba3c0",
                background: isActive ? "rgba(108,99,255,0.15)" : "transparent",
                textDecoration: "none", fontSize: "12.5px",
                borderLeft: isActive ? "3px solid #6c63ff" : "3px solid transparent",
              })}>
              <span style={{ fontSize: "14px" }}>{item.icon}</span>{item.label}
            </NavLink>
          )
        })}
      </div>
      <div style={{ padding: "12px 8px", borderTop: "1px solid rgba(255,255,255,0.07)" }}>
        <div onClick={() => { logout(); navigate("/login") }}
          style={{ padding: "8px 10px", borderRadius: "8px", background: "#14161f", display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }}>
          <div style={{ width: "30px", height: "30px", borderRadius: "50%", background: "#6c63ff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700, color: "#fff" }}>{initials}</div>
          <div>
            <div style={{ fontSize: "12px", fontWeight: 500 }}>{user?.full_name || "Admin"}</div>
            <div style={{ fontSize: "10px", color: "#636882" }}>{(user?.role || "super_admin").replace(/_/g, " ")}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
