import { useQuery } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Card } from "../components/ui/Card"

const PAGE_CONFIG: Record<string, { endpoint: string; label: string; fields: string[] }> = {
  BillingPage:    { endpoint: "/api/v1/invoices/",           label: "Billing",    fields: ["invoice_number","status","total","amount_due","due_date"] },
  CRMPage:        { endpoint: "/api/v1/leads/",              label: "CRM Leads",  fields: ["full_name","phone","source","status","expected_value"] },
  InventoryPage:  { endpoint: "/api/v1/inventory/products",  label: "Inventory",  fields: ["sku","name","category","stock_quantity","sell_price"] },
  StaffPage:      { endpoint: "/api/v1/staff/",              label: "Staff",      fields: ["id","department","designation","kpi_score"] },
  AttendancePage: { endpoint: "/api/v1/attendance/today?branch_id=1", label: "Attendance", fields: ["total_checkins","in_gym_now","date"] },
  ReportsPage:    { endpoint: "/api/v1/reports/membership-summary", label: "Reports", fields: [] },
  BranchesPage:   { endpoint: "/api/v1/branches/",           label: "Branches",   fields: ["name","city","capacity","is_active"] },
  SettingsPage:   { endpoint: "",                            label: "Settings",   fields: [] },
}

export default function SettingsPage() {
  const cfg = PAGE_CONFIG["SettingsPage"] || { endpoint: "", label: "SettingsPage", fields: [] }
  
  const { data, isLoading } = useQuery({
    queryKey: ["SettingsPage"],
    queryFn: () => cfg.endpoint ? api.get(cfg.endpoint).then(r => r.data) : Promise.resolve(null),
    enabled: !!cfg.endpoint,
  })

  const items = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : data ? [data] : []

  return (
    <div>
      <div style={{ fontSize: "15px", fontWeight: 600, marginBottom: "20px" }}>{cfg.label}</div>
      <Card>
        {isLoading ? (
          <div style={{ color: "#636882", padding: "40px", textAlign: "center" }}>Loading {cfg.label}...</div>
        ) : cfg.fields.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                  {cfg.fields.map(f => (
                    <th key={f} style={{ padding: "10px 14px", textAlign: "left", color: "#636882", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                      {f.replace(/_/g, " ")}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {items.map((item: any, i: number) => (
                  <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                    {cfg.fields.map(f => (
                      <td key={f} style={{ padding: "11px 14px", color: "#9ba3c0" }}>{String(item[f] ?? "—")}</td>
                    ))}
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={cfg.fields.length} style={{ padding: "40px", textAlign: "center", color: "#636882" }}>No {cfg.label.toLowerCase()} found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ color: "#636882", padding: "20px" }}>
            <pre style={{ fontSize: "12px", whiteSpace: "pre-wrap" }}>{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </Card>
    </div>
  )
}
