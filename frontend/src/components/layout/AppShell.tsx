import { Outlet } from "react-router-dom"
import Sidebar from "./Sidebar"
import Header from "./Header"

export default function AppShell() {
  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      <Sidebar />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", marginLeft: "220px" }}>
        <Header />
        <main style={{ flex: 1, overflowY: "auto", padding: "24px", background: "#0a0b0e" }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
