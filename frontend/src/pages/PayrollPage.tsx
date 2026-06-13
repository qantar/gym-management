import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import { KpiCard } from "../components/ui/Card"
import toast from "react-hot-toast"

const statusVariant = (s: string): any => ({
  draft:"gray", approved:"info", paid:"success", cancelled:"danger"
}[s] || "gray")

export default function PayrollPage() {
  const [addOpen, setAddOpen] = useState(false)
  const [selectedRun, setSelectedRun] = useState<any>(null)
  const [slipEdit, setSlipEdit] = useState<any>(null)
  const [form, setForm] = useState({ period_start:"", period_end:"", pay_date:"", notes:"", branch_id: null as number|null })
  const [slipForm, setSlipForm] = useState({ bonus:"", commission:"", overtime_hours:"", overtime_pay:"", deduction_other:"", notes:"" })
  const qc = useQueryClient()

  const { data: summary } = useQuery({
    queryKey: ["payroll-summary"],
    queryFn: () => api.get("/api/v1/payroll/summary").then(r => r.data),
  })

  const { data: runs, isLoading } = useQuery({
    queryKey: ["payroll-runs"],
    queryFn: () => api.get("/api/v1/payroll/runs").then(r => r.data),
  })

  const { data: slips } = useQuery({
    queryKey: ["payroll-slips", selectedRun?.id],
    queryFn: () => selectedRun ? api.get(`/api/v1/payroll/runs/${selectedRun.id}/slips`).then(r => r.data) : null,
    enabled: !!selectedRun,
  })

  const createRun = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/payroll/runs", p).then(r => r.data),
    onSuccess: (d) => {
      toast.success(`Payroll run created — SAR ${parseFloat(d.total_net||"0").toLocaleString()} net`)
      qc.invalidateQueries({ queryKey: ["payroll-runs"] })
      qc.invalidateQueries({ queryKey: ["payroll-summary"] })
      setAddOpen(false)
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed to create payroll run"),
  })

  const approveRun = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/payroll/runs/${id}/approve`).then(r => r.data),
    onSuccess: (d) => { toast.success(d.message); qc.invalidateQueries({ queryKey: ["payroll-runs"] }); setSelectedRun((r:any) => r ? {...r, status:"approved"} : r) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Approval failed"),
  })

  const payRun = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/payroll/runs/${id}/pay`).then(r => r.data),
    onSuccess: (d) => { toast.success(d.message); qc.invalidateQueries({ queryKey: ["payroll-runs"] }); setSelectedRun((r:any) => r ? {...r, status:"paid"} : r) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Payment failed"),
  })

  const updateSlip = useMutation({
    mutationFn: ({ runId, slipId, data }: { runId:number; slipId:number; data:any }) =>
      api.put(`/api/v1/payroll/runs/${runId}/slips/${slipId}`, data).then(r => r.data),
    onSuccess: () => { toast.success("Slip updated"); qc.invalidateQueries({ queryKey: ["payroll-slips"] }); setSlipEdit(null) },
  })

  const runList: any[] = runs?.items || []
  const slipList: any[] = Array.isArray(slips) ? slips : []

  const fmtSAR = (v: any) => `SAR ${parseFloat(v||"0").toLocaleString("en-SA",{minimumFractionDigits:2})}`

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Payroll</h1>
        <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>Run Payroll</Btn>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"16px", marginBottom:"20px" }}>
        <KpiCard title="Headcount" value={summary?.headcount||0} color="#6c63ff" />
        <KpiCard title="Last Run Net" value={summary?.last_run_net ? fmtSAR(summary.last_run_net) : "—"} delta={summary?.last_run_date || ""} color="#00e5a0" />
        <KpiCard title="YTD Total" value={summary?.ytd_total ? fmtSAR(summary.ytd_total) : "—"} color="#4fc3f7" />
        <KpiCard title="Last Status" value={summary?.last_run_status || "—"} color="#ffc107" />
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"340px 1fr", gap:"16px" }}>
        {/* Run list */}
        <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
          <div style={{ padding:"14px 16px", borderBottom:"1px solid rgba(255,255,255,0.07)", fontSize:"13px", fontWeight:600 }}>Payroll Runs</div>
          {isLoading ? (
            <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading…</div>
          ) : runList.length === 0 ? (
            <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>
              No payroll runs yet.<br/><br/>
              <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>Create First Run</Btn>
            </div>
          ) : (
            <div style={{ overflow:"auto", maxHeight:"600px" }}>
              {runList.map((run: any) => (
                <div key={run.id} onClick={() => setSelectedRun(run)}
                  style={{ padding:"14px 16px", borderBottom:"1px solid rgba(255,255,255,0.05)", cursor:"pointer",
                    background:selectedRun?.id===run.id?"rgba(108,99,255,0.1)":"transparent",
                    borderLeft:`3px solid ${selectedRun?.id===run.id?"#6c63ff":"transparent"}` }}
                  onMouseEnter={e => selectedRun?.id!==run.id && ((e.currentTarget as HTMLDivElement).style.background="rgba(255,255,255,0.02)")}
                  onMouseLeave={e => selectedRun?.id!==run.id && ((e.currentTarget as HTMLDivElement).style.background="transparent")}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"6px" }}>
                    <div style={{ fontSize:"13px", fontWeight:600 }}>
                      {new Date(run.period_start).toLocaleDateString("en-SA",{month:"short"})} {new Date(run.period_start).getFullYear()}
                    </div>
                    <Badge variant={statusVariant(run.status)}>{run.status}</Badge>
                  </div>
                  <div style={{ fontSize:"11px", color:"#636882", marginBottom:"4px" }}>
                    {new Date(run.period_start).toLocaleDateString()} – {new Date(run.period_end).toLocaleDateString()}
                  </div>
                  <div style={{ display:"flex", justifyContent:"space-between", fontSize:"12px" }}>
                    <span style={{ color:"#636882" }}>Net</span>
                    <span style={{ fontWeight:600, color:"#00e5a0" }}>{fmtSAR(run.total_net)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Run detail */}
        <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
          {!selectedRun ? (
            <div style={{ padding:"60px", textAlign:"center", color:"#636882" }}>← Select a payroll run to view details</div>
          ) : (
            <>
              {/* Run header */}
              <div style={{ padding:"16px 20px", borderBottom:"1px solid rgba(255,255,255,0.07)", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                <div>
                  <div style={{ fontSize:"14px", fontWeight:600 }}>
                    {new Date(selectedRun.period_start).toLocaleDateString()} – {new Date(selectedRun.period_end).toLocaleDateString()}
                  </div>
                  <div style={{ fontSize:"11px", color:"#636882", marginTop:"2px" }}>Pay date: {new Date(selectedRun.pay_date).toLocaleDateString()}</div>
                </div>
                <div style={{ display:"flex", gap:"8px", alignItems:"center" }}>
                  <Badge variant={statusVariant(selectedRun.status)}>{selectedRun.status}</Badge>
                  {selectedRun.status==="draft" && <Btn size="sm" variant="primary" onClick={() => approveRun.mutate(selectedRun.id)}>Approve</Btn>}
                  {selectedRun.status==="approved" && <Btn size="sm" variant="success" onClick={() => payRun.mutate(selectedRun.id)}>💸 Pay All</Btn>}
                </div>
              </div>

              {/* Totals bar */}
              <div style={{ padding:"14px 20px", borderBottom:"1px solid rgba(255,255,255,0.07)", display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"12px" }}>
                {[
                  { label:"Gross", value:fmtSAR(selectedRun.total_gross), color:"#f0f2ff" },
                  { label:"Deductions", value:fmtSAR(selectedRun.total_deductions), color:"#ff6b6b" },
                  { label:"Commissions", value:fmtSAR(selectedRun.total_commissions), color:"#ffc107" },
                  { label:"Net Pay", value:fmtSAR(selectedRun.total_net), color:"#00e5a0" },
                ].map(s => (
                  <div key={s.label}>
                    <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>{s.label}</div>
                    <div style={{ fontSize:"16px", fontWeight:700, color:s.color as string }}>{s.value}</div>
                  </div>
                ))}
              </div>

              {/* Slip table */}
              <div style={{ overflow:"auto" }}>
                <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12px" }}>
                  <thead>
                    <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                      {["Staff ID","Base","Days","Absent","OT Pay","Bonus","Commission","Deductions","Net","Status","Edit"].map(h => (
                        <th key={h} style={{ padding:"10px 12px", textAlign:"left", color:"#636882", fontSize:"10px", textTransform:"uppercase", letterSpacing:"0.5px", whiteSpace:"nowrap" }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {slipList.map((slip: any) => (
                      <tr key={slip.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                        <td style={{ padding:"10px 12px", fontWeight:600, color:"#6c63ff" }}>#{slip.staff_id}</td>
                        <td style={{ padding:"10px 12px" }}>{fmtSAR(slip.base_salary)}</td>
                        <td style={{ padding:"10px 12px", color:"#00e5a0" }}>{slip.days_worked}</td>
                        <td style={{ padding:"10px 12px", color:slip.days_absent>0?"#ff6b6b":"#636882" }}>{slip.days_absent}</td>
                        <td style={{ padding:"10px 12px" }}>{fmtSAR(slip.overtime_pay)}</td>
                        <td style={{ padding:"10px 12px" }}>{fmtSAR(slip.bonus)}</td>
                        <td style={{ padding:"10px 12px" }}>{fmtSAR(slip.commission)}</td>
                        <td style={{ padding:"10px 12px", color:"#ff6b6b" }}>-{fmtSAR(slip.total_deductions)}</td>
                        <td style={{ padding:"10px 12px", fontWeight:700, color:"#00e5a0" }}>{fmtSAR(slip.net)}</td>
                        <td style={{ padding:"10px 12px" }}><Badge variant={slip.is_paid?"success":"gray"}>{slip.is_paid?"Paid":"Pending"}</Badge></td>
                        <td style={{ padding:"10px 12px" }}>
                          {selectedRun.status==="draft" && (
                            <Btn size="sm" onClick={() => { setSlipEdit(slip); setSlipForm({ bonus:slip.bonus||"0", commission:slip.commission||"0", overtime_hours:slip.overtime_hours||"0", overtime_pay:slip.overtime_pay||"0", deduction_other:slip.deduction_other||"0", notes:slip.notes||"" }) }}>Edit</Btn>
                          )}
                        </td>
                      </tr>
                    ))}
                    {slipList.length===0 && (
                      <tr><td colSpan={11} style={{ padding:"30px", textAlign:"center", color:"#636882" }}>Loading slips…</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Create Run Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="New Payroll Run">
        <div style={{ background:"rgba(108,99,255,0.08)", border:"1px solid rgba(108,99,255,0.2)", borderRadius:"8px", padding:"12px 14px", marginBottom:"16px", fontSize:"12px", color:"#9ba3c0" }}>
          This will auto-generate pay slips for all active staff based on their base salary, attendance records, and GOSI deductions (10%).
        </div>
        <FormRow cols={2}>
          <FormGroup label="Period Start"><input type="date" value={form.period_start} onChange={e => setForm(f=>({...f,period_start:e.target.value}))} /></FormGroup>
          <FormGroup label="Period End"><input type="date" value={form.period_end} onChange={e => setForm(f=>({...f,period_end:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Pay Date"><input type="date" value={form.pay_date} onChange={e => setForm(f=>({...f,pay_date:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Notes"><input value={form.notes} onChange={e => setForm(f=>({...f,notes:e.target.value}))} placeholder="June 2026 payroll" /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createRun.mutate(form)}>Generate Payroll</Btn>
        </div>
      </Modal>

      {/* Edit Slip Modal */}
      {slipEdit && (
        <Modal open={!!slipEdit} onClose={() => setSlipEdit(null)} title={`Edit Pay Slip — Staff #${slipEdit.staff_id}`} width={420}>
          <FormRow cols={2}>
            <FormGroup label="Bonus (SAR)"><input type="number" value={slipForm.bonus} onChange={e => setSlipForm(f=>({...f,bonus:e.target.value}))} /></FormGroup>
            <FormGroup label="Commission (SAR)"><input type="number" value={slipForm.commission} onChange={e => setSlipForm(f=>({...f,commission:e.target.value}))} /></FormGroup>
          </FormRow>
          <FormRow cols={2}>
            <FormGroup label="OT Hours"><input type="number" value={slipForm.overtime_hours} onChange={e => setSlipForm(f=>({...f,overtime_hours:e.target.value}))} /></FormGroup>
            <FormGroup label="OT Pay (SAR)"><input type="number" value={slipForm.overtime_pay} onChange={e => setSlipForm(f=>({...f,overtime_pay:e.target.value}))} /></FormGroup>
          </FormRow>
          <FormRow>
            <FormGroup label="Other Deductions (SAR)"><input type="number" value={slipForm.deduction_other} onChange={e => setSlipForm(f=>({...f,deduction_other:e.target.value}))} /></FormGroup>
          </FormRow>
          <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"8px" }}>
            <Btn onClick={() => setSlipEdit(null)}>Cancel</Btn>
            <Btn variant="primary" onClick={() => updateSlip.mutate({
              runId: selectedRun.id, slipId: slipEdit.id,
              data: { bonus:parseFloat(slipForm.bonus), commission:parseFloat(slipForm.commission), overtime_hours:parseFloat(slipForm.overtime_hours), overtime_pay:parseFloat(slipForm.overtime_pay), deduction_other:parseFloat(slipForm.deduction_other), notes:slipForm.notes },
            })}>Save Changes</Btn>
          </div>
        </Modal>
      )}
    </div>
  )
}
