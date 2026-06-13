import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import toast from "react-hot-toast"

const BRANCH_ID = 1
const ROOMS = ["Main Floor", "Studio A", "Studio B", "Spinning Room", "Boxing Ring", "Yoga Room", "Free Weights"]
const COLORS = ["#6c63ff","#00e5a0","#4fc3f7","#ffc107","#ff6b6b","#ff9800","#e91e63"]
const DAYS = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]
const HOURS = Array.from({ length: 18 }, (_, i) => i + 5) // 05:00 – 22:00

function getWeekDates(offset = 0) {
  const today = new Date()
  const day = today.getDay()
  const sun = new Date(today)
  sun.setDate(today.getDate() - day + offset * 7)
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(sun)
    d.setDate(sun.getDate() + i)
    return d
  })
}

export default function SchedulingPage() {
  const [view, setView] = useState<"week"|"day"|"list">("week")
  const [weekOffset, setWeekOffset] = useState(0)
  const [addOpen, setAddOpen] = useState(false)
  const [detailClass, setDetailClass] = useState<any>(null)
  const [bookOpen, setBookOpen] = useState<any>(null)
  const [memberId, setMemberId] = useState("")
  const qc = useQueryClient()

  const weekDates = getWeekDates(weekOffset)
  const dateFrom = weekDates[0]
  const dateTo = weekDates[6]

  const [form, setForm] = useState({
    name: "", description: "", room: "Main Floor", start_time: "", end_time: "",
    capacity: "20", is_recurring: false, recurrence_rule: "", color: "#6c63ff", branch_id: BRANCH_ID,
  })

  const { data: schedules, isLoading } = useQuery({
    queryKey: ["schedules", BRANCH_ID, weekOffset],
    queryFn: () => api.get(`/api/v1/schedules/?branch_id=${BRANCH_ID}&date_from=${dateFrom.toISOString()}&date_to=${new Date(dateTo.getTime() + 86400000).toISOString()}`).then(r => r.data),
    refetchInterval: 60000,
  })

  const classList: any[] = Array.isArray(schedules) ? schedules : []

  const createClass = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/schedules/", {
      ...p, capacity: parseInt(p.capacity), branch_id: BRANCH_ID,
    }).then(r => r.data),
    onSuccess: (d) => {
      toast.success(`${d.first?.name || "Class"} created${d.created > 1 ? ` (${d.created} recurring instances)` : ""}`)
      qc.invalidateQueries({ queryKey: ["schedules"] })
      setAddOpen(false)
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const deleteClass = useMutation({
    mutationFn: (id: number) => api.delete(`/api/v1/schedules/${id}`).then(r => r.data),
    onSuccess: () => { toast.success("Class deleted"); qc.invalidateQueries({ queryKey: ["schedules"] }); setDetailClass(null) },
  })

  const bookClass = useMutation({
    mutationFn: ({ scheduleId, memberId }: { scheduleId: number; memberId: number }) =>
      api.post(`/api/v1/schedules/${scheduleId}/book?member_id=${memberId}`).then(r => r.data),
    onSuccess: (d) => {
      toast.success(d.status === "waitlist" ? `Added to waitlist (position ${d.position})` : "Booked successfully!")
      qc.invalidateQueries({ queryKey: ["schedules"] })
      setBookOpen(null)
      setMemberId("")
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Booking failed"),
  })

  // Place class in correct hour/day cell
  const getClassesForCell = (dayDate: Date, hour: number) => {
    return classList.filter(c => {
      const start = new Date(c.start_time)
      return start.toDateString() === dayDate.toDateString() && start.getHours() === hour
    })
  }

  const capacityColor = (enrolled: number, capacity: number) => {
    const pct = capacity > 0 ? (enrolled / capacity) : 0
    return pct >= 1 ? "#ff6b6b" : pct >= 0.8 ? "#ffc107" : "#00e5a0"
  }

  const fmt = (d: Date) => d.toLocaleDateString("en-SA", { month:"short", day:"numeric" })
  const fmtTime = (iso: string) => new Date(iso).toLocaleTimeString("en-SA", { hour:"2-digit", minute:"2-digit" })

  return (
    <div style={{ height: "calc(100vh - 100px)", display: "flex", flexDirection: "column" }}>
      {/* Toolbar */}
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"16px", flexShrink:0 }}>
        <div style={{ display:"flex", gap:"8px", alignItems:"center" }}>
          <Btn size="sm" onClick={() => setWeekOffset(o => o - 1)}>←</Btn>
          <span style={{ fontSize:"13px", fontWeight:600, minWidth:"180px", textAlign:"center" }}>
            {fmt(weekDates[0])} – {fmt(weekDates[6])}
          </span>
          <Btn size="sm" onClick={() => setWeekOffset(o => o + 1)}>→</Btn>
          <Btn size="sm" onClick={() => setWeekOffset(0)}>Today</Btn>
        </div>

        <div style={{ display:"flex", gap:"4px", background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"8px", padding:"3px" }}>
          {(["week","day","list"] as const).map(v => (
            <button key={v} onClick={() => setView(v)}
              style={{ padding:"5px 14px", borderRadius:"5px", cursor:"pointer", fontSize:"12px", border:"none", background:view===v?"#1f2235":"transparent", color:view===v?"#f0f2ff":"#636882", fontFamily:"inherit", textTransform:"capitalize" }}>
              {v}
            </button>
          ))}
        </div>

        <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>+ Add Class</Btn>
      </div>

      {/* Stats strip */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"12px", marginBottom:"16px", flexShrink:0 }}>
        {[
          { label:"Classes This Week", value:classList.length, color:"#6c63ff" },
          { label:"Total Capacity", value:classList.reduce((s,c) => s+c.capacity,0), color:"#4fc3f7" },
          { label:"Total Enrolled", value:classList.reduce((s,c) => s+c.enrolled,0), color:"#00e5a0" },
          { label:"Full Classes", value:classList.filter(c => c.enrolled >= c.capacity).length, color:"#ff6b6b" },
        ].map(k => (
          <div key={k.label} style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"8px", padding:"12px 16px" }}>
            <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", marginBottom:"3px" }}>{k.label}</div>
            <div style={{ fontSize:"22px", fontWeight:700, color:k.color as string }}>{k.value}</div>
          </div>
        ))}
      </div>

      {/* Calendar */}
      <div style={{ flex:1, overflow:"auto", background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px" }}>
        {isLoading ? (
          <div style={{ padding:"60px", textAlign:"center", color:"#636882" }}>Loading schedule…</div>
        ) : view === "week" ? (
          <div style={{ display:"grid", gridTemplateColumns:"56px repeat(7,1fr)", minWidth:"900px" }}>
            {/* Header */}
            <div style={{ borderBottom:"1px solid rgba(255,255,255,0.07)", padding:"10px 8px" }} />
            {weekDates.map((d, i) => {
              const isToday = d.toDateString() === new Date().toDateString()
              return (
                <div key={i} style={{ borderBottom:"1px solid rgba(255,255,255,0.07)", borderLeft:"1px solid rgba(255,255,255,0.04)", padding:"10px 8px", textAlign:"center" }}>
                  <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px" }}>{DAYS[d.getDay()]}</div>
                  <div style={{ fontSize:"16px", fontWeight:700, color:isToday?"#6c63ff":"#f0f2ff", marginTop:"2px",
                    background:isToday?"rgba(108,99,255,0.15)":"transparent", borderRadius:"50%", width:"28px", height:"28px",
                    display:"flex", alignItems:"center", justifyContent:"center", margin:"4px auto 0" }}>
                    {d.getDate()}
                  </div>
                </div>
              )
            })}

            {/* Time grid */}
            {HOURS.map(hour => (
              <>
                <div key={`h${hour}`} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", padding:"8px 6px", textAlign:"right", fontSize:"10px", color:"#636882", paddingTop:"6px" }}>
                  {String(hour).padStart(2,"0")}:00
                </div>
                {weekDates.map((d, di) => {
                  const classes = getClassesForCell(d, hour)
                  return (
                    <div key={`${hour}-${di}`} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", borderLeft:"1px solid rgba(255,255,255,0.04)", padding:"3px", minHeight:"52px", position:"relative" }}>
                      {classes.map(c => (
                        <div key={c.id} onClick={() => setDetailClass(c)}
                          style={{ background:c.color+"22", borderLeft:`3px solid ${c.color}`, borderRadius:"0 4px 4px 0", padding:"4px 6px", marginBottom:"2px", cursor:"pointer", transition:"opacity 0.15s" }}
                          onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.opacity = "0.8"}
                          onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.opacity = "1"}>
                          <div style={{ fontSize:"11px", fontWeight:600, color:c.color, lineHeight:1.2 }}>{c.name}</div>
                          <div style={{ fontSize:"10px", color:"#9ba3c0" }}>
                            {fmtTime(c.start_time)} · {c.room}
                          </div>
                          <div style={{ fontSize:"10px", color:capacityColor(c.enrolled,c.capacity) }}>
                            {c.enrolled}/{c.capacity}
                          </div>
                        </div>
                      ))}
                    </div>
                  )
                })}
              </>
            ))}
          </div>
        ) : view === "list" ? (
          <div style={{ padding:"16px" }}>
            {classList.length === 0 ? (
              <div style={{ textAlign:"center", color:"#636882", padding:"60px" }}>No classes this week.</div>
            ) : (
              <div style={{ display:"flex", flexDirection:"column", gap:"8px" }}>
                {[...classList].sort((a,b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()).map(c => (
                  <div key={c.id} onClick={() => setDetailClass(c)}
                    style={{ background:"#14161f", border:`1px solid ${c.color}33`, borderLeft:`3px solid ${c.color}`, borderRadius:"0 8px 8px 0", padding:"14px 16px", cursor:"pointer", display:"flex", alignItems:"center", gap:"16px" }}>
                    <div style={{ width:"60px", textAlign:"center", flexShrink:0 }}>
                      <div style={{ fontSize:"11px", color:"#636882" }}>{DAYS[new Date(c.start_time).getDay()]}</div>
                      <div style={{ fontSize:"14px", fontWeight:700 }}>{fmtTime(c.start_time)}</div>
                    </div>
                    <div style={{ flex:1 }}>
                      <div style={{ fontSize:"13px", fontWeight:600 }}>{c.name}</div>
                      <div style={{ fontSize:"11px", color:"#636882" }}>{c.room} · {Math.round((new Date(c.end_time).getTime()-new Date(c.start_time).getTime())/60000)} min</div>
                    </div>
                    <div style={{ textAlign:"right" }}>
                      <div style={{ fontSize:"13px", fontWeight:600, color:capacityColor(c.enrolled,c.capacity) }}>{c.enrolled}/{c.capacity}</div>
                      <div style={{ fontSize:"10px", color:"#636882" }}>enrolled</div>
                    </div>
                    {c.is_full && <Badge variant="danger">Full</Badge>}
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          // Day view — today
          <div style={{ display:"grid", gridTemplateColumns:"56px 1fr", padding:"0" }}>
            {HOURS.map(hour => {
              const today = new Date()
              const classes = getClassesForCell(today, hour)
              return (
                <>
                  <div key={`dh${hour}`} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", padding:"8px 6px", textAlign:"right", fontSize:"10px", color:"#636882" }}>
                    {String(hour).padStart(2,"0")}:00
                  </div>
                  <div key={`dc${hour}`} style={{ borderBottom:"1px solid rgba(255,255,255,0.04)", borderLeft:"1px solid rgba(255,255,255,0.04)", padding:"4px 8px", minHeight:"56px" }}>
                    {classes.map(c => (
                      <div key={c.id} onClick={() => setDetailClass(c)}
                        style={{ background:c.color+"22", borderLeft:`3px solid ${c.color}`, borderRadius:"0 6px 6px 0", padding:"6px 10px", marginBottom:"4px", cursor:"pointer" }}>
                        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                          <div>
                            <div style={{ fontSize:"13px", fontWeight:600, color:c.color }}>{c.name}</div>
                            <div style={{ fontSize:"11px", color:"#636882" }}>{fmtTime(c.start_time)} – {fmtTime(c.end_time)} · {c.room}</div>
                          </div>
                          <div style={{ fontSize:"12px", fontWeight:600, color:capacityColor(c.enrolled,c.capacity) }}>{c.enrolled}/{c.capacity}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )
            })}
          </div>
        )}
      </div>

      {/* Add Class Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Class / Session">
        <FormRow cols={2}>
          <FormGroup label="Class Name"><input value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} placeholder="CrossFit WOD" /></FormGroup>
          <FormGroup label="Room">
            <select value={form.room} onChange={e => setForm(f=>({...f,room:e.target.value}))}>
              {ROOMS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </FormGroup>
        </FormRow>
        <FormRow cols={3}>
          <FormGroup label="Start Time"><input type="datetime-local" value={form.start_time} onChange={e => setForm(f=>({...f,start_time:e.target.value}))} /></FormGroup>
          <FormGroup label="End Time"><input type="datetime-local" value={form.end_time} onChange={e => setForm(f=>({...f,end_time:e.target.value}))} /></FormGroup>
          <FormGroup label="Capacity"><input type="number" value={form.capacity} onChange={e => setForm(f=>({...f,capacity:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Color">
            <div style={{ display:"flex", gap:"6px", alignItems:"center" }}>
              {COLORS.map(c => (
                <div key={c} onClick={() => setForm(f=>({...f,color:c}))}
                  style={{ width:"22px", height:"22px", borderRadius:"50%", background:c, cursor:"pointer", border:`2px solid ${form.color===c?"#fff":"transparent"}`, flexShrink:0 }} />
              ))}
            </div>
          </FormGroup>
          <FormGroup label="Recurring">
            <div style={{ display:"flex", alignItems:"center", gap:"10px", paddingTop:"8px" }}>
              <label style={{ display:"flex", alignItems:"center", gap:"6px", cursor:"pointer", fontSize:"12px" }}>
                <input type="checkbox" checked={form.is_recurring} onChange={e => setForm(f=>({...f,is_recurring:e.target.checked}))} />
                Weekly repeat (4 weeks)
              </label>
            </div>
          </FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Description (optional)"><input value={form.description} onChange={e => setForm(f=>({...f,description:e.target.value}))} placeholder="High intensity interval training…" /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createClass.mutate(form)}>
            {form.is_recurring ? "Create (×4 weeks)" : "Add Class"}
          </Btn>
        </div>
      </Modal>

      {/* Class Detail Modal */}
      {detailClass && (
        <Modal open={!!detailClass} onClose={() => setDetailClass(null)} title={detailClass.name}>
          <div style={{ background:"#14161f", borderRadius:"8px", padding:"14px", marginBottom:"16px", display:"grid", gridTemplateColumns:"1fr 1fr", gap:"10px" }}>
            {[
              ["Room", detailClass.room || "—"],
              ["Date", new Date(detailClass.start_time).toLocaleDateString()],
              ["Start", fmtTime(detailClass.start_time)],
              ["End", fmtTime(detailClass.end_time)],
              ["Enrolled", `${detailClass.enrolled} / ${detailClass.capacity}`],
              ["Spots Left", `${detailClass.spots_left}`],
            ].map(([l,v]) => (
              <div key={l}>
                <div style={{ fontSize:"10px", color:"#636882", textTransform:"uppercase", letterSpacing:"0.4px", marginBottom:"2px" }}>{l}</div>
                <div style={{ fontSize:"13px", fontWeight:500 }}>{v}</div>
              </div>
            ))}
          </div>
          {/* Capacity bar */}
          <div style={{ marginBottom:"16px" }}>
            <div style={{ display:"flex", justifyContent:"space-between", fontSize:"11px", color:"#636882", marginBottom:"4px" }}>
              <span>Capacity</span><span>{Math.round(detailClass.enrolled/detailClass.capacity*100)}%</span>
            </div>
            <div style={{ height:"6px", background:"#1f2235", borderRadius:"3px", overflow:"hidden" }}>
              <div style={{ height:"6px", borderRadius:"3px", background:capacityColor(detailClass.enrolled,detailClass.capacity), width:`${Math.min(100,detailClass.enrolled/detailClass.capacity*100)}%`, transition:"width 0.4s" }} />
            </div>
          </div>
          <div style={{ display:"flex", gap:"8px" }}>
            <Btn variant="primary" onClick={() => { setBookOpen(detailClass); setDetailClass(null) }}>Book Member</Btn>
            <Btn variant="danger" onClick={() => deleteClass.mutate(detailClass.id)}>Delete</Btn>
            <Btn onClick={() => setDetailClass(null)} style={{ marginLeft:"auto" }}>Close</Btn>
          </div>
        </Modal>
      )}

      {/* Book Member Modal */}
      {bookOpen && (
        <Modal open={!!bookOpen} onClose={() => { setBookOpen(null); setMemberId("") }} title={`Book: ${bookOpen.name}`} width={380}>
          <div style={{ background:"#14161f", borderRadius:"6px", padding:"10px 14px", marginBottom:"14px", fontSize:"12px" }}>
            {new Date(bookOpen.start_time).toLocaleString()} · {bookOpen.room} · {bookOpen.spots_left} spots left
          </div>
          <FormGroup label="Member ID">
            <input type="number" value={memberId} onChange={e => setMemberId(e.target.value)} placeholder="Enter member ID" autoFocus />
          </FormGroup>
          <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"14px" }}>
            <Btn onClick={() => { setBookOpen(null); setMemberId("") }}>Cancel</Btn>
            <Btn variant="primary" onClick={() => memberId && bookClass.mutate({ scheduleId: bookOpen.id, memberId: parseInt(memberId) })}>
              {bookOpen.spots_left <= 0 ? "Add to Waitlist" : "Book Now"}
            </Btn>
          </div>
        </Modal>
      )}
    </div>
  )
}
