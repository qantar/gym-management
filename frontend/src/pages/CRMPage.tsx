import { useState, useRef } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import toast from "react-hot-toast"

const STAGES = [
  { key: "new",       label: "New",          color: "#4fc3f7" },
  { key: "contacted", label: "Contacted",    color: "#ffc107" },
  { key: "trial",     label: "Trial",        color: "#ff9800" },
  { key: "proposal",  label: "Proposal",     color: "#6c63ff" },
  { key: "won",       label: "Won ✓",        color: "#00e5a0" },
  { key: "lost",      label: "Lost ✗",       color: "#ff6b6b" },
]
const SOURCES = ["walk_in","instagram","facebook","google","referral","website","whatsapp","other"]

interface Lead {
  id: number; full_name: string; phone: string; email: string | null
  source: string; status: string; expected_value: string | null
  next_follow_up: string | null; created_at: string; notes: string | null
}

export default function CRMPage() {
  const [addOpen, setAddOpen] = useState(false)
  const [detailLead, setDetailLead] = useState<Lead | null>(null)
  const [dragging, setDragging] = useState<Lead | null>(null)
  const [form, setForm] = useState({ full_name: "", phone: "", email: "", source: "walk_in", status: "new", expected_value: "", next_follow_up: "", notes: "", branch_id: 1 })
  const qc = useQueryClient()

  const { data: leadsData } = useQuery({
    queryKey: ["leads"],
    queryFn: () => api.get("/api/v1/leads/?page_size=200").then(r => r.data),
    refetchInterval: 30000,
  })

  const leads: Lead[] = leadsData?.items || []

  const byStage = (status: string) => leads.filter(l => l.status === status)

  const createLead = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/leads/", {
      ...p, expected_value: p.expected_value ? parseFloat(p.expected_value) : null,
      next_follow_up: p.next_follow_up || null,
    }).then(r => r.data),
    onSuccess: () => { toast.success("Lead added"); qc.invalidateQueries({ queryKey: ["leads"] }); setAddOpen(false) },
    onError: () => toast.error("Failed to add lead"),
  })

  const moveLead = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.put(`/api/v1/leads/${id}`, { status }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  })

  // Drag handlers
  const handleDragStart = (lead: Lead) => setDragging(lead)
  const handleDrop = (stage: string) => {
    if (!dragging || dragging.status === stage) return
    moveLead.mutate({ id: dragging.id, status: stage })
    toast.success(`${dragging.full_name} → ${stage}`)
    setDragging(null)
  }

  const totalValue = leads.filter(l => l.status === "won")
    .reduce((s, l) => s + parseFloat(l.expected_value || "0"), 0)

  const convRate = leads.length > 0
    ? ((leads.filter(l => l.status === "won").length / leads.filter(l => ["won","lost"].includes(l.status)).length || 0) * 100).toFixed(1)
    : "0"

  return (
    <div>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <h1 style={{ fontSize: "15px", fontWeight: 600 }}>CRM Pipeline</h1>
        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={() => toast("Bulk follow-up scheduled", { icon: "📅" })}
            style={{ padding: "6px 12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#9ba3c0", cursor: "pointer", fontSize: "12px" }}>
            Bulk Follow-up
          </button>
          <button onClick={() => setAddOpen(true)}
            style={{ padding: "6px 14px", borderRadius: "6px", border: "none", background: "#6c63ff", color: "#fff", cursor: "pointer", fontSize: "12px", fontWeight: 500 }}>
            + Add Lead
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "14px", marginBottom: "20px" }}>
        {[
          { label: "Total Leads", value: leads.length, color: "#6c63ff" },
          { label: "Conversion Rate", value: `${convRate}%`, color: "#00e5a0" },
          { label: "Won Revenue", value: `SAR ${totalValue.toLocaleString()}`, color: "#ffc107" },
          { label: "Avg Cycle", value: "4.2 days", color: "#4fc3f7" },
        ].map(k => (
          <div key={k.label} style={{ background: "#0f1117", border: "1px solid rgba(255,255,255,0.07)", borderTop: `2px solid ${k.color}`, borderRadius: "10px", padding: "14px 16px" }}>
            <div style={{ fontSize: "10px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "3px" }}>{k.label}</div>
            <div style={{ fontSize: "22px", fontWeight: 700 }}>{k.value}</div>
          </div>
        ))}
      </div>

      {/* Kanban Board */}
      <div style={{ display: "flex", gap: "10px", overflowX: "auto", paddingBottom: "8px", minHeight: "500px" }}>
        {STAGES.map(stage => {
          const stageLeads = byStage(stage.key)
          return (
            <div
              key={stage.key}
              onDragOver={e => { e.preventDefault(); (e.currentTarget as HTMLDivElement).style.background = "rgba(108,99,255,0.08)" }}
              onDragLeave={e => ((e.currentTarget as HTMLDivElement).style.background = "transparent")}
              onDrop={e => { (e.currentTarget as HTMLDivElement).style.background = "transparent"; handleDrop(stage.key) }}
              style={{ minWidth: "190px", flex: "0 0 190px", background: "transparent", borderRadius: "8px", padding: "4px", transition: "background 0.15s" }}
            >
              {/* Column header */}
              <div style={{ padding: "8px 4px 10px", display: "flex", alignItems: "center", gap: "6px" }}>
                <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: stage.color, display: "inline-block", flexShrink: 0 }} />
                <span style={{ fontSize: "11px", fontWeight: 600, color: stage.color, textTransform: "uppercase", letterSpacing: "0.5px" }}>{stage.label}</span>
                <span style={{ marginLeft: "auto", background: "#1f2235", fontSize: "10px", padding: "1px 7px", borderRadius: "10px", color: "#9ba3c0" }}>{stageLeads.length}</span>
              </div>

              {/* Cards */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {stageLeads.map(lead => (
                  <div
                    key={lead.id}
                    draggable
                    onDragStart={() => handleDragStart(lead)}
                    onDragEnd={() => setDragging(null)}
                    onClick={() => setDetailLead(lead)}
                    style={{
                      background: "#0f1117", border: `1px solid ${dragging?.id === lead.id ? stage.color : "rgba(255,255,255,0.07)"}`,
                      borderRadius: "8px", padding: "12px", cursor: "grab",
                      opacity: dragging?.id === lead.id ? 0.5 : 1,
                      transition: "border-color 0.15s, transform 0.1s",
                      transform: dragging?.id === lead.id ? "scale(0.97)" : "none",
                    }}
                    onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.borderColor = stage.color}
                    onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.borderColor = dragging?.id === lead.id ? stage.color : "rgba(255,255,255,0.07)"}
                  >
                    <div style={{ fontSize: "12.5px", fontWeight: 600, marginBottom: "4px" }}>{lead.full_name}</div>
                    <div style={{ fontSize: "11px", color: "#636882", marginBottom: "6px" }}>
                      {lead.source.replace(/_/g," ")} · {lead.phone}
                    </div>
                    {lead.expected_value && (
                      <div style={{ fontSize: "12px", fontWeight: 600, color: "#00e5a0", marginBottom: "6px" }}>
                        SAR {parseFloat(lead.expected_value).toLocaleString()}
                      </div>
                    )}
                    {lead.next_follow_up && (
                      <div style={{ fontSize: "10px", color: "#ffc107" }}>
                        📅 {new Date(lead.next_follow_up).toLocaleDateString()}
                      </div>
                    )}
                    <div style={{ display: "flex", gap: "4px", marginTop: "8px" }}>
                      <button
                        onClick={e => { e.stopPropagation(); toast.success(`Follow-up scheduled for ${lead.full_name}`) }}
                        style={{ flex: 1, padding: "3px", fontSize: "10px", borderRadius: "4px", border: "1px solid rgba(255,255,255,0.08)", background: "transparent", color: "#9ba3c0", cursor: "pointer", fontFamily: "inherit" }}>
                        Follow-up
                      </button>
                      {stage.key !== "won" && stage.key !== "lost" && (
                        <button
                          onClick={e => {
                            e.stopPropagation()
                            const nextIdx = STAGES.findIndex(s => s.key === stage.key)
                            const next = STAGES[nextIdx + 1]
                            if (next) moveLead.mutate({ id: lead.id, status: next.key })
                          }}
                          style={{ flex: 1, padding: "3px", fontSize: "10px", borderRadius: "4px", border: "none", background: stage.color + "22", color: stage.color, cursor: "pointer", fontFamily: "inherit" }}>
                          → Next
                        </button>
                      )}
                    </div>
                  </div>
                ))}

                {/* Add to this column */}
                <button
                  onClick={() => { setForm(f => ({ ...f, status: stage.key })); setAddOpen(true) }}
                  style={{ padding: "8px", borderRadius: "6px", border: "1px dashed rgba(255,255,255,0.12)", background: "transparent", color: "#636882", cursor: "pointer", fontSize: "11px", fontFamily: "inherit", width: "100%" }}>
                  + Add
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Add Lead Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Lead">
        <FormRow cols={2}>
          <FormGroup label="Full Name"><input value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))} placeholder="Khalid Nasser" /></FormGroup>
          <FormGroup label="Phone"><input value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} placeholder="+966 5X XXX XXXX" /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Source">
            <select value={form.source} onChange={e => setForm(f => ({ ...f, source: e.target.value }))}>
              {SOURCES.map(s => <option key={s} value={s}>{s.replace(/_/g," ")}</option>)}
            </select>
          </FormGroup>
          <FormGroup label="Stage">
            <select value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
              {STAGES.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
          </FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Expected Value (SAR)"><input type="number" value={form.expected_value} onChange={e => setForm(f => ({ ...f, expected_value: e.target.value }))} placeholder="2400" /></FormGroup>
          <FormGroup label="Follow-up Date"><input type="datetime-local" value={form.next_follow_up} onChange={e => setForm(f => ({ ...f, next_follow_up: e.target.value }))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Notes"><textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} placeholder="Interested in morning PT sessions…" /></FormGroup>
        </FormRow>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createLead.mutate(form)}>Add Lead</Btn>
        </div>
      </Modal>

      {/* Lead Detail Modal */}
      {detailLead && (
        <Modal open={!!detailLead} onClose={() => setDetailLead(null)} title={detailLead.full_name}>
          <div style={{ display: "grid", gap: "10px" }}>
            {[
              { label: "Phone", value: detailLead.phone },
              { label: "Email", value: detailLead.email || "—" },
              { label: "Source", value: detailLead.source.replace(/_/g," ") },
              { label: "Status", value: detailLead.status },
              { label: "Expected Value", value: detailLead.expected_value ? `SAR ${parseFloat(detailLead.expected_value).toLocaleString()}` : "—" },
              { label: "Next Follow-up", value: detailLead.next_follow_up ? new Date(detailLead.next_follow_up).toLocaleString() : "—" },
              { label: "Notes", value: detailLead.notes || "—" },
            ].map(r => (
              <div key={r.label} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ fontSize: "12px", color: "#636882" }}>{r.label}</span>
                <span style={{ fontSize: "12px", fontWeight: 500 }}>{r.value}</span>
              </div>
            ))}
          </div>
          <div style={{ display: "flex", gap: "8px", marginTop: "16px" }}>
            <Btn onClick={() => { moveLead.mutate({ id: detailLead.id, status: "won" }); setDetailLead(null); toast.success("Lead won! 🎉") }} variant="success">Mark Won</Btn>
            <Btn onClick={() => { moveLead.mutate({ id: detailLead.id, status: "lost" }); setDetailLead(null) }} variant="danger">Mark Lost</Btn>
            <Btn onClick={() => toast.success("Follow-up scheduled")}>Schedule Follow-up</Btn>
            <Btn onClick={() => setDetailLead(null)} style={{ marginLeft: "auto" }}>Close</Btn>
          </div>
        </Modal>
      )}
    </div>
  )
}
