import { ReactNode } from "react"

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  width?: number
}

export function Modal({ open, onClose, title, children, width = 580 }: ModalProps) {
  if (!open) return null
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#14161f", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "12px", padding: "24px", width, maxWidth: "95vw", maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
          <h2 style={{ fontSize: "16px", fontWeight: 600 }}>{title}</h2>
          <button onClick={onClose} style={{ background: "none", border: "none", color: "#636882", cursor: "pointer", fontSize: "20px", lineHeight: 1 }}>×</button>
        </div>
        {children}
      </div>
    </div>
  )
}
