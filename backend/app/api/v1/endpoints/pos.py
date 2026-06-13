from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import date
from typing import Optional, List
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.pos import Sale, SaleItem, SaleStatus
from app.models.inventory import Product, StockMovement
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int
    unit_price: Decimal
    discount: Decimal = Decimal("0")


class SaleIn(BaseModel):
    branch_id: int
    member_id: Optional[int] = None
    items: List[SaleItemIn]
    payment_method: str = "cash"
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("15")
    notes: Optional[str] = None


class SaleItemOut(BaseModel):
    id: int
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Decimal
    discount: Decimal
    line_total: Decimal
    class Config: from_attributes = True


class SaleOut(BaseModel):
    id: int
    sale_number: str
    branch_id: int
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    payment_method: str
    status: SaleStatus
    items: List[SaleItemOut]
    class Config: from_attributes = True


@router.post("/sales", response_model=SaleOut, status_code=201)
async def create_sale(
    payload: SaleIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subtotal = Decimal("0")
    db_items = []

    for item in payload.items:
        # Validate product & stock
        r = await db.execute(select(Product).where(Product.id == item.product_id))
        product = r.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock_quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.name}")

        line_total = (item.unit_price - item.discount) * item.quantity
        subtotal += line_total

        # Deduct stock
        qty_before = product.stock_quantity
        product.stock_quantity -= item.quantity
        db.add(StockMovement(
            product_id=product.id, branch_id=payload.branch_id,
            movement_type="sale_out", quantity=item.quantity,
            quantity_before=qty_before, quantity_after=product.stock_quantity,
            created_by_id=current_user.id,
        ))

        db_items.append(SaleItem(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount=item.discount,
            line_total=line_total,
        ))

    net = subtotal - payload.discount_amount
    tax_amount = net * (payload.tax_rate / 100)
    total = net + tax_amount

    sale = Sale(
        sale_number=f"POS-{str(uuid.uuid4())[:8].upper()}",
        branch_id=payload.branch_id,
        member_id=payload.member_id,
        cashier_id=current_user.id,
        subtotal=subtotal,
        discount_amount=payload.discount_amount,
        tax_amount=tax_amount,
        total=total,
        payment_method=payload.payment_method,
        notes=payload.notes,
        items=db_items,
    )
    db.add(sale)
    await db.commit()
    await db.refresh(sale)
    return sale


@router.get("/sales", response_model=list[SaleOut])
async def list_sales(
    branch_id: Optional[int] = None,
    date_from: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Sale)
    if branch_id:
        query = query.where(Sale.branch_id == branch_id)
    if date_from:
        query = query.where(func.date(Sale.created_at) >= date_from)
    query = query.order_by(Sale.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    r = await db.execute(query)
    return r.unique().scalars().all()


@router.get("/sales/summary")
async def sales_summary(
    branch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    r = await db.execute(
        select(func.sum(Sale.total), func.count(Sale.id)).where(
            func.date(Sale.created_at) == today,
            Sale.branch_id == branch_id,
            Sale.status == SaleStatus.COMPLETED,
        )
    )
    total_revenue, count = r.one()
    return {"today_revenue": str(total_revenue or 0), "today_transactions": count, "date": str(today)}


@router.post("/sales/{sale_id}/void")
async def void_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = r.unique().scalar_one_or_none()
    if not sale:
        raise HTTPException(404, "Sale not found")
    if sale.status != SaleStatus.COMPLETED:
        raise HTTPException(400, "Can only void completed sales")
    # Restore stock
    for item in sale.items:
        p_r = await db.execute(select(Product).where(Product.id == item.product_id))
        product = p_r.scalar_one_or_none()
        if product:
            product.stock_quantity += item.quantity
    sale.status = SaleStatus.VOIDED
    await db.commit()
    return {"message": "Sale voided"}


@router.get("/products/search")
async def search_products(
    q: str = Query(..., min_length=1),
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from sqlalchemy import or_
    query = select(Product).where(
        Product.is_deleted == False,
        Product.is_active == True,
        or_(Product.name.ilike(f"%{q}%"), Product.sku.ilike(f"%{q}%"), Product.barcode.ilike(f"%{q}%")),
    ).limit(20)
    r = await db.execute(query)
    return r.unique().scalars().all()
