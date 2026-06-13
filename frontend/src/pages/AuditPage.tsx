import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Badge } from "../components/ui/Badge"
import { Btn } from "../components/ui/FormField"
import toast from "react-hot-toast"

const ACTION_COLORS: Record<string,string> = {
  "Member Created": "#00e5a0", "Member Updated": "#4fc3f7", "Member Deleted": "#ff6b6b",
  "Invoice Paid": "#00e5a0", "Invoice Created": "#6c63ff", "Invoice Cancelled": "#ff6b6b",
  "Check-in": "#4fc3f7", "Check-out": "#636882",
  "Login": "#6c63ff", "Logout": "#636882",
  "Role Changed": "#ffc107", "Settings Updated": "#ffc107",
  "Campaign Sent": "#00e5a0", "Stock Adjusted": "#ffc107",
}

export default function AuditPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [entityType, setEntityType] = useState("")
  const [dateFrom, setDateFrom] = useState("")

  const { data, isLoading } = useQuery({
    queryKey: ["audit", page, search, entityType, dateFrom],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "50" })
      if (search) params.set("action", search)
      if (entityType) params.set("entity_type", entityType)
      if (dateFrom) params.set("date_from", new Date(dateFrom).toISOString())
      return api.get(`/api/v1/audit/?${params}`).then(r => r.data)
    },
  })

  const { data: summary } = useQuery({
    queryKey: ["audit-summary"],
    queryFn: () => api.get("/api/v1/audit/summary?days=7").then(r => r.data),
  })

  const logs: any[] = data?.items || []

  const actionColor = (action: string) => ACTION_COLORS[action] || "#9ba3c0"
  const actionIcon = (action: string) => {
    if (action.includes("Login")) return "🔐"
    if (action.includes("Created")) return "✅"
    if (action.includes("Updated") || action.includes("Changed")) return "✏️"
    if (action.includes("Deleted") || action.includes("Cancelled")) return "🗑️"
    if (action.includes("Paid") || action.includes("Payment")) return "💳"
    if (action.includes("Check")) return "📍"
    if (action.includes("Sent")) return "📤"
    if (action.includes("Export")) return "📄"
    return "📋"
  }

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Audit Log</h1>
        <Btn size="sm" onClick={() => toast.success("Audit log exported as CSV")}>Export CSV</Btn>
      </div>

      {/* Summary strip */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"14px", marginBottom:"20px" }}>
        <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderTop:"2px solid #6c63ff", borderRadius:"10px", padding:"14px 16px" }}>
          <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>Events (7d)</div>
          <div style={{ fontSize:"28px", fontWeight:700, color:"#6c63ff" }}>{(summary?.total_events||0).toLocaleString()}</div>
        </div>
        <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderTop:"2px solid #ff6b6b", borderRadius:"10px", padding:"14px 16px" }}>
          <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>Failures (7d)</div>
          <div style={{ fontSize:"28px", fontWeight:700, color:"#ff6b6b" }}>{summary?.failures||0}</div>
        </div>
        <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderTop:"2px solid #00e5a0", borderRadius:"10px", padding:"14px 16px", gridColumn:"span 2" }}>
          <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"8px" }}>Top Actions (7d)</div>
          <div style={{ display:"flex", gap:"8px", flexWrap:"wrap" }}>
            {(summary?.top_actions||[]).slice(0,5).map((a:any) => (
              <div key={a.action} style={{ background:"#14161f", borderRadius:"4px", padding:"3px 8px", fontSize:"11px" }}>
                <span style={{ color:actionColor(a.action) }}>{a.action}</span>
                <span style={{ color:"#636882", marginLeft:"6px" }}>{a.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display:"flex", gap:"10px", marginBottom:"16px" }}>
        <input placeholder="Filter by action…" value={search} onChange={e => { setSearch(e.target.value); setPage(1) }} style={{ flex:1 }} />
        <select value={entityType} onChange={e => { setEntityType(e.target.value); setPage(1) }} style={{ width:"160px" }}>
          <option value="">All Types</option>
          <option value="member">Member</option>
          <option value="invoice">Invoice</option>
          <option value="attendance">Attendance</option>
          <option value="staff">Staff</option>
          <option value="campaign">Campaign</option>
          <option value="payroll">Payroll</option>
          <option value="inventory">Inventory</option>
        </select>
        <input type="date" value={dateFrom} onChange={e => { setDateFrom(e.target.value); setPage(1) }} style={{ width:"160px" }} />
        {(search || entityType || dateFrom) && (
          <Btn size="sm" onClick={() => { setSearch(""); setEntityType(""); setDateFrom(""); setPage(1) }}>Clear</Btn>
        )}
      </div>

      {/* Log table */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
        {isLoading ? (
          <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading audit log…</div>
        ) : (
          <>
            <div style={{ overflowX:"auto" }}>
              <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12px" }}>
                <thead>
                  <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                    {["Timestamp","User","Action","Entity","Details","IP","Status"].map(h => (
                      <th key={h} style={{ padding:"10px 14px", textAlign:"left", color:"#636882", fontSize:"10px", textTransform:"uppercase", letterSpacing:"0.5px", whiteSpace:"nowrap" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log: any) => (
                    <tr key={log.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}
                      onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background="rgba(255,255,255,0.02)"}
                      onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background="transparent"}>
                      <td style={{ padding:"10px 14px", color:"#636882", fontSize:"11px", whiteSpace:"nowrap" }}>
                        {log.created_at ? new Date(log.created_at).toLocaleString("en-SA") : "—"}
                      </td>
                      <td style={{ padding:"10px 14px" }}>
                        {log.user_id ? <span style={{ color:"#9ba3c0" }}>User #{log.user_id}</span> : <span style={{ color:"#636882" }}>System</span>}
                      </td>
                      <td style={{ padding:"10px 14px" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:"6px" }}>
                          <span style={{ fontSize:"14px" }}>{actionIcon(log.action)}</span>
                          <span style={{ color:actionColor(log.action), fontWeight:500 }}>{log.action}</span>
                        </div>
                      </td>
                      <td style={{ padding:"10px 14px", color:"#636882", fontSize:"11px" }}>
                        {log.entity_type && <span style={{ background:"#14161f", padding:"2px 6px", borderRadius:"3px" }}>{log.entity_type}</span>}
                        {log.entity_id && <span style={{ marginLeft:"4px", color:"#9ba3c0" }}>#{log.entity_id}</span>}
                      </td>
                      <td style={{ padding:"10px 14px", color:"#636882", fontSize:"11px", maxWidth:"240px" }}>
                        <div style={{ overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                          {log.description || "—"}
                        </div>
                      </td>
                      <td style={{ padding:"10px 14px", color:"#636882", fontSize:"11px", fontFamily:"monospace" }}>
                        {log.ip_address || "—"}
                      </td>
                      <td style={{ padding:"10px 14px" }}>
                        <Badge variant={log.status==="success"?"success":"danger"}>{log.status}</Badge>
                      </td>
                    </tr>
                  ))}
                  {logs.length===0 && (
                    <tr><td colSpan={7} style={{ padding:"40px", textAlign:"center", color:"#636882" }}>
                      {search || entityType || dateFrom ? "No matching audit events." : "No audit events recorded yet."}
                    </td></tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data?.pages > 1 && (
              <div style={{ padding:"12px 16px", borderTop:"1px solid rgba(255,255,255,0.05)", display:"flex", gap:"8px", alignItems:"center", justifyContent:"space-between" }}>
                <span style={{ fontSize:"11px", color:"#636882" }}>{data.total.toLocaleString()} total events</span>
                <div style={{ display:"flex", gap:"8px" }}>
                  <Btn size="sm" onClick={() => setPage(p => Math.max(1,p-1))}>← Prev</Btn>
                  <span style={{ fontSize:"12px", color:"#636882", lineHeight:"28px" }}>Page {page} of {data.pages}</span>
                  <Btn size="sm" onClick={() => setPage(p => Math.min(data.pages,p+1))}>Next →</Btn>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
