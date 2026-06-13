from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIAL = "partial"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    ONLINE = "online"
    CHEQUE = "cheque"


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(30), unique=True, index=True, nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    membership_id = Column(Integer, ForeignKey("memberships.id"), nullable=True)
    description = Column(Text, nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=15.0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    amount_due = Column(Numeric(10, 2), nullable=False)
    status = Column(SAEnum(InvoiceStatus), default=InvoiceStatus.PENDING)
    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    member = relationship("Member", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice", lazy="dynamic")


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(SAEnum(PaymentMethod), nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
