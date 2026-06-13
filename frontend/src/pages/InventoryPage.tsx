import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import { Modal } from "../components/ui/Modal"
import { FormRow, FormGroup, Btn } from "../components/ui/FormField"
import { Badge } from "../components/ui/Badge"
import { KpiCard } from "../components/ui/Card"
import toast from "react-hot-toast"

const CATEGORIES = ["supplements","apparel","equipment","accessories","food","other"]

export default function InventoryPage() {
  const [search, setSearch] = useState("")
  const [category, setCategory] = useState("")
  const [lowStock, setLowStock] = useState(false)
  const [addOpen, setAddOpen] = useState(false)
  const [adjustOpen, setAdjustOpen] = useState<any>(null)
  const [poOpen, setPoOpen] = useState(false)
  const [form, setForm] = useState({ sku:"", name:"", category:"supplements", brand:"", cost_price:"", sell_price:"", stock_quantity:"0", reorder_level:"10", barcode:"", branch_id:1 })
  const [adjForm, setAdjForm] = useState({ quantity:"", movement_type:"in", notes:"", branch_id:1 })
  const [poForm, setPoForm] = useState({ supplier_name:"", total_amount:"", expected_delivery:"", notes:"", branch_id:1 })
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["inventory", search, category, lowStock],
    queryFn: () => api.get(`/api/v1/inventory/products?page_size=50${search?`&search=${search}`:""}${category?`&category=${category}`:""}${lowStock?"&low_stock=true":""}`).then(r => r.data),
  })

  const { data: valuation } = useQuery({
    queryKey: ["inventory-valuation"],
    queryFn: () => api.get("/api/v1/inventory/valuation").then(r => r.data),
  })

  const { data: alerts } = useQuery({
    queryKey: ["low-stock-alerts"],
    queryFn: () => api.get("/api/v1/inventory/alerts/low-stock").then(r => r.data),
  })

  const createProduct = useMutation({
    mutationFn: (p: typeof form) => api.post("/api/v1/inventory/products", {
      ...p, cost_price: parseFloat(p.cost_price), sell_price: parseFloat(p.sell_price),
      stock_quantity: parseInt(p.stock_quantity), reorder_level: parseInt(p.reorder_level),
    }).then(r => r.data),
    onSuccess: () => { toast.success("Product added"); qc.invalidateQueries({ queryKey: ["inventory"] }); setAddOpen(false) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Failed"),
  })

  const adjustStock = useMutation({
    mutationFn: (p: { product_id: number } & typeof adjForm) => api.post("/api/v1/inventory/adjust", {
      ...p, quantity: parseInt(p.quantity),
    }).then(r => r.data),
    onSuccess: (d) => { toast.success(`Stock updated: ${d.new_quantity} units`); qc.invalidateQueries({ queryKey: ["inventory"] }); setAdjustOpen(null) },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Adjustment failed"),
  })

  const createPO = useMutation({
    mutationFn: (p: typeof poForm) => api.post("/api/v1/inventory/purchase-orders", {
      ...p, total_amount: parseFloat(p.total_amount), items: [], expected_delivery: p.expected_delivery || null,
    }).then(r => r.data),
    onSuccess: (d) => { toast.success(`PO ${d.po_number} created`); setPoOpen(false) },
    onError: () => toast.error("Failed to create PO"),
  })

  const stockStatus = (qty: number, reorder: number) => {
    if (qty === 0) return { variant: "danger" as const, label: "Out of Stock" }
    if (qty <= reorder) return { variant: "warning" as const, label: "Low Stock" }
    return { variant: "success" as const, label: "In Stock" }
  }

  const margin = (cost: string, sell: string) => (((parseFloat(sell) - parseFloat(cost)) / parseFloat(sell)) * 100).toFixed(0)

  return (
    <div>
      <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"20px" }}>
        <h1 style={{ fontSize:"15px", fontWeight:600 }}>Inventory</h1>
        <div style={{ display:"flex", gap:"8px" }}>
          <Btn size="sm" onClick={() => setPoOpen(true)}>+ Purchase Order</Btn>
          <Btn size="sm" variant="primary" onClick={() => setAddOpen(true)}>+ Add Product</Btn>
        </div>
      </div>

      {/* KPIs */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:"16px", marginBottom:"20px" }}>
        <KpiCard title="Total SKUs" value={data?.total||0} color="#6c63ff" />
        <KpiCard title="Low Stock" value={alerts?.length||0} delta="Needs reorder" color="#ffc107" />
        <KpiCard title="Inventory Value" value={`SAR ${parseFloat(valuation?.cost_value||"0").toLocaleString()}`} color="#4fc3f7" />
        <KpiCard title="Potential Revenue" value={`SAR ${parseFloat(valuation?.sell_value||"0").toLocaleString()}`} color="#00e5a0" />
      </div>

      {/* Filters */}
      <div style={{ display:"flex", gap:"10px", marginBottom:"16px" }}>
        <input placeholder="Search SKU, name, barcode…" value={search} onChange={e => setSearch(e.target.value)} style={{ flex:1 }} />
        <select value={category} onChange={e => setCategory(e.target.value)} style={{ width:"160px" }}>
          <option value="">All Categories</option>
          {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <button onClick={() => setLowStock(l => !l)}
          style={{ padding:"8px 14px", borderRadius:"6px", border:`1px solid ${lowStock?"#ffc107":"rgba(255,255,255,0.12)"}`, background: lowStock?"rgba(255,193,7,0.1)":"transparent", color: lowStock?"#ffc107":"#9ba3c0", cursor:"pointer", fontSize:"12px", fontFamily:"inherit" }}>
          ⚠️ Low Stock{alerts?.length ? ` (${alerts.length})` : ""}
        </button>
      </div>

      {/* Table */}
      <div style={{ background:"#0f1117", border:"1px solid rgba(255,255,255,0.07)", borderRadius:"10px", overflow:"hidden" }}>
        {isLoading ? (
          <div style={{ padding:"40px", textAlign:"center", color:"#636882" }}>Loading inventory…</div>
        ) : (
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:"12.5px" }}>
              <thead>
                <tr style={{ borderBottom:"1px solid rgba(255,255,255,0.07)" }}>
                  {["SKU","Product","Category","Stock","Reorder","Cost","Sell","Margin","Status","Actions"].map(h => (
                    <th key={h} style={{ padding:"10px 14px", textAlign:"left", color:"#636882", fontSize:"11px", textTransform:"uppercase", letterSpacing:"0.5px", whiteSpace:"nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(data?.items||[]).map((p: any) => {
                  const ss = stockStatus(p.stock_quantity, p.reorder_level)
                  return (
                    <tr key={p.id} style={{ borderBottom:"1px solid rgba(255,255,255,0.03)" }}>
                      <td style={{ padding:"11px 14px", fontSize:"11px", color:"#636882", fontFamily:"monospace" }}>{p.sku}</td>
                      <td style={{ padding:"11px 14px", fontWeight:600 }}>{p.name}</td>
                      <td style={{ padding:"11px 14px" }}><Badge variant="gray">{p.category}</Badge></td>
                      <td style={{ padding:"11px 14px", fontWeight:600, color: p.stock_quantity===0?"#ff6b6b":p.stock_quantity<=p.reorder_level?"#ffc107":"#00e5a0" }}>{p.stock_quantity}</td>
                      <td style={{ padding:"11px 14px", color:"#636882" }}>{p.reorder_level}</td>
                      <td style={{ padding:"11px 14px", color:"#636882" }}>SAR {parseFloat(p.cost_price).toFixed(2)}</td>
                      <td style={{ padding:"11px 14px", fontWeight:600 }}>SAR {parseFloat(p.sell_price).toFixed(2)}</td>
                      <td style={{ padding:"11px 14px", color:"#00e5a0" }}>{margin(p.cost_price, p.sell_price)}%</td>
                      <td style={{ padding:"11px 14px" }}><Badge variant={ss.variant}>{ss.label}</Badge></td>
                      <td style={{ padding:"11px 14px" }}>
                        <div style={{ display:"flex", gap:"4px" }}>
                          <Btn size="sm" onClick={() => { setAdjustOpen(p); setAdjForm({ quantity:"", movement_type:"in", notes:"", branch_id:1 }) }}>Adjust</Btn>
                          {p.stock_quantity <= p.reorder_level && (
                            <Btn size="sm" variant="primary" onClick={() => { setPoForm(f => ({...f, supplier_name:""})); setPoOpen(true) }}>Reorder</Btn>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {!(data?.items||[]).length && (
                  <tr><td colSpan={10} style={{ padding:"40px", textAlign:"center", color:"#636882" }}>No products found. Add your first product.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Product Modal */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="Add Product">
        <FormRow cols={2}>
          <FormGroup label="SKU"><input value={form.sku} onChange={e => setForm(f=>({...f,sku:e.target.value}))} placeholder="PRO-WHY-2KG" /></FormGroup>
          <FormGroup label="Category">
            <select value={form.category} onChange={e => setForm(f=>({...f,category:e.target.value}))}>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Product Name"><input value={form.name} onChange={e => setForm(f=>({...f,name:e.target.value}))} placeholder="Whey Protein 2kg Vanilla" /></FormGroup>
        </FormRow>
        <FormRow cols={3}>
          <FormGroup label="Cost Price (SAR)"><input type="number" value={form.cost_price} onChange={e => setForm(f=>({...f,cost_price:e.target.value}))} /></FormGroup>
          <FormGroup label="Sell Price (SAR)"><input type="number" value={form.sell_price} onChange={e => setForm(f=>({...f,sell_price:e.target.value}))} /></FormGroup>
          <FormGroup label="Barcode"><input value={form.barcode} onChange={e => setForm(f=>({...f,barcode:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow cols={2}>
          <FormGroup label="Initial Stock"><input type="number" value={form.stock_quantity} onChange={e => setForm(f=>({...f,stock_quantity:e.target.value}))} /></FormGroup>
          <FormGroup label="Reorder Level"><input type="number" value={form.reorder_level} onChange={e => setForm(f=>({...f,reorder_level:e.target.value}))} /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setAddOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createProduct.mutate(form)}>Add Product</Btn>
        </div>
      </Modal>

      {/* Adjust Stock Modal */}
      {adjustOpen && (
        <Modal open={!!adjustOpen} onClose={() => setAdjustOpen(null)} title={`Adjust Stock — ${adjustOpen.name}`} width={380}>
          <div style={{ background:"#14161f", borderRadius:"6px", padding:"10px 14px", marginBottom:"16px", fontSize:"12px" }}>
            Current: <strong style={{ color:"#6c63ff" }}>{adjustOpen.stock_quantity} units</strong>
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:"6px", marginBottom:"14px" }}>
            {[{v:"in",l:"➕ Stock In"},{v:"out",l:"➖ Stock Out"},{v:"set",l:"✏️ Set Qty"}].map(m => (
              <button key={m.v} onClick={() => setAdjForm(f=>({...f,movement_type:m.v}))}
                style={{ padding:"8px", borderRadius:"6px", border:`1px solid ${adjForm.movement_type===m.v?"#6c63ff":"rgba(255,255,255,0.12)"}`, background: adjForm.movement_type===m.v?"rgba(108,99,255,0.15)":"transparent", color: adjForm.movement_type===m.v?"#6c63ff":"#9ba3c0", cursor:"pointer", fontSize:"11px", fontFamily:"inherit" }}>
                {m.l}
              </button>
            ))}
          </div>
          <FormGroup label="Quantity">
            <input type="number" value={adjForm.quantity} onChange={e => setAdjForm(f=>({...f,quantity:e.target.value}))} placeholder="0" />
          </FormGroup>
          <div style={{ margin:"12px 0" }}>
            <FormGroup label="Notes">
              <input value={adjForm.notes} onChange={e => setAdjForm(f=>({...f,notes:e.target.value}))} placeholder="Reason for adjustment…" />
            </FormGroup>
          </div>
          <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
            <Btn onClick={() => setAdjustOpen(null)}>Cancel</Btn>
            <Btn variant="primary" onClick={() => adjustStock.mutate({ product_id: adjustOpen.id, ...adjForm })}>Apply Adjustment</Btn>
          </div>
        </Modal>
      )}

      {/* Purchase Order Modal */}
      <Modal open={poOpen} onClose={() => setPoOpen(false)} title="New Purchase Order">
        <FormRow cols={2}>
          <FormGroup label="Supplier"><input value={poForm.supplier_name} onChange={e => setPoForm(f=>({...f,supplier_name:e.target.value}))} placeholder="NutriTech Arabia" /></FormGroup>
          <FormGroup label="Expected Delivery"><input type="date" value={poForm.expected_delivery} onChange={e => setPoForm(f=>({...f,expected_delivery:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Total Amount (SAR)"><input type="number" value={poForm.total_amount} onChange={e => setPoForm(f=>({...f,total_amount:e.target.value}))} /></FormGroup>
        </FormRow>
        <FormRow>
          <FormGroup label="Notes"><textarea value={poForm.notes} onChange={e => setPoForm(f=>({...f,notes:e.target.value}))} placeholder="Line items, product details…" /></FormGroup>
        </FormRow>
        <div style={{ display:"flex", justifyContent:"flex-end", gap:"8px" }}>
          <Btn onClick={() => setPoOpen(false)}>Cancel</Btn>
          <Btn variant="primary" onClick={() => createPO.mutate(poForm)}>Submit Order</Btn>
        </div>
      </Modal>
    </div>
  )
}
