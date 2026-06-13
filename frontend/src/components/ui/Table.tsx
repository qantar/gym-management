import { ReactNode } from "react"

export function Table({ children }: { children: ReactNode }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
        {children}
      </table>
    </div>
  )
}

export function Th({ children }: { children: ReactNode }) {
  return <th style={{ padding: "10px 14px", textAlign: "left", color: "#636882", fontWeight: 500, fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: "1px solid rgba(255,255,255,0.07)" }}>{children}</th>
}

export function Td({ children, style }: { children: ReactNode; style?: React.CSSProperties }) {
  return <td style={{ padding: "11px 14px", borderBottom: "1px solid rgba(255,255,255,0.03)", color: "#9ba3c0", verticalAlign: "middle", ...style }}>{children}</td>
}
