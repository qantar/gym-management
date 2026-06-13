from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.inventory import Product, StockMovement, PurchaseOrder, ProductCategory
from app.models.user import User, UserRole
from app.schemas.inventory import ProductCreate, StockAdjustment, ProductResponse
from app.schemas.common import PaginatedResponse
from pydantic import BaseModel
from datetime import date as DateType
from typing import Optional as Opt, List

router = APIRouter()


class PurchaseOrderCreate(BaseModel):
    branch_id: int
    supplier_name: str
    items: List[dict]
    total_amount: Decimal
    expected_delivery: Opt[DateType] = None
    notes: Opt[str] = None


@router.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    branch_id: Optional[int] = None,
    category: Optional[ProductCategory] = None,
    low_stock: bool = False,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Product).where(Product.is_deleted == False)
    if branch_id:
        query = query.where(Product.branch_id == branch_id)
    if category:
        query = query.where(Product.category == category)
    if low_stock:
        query = query.where(Product.stock_quantity <= Product.reorder_level)
    if search:
        query = query.where(
            or_(Product.name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%"), Product.barcode.ilike(f"%{search}%"))
        )
    query = query.order_by(Product.name)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(items=result.scalars().all(), total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size)


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(select(Product).where(Product.sku == payload.sku))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"SKU '{payload.sku}' already exists")
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Product).where(Product.id == product_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Product not found")
    return p


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int, payload: dict,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(Product).where(Product.id == product_id))
    p = r.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Product not found")
    for k, v in payload.items():
        if hasattr(p, k):
            setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    return p


@router.post("/adjust")
async def adjust_stock(
    payload: StockAdjustment,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(Product).where(Product.id == payload.product_id))
    product = r.scalar_one_or_none()
    if not product:
        raise HTTPException(404, "Product not found")
    qty_before = product.stock_quantity
    if payload.movement_type == "in":
        product.stock_quantity += payload.quantity
    elif payload.movement_type == "out":
        if product.stock_quantity < payload.quantity:
            raise HTTPException(400, "Insufficient stock")
        product.stock_quantity -= payload.quantity
    elif payload.movement_type == "set":
        product.stock_quantity = payload.quantity
    movement = StockMovement(
        product_id=product.id, branch_id=payload.branch_id,
        movement_type=payload.movement_type, quantity=payload.quantity,
        quantity_before=qty_before, quantity_after=product.stock_quantity,
        notes=payload.notes, created_by_id=current_user.id,
    )
    db.add(movement)
    await db.commit()
    return {"new_quantity": product.stock_quantity, "movement_type": payload.movement_type}


@router.get("/products/{product_id}/movements")
async def product_movements(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(StockMovement).where(StockMovement.product_id == product_id).order_by(StockMovement.created_at.desc()).limit(50))
    return r.scalars().all()


@router.get("/alerts/low-stock")
async def low_stock_alerts(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Product).where(Product.is_deleted == False, Product.stock_quantity <= Product.reorder_level, Product.is_active == True)
    if branch_id:
        query = query.where(Product.branch_id == branch_id)
    r = await db.execute(query)
    products = r.scalars().all()
    return [{"id": p.id, "name": p.name, "sku": p.sku, "stock": p.stock_quantity, "reorder_level": p.reorder_level, "status": "out_of_stock" if p.stock_quantity == 0 else "low_stock"} for p in products]


@router.get("/valuation")
async def inventory_valuation(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = select(
        func.count(Product.id),
        func.sum(Product.stock_quantity * Product.cost_price),
        func.sum(Product.stock_quantity * Product.sell_price),
    ).where(Product.is_deleted == False, Product.is_active == True)
    if branch_id:
        q = q.where(Product.branch_id == branch_id)
    r = await db.execute(q)
    count, cost_val, sell_val = r.one()
    return {"sku_count": count, "cost_value": str(cost_val or 0), "sell_value": str(sell_val or 0), "potential_margin": str((sell_val or 0) - (cost_val or 0))}


@router.post("/purchase-orders", status_code=201)
async def create_purchase_order(payload: PurchaseOrderCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    import uuid
    po = PurchaseOrder(
        po_number=f"PO-{str(uuid.uuid4())[:8].upper()}",
        branch_id=payload.branch_id,
        supplier_name=payload.supplier_name,
        total_amount=payload.total_amount,
        expected_delivery=payload.expected_delivery,
        notes=payload.notes,
        created_by_id=current_user.id,
    )
    db.add(po)
    await db.commit()
    await db.refresh(po)
    return po


@router.get("/purchase-orders")
async def list_purchase_orders(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = select(PurchaseOrder)
    if branch_id:
        q = q.where(PurchaseOrder.branch_id == branch_id)
    q = q.order_by(PurchaseOrder.created_at.desc())
    r = await db.execute(q)
    return r.scalars().all()


@router.put("/purchase-orders/{po_id}/receive")
async def receive_purchase_order(po_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date
    r = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = r.scalar_one_or_none()
    if not po:
        raise HTTPException(404, "Purchase order not found")
    po.status = "received"
    po.received_at = date.today()
    await db.commit()
    return {"message": "Purchase order marked as received"}
