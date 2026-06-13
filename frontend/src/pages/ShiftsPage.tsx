import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import toast from "react-hot-toast"

const BRANCH_ID = 1
const DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
const STATUS_COLOR: Record<string,string> = { scheduled:"#6c63ff", confirmed:"#00e5a0", completed:"#636882", absent:"#ff6b6b", cancelled:"#ff6b6b" }

function getWeekDates(offset = 0) {
  const today = new Date()
  const sun = new Date(today)
  sun.setDate(today.getDate() - today.getDay() + offset * 7)
  return Array.from({ length: 7 }, (_, i) => { const d = new Date(sun); d.setDate(sun.getDate() + i); return d })
}

export default function ShiftsPage() {
  const [weekOffset, setWeekOffset] = useState(0)
  const [addOpen, setAddOpen] = useState(false)
  const [form, setForm] = useState({ staff_id:"", shift_date:"", start_time:"08:00", end_time:"16:00", notes:"", is_recurring:false, recurrence_rule:"weekly" })
  const qc = useQueryClient()

  const weekDates = getWeekDates(weekOffset)
  const weekStart = weekDates[0].toISOString().split("T")[0]

  const { data: shifts, isLoading } = useQuery({
    queryKey: ["shifts", BRANCH_ID, weekStart],
    queryFn: () => api.get(`/api/v1/shifts/?branch_id=${BRANCH_ID}&week_start=${weekStart}`).then(r => r.data),
  })

  const createShift = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/shifts/", { ...p, staff_id: parseInt(p.staff_id), branch_id: BRANCH_ID, is_recurring: p.is_recurring, recurrence_rule: p.is_recurring ? p.recurrence_rule : null }).then(r => r.data),
    onSuccess: (d) => { toast.success(`${d.created} shift(s) created`); qc.invalidateQueries({ queryKey: ["shifts"] }); setAddOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const deleteShift = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/shifts/${id}`).then(r => r.data),
    onSuccess: () => { toast.success("Shift deleted"); qc.invalidateQueries({ queryKey: ["shifts"] }) },
  })

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.put(`/api/v1/shifts/${id}`, { status }).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shifts"] }),
  })

  const shiftList: any[] = Array.isArray(shifts) ? shifts : []

  const getShiftsForDay = (d: Date) =>
    shiftList.filter(s => s.shift_date === d.toISOString().split("T")[0])

  const fmt = (d: Date) => d.toLocaleDateString("en-SA", { month:"short", day:"numeric" })

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Staff Shifts</h1>
        <div style={{ display:"flex", gap:"8px", alignItems:"center" }}>
          <Btn size="sm" onClick={() => setWeekOffset(o => o-1)}>←</Btn>
          <span style={{ fontSize:"12px", minWidth:"160px", textAlign:"center" }}>{fmt(weekDates[0])} – {fmt(weekDates[6])}</span>
          <Btn size="sm" onClick={() => setWeekOffset(o => o+1)}>→</Btn>
          <Btn size="sm" onClick={() => setWeekOffset(0)}>Today</Btn>
          <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>+ Add Shift</Btn>
        </div>
      </div>

      {/* Weekly grid */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
        {/* Header */}
        <div style={{ display:"grid", gridTemplateColumns:"80px repeat(7,1fr)", borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
          <div style={{ padding:"10px 12px", fontSize:"10px", color:"#636882" }}>STAFF</div>
          {weekDates.map((d, i) => {
            const isToday = d.toDateString() === new Date().toDateString()
            return (
              <div key={i} style={{ padding:"10px 8px", textAlign:"center", borderLeft:"1px solid rgba(255,255,255,0.04)" }}>
                <div style={{ fontSize:"10px", color:"#636882" }}>{DAYS[d.getDay()]}</div>
                <div style={{ fontSize:"14px", fontWeight:700, color:isToday?"#6c63ff":"#f0f2ff",
                  background:isToday?"rgba(108,99,255,0.15)":"transparent",
                  borderRadius:"50%", width:"26px", height:"26px", display:"flex", alignItems:"center", justifyContent:"center", margin:"2px auto 0" }}>
                  {d.getDate()}
                </div>
              </div>
            )
          })}
        </div>

        {isLoading ? (
          <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading shifts…</div>
        ) : shiftList.length === 0 ? (
          <div style={{ padding:"60px", textAlign:"center", color:"#636882" }}>
            No shifts this week.<br/><br/>
            <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>Schedule First Shift</Btn>
          </div>
        ) : (
          // Group by staff
          [...new Set(shiftList.map(s => s.staff_id))].map(staffId => (
            <div key={staffId} style={{ display:"grid", gridTemplateColumns:"80px repeat(7,1fr)", borderBottom:"1px solid rgba(255,255,255,0.04)" }}>
              <div style={{ padding:"8px 12px", display:"flex", alignItems:"center" }}>
                <div style={{ width:"28px", height:"28px", borderRadius:"50%", background:"#6c63ff", display:"flex", alignItems:"center", justifyContent:"center", fontSize:"11px", fontWeight:700, color:"#fff" }}>
                  #{staffId}
                </div>
              </div>
              {weekDates.map((d, di) => {
                const dayShifts = getShiftsForDay(d).filter(s => s.staff_id === staffId)
                return (
                  <div key={di} style={{ padding:"4px", borderLeft:"1px solid rgba(255,255,255,0.04)", minHeight:"60px" }}>
                    {dayShifts.map(shift => (
                      <div key={shift.id}
                        style={{ background:`${STATUS_COLOR[shift.status] || "#6c63ff"}22`, borderLeft:`2px solid ${STATUS_COLOR[shift.status] || "#6c63ff"}`, borderRadius:"0 4px 4px 0", padding:"4px 6px", marginBottom:"2px", fontSize:"10px" }}>
                        <div style={{ fontWeight:600, color:STATUS_COLOR[shift.status] || "#6c63ff" }}>{shift.start_time}–{shift.end_time}</div>
                        <div style={{ display:"flex", gap:"3px", marginTop:"2px" }}>
                          {["confirmed","absent"].map(s => (
                            <button key={s} onClick={() => updateStatus.mutate({ id:shift.id, status:s })}
                              style={{ padding:"1px 4px", borderRadius:"2px", border:"none", background:"rgba(255,255,255,0.1)", color:"#9ba3c0", cursor:"pointer", fontSize:"9px", fontFamily:"inherit" }}>
                              {s === "confirmed" ? "✓" : "✗"}
                            </button>
                          ))}
                          <button onClick={() => deleteShift.mutate(shift.id)}
                            style={{ padding:"1px 4px", borderRadius:"2px", border:"none", background:"rgba(255,107,107,0.15)", color:"#ff6b6b", cursor:"pointer", fontSize:"9px", fontFamily:"inherit" }}>
                            ×
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              })}
            </div>
          ))
        )}
      </div>

      {/* Add Shift Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Schedule Shift">
        <FormRow cols={2}>
          <FormGroup label="Staff ID"><input type="number" value={form.staff_id} onChange={e => setForm(f=>({...f,staff_id:e.target.value}))} placeholder="1" /></FormGroup>
          <FormGroup label="Date"><input type="date" value={form.shift_date} onChange={e => setForm(f=>({...f,shift_date:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Start Time"><input type="time" value={form.start_time} onChange={e => setForm(f=>({...f,start_time:e.target.value}))} /></FormGroup>
          <FormGroup label="End Time"><input type="time" value={form.end_time} onChange={e => setForm(f=>({...f,end_time:e.target.value}))} /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", alignItems:"center", gap:"10px", marginBottom:"14px" }}>
          <label style={{ display:"flex", alignItems:"center", gap:"6px", cursor:"pointer", fontSize:"12px" }}>
            <input type="checkbox" checked={form.is_recurring} onChange={e => setForm(f=>({...f,is_recurring:e.target.checked}))} />
            Recurring
          </label>
          {form.is_recurring && (
            <select value={form.recurrence_rule} onChange={e => setForm(f=>({...f,recurrence_rule:e.target.value}))} style={{ width:"120px" }}>
              <option value="weekly">Weekly (4 weeks)</option>
              <option value="biweekly">Bi-weekly</option>
            </select>
          )}
        </div>
        <FormRow>
          <FormGroup label="Notes"><input value={form.notes} onChange={e => setForm(f=>({...f,notes:e.target.value}))} placeholder="Morning opening shift" /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createShift.mutate(form)}>
            {form.is_recurring ? "Schedule (Recurring)" : "Schedule Shift"}
          </Btn>
        </div>
      </Modal>
    </div>
  )
}
