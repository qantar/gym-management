import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Card, KpiCard } from "../components/ui/Card"
import toast from "react-hot-toast"
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts"

const BRANCH_ID = 1
const TT_STYLE = { background:"#1a1d2a", border:"1px solid rgba(255,255,255,0.1)", borderRadius:"6px", color:"#f0f2ff", fontSize:"12px" }

export default function ReportsPage() {
  const [revenueRange, setRevenueRange] = useState("180")

  const { data: revenue } = useQuery({
    queryKey: ["report-revenue", revenueRange],
    queryFn: () => api.get(`/api/v1/reports/revenue?branch_id=${BRANCH_ID}&group_by=month`).then(r => r.data),
  })

  const { data: membership } = useQuery({
    queryKey: ["report-membership"],
    queryFn: () => api.get(`/api/v1/reports/membership-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: crm } = useQuery({
    queryKey: ["report-crm"],
    queryFn: () => api.get(`/api/v1/reports/crm-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: retention } = useQuery({
    queryKey: ["report-retention"],
    queryFn: () => api.get(`/api/v1/reports/retention?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: staffData } = useQuery({
    queryKey: ["report-staff"],
    queryFn: () => api.get(`/api/v1/reports/staff-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: invData } = useQuery({
    queryKey: ["report-inventory"],
    queryFn: () => api.get(`/api/v1/reports/inventory-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: pos } = useQuery({
    queryKey: ["report-pos"],
    queryFn: () => api.get(`/api/v1/reports/pos-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const membershipPieData = membership ? [
    { name: "Active", value: membership.active || 0, color: "#00e5a0" },
    { name: "Expired", value: membership.expired || 0, color: "#ff6b6b" },
    { name: "Frozen", value: membership.frozen || 0, color: "#ffc107" },
    { name: "Suspended", value: membership.suspended || 0, color: "#636882" },
  ] : []

  const crmFunnelData = crm ? [
    { stage: "New", count: crm.new || 0 },
    { stage: "Contacted", count: crm.contacted || 0 },
    { stage: "Trial", count: crm.trial || 0 },
    { stage: "Proposal", count: crm.proposal || 0 },
    { stage: "Won", count: crm.won || 0 },
  ] : []

  const exportReport = (type: string) => toast.success(`${type} report exported`, { icon: "📄" })

  const chartCard = (title: string, sub: string, children: React.ReactNode) => (
    <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", padding:"20px" }}>
      <div style={{ marginBottom:"16px" }}>
        <div style={{ fontSize:"13px", fontWeight:600 }}>{title}</div>
        <div style={{ fontSize:"11px", color:"#636882", marginTop:"2px" }}>{sub}</div>
      </div>
      {children}
    </div>
  )

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Business Intelligence</h1>
        <div style={{ display:"flex", gap:"8px" }}>
          <button onClick={() => exportReport("Full")} style={{ padding:"6px 12px", borderRadius:"6px", border:"1px solid rgba(255,255,255,0.12)", background:"transparent", color:"#9ba3c0", cursor:"pointer", fontSize:"12px" }}>Export All</button>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:"14px", marginBottom:"20px" }}>
        <KpiCard title="Total Revenue" value={`SAR ${parseFloat(revenue?.total_revenue||"0").toLocaleString()}`} delta={`${revenue?.total_invoices||0} invoices`} color="#6c63ff" />
        <KpiCard title="Active Members" value={membership?.active||0} delta={`+${membership?.new_this_month||0} this month`} color="#00e5a0" />
        <KpiCard title="Conversion Rate" value={`${crm?.conversion_rate||0}%`} delta={`${crm?.won||0} won`} color="#4fc3f7" />
        <KpiCard title="Staff Headcount" value={staffData?.headcount||0} delta={`Payroll SAR ${parseFloat(staffData?.total_monthly_salary||"0").toLocaleString()}`} color="#ffc107" />
        <KpiCard title="Inventory Value" value={`SAR ${parseFloat(invData?.inventory_value||"0").toLocaleString()}`} delta={`${invData?.out_of_stock_items||0} out of stock`} color="#ff6b6b" />
      </div>

      {/* Row 1: Revenue + Membership split */}
      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:"16px", marginBottom:"16px" }}>
        {chartCard("Revenue Trend", "Monthly invoiced revenue", (
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={revenue?.data||[]}>
              <defs>
                <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6c63ff" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6c63ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="period" stroke="#636882" tick={{ fontSize:10 }} tickFormatter={v => v?.slice?.(0,7)||v} />
              <YAxis stroke="#636882" tick={{ fontSize:10 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TT_STYLE} formatter={(v: any) => [`SAR ${parseFloat(v).toLocaleString()}`, "Revenue"]} />
              <Area type="monotone" dataKey="revenue" stroke="#6c63ff" fill="url(#rg)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        ))}

        {chartCard("Membership Status", "Current distribution", (
          <div style={{ display:"flex", flexDirection:"column", alignItems:"center" }}>
            <PieChart width={160} height={160}>
              <Pie data={membershipPieData} cx={75} cy={75} innerRadius={48} outerRadius={70} dataKey="value" strokeWidth={0}>
                {membershipPieData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Pie>
            </PieChart>
            <div style={{ width:"100%", marginTop:"8px" }}>
              {membershipPieData.map(d => (
                <div key={d.name} style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"6px" }}>
                  <div style={{ width:"8px", height:"8px", borderRadius:"2px", background:d.color, flexShrink:0 }} />
                  <span style={{ flex:1, fontSize:"11px", color:"#9ba3c0" }}>{d.name}</span>
                  <span style={{ fontSize:"12px", fontWeight:600 }}>{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Row 2: Retention + CRM Funnel + POS */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:"16px", marginBottom:"16px" }}>
        {chartCard("Member Retention", "Active members trend", (
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={retention||[]}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" stroke="#636882" tick={{ fontSize:10 }} />
              <YAxis stroke="#636882" tick={{ fontSize:10 }} />
              <Tooltip contentStyle={TT_STYLE} />
              <Line type="monotone" dataKey="active" stroke="#00e5a0" strokeWidth={2} dot={{ fill:"#00e5a0", r:3 }} />
            </LineChart>
          </ResponsiveContainer>
        ))}

        {chartCard("CRM Funnel", "Lead stage distribution", (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={crmFunnelData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis type="number" stroke="#636882" tick={{ fontSize:10 }} />
              <YAxis type="category" dataKey="stage" stroke="#636882" tick={{ fontSize:10 }} width={60} />
              <Tooltip contentStyle={TT_STYLE} />
              <Bar dataKey="count" fill="#6c63ff" radius={[0,4,4,0]} />
            </BarChart>
          </ResponsiveContainer>
        ))}

        {chartCard("POS Summary", "This month", (
          <div style={{ display:"grid", gap:"12px", marginTop:"8px" }}>
            {[
              { label:"Revenue", value:`SAR ${parseFloat(pos?.total_revenue||"0").toLocaleString()}`, color:"#6c63ff" },
              { label:"Transactions", value:pos?.transaction_count||0, color:"#00e5a0" },
              { label:"Avg Sale", value: pos?.transaction_count > 0 ? `SAR ${(parseFloat(pos?.total_revenue||"0")/pos?.transaction_count).toFixed(2)}` : "—", color:"#4fc3f7" },
              { label:"Inventory Items", value:`${invData?.sku_count||0} SKUs`, color:"#ffc107" },
              { label:"Low Stock", value:invData?.low_stock_items||0, color:"#ff6b6b" },
            ].map(r => (
              <div key={r.label} style={{ display:"flex", justifyContent:"space-between", padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ fontSize:"12px", color:"#636882" }}>{r.label}</span>
                <span style={{ fontSize:"13px", fontWeight:600, color:r.color as string }}>{r.value}</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      {/* Report Cards */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", padding:"20px" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"16px" }}>
          <div style={{ fontSize:"13px", fontWeight:600 }}>Export Reports</div>
          <button onClick={() => toast("Scheduling recurring report…")} style={{ padding:"5px 12px", borderRadius:"5px", border:"1px solid rgba(255,255,255,0.12)", background:"transparent", color:"#9ba3c0", cursor:"pointer", fontSize:"11px" }}>Schedule</button>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"10px" }}>
          {[
            { icon:"📊", title:"Membership", desc:"Active, expired, frozen", endpoint:"membership-summary" },
            { icon:"💰", title:"Revenue",    desc:"Billing & collections",   endpoint:"revenue" },
            { icon:"✅", title:"Attendance", desc:"Check-in analytics",      endpoint:"attendance-heatmap" },
            { icon:"👥", title:"Staff",      desc:"KPIs & payroll",          endpoint:"staff-summary" },
            { icon:"📦", title:"Inventory",  desc:"Stock & valuation",       endpoint:"inventory-summary" },
            { icon:"🎯", title:"CRM",        desc:"Leads & conversions",     endpoint:"crm-summary" },
            { icon:"🛒", title:"POS Sales",  desc:"Sales & products",        endpoint:"pos-summary" },
            { icon:"🏢", title:"Branches",   desc:"Multi-location analysis", endpoint:"" },
          ].map(r => (
            <div key={r.title} onClick={() => exportReport(r.title)}
              style={{ background:"#14161f", border:"1px solid rgba(255,255,255,0.05)", borderRadius:"8px", padding:"14px", cursor:"pointer", transition:"border-color 0.15s" }}
              onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(108,99,255,0.4)"}
              onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.05)"}>
              <div style={{ fontSize:"22px", marginBottom:"6px" }}>{r.icon}</div>
              <div style={{ fontSize:"12px", fontWeight:600, marginBottom:"3px" }}>{r.title}</div>
              <div style={{ fontSize:"11px", color:"#636882" }}>{r.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
