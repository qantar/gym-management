from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.inventory import Product, StockMovement
from app.models.user import User
from app.schemas.inventory import ProductCreate, StockAdjustment, ProductResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    branch_id: Optional[int] = None, low_stock: bool = False,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = select(Product).where(Product.is_deleted == False)
    if branch_id:
        query = query.where(Product.branch_id == branch_id)
    if low_stock:
        query = query.where(Product.stock_quantity <= Product.reorder_level)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(items=result.scalars().all(), total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size)


@router.post("/products", response_model=ProductResponse, status_code=201)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.post("/adjust")
async def adjust_stock(payload: StockAdjustment, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Product).where(Product.id == payload.product_id))
    product = r.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    qty_before = product.stock_quantity
    if payload.movement_type == "in":
        product.stock_quantity += payload.quantity
    elif payload.movement_type == "out":
        if product.stock_quantity < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        product.stock_quantity -= payload.quantity
    movement = StockMovement(
        product_id=product.id, branch_id=payload.branch_id,
        movement_type=payload.movement_type, quantity=payload.quantity,
        quantity_before=qty_before, quantity_after=product.stock_quantity,
        notes=payload.notes, created_by_id=current_user.id,
    )
    db.add(movement)
    await db.commit()
    return {"message": "Stock adjusted", "new_quantity": product.stock_quantity}
