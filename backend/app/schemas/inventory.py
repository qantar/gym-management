from pydantic import BaseModel
from typing import Optional
from datetime import date
from decimal import Decimal
from app.models.inventory import ProductCategory


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: ProductCategory
    brand: Optional[str] = None
    cost_price: Decimal
    sell_price: Decimal
    stock_quantity: int = 0
    reorder_level: int = 10
    barcode: Optional[str] = None
    branch_id: Optional[int] = None
    expiry_date: Optional[date] = None


class StockAdjustment(BaseModel):
    product_id: int
    branch_id: int
    quantity: int
    movement_type: str
    notes: Optional[str] = None


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    category: ProductCategory
    cost_price: Decimal
    sell_price: Decimal
    stock_quantity: int
    reorder_level: int
    is_active: bool
    created_at: date

    class Config:
        from_attributes = True
