import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { api } from "../lib/api"
import { useAuthStore } from "../stores/auth"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import toast from "react-hot-toast"

const TABS = ["General","Security","Roles","Notifications","Billing","About"]

const ROLES = [
  { name:"Super Admin",    perms:"Full access to everything",                    variant:"danger" as const },
  { name:"Owner",          perms:"Business oversight, all reports",              variant:"danger" as const },
  { name:"Regional Mgr",  perms:"Multi-branch management & reports",            variant:"warning" as const },
  { name:"Branch Manager", perms:"Single branch operations",                    variant:"warning" as const },
  { name:"Front Desk",     perms:"Check-in, members, basic billing",            variant:"info" as const },
  { name:"Trainer",        perms:"Schedule, assigned members, attendance",      variant:"info" as const },
  { name:"Accountant",     perms:"Finance, invoices, reports",                  variant:"purple" as const },
  { name:"Sales Rep",      perms:"CRM, leads, membership sales",                variant:"success" as const },
  { name:"Inventory Mgr",  perms:"Inventory, POS, purchase orders",             variant:"gray" as const },
  { name:"HR Manager",     perms:"Staff, payroll, recruitment",                 variant:"gray" as const },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("General")
  const [gymName, setGymName] = useState("FitZone Elite Gym")
  const [taxRate, setTaxRate] = useState("15")
  const [currency, setCurrency] = useState("SAR")
  const [smsTemplate, setSmsTemplate] = useState("Hi {name}, your {plan} expires on {date}. Renew at our desk or call +966-XX-XXXXXX.")
  const [emailTemplate, setEmailTemplate] = useState("Dear {name}, invoice #{invoice_id} of {amount} SAR is due on {date}.")
  const [mfa, setMfa] = useState(true)
  const [sessionTimeout, setSessionTimeout] = useState("30")
  const [auditLogging, setAuditLogging] = useState(true)
  const { user } = useAuthStore()

  const tabStyle = (t: string): React.CSSProperties => ({
    padding:"7px 16px", borderRadius:"5px", cursor:"pointer", fontSize:"12px",
    border:"none", background: activeTab===t ? "#1f2235" : "transparent",
    color: activeTab===t ? "#f0f2ff" : "#636882", fontFamily:"inherit", fontWeight: activeTab===t ? 500 : 400,
  })

  const section = (title: string, children: React.ReactNode) => (
    <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", padding:"20px", marginBottom:"16px" }}>
      <div style={{ fontSize:"13px", fontWeight:600, marginBottom:"16px", paddingBottom:"10px", borderBottom:"1px solid rgba(255,255,255,0.07)" }}>{title}</div>
      {children}
    </div>
  )

  return (
    <div>
      <h1 style={{ fontSize:"15px", fontWeight:600, marginBottom:"20px" }}>Settings</h1>

      {/* Tab bar */}
      <div style={{ display:"flex", gap:"2px", background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"8px", padding:"3px", marginBottom:"20px", width:"fit-content" }}>
        {TABS.map(t => <button key={t} onClick={() => setActiveTab(t)} style={tabStyle(t)}>{t}</button>)}
      </div>

      {activeTab === "General" && (
        <>
          {section("Gym Information", (
            <>
              <FormRow cols={2}>
                <FormGroup label="Gym Name"><input value={gymName} onChange={e => setGymName(e.target.value)} /></FormGroup>
                <FormGroup label="Currency">
                  <select value={currency} onChange={e => setCurrency(e.target.value)}>
                    <option value="SAR">SAR — Saudi Riyal</option>
                    <option value="AED">AED — UAE Dirham</option>
                    <option value="USD">USD — US Dollar</option>
                    <option value="EGP">EGP — Egyptian Pound</option>
                  </select>
                </FormGroup>
              </FormRow>
              <FormRow cols={2}>
                <FormGroup label="VAT Rate (%)"><input type="number" value={taxRate} onChange={e => setTaxRate(e.target.value)} /></FormGroup>
                <FormGroup label="Timezone">
                  <select>
                    <option>Asia/Riyadh (UTC+3)</option>
                    <option>Asia/Dubai (UTC+4)</option>
                    <option>UTC</option>
                  </select>
                </FormGroup>
              </FormRow>
              <Btn variant="primary" size="sm" onClick={() => toast.success("Settings saved")}>Save Changes</Btn>
            </>
          ))}
          {section("Localization", (
            <FormRow cols={2}>
              <FormGroup label="Date Format">
                <select><option>DD/MM/YYYY</option><option>MM/DD/YYYY</option><option>YYYY-MM-DD</option></select>
              </FormGroup>
              <FormGroup label="Language">
                <select><option>English</option><option>Arabic</option></select>
              </FormGroup>
            </FormRow>
          ))}
        </>
      )}

      {activeTab === "Security" && section("Security Settings", (
        <>
          <div style={{ display:"flex", flexDirection:"column", gap:"14px" }}>
            {[
              { label:"Multi-Factor Authentication", sub:"Require MFA for all staff logins", val:mfa, set:setMfa },
              { label:"Audit Logging", sub:"Log all user actions and system events", val:auditLogging, set:setAuditLogging },
            ].map(s => (
              <div key={s.label} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"12px", background:"#14161f", borderRadius:"8px" }}>
                <div>
                  <div style={{ fontSize:"13px", fontWeight:500 }}>{s.label}</div>
                  <div style={{ fontSize:"11px", color:"#636882", marginTop:"2px" }}>{s.sub}</div>
                </div>
                <button onClick={() => s.set(!s.val)}
                  style={{ width:"44px", height:"22px", borderRadius:"11px", border:"none", background:s.val?"#6c63ff":"#1f2235", cursor:"pointer", position:"relative", transition:"background 0.2s" }}>
                  <span style={{ position:"absolute", top:"3px", left:s.val?"24px":"3px", width:"16px", height:"16px", borderRadius:"50%", background:"#fff", transition:"left 0.2s", display:"block" }} />
                </button>
              </div>
            ))}
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"12px", background:"#14161f", borderRadius:"8px" }}>
              <div>
                <div style={{ fontSize:"13px", fontWeight:500 }}>Session Timeout</div>
                <div style={{ fontSize:"11px", color:"#636882", marginTop:"2px" }}>Auto-logout after inactivity</div>
              </div>
              <select value={sessionTimeout} onChange={e => setSessionTimeout(e.target.value)} style={{ width:"140px" }}>
                <option value="15">15 minutes</option>
                <option value="30">30 minutes</option>
                <option value="60">1 hour</option>
                <option value="240">4 hours</option>
              </select>
            </div>
          </div>
          <div style={{ marginTop:"16px" }}>
            <Btn variant="primary" size="sm" onClick={() => toast.success("Security settings saved")}>Save Security</Btn>
          </div>
        </>
      ))}

      {activeTab === "Roles" && section("Role Permissions Matrix", (
        <div style={{ display:"flex", flexDirection:"column", gap:"8px" }}>
          {ROLES.map(r => (
            <div key={r.name} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"10px 14px", background:"#14161f", borderRadius:"8px" }}>
              <div>
                <div style={{ fontSize:"13px", fontWeight:500 }}>{r.name}</div>
                <div style={{ fontSize:"11px", color:"#636882", marginTop:"1px" }}>{r.perms}</div>
              </div>
              <div style={{ display:"flex", gap:"8px", alignItems:"center" }}>
                <Badge variant={r.variant}>{r.variant === "danger" ? "Admin" : r.variant === "warning" ? "Manager" : r.variant === "info" ? "Staff" : "Limited"}</Badge>
                <Btn size="sm" onClick={() => toast("Permission editor coming soon")}>Edit</Btn>
              </div>
            </div>
          ))}
        </div>
      ))}

      {activeTab === "Notifications" && section("Message Templates", (
        <>
          <FormGroup label="Membership Expiry SMS">
            <textarea value={smsTemplate} onChange={e => setSmsTemplate(e.target.value)} rows={3} />
          </FormGroup>
          <div style={{ margin:"12px 0" }}>
            <FormGroup label="Invoice Reminder Email">
              <textarea value={emailTemplate} onChange={e => setEmailTemplate(e.target.value)} rows={3} />
            </FormGroup>
          </div>
          <div style={{ fontSize:"11px", color:"#636882", marginBottom:"12px" }}>
            Variables: {"{name}"} {"{plan}"} {"{date}"} {"{amount}"} {"{invoice_id}"} {"{branch}"}
          </div>
          <Btn variant="primary" size="sm" onClick={() => toast.success("Templates saved")}>Save Templates</Btn>
        </>
      ))}

      {activeTab === "About" && section("System Information", (
        <div style={{ display:"grid", gap:"10px" }}>
          {[
            ["Version", "GymOS Enterprise v1.0.0"],
            ["Build", "2026.06.13"],
            ["Current User", `${user?.full_name || "—"} (${user?.role || "—"})`],
            ["API", "http://localhost:8000/api/docs"],
            ["Database", "PostgreSQL 16"],
            ["Cache", "Redis 7"],
            ["Runtime", "Python 3.13 + FastAPI"],
            ["Frontend", "React 18 + Vite + TypeScript"],
          ].map(([l, v]) => (
            <div key={l} style={{ display:"flex", justifyContent:"space-between", padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
              <span style={{ fontSize:"12px", color:"#636882" }}>{l}</span>
              <span style={{ fontSize:"12px", fontWeight:500 }}>{v}</span>
            </div>
          ))}
          <div style={{ marginTop:"8px" }}>
            <Btn size="sm" onClick={() => window.open("http://localhost:8000/api/docs", "_blank")}>Open API Docs</Btn>
          </div>
        </div>
      ))}
    </div>
  )
}
