from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, JSON, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin


class SaleStatus(str, enum.Enum):
    COMPLETED = "completed"
    VOIDED = "voided"
    REFUNDED = "refunded"


class Sale(TimestampMixin, Base):
    __tablename__ = "pos_sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(String(30), unique=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    cashier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)
    status = Column(SAEnum(SaleStatus), default=SaleStatus.COMPLETED)
    notes = Column(String(255), nullable=True)
    receipt_printed = Column(Integer, default=0)

    items = relationship("SaleItem", back_populates="sale", lazy="joined")


class SaleItem(TimestampMixin, Base):
    __tablename__ = "pos_sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("pos_sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount = Column(Numeric(10, 2), default=0)
    line_total = Column(Numeric(10, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")
