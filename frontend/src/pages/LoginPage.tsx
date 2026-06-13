import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useAuthStore } from "../stores/auth"
import toast from "react-hot-toast"

export default function LoginPage() {
  const [email, setEmail] = useState("admin@gymos.sa")
  const [password, setPassword] = useState("Admin@123")
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(email, password)
      navigate("/dashboard")
    } catch {
      toast.error("Invalid credentials")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#0a0b0e" }}>
      <div style={{ width: "380px", background: "#0f1117", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px", padding: "40px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px" }}>
          <div style={{ width: "36px", height: "36px", background: "#6c63ff", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: "18px" }}>G</div>
          <div>
            <div style={{ fontSize: "18px", fontWeight: 600 }}>GymOS Enterprise</div>
            <div style={{ fontSize: "11px", color: "#636882" }}>Staff Portal — Authorized Access Only</div>
          </div>
        </div>
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: "16px" }}>
            <label style={{ fontSize: "11px", fontWeight: 500, color: "#636882", textTransform: "uppercase", letterSpacing: "0.5px", display: "block", marginBottom: "6px" }}>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </div>
          <div style={{ marginBottom: "24px" }}>
            <label style={{ fontSize: "11px", fontWeight: 500, color: "#636882", textTransform: "uppercase", letterSpacing: "0.5px", display: "block", marginBottom: "6px" }}>Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <button type="submit" disabled={loading} style={{ width: "100%", padding: "10px", borderRadius: "8px", border: "none", background: "#6c63ff", color: "#fff", fontWeight: 600, cursor: "pointer", fontSize: "14px", opacity: loading ? 0.7 : 1 }}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div style={{ marginTop: "20px", padding: "12px", background: "#14161f", borderRadius: "8px", fontSize: "11px", color: "#636882" }}>
          Default: admin@gymos.sa / Admin@123
        </div>
      </div>
    </div>
  )
}
