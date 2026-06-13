import { useQuery } from "@tanstack/react-query"
import { api } from "../lib/api"
import { KpiCard } from "../components/ui/Card"
import { Card } from "../components/ui/Card"
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts"

const revenueData = [
  { month: "Jan", revenue: 380000, target: 400000 },
  { month: "Feb", revenue: 420000, target: 410000 },
  { month: "Mar", revenue: 390000, target: 430000 },
  { month: "Apr", revenue: 460000, target: 440000 },
  { month: "May", revenue: 510000, target: 480000 },
  { month: "Jun", revenue: 487200, target: 490000 },
]

const membershipData = [
  { name: "Premium", value: 45, color: "#6c63ff" },
  { name: "Standard", value: 31, color: "#4fc3f7" },
  { name: "Basic", value: 16, color: "#00e5a0" },
  { name: "Corporate", value: 8, color: "#ffc107" },
]

export default function DashboardPage() {
  const { data: kpis } = useQuery({
    queryKey: ["dashboard-kpis"],
    queryFn: () => api.get("/api/v1/dashboard/kpis").then(r => r.data),
    refetchInterval: 30000,
  })

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <div>
          <div style={{ fontSize: "14px", fontWeight: 600, marginBottom: "3px" }}>Good morning 👋</div>
          <div style={{ fontSize: "12px", color: "#636882" }}>Saturday, June 13, 2026</div>
        </div>
        <button style={{ padding: "7px 16px", borderRadius: "6px", background: "#6c63ff", border: "none", color: "#fff", cursor: "pointer", fontSize: "12px", fontWeight: 500 }}>+ Add Member</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: "16px", marginBottom: "20px" }}>
        <KpiCard title="Active Members" value={kpis?.active_members?.toLocaleString() || "2,847"} delta="↑ +124 this month" color="#6c63ff" />
        <KpiCard title="Revenue Today" value={`SAR ${Number(kpis?.revenue_today || 18420).toLocaleString()}`} delta="↑ +8.3% vs yesterday" color="#00e5a0" />
        <KpiCard title="Check-ins Today" value={kpis?.checkins_today || 347} delta="47 currently inside" color="#4fc3f7" />
        <KpiCard title="Expiring (7d)" value={kpis?.expiring_7d || 89} delta="↓ Needs attention" color="#ffc107" />
        <KpiCard title="Overdue Invoices" value={kpis?.overdue_invoices || 12} delta="SAR 34,200 total" color="#ff6b6b" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "20px" }}>
        <Card>
          <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "16px" }}>Revenue Overview</div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={revenueData}>
              <defs>
                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6c63ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6c63ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" stroke="#636882" tick={{ fontSize: 11 }} />
              <YAxis stroke="#636882" tick={{ fontSize: 11 }} tickFormatter={v => `${v/1000}k`} />
              <Tooltip contentStyle={{ background: "#1a1d2a", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "6px", color: "#f0f2ff" }} formatter={(v: number) => [`SAR ${v.toLocaleString()}`, ""]} />
              <Area type="monotone" dataKey="revenue" stroke="#6c63ff" fill="url(#revGrad)" strokeWidth={2} />
              <Area type="monotone" dataKey="target" stroke="rgba(255,255,255,0.2)" fill="none" strokeDasharray="5 5" strokeWidth={1} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "16px" }}>Membership Distribution</div>
          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            <PieChart width={160} height={160}>
              <Pie data={membershipData} cx={75} cy={75} innerRadius={50} outerRadius={72} dataKey="value" strokeWidth={0}>
                {membershipData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
              </Pie>
            </PieChart>
            <div style={{ flex: 1 }}>
              {membershipData.map(d => (
                <div key={d.name} style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                  <div style={{ width: "10px", height: "10px", borderRadius: "2px", background: d.color, flexShrink: 0 }} />
                  <span style={{ flex: 1, fontSize: "12px", color: "#9ba3c0" }}>{d.name}</span>
                  <span style={{ fontSize: "12px", fontWeight: 600, color: d.color }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "16px" }}>⚠️ Members Expiring This Week</div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
              {["Member", "Plan", "Expires", "Value", "Action"].map(h => (
                <th key={h} style={{ padding: "8px 12px", textAlign: "left", color: "#636882", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ["Noor Salem", "Basic Monthly", "Jun 15", "SAR 180"],
              ["Ali Hassan", "Premium Annual", "Jun 16", "SAR 2,400"],
              ["Rania Khalid", "Standard Monthly", "Jun 17", "SAR 280"],
            ].map(([name, plan, exp, val]) => (
              <tr key={name} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                <td style={{ padding: "10px 12px", fontWeight: 600 }}>{name}</td>
                <td style={{ padding: "10px 12px", color: "#9ba3c0" }}>{plan}</td>
                <td style={{ padding: "10px 12px", color: "#ffc107" }}>{exp}</td>
                <td style={{ padding: "10px 12px", fontWeight: 600 }}>{val}</td>
                <td style={{ padding: "10px 12px" }}>
                  <button style={{ padding: "4px 10px", borderRadius: "5px", background: "#6c63ff", border: "none", color: "#fff", cursor: "pointer", fontSize: "11px" }}>Renew</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
