import { ReactNode } from "react"

export function FormRow({ children, cols = 1 }: { children: ReactNode; cols?: number }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: "16px", marginBottom: "16px" }}>
      {children}
    </div>
  )
}

export function FormGroup({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
      <label style={{ fontSize: "11px", fontWeight: 500, color: "#636882", textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</label>
      {children}
    </div>
  )
}

export function Btn({ children, onClick, variant = "default", size = "md", type = "button" }: {
  children: ReactNode; onClick?: () => void; variant?: "default" | "primary" | "success" | "danger"; size?: "sm" | "md"; type?: "button" | "submit"
}) {
  const colors = {
    default: { bg: "transparent", border: "rgba(255,255,255,0.12)", color: "#f0f2ff" },
    primary: { bg: "#6c63ff", border: "#6c63ff", color: "#fff" },
    success: { bg: "rgba(0,229,160,0.15)", border: "#00e5a0", color: "#00e5a0" },
    danger:  { bg: "rgba(255,107,107,0.15)", border: "#ff6b6b", color: "#ff6b6b" },
  }
  const c = colors[variant]
  const padding = size === "sm" ? "4px 10px" : "7px 14px"
  const fontSize = size === "sm" ? "11px" : "12px"
  return (
    <button type={type} onClick={onClick} style={{ padding, fontSize, borderRadius: "6px", border: `1px solid ${c.border}`, background: c.bg, color: c.color, cursor: "pointer", fontFamily: "inherit" }}>
      {children}
    </button>
  )
}
