import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Card } from "../components/ui/Card"
import { Badge } from "../components/ui/Badge"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import toast from "react-hot-toast"

export default function MembersPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState("")
  const [addOpen, setAddOpen] = useState(false)
  const [form, setForm] = useState({ first_name: "", last_name: "", phone: "", email: "", branch_id: 1 })
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["members", search],
    queryFn: () => api.get(`/api/v1/members/?search=${search}&page_size=50`).then(r => r.data),
  })

  const createMember = useMutation({
    mutationFn: (payload: typeof form) => api.post("/api/v1/members/", payload).then(r => r.data),
    onSuccess: () => { toast.success("Member added"); qc.invalidateQueries({ queryKey: ["members"] }); setAddOpen(false) },
    onError: () => toast.error("Failed to add member"),
  })

  const statusVariant = (s: string) => ({ active: "success", expired: "danger", frozen: "warning", suspended: "danger" }[s] || "gray") as any

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h1 style={{ fontSize: "15px", fontWeight: 600 }}>Members <span style={{ color: "#636882", fontWeight: 400, fontSize: "12px" }}>{data?.total?.toLocaleString() || 0} total</span></h1>
        <div style={{ display: "flex", gap: "10px" }}>
          <input placeholder="Search name, ID, phone..." value={search} onChange={e => setSearch(e.target.value)} style={{ width: "240px" }} />
          <Btn variant="primary" onClick={() => setAddOpen(true)}>+ Add Member</Btn>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px", marginBottom: "20px" }}>
        <Card><div style={{ fontSize: "11px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "4px" }}>Total Active</div><div style={{ fontSize: "24px", fontWeight: 600 }}>{data?.total?.toLocaleString() || 0}</div></Card>
        <Card><div style={{ fontSize: "11px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "4px" }}>New This Month</div><div style={{ fontSize: "24px", fontWeight: 600 }}>124</div><div style={{ fontSize: "11px", color: "#00e5a0", marginTop: "4px" }}>↑ +18%</div></Card>
        <Card><div style={{ fontSize: "11px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "4px" }}>Frozen</div><div style={{ fontSize: "24px", fontWeight: 600 }}>43</div></Card>
        <Card><div style={{ fontSize: "11px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.6px", marginBottom: "4px" }}>Avg LTV</div><div style={{ fontSize: "24px", fontWeight: 600 }}>SAR 8,420</div></Card>
      </div>

      <Card>
        {isLoading ? (
          <div style={{ textAlign: "center", color: "#636882", padding: "40px" }}>Loading members...</div>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                  {["Member", "Plan", "Status", "Check-ins", "Balance", "Joined", "Actions"].map(h => (
                    <th key={h} style={{ padding: "10px 14px", textAlign: "left", color: "#636882", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.5px" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(data?.items || []).map((m: any) => (
                  <tr key={m.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
                    <td style={{ padding: "11px 14px" }}>
                      <div style={{ fontWeight: 600 }}>{m.first_name} {m.last_name}</div>
                      <div style={{ fontSize: "11px", color: "#636882" }}>{m.member_id} · {m.phone}</div>
                    </td>
                    <td style={{ padding: "11px 14px" }}><Badge variant="purple">Premium</Badge></td>
                    <td style={{ padding: "11px 14px" }}><Badge variant={statusVariant(m.status)}>{m.status}</Badge></td>
                    <td style={{ padding: "11px 14px", color: "#9ba3c0" }}>{m.total_checkins}</td>
                    <td style={{ padding: "11px 14px", color: "#00e5a0" }}>Paid</td>
                    <td style={{ padding: "11px 14px", color: "#636882" }}>{new Date(m.created_at).toLocaleDateString()}</td>
                    <td style={{ padding: "11px 14px" }}>
                      <div style={{ display: "flex", gap: "4px" }}>
                        <Btn size="sm" onClick={() => navigate(`/members/${m.id}`)}>View</Btn>
                        <Btn size="sm">Edit</Btn>
                      </div>
                    </td>
                  </tr>
                ))}
                {!data?.items?.length && (
                  <tr><td colSpan={7} style={{ padding: "40px", textAlign: "center", color: "#636882" }}>No members found. Add your first member.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add New Member">
        <FormRow cols={2}>
          <FormGroup label="First Name"><input value={form.first_name} onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))} placeholder="Ahmed" /></FormGroup>
          <FormGroup label="Last Name"><input value={form.last_name} onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))} placeholder="Al-Rashid" /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Phone"><input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} placeholder="+966 5X XXX XXXX" /></FormGroup>
          <FormGroup label="Email"><input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} placeholder="ahmed@email.com" /></FormGroup>
        </FormRow>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createMember.mutate(form)}>Add Member</Btn>
        </div>
      </Modal>
    </div>
  )
}
