import { useState, useRef, useCallback, useEffect } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../lib/api"
import toast from "react-hot-toast"

interface Product { id: number; name: string; sku: string; sell_price: string; stock_quantity: number; category: string }
interface CartItem extends Product { qty: number; discount: number }

const TAX_RATE = 0.15

const btn = (label: string, onClick: () => void, style: React.CSSProperties = {}) => (
  <button onClick={onClick} style={{ padding: "7px 14px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#f0f2ff", cursor: "pointer", fontSize: "12px", fontFamily: "inherit", ...style }}>{label}</button>
)

export default function POSPage() {
  const [cart, setCart] = useState<CartItem[]>([])
  const [search, setSearch] = useState("")
  const [payMethod, setPayMethod] = useState("cash")
  const [memberSearch, setMemberSearch] = useState("")
  const [selectedMember, setSelectedMember] = useState<{ id: number; name: string } | null>(null)
  const [discount, setDiscount] = useState(0)
  const [coupon, setCoupon] = useState("")
  const searchRef = useRef<HTMLInputElement>(null)
  const qc = useQueryClient()

  // Auto-focus barcode field
  useEffect(() => { searchRef.current?.focus() }, [])

  const { data: products } = useQuery({
    queryKey: ["pos-products", search],
    queryFn: () => search.length > 1
      ? api.get(`/api/v1/pos/products/search?q=${search}`).then(r => r.data)
      : api.get("/api/v1/inventory/products?page_size=50").then(r => r.data.items || []),
    placeholderData: [],
  })

  const { data: summary } = useQuery({
    queryKey: ["pos-summary"],
    queryFn: () => api.get("/api/v1/pos/sales/summary?branch_id=1").then(r => r.data),
    refetchInterval: 60000,
  })

  const addToCart = useCallback((p: Product) => {
    if (p.stock_quantity === 0) { toast.error("Out of stock"); return }
    setCart(prev => {
      const ex = prev.find(c => c.id === p.id)
      if (ex) {
        if (ex.qty >= p.stock_quantity) { toast.error("Max stock reached"); return prev }
        return prev.map(c => c.id === p.id ? { ...c, qty: c.qty + 1 } : c)
      }
      return [...prev, { ...p, qty: 1, discount: 0 }]
    })
    // Clear search so next scan works
    setSearch("")
    searchRef.current?.focus()
  }, [])

  // Barcode scan: if search exactly matches SKU/barcode, add immediately
  const handleSearchKey = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && products?.length === 1) {
      addToCart(products[0])
    }
  }

  const removeFromCart = (id: number) => setCart(prev => prev.filter(c => c.id !== id))
  const updateQty = (id: number, qty: number) => {
    if (qty <= 0) { removeFromCart(id); return }
    setCart(prev => prev.map(c => c.id === id ? { ...c, qty } : c))
  }
  const updateItemDiscount = (id: number, d: number) =>
    setCart(prev => prev.map(c => c.id === id ? { ...c, discount: d } : c))

  const subtotal = cart.reduce((s, c) => s + (parseFloat(c.sell_price) - c.discount) * c.qty, 0)
  const discountAmount = (discount / 100) * subtotal
  const taxable = subtotal - discountAmount
  const taxAmount = taxable * TAX_RATE
  const total = taxable + taxAmount

  const checkout = useMutation({
    mutationFn: () => api.post("/api/v1/pos/sales", {
      branch_id: 1,
      member_id: selectedMember?.id || null,
      payment_method: payMethod,
      discount_amount: discountAmount.toFixed(2),
      tax_rate: "15",
      items: cart.map(c => ({
        product_id: c.id,
        quantity: c.qty,
        unit_price: c.sell_price,
        discount: c.discount.toFixed(2),
      })),
    }).then(r => r.data),
    onSuccess: (sale) => {
      toast.success(`Sale ${sale.sale_number} — SAR ${parseFloat(sale.total).toFixed(2)}`)
      setCart([])
      setDiscount(0)
      setSelectedMember(null)
      qc.invalidateQueries({ queryKey: ["pos-summary"] })
      qc.invalidateQueries({ queryKey: ["pos-products"] })
      // Print receipt via Electron if available
      if (window.gymos) {
        const html = generateReceipt(sale)
        window.gymos.printHTML(html)
      }
    },
    onError: (e: any) => toast.error(e.response?.data?.detail || "Checkout failed"),
  })

  const generateReceipt = (sale: any) => `
    <html><head><style>
      body{font-family:monospace;font-size:12px;width:300px;margin:auto}
      h2{text-align:center}hr{border:1px dashed #ccc}
      .row{display:flex;justify-content:space-between}
      .total{font-weight:bold;font-size:14px}
    </style></head><body>
    <h2>GymOS Enterprise</h2>
    <div style="text-align:center">Al Malaz Branch<br>${new Date().toLocaleString()}</div>
    <hr/>
    ${sale.items.map((i: any) => `<div class="row"><span>${i.product_name} x${i.quantity}</span><span>SAR ${parseFloat(i.line_total).toFixed(2)}</span></div>`).join("")}
    <hr/>
    <div class="row"><span>Subtotal</span><span>SAR ${parseFloat(sale.subtotal).toFixed(2)}</span></div>
    <div class="row"><span>Discount</span><span>-SAR ${parseFloat(sale.discount_amount).toFixed(2)}</span></div>
    <div class="row"><span>VAT 15%</span><span>SAR ${parseFloat(sale.tax_amount).toFixed(2)}</span></div>
    <hr/>
    <div class="row total"><span>TOTAL</span><span>SAR ${parseFloat(sale.total).toFixed(2)}</span></div>
    <div style="text-align:center;margin-top:12px">Payment: ${sale.payment_method.toUpperCase()}<br/>${sale.sale_number}</div>
    <hr/>
    <div style="text-align:center">Thank you!</div>
    </body></html>`

  const colStyle = {
    background: "#0f1117", border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column" as const,
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: "16px", height: "calc(100vh - 100px)" }}>
      {/* ── LEFT: Product Grid ── */}
      <div style={{ ...colStyle, overflow: "hidden" }}>
        {/* KPI strip */}
        <div style={{ display: "flex", gap: "12px", marginBottom: "14px", flexShrink: 0 }}>
          {[
            { label: "Today Revenue", value: `SAR ${parseFloat(summary?.today_revenue || "0").toLocaleString("en-SA", { minimumFractionDigits: 2 })}`, color: "#00e5a0" },
            { label: "Transactions", value: summary?.today_transactions || 0, color: "#4fc3f7" },
            { label: "Cart Items", value: cart.reduce((s, c) => s + c.qty, 0), color: "#6c63ff" },
          ].map(k => (
            <div key={k.label} style={{ background: "#14161f", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "8px", padding: "10px 14px", flex: 1 }}>
              <div style={{ fontSize: "10px", color: "#636882", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "3px" }}>{k.label}</div>
              <div style={{ fontSize: "18px", fontWeight: 600, color: k.color as string }}>{k.value}</div>
            </div>
          ))}
        </div>

        {/* Barcode / search */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "14px", flexShrink: 0 }}>
          <input
            ref={searchRef}
            value={search}
            onChange={e => setSearch(e.target.value)}
            onKeyDown={handleSearchKey}
            placeholder="🔍 Barcode scan or search products…"
            style={{ flex: 1 }}
          />
          <select value={payMethod} onChange={e => setPayMethod(e.target.value)} style={{ width: "120px" }}>
            <option value="cash">💵 Cash</option>
            <option value="card">💳 Card</option>
            <option value="bank_transfer">🏦 Bank</option>
          </select>
        </div>

        {/* Products grid */}
        <div style={{ flex: 1, overflowY: "auto", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: "10px", alignContent: "start" }}>
          {(products as Product[] || []).map(p => (
            <div key={p.id}
              onClick={() => addToCart(p)}
              style={{
                background: "#14161f", border: `1px solid ${p.stock_quantity === 0 ? "rgba(255,107,107,0.3)" : "rgba(255,255,255,0.07)"}`,
                borderRadius: "8px", padding: "12px", cursor: p.stock_quantity === 0 ? "not-allowed" : "pointer",
                opacity: p.stock_quantity === 0 ? 0.5 : 1, transition: "all 0.12s",
              }}
              onMouseEnter={e => p.stock_quantity > 0 && ((e.currentTarget as HTMLDivElement).style.borderColor = "#6c63ff")}
              onMouseLeave={e => ((e.currentTarget as HTMLDivElement).style.borderColor = p.stock_quantity === 0 ? "rgba(255,107,107,0.3)" : "rgba(255,255,255,0.07)")}
            >
              <div style={{ fontSize: "10px", color: "#636882", marginBottom: "4px", textTransform: "uppercase" }}>{p.category}</div>
              <div style={{ fontSize: "12px", fontWeight: 600, marginBottom: "6px", lineHeight: 1.3 }}>{p.name}</div>
              <div style={{ fontSize: "14px", fontWeight: 700, color: "#6c63ff" }}>SAR {parseFloat(p.sell_price).toFixed(2)}</div>
              <div style={{ fontSize: "10px", color: p.stock_quantity <= 5 ? "#ffc107" : "#636882", marginTop: "4px" }}>
                {p.stock_quantity === 0 ? "Out of stock" : `Stock: ${p.stock_quantity}`}
              </div>
            </div>
          ))}
          {(!products || (products as Product[]).length === 0) && (
            <div style={{ gridColumn: "1/-1", textAlign: "center", color: "#636882", padding: "40px" }}>
              {search ? "No products found" : "Loading products…"}
            </div>
          )}
        </div>
      </div>

      {/* ── RIGHT: Cart ── */}
      <div style={{ ...colStyle, gap: 0 }}>
        <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "12px", flexShrink: 0 }}>
          🛒 Cart {cart.length > 0 && <span style={{ color: "#636882", fontWeight: 400 }}>({cart.length} items)</span>}
        </div>

        {/* Member lookup */}
        <div style={{ marginBottom: "10px", flexShrink: 0 }}>
          {selectedMember ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 10px", background: "rgba(108,99,255,0.1)", borderRadius: "6px", border: "1px solid rgba(108,99,255,0.3)" }}>
              <span style={{ fontSize: "12px", color: "#6c63ff" }}>👤 {selectedMember.name}</span>
              <button onClick={() => setSelectedMember(null)} style={{ background: "none", border: "none", color: "#636882", cursor: "pointer" }}>×</button>
            </div>
          ) : (
            <input placeholder="Attach member (optional)…" value={memberSearch} onChange={e => setMemberSearch(e.target.value)} style={{ fontSize: "12px" }} />
          )}
        </div>

        {/* Cart items */}
        <div style={{ flex: 1, overflowY: "auto", marginBottom: "12px" }}>
          {cart.length === 0 ? (
            <div style={{ textAlign: "center", color: "#636882", padding: "40px 0", fontSize: "12px" }}>
              Scan a product or click to add
            </div>
          ) : cart.map(item => (
            <div key={item.id} style={{ padding: "10px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "6px" }}>
                <div>
                  <div style={{ fontSize: "12px", fontWeight: 600 }}>{item.name}</div>
                  <div style={{ fontSize: "10px", color: "#636882" }}>{item.sku} · SAR {parseFloat(item.sell_price).toFixed(2)}</div>
                </div>
                <button onClick={() => removeFromCart(item.id)} style={{ background: "none", border: "none", color: "#636882", cursor: "pointer", fontSize: "16px", lineHeight: 1 }}>×</button>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                  <button onClick={() => updateQty(item.id, item.qty - 1)} style={{ width: "24px", height: "24px", borderRadius: "4px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#f0f2ff", cursor: "pointer", fontSize: "14px" }}>−</button>
                  <span style={{ width: "28px", textAlign: "center", fontSize: "13px", fontWeight: 600 }}>{item.qty}</span>
                  <button onClick={() => updateQty(item.id, item.qty + 1)} style={{ width: "24px", height: "24px", borderRadius: "4px", border: "1px solid rgba(255,255,255,0.12)", background: "transparent", color: "#f0f2ff", cursor: "pointer", fontSize: "14px" }}>+</button>
                </div>
                <input
                  type="number" placeholder="Disc" value={item.discount || ""}
                  onChange={e => updateItemDiscount(item.id, parseFloat(e.target.value) || 0)}
                  style={{ width: "60px", fontSize: "11px", padding: "3px 6px" }}
                />
                <div style={{ marginLeft: "auto", fontSize: "13px", fontWeight: 600, color: "#6c63ff" }}>
                  SAR {((parseFloat(item.sell_price) - item.discount) * item.qty).toFixed(2)}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Totals */}
        <div style={{ borderTop: "1px solid rgba(255,255,255,0.07)", paddingTop: "12px", flexShrink: 0 }}>
          {[
            { label: "Subtotal", value: `SAR ${subtotal.toFixed(2)}` },
            { label: "Discount", value: `-SAR ${discountAmount.toFixed(2)}`, color: "#ffc107" },
            { label: "VAT 15%", value: `SAR ${taxAmount.toFixed(2)}`, muted: true },
          ].map(r => (
            <div key={r.label} style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px", fontSize: "12px" }}>
              <span style={{ color: r.muted ? "#636882" : "#9ba3c0" }}>{r.label}</span>
              <span style={{ color: r.color || "#9ba3c0" }}>{r.value}</span>
            </div>
          ))}

          {/* Cart-level discount */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
            <span style={{ fontSize: "11px", color: "#636882", flexShrink: 0 }}>Cart discount %</span>
            <input type="number" min={0} max={100} value={discount} onChange={e => setDiscount(parseFloat(e.target.value) || 0)} style={{ flex: 1, fontSize: "12px", padding: "4px 8px" }} />
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "14px", fontSize: "16px", fontWeight: 700 }}>
            <span>Total</span>
            <span style={{ color: "#6c63ff" }}>SAR {total.toFixed(2)}</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "8px" }}>
            <button
              onClick={() => { setCart([]); setDiscount(0) }}
              style={{ padding: "10px", borderRadius: "6px", border: "1px solid rgba(255,107,107,0.4)", background: "rgba(255,107,107,0.1)", color: "#ff6b6b", cursor: "pointer", fontSize: "12px", fontFamily: "inherit" }}
            >Clear</button>
            <button
              onClick={() => cart.length > 0 ? checkout.mutate() : toast.error("Cart is empty")}
              disabled={checkout.isPending || cart.length === 0}
              style={{ padding: "10px", borderRadius: "6px", border: "none", background: cart.length === 0 ? "#2a2d3e" : "#6c63ff", color: "#fff", cursor: cart.length === 0 ? "not-allowed" : "pointer", fontSize: "13px", fontWeight: 600, fontFamily: "inherit", opacity: checkout.isPending ? 0.7 : 1 }}
            >{checkout.isPending ? "Processing…" : `💳 Charge SAR ${total.toFixed(2)}`}</button>
          </div>
        </div>
      </div>
    </div>
  )
}

// Extend window type for Electron preload
declare global {
  interface Window {
    gymos?: {
      printHTML: (html: string) => Promise<void>
      getVersion: () => Promise<string>
      minimize: () => void
      maximize: () => void
      close: () => void
      onNavigate: (cb: (route: string) => void) => void
    }
  }
}
