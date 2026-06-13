import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import { KpiCard } from "../components/ui/Card"
import toast from "react-hot-toast"

const TYPES = ["email","sms","whatsapp","multi"]
const SEGMENTS = ["all_members","active","expiring_7d","expiring_30d","expired","frozen","inactive_30d","new_this_month","premium_only"]
const STATUS_TABS = ["all","draft","scheduled","sent","cancelled"]

const typeIcon = (t: string) => ({ email:"📧", sms:"📱", whatsapp:"💬", multi:"🔀" }[t] || "📢")
const statusVariant = (s: string): any => ({ sent:"success", scheduled:"info", draft:"gray", sending:"warning", cancelled:"danger", paused:"warning" }[s] || "gray")

export default function MarketingPage() {
  const [tab, setTab] = useState("all")
  const [addOpen, setAddOpen] = useState(false)
  const [couponOpen, setCouponOpen] = useState(false)
  const [preview, setPreview] = useState<any>(null)
  const [form, setForm] = useState({ name:"", description:"", campaign_type:"sms", target_segment:"all_members", subject:"", message_body:"", scheduled_at:"" })
  const [couponForm, setCouponForm] = useState({ code:"", discount_type:"percentage", discount_value:"", min_purchase:"0", max_uses:"", valid_until:"", description:"" })
  const [segmentCount, setSegmentCount] = useState<number|null>(null)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["campaigns", tab],
    queryFn: () => api.get(`/api/v1/marketing/campaigns${tab !== "all" ? `?status=${tab}` : ""}`).then(r => r.data),
  })

  const { data: stats } = useQuery({
    queryKey: ["campaign-stats"],
    queryFn: () => api.get("/api/v1/marketing/campaigns/stats/overview").then(r => r.data),
  })

  const { data: coupons } = useQuery({
    queryKey: ["coupons"],
    queryFn: () => api.get("/api/v1/marketing/coupons").then(r => r.data),
  })

  const createCampaign = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/marketing/campaigns", {
      ...p, scheduled_at: p.scheduled_at ? new Date(p.scheduled_at).toISOString() : null,
    }).then(r => r.data),
    onSuccess: (d) => { toast.success(`Campaign "${d.name}" created`); qc.invalidateQueries({ queryKey: ["campaigns"] }); setAddOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const sendCampaign = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/marketing/campaigns/${id}/send`).then(r => r.data),
    onSuccess: (d) => { toast.success(d.message); qc.invalidateQueries({ queryKey: ["campaigns"] }); setPreview(null) },
  })

  const cancelCampaign = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/marketing/campaigns/${id}/cancel`).then(r => r.data),
    onSuccess: () => { toast.success("Campaign cancelled"); qc.invalidateQueries({ queryKey: ["campaigns"] }) },
  })

  const createCoupon = useMutation({
    mutationFn: (p: typeof couponForm) => api.post("/api/v1/marketing/coupons", {
      ...p, discount_value: parseFloat(p.discount_value), min_purchase: parseFloat(p.min_purchase),
      max_uses: p.max_uses ? parseInt(p.max_uses) : null,
      valid_until: p.valid_until ? new Date(p.valid_until).toISOString() : null,
    }).then(r => r.data),
    onSuccess: (d) => { toast.success(`Coupon ${d.code} created`); qc.invalidateQueries({ queryKey: ["coupons"] }); setCouponOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const fetchSegmentCount = async (seg: string) => {
    const r = await api.get(`/api/v1/marketing/segments/count?segment=${seg}`)
    setSegmentCount(r.data.count)
  }

  const campaigns = data?.items || []
  const couponList: any[] = Array.isArray(coupons) ? coupons : []

  const VARIABLES = ["{name}","{plan}","{date}","{branch}","{amount}","{expiry}"]

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Marketing Campaigns</h1>
        <div style={{ display:"flex", gap:"8px" }}>
          <Btn size="sm" onClick={() => setCouponOpen(true)}>🎟️ Coupons</Btn>
          <Btn size="sm" variant="primary" onClick={() => setAddOpen(true)}>+ New Campaign</Btn>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:"14px", marginBottom:"20px" }}>
        <KpiCard title="Total Sent" value={(stats?.total_sent||0).toLocaleString()} color="#6c63ff" />
        <KpiCard title="Delivery Rate" value={`${stats?.delivery_rate||0}%`} color="#00e5a0" />
        <KpiCard title="Open Rate" value={`${stats?.open_rate||0}%`} color="#4fc3f7" />
        <KpiCard title="Conversion Rate" value={`${stats?.conversion_rate||0}%`} color="#ffc107" />
        <KpiCard title="Campaigns" value={stats?.total_campaigns||0} color="#ff6b6b" />
      </div>

      {/* Status tabs */}
      <div style={{ display:"flex", gap:"2px", background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"8px", padding:"3px", marginBottom:"16px", width:"fit-content" }}>
        {STATUS_TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ padding:"6px 14px", borderRadius:"5px", cursor:"pointer", fontSize:"12px", border:"none", background: tab===t?"#1f2235":"transparent", color: tab===t?"#f0f2ff":"#636882", fontFamily:"inherit", fontWeight: tab===t?500:400 }}>
            {t.charAt(0).toUpperCase()+t.slice(1)}
          </button>
        ))}
      </div>

      {/* Campaigns table */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden", marginBottom:"20px" }}>
        {isLoading ? <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading…</div> : (
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12.5px" }}>
              <thead>
                <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                  {["Campaign","Type","Segment","Status","Recipients","Sent","Delivered","Open %","Actions"].map(h => (
                    <th key={h} style={{ padding:"10px 14px", textAlign:"left", color:"#636882", fontSize:"11px", textTransform:"uppercase", letterSpacing:"0.5px", whiteSpace:"nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c: any) => (
                  <tr key={c.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                    <td style={{ padding:"11px 14px" }}>
                      <div style={{ fontWeight:600 }}>{c.name}</div>
                      {c.scheduled_at && <div style={{ fontSize:"10px", color:"#636882" }}>📅 {new Date(c.scheduled_at).toLocaleString()}</div>}
                    </td>
                    <td style={{ padding:"11px 14px" }}><span style={{ fontSize:"16px" }}>{typeIcon(c.campaign_type)}</span> <span style={{ fontSize:"11px", color:"#9ba3c0" }}>{c.campaign_type}</span></td>
                    <td style={{ padding:"11px 14px", fontSize:"11px", color:"#636882" }}>{c.target_segment?.replace(/_/g," ")}</td>
                    <td style={{ padding:"11px 14px" }}><Badge variant={statusVariant(c.status)}>{c.status}</Badge></td>
                    <td style={{ padding:"11px 14px", color:"#9ba3c0" }}>{(c.recipient_count||0).toLocaleString()}</td>
                    <td style={{ padding:"11px 14px", color:"#9ba3c0" }}>{(c.sent_count||0).toLocaleString()}</td>
                    <td style={{ padding:"11px 14px", color:"#00e5a0" }}>{(c.delivered_count||0).toLocaleString()}</td>
                    <td style={{ padding:"11px 14px", color:"#4fc3f7" }}>
                      {c.sent_count > 0 ? `${((c.opened_count||0)/c.sent_count*100).toFixed(1)}%` : "—"}
                    </td>
                    <td style={{ padding:"11px 14px" }}>
                      <div style={{ display:"flex", gap:"4px" }}>
                        <Btn size="sm" onClick={() => setPreview(c)}>View</Btn>
                        {["draft","scheduled"].includes(c.status) && (
                          <Btn size="sm" variant="primary" onClick={() => sendCampaign.mutate(c.id)}>Send</Btn>
                        )}
                        {["draft","scheduled"].includes(c.status) && (
                          <Btn size="sm" variant="danger" onClick={() => cancelCampaign.mutate(c.id)}>Cancel</Btn>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!campaigns.length && (
                  <tr><td colSpan={9} style={{ padding:"40px", textAlign:"center", color:"#636882" }}>No campaigns. Create your first one.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Coupons section */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", padding:"20px" }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"14px" }}>
          <div style={{ fontSize:"13px", fontWeight:600 }}>🎟️ Coupons & Promotions</div>
          <Btn size="sm" variant="primary" onClick={() => setCouponOpen(true)}>+ New Coupon</Btn>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))", gap:"10px" }}>
          {couponList.map((c: any) => (
            <div key={c.id} style={{ background:"#14161f", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"8px", padding:"14px" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"8px" }}>
                <span style={{ fontFamily:"monospace", fontWeight:700, color:"#6c63ff", fontSize:"14px" }}>{c.code}</span>
                <Badge variant={c.is_active?"success":"gray"}>{c.is_active?"Active":"Inactive"}</Badge>
              </div>
              <div style={{ fontSize:"18px", fontWeight:700, marginBottom:"4px" }}>
                {c.discount_type==="percentage" ? `${c.discount_value}% OFF` : `SAR ${c.discount_value} OFF`}
              </div>
              <div style={{ fontSize:"11px", color:"#636882" }}>
                {c.max_uses ? `${c.uses_count}/${c.max_uses} uses` : `${c.uses_count} uses`}
                {c.valid_until && ` · Expires ${new Date(c.valid_until).toLocaleDateString()}`}
              </div>
            </div>
          ))}
          {!couponList.length && (
            <div style={{ color:"#636882", fontSize:"12px", gridColumn:"1/-1", textAlign:"center", padding:"20px" }}>
              No coupons created yet.
            </div>
          )}
        </div>
      </div>

      {/* Create Campaign Modal */}
      <Modal open={addOpen} onClose={() => { setAddOpen(false); setSegmentCount(null) }} title="New Campaign">
        <FormRow cols={2}>
          <FormGroup label="Campaign Name"><input value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} placeholder="Ramadan Special 2026" /></FormGroup>
          <FormGroup label="Type">
            <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"6px" }}>
              {TYPES.map(t => (
                <button key={t} onClick={() => setForm(f=>({...f,campaign_type:t}))}
                  style={{ padding:"7px 4px", borderRadius:"6px", border:`1px solid ${form.campaign_type===t?"#6c63ff":"rgba(255,255,255,0.1)"}`, background: form.campaign_type===t?"rgba(108,99,255,0.15)":"transparent", color: form.campaign_type===t?"#6c63ff":"#9ba3c0", cursor:"pointer", fontSize:"11px", fontFamily:"inherit", display:"flex", flexDirection:"column", alignItems:"center", gap:"3px" }}>
                  <span style={{ fontSize:"14px" }}>{typeIcon(t)}</span>{t}
                </button>
              ))}
            </div>
          </FormGroup>
        </FormRow>

        <div style={{ marginBottom:"14px" }}>
          <label style={{ fontSize:"11px", fontWeight:500, color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", display:"block", marginBottom:"6px" }}>Target Segment</label>
          <div style={{ display:"flex", gap:"8px" }}>
            <select value={form.target_segment} onChange={e => { setForm(f=>({...f,target_segment:e.target.value})); fetchSegmentCount(e.target.value) }} style={{ flex:1 }}>
              {SEGMENTS.map(s => <option key={s} value={s}>{s.replace(/_/g," ")}</option>)}
            </select>
            {segmentCount !== null && (
              <div style={{ padding:"8px 14px", background:"rgba(108,99,255,0.1)", borderRadius:"6px", fontSize:"12px", color:"#6c63ff", whiteSpace:"nowrap" }}>
                👥 {segmentCount.toLocaleString()} recipients
              </div>
            )}
          </div>
        </div>

        {form.campaign_type === "email" && (
          <FormRow>
            <FormGroup label="Email Subject"><input value={form.subject} onChange={e => setForm(f=>({...f,subject:e.target.value}))} placeholder="Don't miss our summer special 🔥" /></FormGroup>
          </FormRow>
        )}

        <FormGroup label={`Message${form.campaign_type==="sms"?" (max 160 chars)":""}`}>
          <textarea
            value={form.message_body}
            onChange={e => setForm(f=>({...f,message_body:e.target.value}))}
            rows={4}
            placeholder={form.campaign_type==="sms" ? "Hi {name}, your {plan} membership expires on {date}. Renew now!" : "Dear {name}, we have an exclusive offer for you…"}
          />
          <div style={{ fontSize:"10px", color:"#636882", marginTop:"4px", display:"flex", gap:"6px", flexWrap:"wrap" }}>
            {VARIABLES.map(v => (
              <button key={v} onClick={() => setForm(f=>({...f,message_body:f.message_body+v}))}
                style={{ padding:"2px 6px", borderRadius:"3px", background:"#14161f", border:"1px solid rgba(255,255,255,0.1)", color:"#6c63ff", cursor:"pointer", fontSize:"10px", fontFamily:"monospace" }}>
                {v}
              </button>
            ))}
          </div>
          {form.campaign_type==="sms" && <div style={{ fontSize:"10px", color: form.message_body.length>160?"#ff6b6b":"#636882", marginTop:"4px" }}>{form.message_body.length}/160</div>}
        </FormGroup>

        <FormRow cols={2} style={{ marginTop:"12px" }}>
          <FormGroup label="Schedule (optional)"><input type="datetime-local" value={form.scheduled_at} onChange={e => setForm(f=>({...f,scheduled_at:e.target.value}))} /></FormGroup>
        </FormRow>

        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn onClick={() => createCampaign.mutate({...form, status:"draft"} as any)}>Save Draft</Btn>
          <Btn variant="primary" onClick={() => createCampaign.mutate(form)}>
            {form.scheduled_at ? "Schedule" : "Create Campaign"}
          </Btn>
        </div>
      </Modal>

      {/* Campaign Preview Modal */}
      {preview && (
        <Modal open={!!preview} onClose={() => setPreview(null)} title={preview.name}>
          <div style={{ display:"grid", gap:"8px", marginBottom:"16px" }}>
            {[
              ["Type", `${typeIcon(preview.campaign_type)} ${preview.campaign_type}`],
              ["Status", preview.status],
              ["Segment", preview.target_segment?.replace(/_/g," ")],
              ["Recipients", preview.recipient_count?.toLocaleString()],
              ["Sent", preview.sent_count?.toLocaleString()],
              ["Delivered", `${preview.delivered_count?.toLocaleString()} (${preview.sent_count>0?(preview.delivered_count/preview.sent_count*100).toFixed(1):0}%)`],
              ["Sent At", preview.sent_at ? new Date(preview.sent_at).toLocaleString() : "—"],
            ].map(([l,v]) => (
              <div key={l} style={{ display:"flex", justifyContent:"space-between", padding:"7px 0", borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
                <span style={{ fontSize:"12px", color:"#636882" }}>{l}</span>
                <span style={{ fontSize:"12px", fontWeight:500 }}>{v}</span>
              </div>
            ))}
          </div>
          <div style={{ background:"#14161f", borderRadius:"8px", padding:"14px", marginBottom:"16px" }}>
            <div style={{ fontSize:"11px", color:"#636882", marginBottom:"8px", textTransform:"uppercase", letterSpacing:"0.5px" }}>Message Preview</div>
            <div style={{ fontSize:"13px", lineHeight:1.6, color:"#f0f2ff" }}>{preview.message_body}</div>
          </div>
          <div style={{ display:"flex", gap:"8px" }}>
            {["draft","scheduled"].includes(preview.status) && (
              <Btn variant="primary" onClick={() => sendCampaign.mutate(preview.id)}>🚀 Send Now</Btn>
            )}
            {["draft","scheduled"].includes(preview.status) && (
              <Btn variant="danger" onClick={() => cancelCampaign.mutate(preview.id)}>Cancel</Btn>
            )}
            <Btn onClick={() => setPreview(null)} style={{ marginLeft:"auto" }}>Close</Btn>
          </div>
        </Modal>
      )}

      {/* Create Coupon Modal */}
      <Modal open={couponOpen} onClose={() => setCouponOpen(false)} title="Create Coupon" width={420}>
        <FormRow cols={2}>
          <FormGroup label="Coupon Code"><input value={couponForm.code} onChange={e => setCouponForm(f=>({...f,code:e.target.value.toUpperCase()}))} placeholder="SUMMER20" style={{ fontFamily:"monospace", letterSpacing:"2px" }} /></FormGroup>
          <FormGroup label="Discount Type">
            <select value={couponForm.discount_type} onChange={e => setCouponForm(f=>({...f,discount_type:e.target.value}))}>
              <option value="percentage">Percentage (%)</option>
              <option value="fixed">Fixed Amount (SAR)</option>
            </select>
          </FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label={couponForm.discount_type==="percentage"?"Discount %":"Discount (SAR)"}>
            <input type="number" value={couponForm.discount_value} onChange={e => setCouponForm(f=>({...f,discount_value:e.target.value}))} placeholder={couponForm.discount_type==="percentage"?"20":"100"} />
          </FormGroup>
          <FormGroup label="Min Purchase (SAR)">
            <input type="number" value={couponForm.min_purchase} onChange={e => setCouponForm(f=>({...f,min_purchase:e.target.value}))} />
          </FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Max Uses (blank = unlimited)">
            <input type="number" value={couponForm.max_uses} onChange={e => setCouponForm(f=>({...f,max_uses:e.target.value}))} placeholder="100" />
          </FormGroup>
          <FormGroup label="Valid Until">
            <input type="date" value={couponForm.valid_until} onChange={e => setCouponForm(f=>({...f,valid_until:e.target.value}))} />
          </FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"8px" }}>
          <Btn onClick={() => setCouponOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createCoupon.mutate(couponForm)}>Create Coupon</Btn>
        </div>
      </Modal>
    </div>
  )
}
