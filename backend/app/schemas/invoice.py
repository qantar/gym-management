from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.invoice import InvoiceStatus, PaymentMethod


class InvoiceCreate(BaseModel):
    member_id: int
    branch_id: int
    membership_id: Optional[int] = None
    description: Optional[str] = None
    subtotal: Decimal
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("15.0")
    due_date: datetime
    notes: Optional[str] = None


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: Decimal
    method: PaymentMethod
    reference: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    invoice_number: str
    member_id: int
    branch_id: int
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    status: InvoiceStatus
    due_date: datetime
    paid_at: Optional[datetime] = None
    created_at: datetime
