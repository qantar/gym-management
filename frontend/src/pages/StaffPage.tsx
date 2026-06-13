import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import { KpiCard } from "../components/ui/Card"
import toast from "react-hot-toast"

const ROLES = ["trainer","front_desk","sales_rep","branch_manager","accountant","hr_manager","inventory_manager"]
const DEPTS = ["Training","Operations","Sales","Finance","Management","HR"]
const EMP_TYPES = ["full_time","part_time","contract","freelance"]

export default function StaffPage() {
  const [addOpen, setAddOpen] = useState(false)
  const [detailStaff, setDetailStaff] = useState<any>(null)
  const [form, setForm] = useState({
    user_id: "", branch_id: 1, employee_id: "", department: "Training",
    designation: "", employment_type: "full_time", base_salary: "",
    commission_rate: "0", hire_date: "", national_id: "", certifications: "",
  })
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["staff"],
    queryFn: () => api.get("/api/v1/staff/?page_size=50").then(r => r.data),
  })

  const { data: payroll } = useQuery({
    queryKey: ["payroll-summary"],
    queryFn: () => api.get("/api/v1/staff/payroll/summary").then(r => r.data),
  })

  const createStaff = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/staff/", {
      ...p, user_id: parseInt(p.user_id), base_salary: parseFloat(p.base_salary),
      commission_rate: parseFloat(p.commission_rate),
    }).then(r => r.data),
    onSuccess: () => { toast.success("Employee added"); qc.invalidateQueries({ queryKey: ["staff"] }); setAddOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const updateKPI = useMutation({
    mutationFn: ({ id, kpi }: { id: number; kpi: number }) =>
      api.put(`/api/v1/staff/${id}`, { kpi_score: kpi }).then(r => r.data),
    onSuccess: () => { toast.success("KPI updated"); qc.invalidateQueries({ queryKey: ["staff"] }) },
  })

  const staffList = data?.items || []

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Staff Management</h1>
        <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>+ Add Employee</Btn>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"16px", marginBottom:"20px" }}>
        <KpiCard title="Total Staff" value={data?.total||0} color="#6c63ff" />
        <KpiCard title="Monthly Payroll" value={`SAR ${parseFloat(payroll?.total_monthly_salary||"0").toLocaleString()}`} color="#00e5a0" />
        <KpiCard title="Avg KPI Score" value={`${payroll?.avg_kpi_score||0}%`} color="#4fc3f7" />
        <KpiCard title="Departments" value={DEPTS.length} color="#ffc107" />
      </div>

      {/* Table */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
        {isLoading ? (
          <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading staff…</div>
        ) : (
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12.5px" }}>
              <thead>
                <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                  {["Employee ID","Department","Designation","Type","Salary","Commission","KPI Score","Actions"].map(h => (
                    <th key={h} style={{ padding:"10px 14px", textAlign:"left", color:"#636882", fontSize:"11px", textTransform:"uppercase", letterSpacing:"0.5px" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {staffList.map((s: any) => (
                  <tr key={s.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}
                    onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = "rgba(255,255,255,0.02)"}
                    onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = "transparent"}>
                    <td style={{ padding:"11px 14px", fontWeight:600, color:"#6c63ff" }}>{s.employee_id}</td>
                    <td style={{ padding:"11px 14px" }}><Badge variant="info">{s.department||"—"}</Badge></td>
                    <td style={{ padding:"11px 14px", color:"#9ba3c0" }}>{s.designation||"—"}</td>
                    <td style={{ padding:"11px 14px" }}><Badge variant="gray">{s.employment_type?.replace(/_/g," ")}</Badge></td>
                    <td style={{ padding:"11px 14px", fontWeight:600 }}>SAR {parseFloat(s.base_salary||"0").toLocaleString()}</td>
                    <td style={{ padding:"11px 14px", color:"#636882" }}>{parseFloat(s.commission_rate||"0")}%</td>
                    <td style={{ padding:"11px 14px" }}>
                      <div style={{ display:"flex", alignItems:"center", gap:"8px" }}>
                        <div style={{ flex:1, height:"4px", background:"#1f2235", borderRadius:"2px", overflow:"hidden" }}>
                          <div style={{ height:"4px", borderRadius:"2px", width:`${s.kpi_score||0}%`, background: parseFloat(s.kpi_score||0) > 85 ? "#00e5a0" : parseFloat(s.kpi_score||0) > 70 ? "#ffc107" : "#ff6b6b" }} />
                        </div>
                        <span style={{ fontSize:"11px", fontWeight:600, width:"32px" }}>{parseFloat(s.kpi_score||0).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td style={{ padding:"11px 14px" }}>
                      <div style={{ display:"flex", gap:"4px" }}>
                        <Btn size="sm" onClick={() => setDetailStaff(s)}>View</Btn>
                        <Btn size="sm" variant="success" onClick={() => { const v = prompt("New KPI score (0-100):"); if(v) updateKPI.mutate({ id: s.id, kpi: parseFloat(v) }) }}>KPI</Btn>
                      </div>
                    </td>
                  </tr>
                ))}
                {!staffList.length && (
                  <tr><td colSpan={8} style={{ padding:"40px", textAlign:"center", color:"#636882" }}>No staff records. Add your first employee.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Staff Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Employee">
        <FormRow cols={2}>
          <FormGroup label="User ID (from Users)"><input type="number" value={form.user_id} onChange={e => setForm(f=>({...f,user_id:e.target.value}))} placeholder="1" /></FormGroup>
          <FormGroup label="Employee ID"><input value={form.employee_id} onChange={e => setForm(f=>({...f,employee_id:e.target.value}))} placeholder="EMP-001" /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Department">
            <select value={form.department} onChange={e => setForm(f=>({...f,department:e.target.value}))}>
              {DEPTS.map(d => <option key={d} value={d}>{d}</option>)}
            </select>
          </FormGroup>
          <FormGroup label="Designation"><input value={form.designation} onChange={e => setForm(f=>({...f,designation:e.target.value}))} placeholder="Head Trainer" /></FormGroup>
        </FormRow>
        <FormRow cols={3}>
          <FormGroup label="Employment Type">
            <select value={form.employment_type} onChange={e => setForm(f=>({...f,employment_type:e.target.value}))}>
              {EMP_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g," ")}</option>)}
            </select>
          </FormGroup>
          <FormGroup label="Base Salary (SAR)"><input type="number" value={form.base_salary} onChange={e => setForm(f=>({...f,base_salary:e.target.value}))} placeholder="5000" /></FormGroup>
          <FormGroup label="Commission %"><input type="number" value={form.commission_rate} onChange={e => setForm(f=>({...f,commission_rate:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Hire Date"><input type="date" value={form.hire_date} onChange={e => setForm(f=>({...f,hire_date:e.target.value}))} /></FormGroup>
          <FormGroup label="National ID"><input value={form.national_id} onChange={e => setForm(f=>({...f,national_id:e.target.value}))} /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createStaff.mutate(form)}>Add Employee</Btn>
        </div>
      </Modal>

      {/* Staff Detail Modal */}
      {detailStaff && (
        <Modal open={!!detailStaff} onClose={() => setDetailStaff(null)} title={`Employee #${detailStaff.employee_id}`}>
          <div style={{ display:"grid", gap:"8px" }}>
            {[
              ["Employee ID", detailStaff.employee_id],
              ["Department", detailStaff.department||"—"],
              ["Designation", detailStaff.designation||"—"],
              ["Employment Type", (detailStaff.employment_type||"").replace(/_/g," ")],
              ["Base Salary", `SAR ${parseFloat(detailStaff.base_salary||0).toLocaleString()}`],
              ["Commission Rate", `${detailStaff.commission_rate||0}%`],
              ["KPI Score", `${parseFloat(detailStaff.kpi_score||0).toFixed(1)}%`],
              ["Hire Date", detailStaff.hire_date ? new Date(detailStaff.hire_date).toLocaleDateString() : "—"],
              ["Certifications", detailStaff.certifications||"—"],
            ].map(([l, v]) => (
              <div key={l} style={{ display:"flex", justifyContent:"space-between", padding:"7px 0", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ fontSize:"12px", color:"#636882" }}>{l}</span>
                <span style={{ fontSize:"12px", fontWeight:500 }}>{v}</span>
              </div>
            ))}
          </div>
          <div style={{ display:"flex", gap:"8px", marginTop:"16px" }}>
            <Btn onClick={() => { api.post(`/api/v1/staff/${detailStaff.id}/attendance?action=checkin`).then(() => toast.success("Checked in")); setDetailStaff(null) }}>Check In</Btn>
            <Btn onClick={() => { api.post(`/api/v1/staff/${detailStaff.id}/attendance?action=checkout`).then(() => toast.success("Checked out")); setDetailStaff(null) }}>Check Out</Btn>
            <Btn onClick={() => setDetailStaff(null)} style={{ marginLeft:"auto" }}>Close</Btn>
          </div>
        </Modal>
      )}
    </div>
  )
}
