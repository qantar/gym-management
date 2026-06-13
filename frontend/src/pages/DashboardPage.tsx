import { useState, useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Card, KpiCard } from "../components/ui/Card"
import { Badge } from "../components/ui/Badge"
import {
  AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts"

const BRANCH_ID = 1
const TT = { background:"#1a1d2a", border:"1px solid rgba(255,255,255,0.1)", borderRadius:"6px", color:"#f0f2ff", fontSize:"12px" }
const STATIC_REVENUE = [
  { month:"Jan", revenue:380000 }, { month:"Feb", revenue:420000 },
  { month:"Mar", revenue:390000 }, { month:"Apr", revenue:460000 },
  { month:"May", revenue:510000 }, { month:"Jun", revenue:487200 },
]
const PIE_DATA = [
  { name:"Premium", value:45, color:"#6c63ff" }, { name:"Standard", value:31, color:"#4fc3f7" },
  { name:"Basic", value:16, color:"#00e5a0" }, { name:"Corporate", value:8, color:"#ffc107" },
]
const EXPIRING = [
  { name:"Noor Salem", plan:"Basic Monthly", expires:"Jun 15", value:"SAR 180" },
  { name:"Ali Hassan", plan:"Premium Annual", expires:"Jun 16", value:"SAR 2,400" },
  { name:"Rania Khalid", plan:"Standard Monthly", expires:"Jun 17", value:"SAR 280" },
  { name:"Tariq Al-Ghamdi", plan:"Premium Annual", expires:"Jun 18", value:"SAR 2,400" },
]

export default function DashboardPage() {
  const [liveTime, setLiveTime] = useState(new Date())
  useEffect(() => { const t = setInterval(() => setLiveTime(new Date()), 60000); return () => clearInterval(t) }, [])

  const { data: kpis } = useQuery({
    queryKey: ["dashboard-kpis", BRANCH_ID],
    queryFn: () => api.get(`/api/v1/dashboard/kpis?branch_id=${BRANCH_ID}`).then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: membership } = useQuery({
    queryKey: ["membership-summary-dash"],
    queryFn: () => api.get(`/api/v1/reports/membership-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: crmData } = useQuery({
    queryKey: ["crm-summary-dash"],
    queryFn: () => api.get(`/api/v1/reports/crm-summary?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const { data: schedules } = useQuery({
    queryKey: ["schedules-today"],
    queryFn: () => {
      const today = new Date(); today.setHours(0,0,0,0)
      const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate()+1)
      return api.get(`/api/v1/schedules/?branch_id=${BRANCH_ID}&date_from=${today.toISOString()}&date_to=${tomorrow.toISOString()}`).then(r => r.data)
    },
  })

  const { data: alerts } = useQuery({
    queryKey: ["low-stock-dash"],
    queryFn: () => api.get(`/api/v1/inventory/alerts/low-stock?branch_id=${BRANCH_ID}`).then(r => r.data),
  })

  const fmt = (v: any) => `SAR ${parseFloat(v||"0").toLocaleString("en-SA", { minimumFractionDigits:0 })}`
  const fmtTime = (iso: string) => new Date(iso).toLocaleTimeString("en-SA", { hour:"2-digit", minute:"2-digit" })

  const capColor = (e:number, c:number) => e>=c?"#ff6b6b":e/c>0.8?"#ffc107":"#00e5a0"

  return (
    <div>
      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <div>
          <div style={{ fontSize:"16px", fontWeight:600, marginBottom:"3px" }}>
            {liveTime.getHours() < 12 ? "Good morning" : liveTime.getHours() < 17 ? "Good afternoon" : "Good evening"} 👋
          </div>
          <div style={{ fontSize:"12px", color:"#636882" }}>
            {liveTime.toLocaleDateString("en-SA",{weekday:"long",year:"numeric",month:"long",day:"numeric"})}
            &nbsp;·&nbsp;
            <span style={{ color:"#00e5a0" }}>● Live</span>
          </div>
        </div>
        <button
          onClick={() => window.location.reload()}
          style={{ padding:"7px 16px", borderRadius:"6px", background:"#6c63ff", border:"none", color:"#fff", cursor:"pointer", fontSize:"12px", fontWeight:500 }}>
          + Add Member
        </button>
      </div>

      {/* KPI Strip */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:"14px", marginBottom:"20px" }}>
        <KpiCard title="Active Members"   value={(kpis?.active_members || membership?.active || 0).toLocaleString()} delta={`+${kpis?.new_members_month||0} this month`} color="#6c63ff" />
        <KpiCard title="Revenue Today"    value={fmt(kpis?.revenue_today)}    delta="↑ live"     color="#00e5a0" />
        <KpiCard title="Check-ins Today"  value={kpis?.checkins_today||0}     delta="visitors"   color="#4fc3f7" />
        <KpiCard title="Expiring (7d)"    value={kpis?.expiring_7d||89}       delta="↓ action needed" color="#ffc107" />
        <KpiCard title="Overdue Invoices" value={kpis?.overdue_invoices||0}   delta="needs collection" color="#ff6b6b" />
      </div>

      {/* Row 1: Revenue + Membership Pie */}
      <div style={{ display:"grid", gridTemplateColumns:"2fr 1fr", gap:"16px", marginBottom:"16px" }}>
        <Card>
          <div style={{ fontSize:"13px", fontWeight:600, marginBottom:"4px" }}>Revenue Overview</div>
          <div style={{ fontSize:"11px", color:"#636882", marginBottom:"16px" }}>Monthly billed revenue · Al Malaz Branch</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={STATIC_REVENUE}>
              <defs>
                <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6c63ff" stopOpacity={0.35}/>
                  <stop offset="95%" stopColor="#6c63ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)"/>
              <XAxis dataKey="month" stroke="#636882" tick={{fontSize:11}}/>
              <YAxis stroke="#636882" tick={{fontSize:11}} tickFormatter={v=>`${v/1000}k`}/>
              <Tooltip contentStyle={TT} formatter={(v:any)=>[`SAR ${Number(v).toLocaleString()}`,"Revenue"]}/>
              <Area type="monotone" dataKey="revenue" stroke="#6c63ff" fill="url(#rg)" strokeWidth={2}/>
            </AreaChart>
          </ResponsiveContainer>
        </Card>

        <Card>
          <div style={{ fontSize:"13px", fontWeight:600, marginBottom:"16px" }}>Membership Mix</div>
          <div style={{ display:"flex", flexDirection:"column", alignItems:"center" }}>
            <PieChart width={140} height={140}>
              <Pie data={PIE_DATA} cx={65} cy={65} innerRadius={42} outerRadius={62} dataKey="value" strokeWidth={0}>
                {PIE_DATA.map((d,i)=><Cell key={i} fill={d.color}/>)}
              </Pie>
            </PieChart>
            <div style={{ width:"100%", marginTop:"10px" }}>
              {PIE_DATA.map(d=>(
                <div key={d.name} style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"6px" }}>
                  <div style={{ width:"8px", height:"8px", borderRadius:"2px", background:d.color, flexShrink:0}}/>
                  <span style={{ flex:1, fontSize:"11px", color:"#9ba3c0" }}>{d.name}</span>
                  <span style={{ fontSize:"12px", fontWeight:600, color:d.color }}>{d.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Row 2: Today's Classes + CRM Pipeline + Low Stock */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:"16px", marginBottom:"16px" }}>
        <Card>
          <div style={{ fontSize:"13px", fontWeight:600, marginBottom:"12px" }}>Today's Classes</div>
          <div style={{ display:"flex", flexDirection:"column", gap:"8px" }}>
            {(Array.isArray(schedules) ? schedules : []).slice(0,5).map((c:any)=>(
              <div key={c.id} style={{ display:"flex", alignItems:"center", gap:"10px", padding:"8px 10px", background:"#14161f", borderLeft:`3px solid ${c.color}`, borderRadius:"0 6px 6px 0" }}>
                <div style={{ width:"48px", flexShrink:0 }}>
                  <div style={{ fontSize:"12px", fontWeight:600 }}>{fmtTime(c.start_time)}</div>
                </div>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:"12px", fontWeight:500 }}>{c.name}</div>
                  <div style={{ fontSize:"10px", color:"#636882" }}>{c.room}</div>
                </div>
                <div style={{ fontSize:"11px", fontWeight:600, color:capColor(c.enrolled,c.capacity) }}>{c.enrolled}/{c.capacity}</div>
              </div>
            ))}
            {(!schedules || (Array.isArray(schedules) && schedules.length===0)) && (
              <div style={{ textAlign:"center", color:"#636882", padding:"20px", fontSize:"12px" }}>No classes today</div>
            )}
          </div>
        </Card>

        <Card>
          <div style={{ fontSize:"13px", fontWeight:600, marginBottom:"12px" }}>CRM Pipeline</div>
          {["new","contacted","trial","proposal","won"].map((stage,i)=>{
            const colors = ["#4fc3f7","#ffc107","#ff9800","#6c63ff","#00e5a0"]
            const count = crmData?.[stage] || 0
            const max = Math.max(...["new","contacted","trial","proposal","won"].map(s=>crmData?.[s]||0), 1)
            return (
              <div key={stage} style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"10px" }}>
                <span style={{ width:"70px", fontSize:"11px", color:"#636882", textTransform:"capitalize" }}>{stage}</span>
                <div style={{ flex:1, height:"6px", background:"#1f2235", borderRadius:"3px", overflow:"hidden" }}>
                  <div style={{ height:"6px", borderRadius:"3px", background:colors[i], width:`${(count/max)*100}%`, transition:"width 0.5s" }}/>
                </div>
                <span style={{ width:"24px", fontSize:"12px", fontWeight:600, textAlign:"right", color:colors[i] }}>{count}</span>
              </div>
            )
          })}
          <div style={{ marginTop:"12px", paddingTop:"10px", borderTop:"1px solid rgba(255,255,255,0.05)", display:"flex", justifyContent:"space-between", fontSize:"12px" }}>
            <span style={{ color:"#636882" }}>Conversion</span>
            <span style={{ fontWeight:600, color:"#00e5a0" }}>{crmData?.conversion_rate||0}%</span>
          </div>
        </Card>

        <Card>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"12px" }}>
            <div style={{ fontSize:"13px", fontWeight:600 }}>⚠️ Low Stock</div>
            <Badge variant="warning">{(alerts||[]).length}</Badge>
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:"6px" }}>
            {(alerts||[]).slice(0,6).map((a:any)=>(
              <div key={a.id} style={{ display:"flex", alignItems:"center", gap:"8px", padding:"7px 10px", background:"#14161f", borderRadius:"6px" }}>
                <div style={{ flex:1 }}>
                  <div style={{ fontSize:"12px", fontWeight:500 }}>{a.name}</div>
                  <div style={{ fontSize:"10px", color:"#636882" }}>{a.sku}</div>
                </div>
                <Badge variant={a.status==="out_of_stock"?"danger":"warning"}>
                  {a.stock} left
                </Badge>
              </div>
            ))}
            {(alerts||[]).length===0 && (
              <div style={{ textAlign:"center", color:"#636882", padding:"20px", fontSize:"12px" }}>All stock levels OK ✓</div>
            )}
          </div>
        </Card>
      </div>

      {/* Row 3: Expiring Members */}
      <Card>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"14px" }}>
          <div style={{ fontSize:"13px", fontWeight:600 }}>⏰ Memberships Expiring This Week</div>
          <button onClick={()=>{}} style={{ padding:"5px 12px", borderRadius:"5px", background:"#6c63ff", border:"none", color:"#fff", cursor:"pointer", fontSize:"11px" }}>
            Send Bulk Reminder
          </button>
        </div>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12.5px" }}>
          <thead>
            <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
              {["Member","Plan","Expires","Value","Action"].map(h=>(
                <th key={h} style={{ padding:"8px 12px", textAlign:"left", color:"#636882", fontSize:"11px", textTransform:"uppercase", letterSpacing:"0.5px" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {EXPIRING.map((m,i)=>(
              <tr key={i} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                <td style={{ padding:"10px 12px", fontWeight:600 }}>{m.name}</td>
                <td style={{ padding:"10px 12px" }}><Badge variant="purple">{m.plan}</Badge></td>
                <td style={{ padding:"10px 12px", color:"#ffc107" }}>{m.expires}</td>
                <td style={{ padding:"10px 12px", fontWeight:600 }}>{m.value}</td>
                <td style={{ padding:"10px 12px" }}>
                  <div style={{ display:"flex", gap:"4px" }}>
                    <button style={{ padding:"3px 10px", borderRadius:"4px", background:"rgba(108,99,255,0.15)", border:"1px solid rgba(108,99,255,0.3)", color:"#6c63ff", cursor:"pointer", fontSize:"11px" }}>Remind</button>
                    <button style={{ padding:"3px 10px", borderRadius:"4px", background:"rgba(0,229,160,0.12)", border:"1px solid rgba(0,229,160,0.3)", color:"#00e5a0", cursor:"pointer", fontSize:"11px" }}>Renew</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
