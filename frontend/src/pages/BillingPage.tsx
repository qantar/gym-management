import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import { KpiCard } from "../components/ui/Card"
import toast from "react-hot-toast"

type InvoiceStatus = "draft"|"pending"|"paid"|"overdue"|"cancelled"|"refunded"|"partial"

const STATUS_TAB: Record<string, InvoiceStatus|undefined> = {
  all: undefined, pending: "pending", overdue: "overdue", paid: "paid",
}

const statusVariant = (s: string): any =>
  ({ paid:"success", overdue:"danger", pending:"warning", partial:"warning", cancelled:"gray", refunded:"gray" }[s] || "gray")

export default function BillingPage() {
  const [tab, setTab] = useState("all")
  const [addOpen, setAddOpen] = useState(false)
  const [payOpen, setPayOpen] = useState<number|null>(null)
  const [page, setPage] = useState(1)
  const [form, setForm] = useState({ member_id: "", branch_id: 1, description: "", subtotal: "", discount_amount: "0", tax_rate: "15", due_date: "", notes: "" })
  const [payForm, setPayForm] = useState({ amount: "", method: "cash", reference: "" })
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["invoices", tab, page],
    queryFn: () => api.get(`/api/v1/invoices/?page=${page}&page_size=20${STATUS_TAB[tab] ? `&status=${STATUS_TAB[tab]}` : ""}`).then(r => r.data),
  })

  const { data: overdueData } = useQuery({
    queryKey: ["invoices-overdue-summary"],
    queryFn: () => api.get("/api/v1/invoices/summary/overdue").then(r => r.data),
  })

  const createInvoice = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/invoices/", {
      ...p, member_id: parseInt(p.member_id), subtotal: parseFloat(p.subtotal),
      discount_amount: parseFloat(p.discount_amount), tax_rate: parseFloat(p.tax_rate),
      due_date: new Date(p.due_date).toISOString(),
    }).then(r => r.data),
    onSuccess: (d) => { toast.success(`Invoice ${d.invoice_number} created`); qc.invalidateQueries({ queryKey: ["invoices"] }); setAddOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const recordPayment = useMutation({
    mutationFn: ({ id, ...p }: { id: number; amount: string; method: string; reference: string }) =>
      api.post(`/api/v1/invoices/${id}/pay`, { invoice_id: id, amount: parseFloat(p.amount), method: p.method, reference: p.reference }).then(r => r.data),
    onSuccess: (d) => { toast.success(d.message); qc.invalidateQueries({ queryKey: ["invoices"] }); setPayOpen(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Payment failed"),
  })

  const runCollections = useMutation({
    mutationFn: () => api.post("/api/v1/invoices/run-collections").then(r => r.data),
    onSuccess: (d) => { toast.success(d.message); qc.invalidateQueries({ queryKey: ["invoices"] }) },
  })

  const cancel = useMutation({
    mutationFn: (id: number) => api.post(`/api/v1/invoices/${id}/cancel`).then(r => r.data),
    onSuccess: () => { toast.success("Invoice cancelled"); qc.invalidateQueries({ queryKey: ["invoices"] }) },
  })

  const invoices = data?.items || []

  const subtotal = parseFloat(form.subtotal || "0")
  const discount = parseFloat(form.discount_amount || "0")
  const tax = (subtotal - discount) * 0.15
  const total = subtotal - discount + tax

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Billing & Payments</h1>
        <div style={{ display:"flex", gap:"8px" }}>
          <Btn onClick={() => runCollections.mutate()} size="sm">Run Collections</Btn>
          <Btn variant="primary" size="sm" onClick={() => setAddOpen(true)}>+ New Invoice</Btn>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"16px", marginBottom:"20px" }}>
        <KpiCard title="Revenue This Month" value="SAR 487,200" delta="↑ +12.4%" color="#00e5a0" />
        <KpiCard title="Outstanding" value={`SAR ${parseFloat(overdueData?.overdue_total||"0").toLocaleString()}`} delta={`${overdueData?.overdue_count||0} overdue`} color="#ff6b6b" />
        <KpiCard title="Collected Today" value="SAR 18,420" color="#6c63ff" />
        <KpiCard title="Pending" value={data?.total||0} color="#ffc107" />
      </div>

      {/* Tabs */}
      <div style={{ display:"flex", gap:"2px", background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"8px", padding:"3px", marginBottom:"16px", width:"fit-content" }}>
        {["all","pending","overdue","paid"].map(t => (
          <button key={t} onClick={() => { setTab(t); setPage(1) }}
            style={{ padding:"6px 16px", borderRadius:"5px", cursor:"pointer", fontSize:"12px", border:"none", background: tab===t ? "#1f2235" : "transparent", color: tab===t ? "#f0f2ff" : "#636882", fontFamily:"inherit", fontWeight: tab===t ? 500 : 400 }}>
            {t.charAt(0).toUpperCase()+t.slice(1)}
            {t==="overdue" && overdueData?.overdue_count > 0 && <span style={{ marginLeft:"6px", background:"#ff6b6b", color:"#fff", fontSize:"10px", padding:"1px 6px", borderRadius:"10px" }}>{overdueData.overdue_count}</span>}
          </button>
        ))}
      </div>

      {/* Table */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
        {isLoading ? (
          <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading invoices…</div>
        ) : (
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12.5px" }}>
              <thead>
                <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                  {["Invoice","Member","Amount","Due","Status","Method","Actions"].map(h => (
                    <th key={h} style={{ padding:"10px 14px", textAlign:"left", color:"#636882", fontSize:"11px", textTransform:"uppercase", letterSpacing:"0.5px" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invoices.map((inv: any) => (
                  <tr key={inv.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                    <td style={{ padding:"11px 14px", fontWeight:600, color:"#6c63ff" }}>{inv.invoice_number}</td>
                    <td style={{ padding:"11px 14px", color:"#9ba3c0" }}>Member #{inv.member_id}</td>
                    <td style={{ padding:"11px 14px", fontWeight:600 }}>SAR {parseFloat(inv.total).toLocaleString("en-SA",{minimumFractionDigits:2})}</td>
                    <td style={{ padding:"11px 14px", color: inv.status==="overdue" ? "#ff6b6b" : "#9ba3c0" }}>{new Date(inv.due_date).toLocaleDateString()}</td>
                    <td style={{ padding:"11px 14px" }}><Badge variant={statusVariant(inv.status)}>{inv.status}</Badge></td>
                    <td style={{ padding:"11px 14px", color:"#636882" }}>—</td>
                    <td style={{ padding:"11px 14px" }}>
                      <div style={{ display:"flex", gap:"4px" }}>
                        {["pending","overdue","partial"].includes(inv.status) && (
                          <Btn size="sm" variant="success" onClick={() => { setPayOpen(inv.id); setPayForm({ amount: inv.amount_due, method:"cash", reference:"" }) }}>Pay</Btn>
                        )}
                        {["pending","overdue"].includes(inv.status) && (
                          <Btn size="sm" variant="danger" onClick={() => cancel.mutate(inv.id)}>Cancel</Btn>
                        )}
                        <Btn size="sm" onClick={() => toast("PDF generation in progress…")}>PDF</Btn>
                      </div>
                    </td>
                  </tr>
                ))}
                {invoices.length === 0 && (
                  <tr><td colSpan={7} style={{ padding:"40px", textAlign:"center", color:"#636882" }}>No invoices found.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data?.pages > 1 && (
          <div style={{ padding:"12px 16px", borderTop:"1px solid rgba(255,255,255,0.05)", display:"flex", gap:"8px", alignItems:"center", justifyContent:"flex-end" }}>
            <Btn size="sm" onClick={() => setPage(p => Math.max(1, p-1))} >← Prev</Btn>
            <span style={{ fontSize:"12px", color:"#636882" }}>Page {page} of {data.pages}</span>
            <Btn size="sm" onClick={() => setPage(p => Math.min(data.pages, p+1))}>Next →</Btn>
          </div>
        )}
      </div>

      {/* Create Invoice Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Create Invoice">
        <FormRow cols={2}>
          <FormGroup label="Member ID"><input type="number" value={form.member_id} onChange={e => setForm(f => ({...f,member_id:e.target.value}))} placeholder="1" /></FormGroup>
          <FormGroup label="Due Date"><input type="date" value={form.due_date} onChange={e => setForm(f => ({...f,due_date:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Description"><input value={form.description} onChange={e => setForm(f => ({...f,description:e.target.value}))} placeholder="Premium Annual Membership Renewal" /></FormGroup>
        </FormRow>
        <FormRow cols={3}>
          <FormGroup label="Amount (SAR)"><input type="number" value={form.subtotal} onChange={e => setForm(f => ({...f,subtotal:e.target.value}))} placeholder="2400" /></FormGroup>
          <FormGroup label="Discount (SAR)"><input type="number" value={form.discount_amount} onChange={e => setForm(f => ({...f,discount_amount:e.target.value}))} /></FormGroup>
          <FormGroup label="Tax Rate (%)"><input type="number" value={form.tax_rate} onChange={e => setForm(f => ({...f,tax_rate:e.target.value}))} /></FormGroup>
        </FormRow>
        <div style={{ background:"#14161f", borderRadius:"6px", padding:"12px", marginBottom:"16px", display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:"8px", fontSize:"12px" }}>
          <div><span style={{ color:"#636882" }}>Subtotal </span><strong>SAR {(subtotal-discount).toFixed(2)}</strong></div>
          <div><span style={{ color:"#636882" }}>VAT 15% </span><strong>SAR {tax.toFixed(2)}</strong></div>
          <div><span style={{ color:"#636882" }}>Total </span><strong style={{ color:"#6c63ff" }}>SAR {total.toFixed(2)}</strong></div>
        </div>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createInvoice.mutate(form)}>Create Invoice</Btn>
        </div>
      </Modal>

      {/* Record Payment Modal */}
      <Modal open={!!payOpen} onClose={() => setPayOpen(null)} title="Record Payment" width={380}>
        <FormGroup label="Amount (SAR)">
          <input type="number" value={payForm.amount} onChange={e => setPayForm(f => ({...f,amount:e.target.value}))} />
        </FormGroup>
        <div style={{ margin:"12px 0" }}>
          <label style={{ fontSize:"11px", fontWeight:500, color:"#636882", textTransform:"uppercase", letterSpacing:"0.5px", display:"block", marginBottom:"6px" }}>Payment Method</label>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:"6px" }}>
            {["cash","card","bank_transfer"].map(m => (
              <button key={m} onClick={() => setPayForm(f => ({...f,method:m}))}
                style={{ padding:"8px", borderRadius:"6px", border:`1px solid ${payForm.method===m?"#6c63ff":"rgba(255,255,255,0.12)"}`, background: payForm.method===m ? "rgba(108,99,255,0.15)":"transparent", color: payForm.method===m ? "#6c63ff":"#9ba3c0", cursor:"pointer", fontSize:"11px", fontFamily:"inherit" }}>
                {m==="cash"?"💵 Cash":m==="card"?"💳 Card":"🏦 Bank"}
              </button>
            ))}
          </div>
        </div>
        <FormGroup label="Reference (optional)">
          <input value={payForm.reference} onChange={e => setPayForm(f => ({...f,reference:e.target.value}))} placeholder="Transaction ID or receipt #" />
        </FormGroup>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px", marginTop:"16px" }}>
          <Btn onClick={() => setPayOpen(null)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => payOpen && recordPayment.mutate({ id: payOpen, ...payForm })}>Record Payment</Btn>
        </div>
      </Modal>
    </div>
  )
}
