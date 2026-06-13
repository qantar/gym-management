from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, Date, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ProductCategory(str, enum.Enum):
    SUPPLEMENTS = "supplements"
    APPAREL = "apparel"
    EQUIPMENT = "equipment"
    ACCESSORIES = "accessories"
    FOOD = "food"
    OTHER = "other"


class Product(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(SAEnum(ProductCategory), nullable=False)
    brand = Column(String(100), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=False)
    sell_price = Column(Numeric(10, 2), nullable=False)
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    max_stock = Column(Integer, nullable=True)
    unit = Column(String(20), default="unit")
    barcode = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    supplier_id = Column(Integer, nullable=True)
    expiry_date = Column(Date, nullable=True)
    tax_rate = Column(Numeric(5, 2), default=15.0)

    stock_movements = relationship("StockMovement", back_populates="product", lazy="dynamic")


class StockMovement(TimestampMixin, Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    movement_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(String(255), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    product = relationship("Product", back_populates="stock_movements")


class PurchaseOrder(TimestampMixin, Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(30), unique=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    supplier_name = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    total_amount = Column(Numeric(10, 2), nullable=False)
    expected_delivery = Column(Date, nullable=True)
    received_at = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
