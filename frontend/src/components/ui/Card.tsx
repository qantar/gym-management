import { ReactNode } from "react"

interface CardProps {
  children: ReactNode
  style?: React.CSSProperties
  onClick?: () => void
}

export function Card({ children, style, onClick }: CardProps) {
  return (
    <div onClick={onClick} style={{
      background: "#14161f", border: "1px solid rgba(255,255,255,0.07)",
      borderRadius: "10px", padding: "18px 20px", ...style,
    }}>{children}</div>
  )
}

export function KpiCard({ title, value, delta, color = "#6c63ff" }: { title: string; value: string | number; delta?: string; color?: string }) {
  return (
    <Card style={{ borderTop: `2px solid ${color}` }}>
      <div style={{ fontSize: "11px", fontWeight: 600, color: "#636882", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "4px" }}>{title}</div>
      <div style={{ fontSize: "24px", fontWeight: 600, lineHeight: 1.2 }}>{value}</div>
      {delta && <div style={{ fontSize: "11px", color: delta.startsWith("↓") ? "#ff6b6b" : "#00e5a0", marginTop: "4px" }}>{delta}</div>}
    </Card>
  )
}
