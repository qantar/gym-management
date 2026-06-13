import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import toast from "react-hot-toast"

export default function BranchesPage() {
  const [addOpen, setAddOpen] = useState(false)
  const [selected, setSelected] = useState<any>(null)
  const [form, setForm] = useState({ name:"", code:"", city:"", address:"", phone:"", email:"", capacity:"500", opening_time:"06:00", closing_time:"23:00" })
  const qc = useQueryClient()

  const { data: branches, isLoading } = useQuery({
    queryKey: ["branches"],
    queryFn: () => api.get("/api/v1/branches/").then(r => r.data),
  })

  const { data: stats } = useQuery({
    queryKey: ["branch-stats", selected?.id],
    queryFn: () => selected ? api.get(`/api/v1/branches/${selected.id}/stats`).then(r => r.data) : null,
    enabled: !!selected,
  })

  const createBranch = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/branches/", { ...p, capacity: parseInt(p.capacity) }).then(r => r.data),
    onSuccess: (d) => { toast.success(`Branch ${d.name} created`); qc.invalidateQueries({ queryKey: ["branches"] }); setAddOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const branchList: any[] = Array.isArray(branches) ? branches : []

  // Util
  const utilColor = (active: number, cap: number) => {
    const pct = cap > 0 ? (active / cap) * 100 : 0
    return pct > 75 ? "#ff6b6b" : pct > 50 ? "#ffc107" : "#00e5a0"
  }

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Branch Management <span style={{ color:"#636882", fontWeight:400, fontSize:"12px" }}>{branchList.length} branches</span></h1>
        <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>+ Add Branch</Btn>
      </div>

      {/* Summary strip */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:"14px", marginBottom:"20px" }}>
        {[
          { label:"Total Branches", value:branchList.length, color:"#6c63ff" },
          { label:"Active", value:branchList.filter(b=>b.is_active).length, color:"#00e5a0" },
          { label:"Opening Soon", value:branchList.filter(b=>!b.is_active).length, color:"#ffc107" },
        ].map(k => (
          <div key={k.label} style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderTop:`2px solid ${k.color}`, borderRadius:"10px", padding:"14px 16px" }}>
            <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>{k.label}</div>
            <div style={{ fontSize:"28px", fontWeight:700, color:k.color as string }}>{k.value}</div>
          </div>
        ))}
      </div>

      {/* Branch cards grid */}
      {isLoading ? (
        <div style={{ textAlign:"center", color:"#636882", padding:"60px" }}>Loading branches…</div>
      ) : (
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))", gap:"16px" }}>
          {branchList.map((b: any) => (
            <div key={b.id} onClick={() => setSelected(b)}
              style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", padding:"18px 20px", cursor:"pointer", transition:"all 0.15s" }}
              onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(108,99,255,0.4)"}
              onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.07)"}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:"14px" }}>
                <div>
                  <div style={{ fontSize:"14px", fontWeight:600 }}>{b.name}</div>
                  <div style={{ fontSize:"11px", color:"#636882", marginTop:"2px" }}>{b.city}</div>
                </div>
                <Badge variant={b.is_active ? "success" : "warning"}>{b.is_active ? "Active" : "Setup"}</Badge>
              </div>

              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"8px", marginBottom:"12px" }}>
                {[
                  { label:"Code", value:b.code },
                  { label:"Capacity", value:b.capacity },
                  { label:"Opens", value:b.opening_time },
                  { label:"Closes", value:b.closing_time },
                ].map(r => (
                  <div key={r.label}>
                    <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.4px" }}>{r.label}</div>
                    <div style={{ fontSize:"12px", fontWeight:500 }}>{r.value}</div>
                  </div>
                ))}
              </div>

              {b.phone && <div style={{ fontSize:"11px", color:"#636882" }}>📞 {b.phone}</div>}
              {b.address && <div style={{ fontSize:"11px", color:"#636882", marginTop:"3px" }}>📍 {b.address}</div>}
            </div>
          ))}

          {/* Add new card */}
          <div onClick={() => setAddOpen(true)}
            style={{ background:"transparent", border:"2px dashed rgba(255,255,255,0.12)", borderRadius:"10px", padding:"18px 20px", cursor:"pointer", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", minHeight:"180px", color:"#636882", transition:"all 0.15s" }}
            onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(108,99,255,0.4)"; (e.currentTarget as HTMLDivElement).style.color = "#6c63ff" }}
            onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.borderColor = "rgba(255,255,255,0.12)"; (e.currentTarget as HTMLDivElement).style.color = "#636882" }}>
            <div style={{ fontSize:"36px", marginBottom:"8px" }}>+</div>
            <div style={{ fontSize:"13px" }}>Add Branch</div>
          </div>
        </div>
      )}

      {/* Branch Detail Modal */}
      {selected && (
        <Modal open={!!selected} onClose={() => setSelected(null)} title={selected.name}>
          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"12px", marginBottom:"16px" }}>
            {[
              { label:"City", value:selected.city },
              { label:"Code", value:selected.code },
              { label:"Capacity", value:selected.capacity },
              { label:"Status", value:selected.is_active ? "Active":"Setup" },
              { label:"Opens", value:selected.opening_time },
              { label:"Closes", value:selected.closing_time },
            ].map(r => (
              <div key={r.label} style={{ background:"#14161f", borderRadius:"6px", padding:"10px 14px" }}>
                <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>{r.label}</div>
                <div style={{ fontSize:"14px", fontWeight:600 }}>{r.value}</div>
              </div>
            ))}
          </div>
          {stats && (
            <div style={{ background:"#14161f", borderRadius:"8px", padding:"14px", marginBottom:"16px" }}>
              <div style={{ fontSize:"12px", fontWeight:600, color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"10px" }}>Live Stats</div>
              <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"8px" }}>
                {[
                  { label:"Active Members", value:stats.active_members||0, color:"#00e5a0" },
                  { label:"Revenue (Month)", value:`SAR ${parseFloat(stats.revenue_month||"0").toLocaleString()}`, color:"#6c63ff" },
                  { label:"Check-ins Today", value:stats.checkins_today||0, color:"#4fc3f7" },
                  { label:"In Gym Now", value:stats.in_gym_now||0, color:"#ffc107" },
                ].map(s => (
                  <div key={s.label} style={{ textAlign:"center" }}>
                    <div style={{ fontSize:"20px", fontWeight:700, color:s.color as string }}>{s.value}</div>
                    <div style={{ fontSize:"10px", color:"#636882", marginTop:"2px" }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
            <Btn onClick={() => toast.success("Switching to branch view…")}>Switch to Branch</Btn>
            <Btn onClick={() => setSelected(null)}>Close</Btn>
          </div>
        </Modal>
      )}

      {/* Add Branch Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add New Branch">
        <FormRow cols={2}>
          <FormGroup label="Branch Name"><input value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} placeholder="Al Nakheel Branch" /></FormGroup>
          <FormGroup label="Code"><input value={form.code} onChange={e => setForm(f=>({...f,code:e.target.value}))} placeholder="RUH-03" /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="City"><input value={form.city} onChange={e => setForm(f=>({...f,city:e.target.value}))} placeholder="Riyadh" /></FormGroup>
          <FormGroup label="Capacity"><input type="number" value={form.capacity} onChange={e => setForm(f=>({...f,capacity:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Address"><input value={form.address} onChange={e => setForm(f=>({...f,address:e.target.value}))} placeholder="Street, District, City" /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Phone"><input value={form.phone} onChange={e => setForm(f=>({...f,phone:e.target.value}))} /></FormGroup>
          <FormGroup label="Email"><input type="email" value={form.email} onChange={e => setForm(f=>({...f,email:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Opening Time"><input type="time" value={form.opening_time} onChange={e => setForm(f=>({...f,opening_time:e.target.value}))} /></FormGroup>
          <FormGroup label="Closing Time"><input type="time" value={form.closing_time} onChange={e => setForm(f=>({...f,closing_time:e.target.value}))} /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createBranch.mutate(form)}>Create Branch</Btn>
        </div>
      </Modal>
    </div>
  )
}
