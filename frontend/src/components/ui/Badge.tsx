type BadgeVariant = "success" | "warning" | "danger" | "info" | "purple" | "gray"

const variants: Record<BadgeVariant, { bg: string; color: string }> = {
  success: { bg: "rgba(0,229,160,0.12)", color: "#00e5a0" },
  warning: { bg: "rgba(255,193,7,0.12)", color: "#ffc107" },
  danger:  { bg: "rgba(255,107,107,0.12)", color: "#ff6b6b" },
  info:    { bg: "rgba(79,195,247,0.12)", color: "#4fc3f7" },
  purple:  { bg: "rgba(108,99,255,0.12)", color: "#6c63ff" },
  gray:    { bg: "rgba(255,255,255,0.06)", color: "#9ba3c0" },
}

export function Badge({ children, variant = "gray" }: { children: React.ReactNode; variant?: BadgeVariant }) {
  const v = variants[variant]
  return (
    <span style={{ padding: "3px 8px", borderRadius: "4px", fontSize: "10.5px", fontWeight: 500, background: v.bg, color: v.color, display: "inline-flex", alignItems: "center" }}>
      {children}
    </span>
  )
}
