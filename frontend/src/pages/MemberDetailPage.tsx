import { useParams, useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Badge } from "../components/ui/Badge"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { useState } from "react"
import toast from "react-hot-toast"

const statusVariant = (s: string): any =>
  ({ active:"success", expired:"danger", frozen:"warning", suspended:"danger" }[s] || "gray")

export default function MemberDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [editOpen, setEditOpen] = useState(false)
  const [freezeOpen, setFreezeOpen] = useState(false)
  const [editForm, setEditForm] = useState<any>({})
  const [freezeForm, setFreezeForm] = useState({ freeze_start:"", freeze_end:"", reason:"" })

  const { data, isLoading, error } = useQuery({
    queryKey: ["member-detail", id],
    queryFn: () => api.get(`/api/v1/members/${id}/profile`).then(r => r.data),
    enabled: !!id,
  })

  const updateMember = useMutation({
    mutationFn: (payload: any) => api.put(`/api/v1/members/${id}`, payload).then(r => r.data),
    onSuccess: () => { toast.success("Member updated"); qc.invalidateQueries({ queryKey: ["member-detail", id] }); setEditOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Update failed"),
  })

  const freezeMembership = useMutation({
    mutationFn: (mId: number) => api.post(`/api/v1/memberships/${mId}/freeze`, freezeForm).then(r => r.data),
    onSuccess: (d) => { toast.success(d.message); qc.invalidateQueries({ queryKey: ["member-detail", id] }); setFreezeOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Freeze failed"),
  })

  const sendReminder = useMutation({
    mutationFn: () => api.post(`/api/v1/notifications/send/expiry-reminders?days_ahead=7`).then(r => r.data),
    onSuccess: () => toast.success("Expiry reminder sent"),
  })

  const downloadPDF = () => {
    window.open(`/api/v1/members/${id}/pdf`, "_blank")
  }

  if (isLoading) return <div style={{ padding:"60px", textAlign:"center", color:"#636882" }}>Loading member profile…</div>
  if (error || !data) return <div style={{ padding:"60px", textAlign:"center", color:"#ff6b6b" }}>Member not found</div>

  const { member, active_membership, all_memberships, outstanding_balance, recent_invoices, attendance_stats, recent_attendance, recent_bookings } = data

  const card = (children: React.ReactNode, style: React.CSSProperties = {}) => (
    <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", padding:"18px 20px", ...style }}>
      {children}
    </div>
  )

  const sectionTitle = (t: string) => (
    <div style={{ fontSize:"12px", fontWeight:600, color:"#636882", textTransform:"uppercase", letterSpacing:"0.6px", marginBottom:"12px" }}>{t}</div>
  )

  return (
    <div>
      {/* Breadcrumb */}
      <div style={{ display:"flex", alignItems:"center", gap:"8px", marginBottom:"20px", fontSize:"12px", color:"#636882" }}>
        <span style={{ cursor:"pointer", color:"#6c63ff" }} onClick={() => navigate("/members")}>Members</span>
        <span>/</span>
        <span style={{ color:"#f0f2ff" }}>{member.first_name} {member.last_name}</span>
      </div>

      {/* Header */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"20px" }}>
        <div style={{ display:"flex", gap:"16px", alignItems:"center" }}>
          <div style={{ width:"64px", height:"64px", borderRadius:"50%", background:"#6c63ff", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"22px", fontWeight:700, color:"#fff", flexShrink:0 }}>
            {member.first_name[0]}{member.last_name[0]}
          </div>
          <div>
            <div style={{ fontSize:"20px", fontWeight:700 }}>{member.first_name} {member.last_name}</div>
            <div style={{ fontSize:"12px", color:"#636882", marginTop:"2px" }}>{member.member_id} · {member.phone}</div>
            <div style={{ marginTop:"6px", display:"flex", gap:"6px" }}>
              <Badge variant={statusVariant(member.status)}>{member.status}</Badge>
              {active_membership && <Badge variant="purple">Active Membership</Badge>}
              {outstanding_balance !== "0" && parseFloat(outstanding_balance) > 0 && (
                <Badge variant="danger">SAR {parseFloat(outstanding_balance).toLocaleString()} outstanding</Badge>
              )}
            </div>
          </div>
        </div>
        <div style={{ display:"flex", gap:"8px", flexWrap:"wrap", justifyContent:"flex-end" }}>
          <Btn size="sm" onClick={downloadPDF}>📄 PDF</Btn>
          <Btn size="sm" onClick={() => sendReminder.mutate()}>📱 Send Reminder</Btn>
          {active_membership && (
            <Btn size="sm" variant="danger" onClick={() => setFreezeOpen(true)}>❄️ Freeze</Btn>
          )}
          <Btn size="sm" variant="primary" onClick={() => { setEditForm({ first_name:member.first_name, last_name:member.last_name, phone:member.phone, email:member.email||"", notes:member.notes||"", medical_notes:member.medical_notes||"" }); setEditOpen(true) }}>✏️ Edit</Btn>
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:"16px", marginBottom:"20px" }}>
        {/* Attendance KPIs */}
        {[
          { label:"All-Time Check-ins", value:attendance_stats.total_all_time, color:"#6c63ff" },
          { label:"This Month", value:attendance_stats.this_month, color:"#00e5a0" },
          { label:"This Year", value:attendance_stats.this_year, color:"#4fc3f7" },
        ].map(k => (
          <div key={k.label} style={{ background:"#0f1117", border:`1px solid rgba(255,255,255,0.07)`, borderTop:`2px solid ${k.color}`, borderRadius:"10px", padding:"14px 16px" }}>
            <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>{k.label}</div>
            <div style={{ fontSize:"28px", fontWeight:700, color:k.color as string }}>{k.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"16px", marginBottom:"16px" }}>
        {/* Personal Info */}
        {card(
          <>
            {sectionTitle("Personal Information")}
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"10px" }}>
              {[
                ["First Name", member.first_name],
                ["Last Name", member.last_name],
                ["Email", member.email || "—"],
                ["Phone", member.phone],
                ["Gender", member.gender || "—"],
                ["Date of Birth", member.date_of_birth || "—"],
                ["Branch ID", member.branch_id],
                ["QR Code", member.qr_code ? "✓ Generated" : "—"],
              ].map(([l, v]) => (
                <div key={l} style={{ padding:"8px 0", borderBottom:"1px solid rgba(255,255,255,0.04)" }}>
                  <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.4px", marginBottom:"2px" }}>{l}</div>
                  <div style={{ fontSize:"12px", fontWeight:500 }}>{String(v)}</div>
                </div>
              ))}
            </div>
            {member.emergency_contact_name && (
              <div style={{ marginTop:"12px", padding:"10px", background:"#14161f", borderRadius:"6px" }}>
                <div style={{ fontSize:"10px", color:"#636882", marginBottom:"4px" }}>EMERGENCY CONTACT</div>
                <div style={{ fontSize:"12px" }}>{member.emergency_contact_name} · {member.emergency_contact_phone}</div>
                <div style={{ fontSize:"11px", color:"#636882" }}>{member.emergency_contact_relation}</div>
              </div>
            )}
            {member.medical_notes && (
              <div style={{ marginTop:"8px", padding:"10px", background:"rgba(255,107,107,0.08)", borderRadius:"6px", border:"1px solid rgba(255,107,107,0.2)" }}>
                <div style={{ fontSize:"10px", color:"#ff6b6b", marginBottom:"4px" }}>⚕️ MEDICAL NOTES</div>
                <div style={{ fontSize:"12px", color:"#f0f2ff" }}>{member.medical_notes}</div>
              </div>
            )}
          </>
        )}

        {/* Membership */}
        {card(
          <>
            {sectionTitle("Memberships")}
            {active_membership ? (
              <div style={{ background:"rgba(108,99,255,0.08)", border:"1px solid rgba(108,99,255,0.25)", borderRadius:"8px", padding:"14px", marginBottom:"12px" }}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:"8px" }}>
                  <span style={{ fontWeight:600, color:"#6c63ff" }}>Active Membership</span>
                  <Badge variant="success">Active</Badge>
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"8px", fontSize:"12px" }}>
                  <div><span style={{ color:"#636882" }}>Start: </span>{active_membership.start_date}</div>
                  <div><span style={{ color:"#636882" }}>End: </span>{active_membership.end_date}</div>
                  <div><span style={{ color:"#636882" }}>Paid: </span>SAR {parseFloat(active_membership.price_paid).toLocaleString()}</div>
                  <div><span style={{ color:"#636882" }}>Freeze days: </span>{active_membership.freeze_days_used}</div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign:"center", color:"#636882", padding:"20px", fontSize:"12px" }}>No active membership</div>
            )}
            <div style={{ fontSize:"11px", color:"#636882", marginBottom:"8px" }}>History ({all_memberships.length})</div>
            {all_memberships.slice(0, 5).map((ms: any) => (
              <div key={ms.id} style={{ display:"flex", justifyContent:"space-between", padding:"6px 0", borderBottom:"1px solid rgba(255,255,255,0.04)", fontSize:"11px" }}>
                <span style={{ color:"#9ba3c0" }}>{ms.start_date} → {ms.end_date}</span>
                <Badge variant={statusVariant(ms.status)} >{ms.status}</Badge>
              </div>
            ))}
          </>
        )}
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"16px", marginBottom:"16px" }}>
        {/* Recent Invoices */}
        {card(
          <>
            {sectionTitle("Recent Invoices")}
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12px" }}>
              <thead>
                <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                  {["Invoice","Total","Due","Status"].map(h => (
                    <th key={h} style={{ padding:"6px 8px", textAlign:"left", color:"#636882", fontSize:"10px", textTransform:"uppercase" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {recent_invoices.map((inv: any) => (
                  <tr key={inv.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                    <td style={{ padding:"8px 8px", color:"#6c63ff", fontWeight:500 }}>{inv.invoice_number}</td>
                    <td style={{ padding:"8px 8px" }}>SAR {parseFloat(inv.total).toLocaleString()}</td>
                    <td style={{ padding:"8px 8px", color:"#636882" }}>{inv.due_date?.slice(0,10)}</td>
                    <td style={{ padding:"8px 8px" }}><Badge variant={({ paid:"success",overdue:"danger",pending:"warning" }[inv.status] || "gray") as any}>{inv.status}</Badge></td>
                  </tr>
                ))}
                {!recent_invoices.length && <tr><td colSpan={4} style={{ padding:"20px", textAlign:"center", color:"#636882" }}>No invoices</td></tr>}
              </tbody>
            </table>
          </>
        )}

        {/* Recent Attendance */}
        {card(
          <>
            {sectionTitle("Recent Attendance")}
            <div style={{ display:"flex", flexDirection:"column", gap:"6px", maxHeight:"280px", overflowY:"auto" }}>
              {recent_attendance.map((a: any) => (
                <div key={a.id} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"6px 8px", background:"#14161f", borderRadius:"5px" }}>
                  <div>
                    <div style={{ fontSize:"11px", fontWeight:500 }}>{new Date(a.check_in).toLocaleString("en-SA")}</div>
                    <div style={{ fontSize:"10px", color:"#636882" }}>via {a.method}{a.duration_minutes ? ` · ${a.duration_minutes}min` : ""}</div>
                  </div>
                  <div style={{ fontSize:"10px", color:a.check_out?"#636882":"#00e5a0" }}>{a.check_out ? "↙ Out" : "↗ In"}</div>
                </div>
              ))}
              {!recent_attendance.length && <div style={{ textAlign:"center", color:"#636882", padding:"20px", fontSize:"12px" }}>No attendance records</div>}
            </div>
          </>
        )}
      </div>

      {/* Notes */}
      {member.notes && card(
        <>
          {sectionTitle("Notes")}
          <div style={{ fontSize:"13px", color:"#9ba3c0", lineHeight:1.6 }}>{member.notes}</div>
        </>
      )}

      {/* Edit Modal */}
      <Modal open={editOpen} onClose={() => setEditOpen(false)} title="Edit Member">
        <FormRow cols={2}>
          <FormGroup label="First Name"><input value={editForm.first_name||""} onChange={e => setEditForm((f:any) => ({...f,first_name:e.target.value}))} /></FormGroup>
          <FormGroup label="Last Name"><input value={editForm.last_name||""} onChange={e => setEditForm((f:any) => ({...f,last_name:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Phone"><input value={editForm.phone||""} onChange={e => setEditForm((f:any) => ({...f,phone:e.target.value}))} /></FormGroup>
          <FormGroup label="Email"><input type="email" value={editForm.email||""} onChange={e => setEditForm((f:any) => ({...f,email:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Notes"><textarea value={editForm.notes||""} onChange={e => setEditForm((f:any) => ({...f,notes:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Medical Notes"><textarea value={editForm.medical_notes||""} onChange={e => setEditForm((f:any) => ({...f,medical_notes:e.target.value}))} /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setEditOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => updateMember.mutate(editForm)}>Save Changes</Btn>
        </div>
      </Modal>

      {/* Freeze Modal */}
      <Modal open={freezeOpen} onClose={() => setFreezeOpen(false)} title="Freeze Membership" width={400}>
        <FormRow cols={2}>
          <FormGroup label="Freeze Start"><input type="date" value={freezeForm.freeze_start} onChange={e => setFreezeForm(f => ({...f,freeze_start:e.target.value}))} /></FormGroup>
          <FormGroup label="Freeze End"><input type="date" value={freezeForm.freeze_end} onChange={e => setFreezeForm(f => ({...f,freeze_end:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Reason"><input value={freezeForm.reason} onChange={e => setFreezeForm(f => ({...f,reason:e.target.value}))} placeholder="Medical / Travel / Other" /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"8px" }}>
          <Btn onClick={() => setFreezeOpen(false)}>Cancel</Btn>
          <Btn variant="danger" onClick={() => active_membership && freezeMembership.mutate(active_membership.id)}>Freeze Membership</Btn>
        </div>
      </Modal>
    </div>
  )
}
