from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.invoice import Invoice, Payment, InvoiceStatus
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, PaymentCreate, InvoiceResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


def generate_invoice_number() -> str:
    return f"INV-{str(uuid.uuid4())[:8].upper()}"


@router.get("/", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[InvoiceStatus] = None,
    member_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Invoice)
    if status:
        query = query.where(Invoice.status == status)
    if member_id:
        query = query.where(Invoice.member_id == member_id)
    if branch_id:
        query = query.where(Invoice.branch_id == branch_id)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(
        items=result.scalars().all(), total=total, page=page,
        page_size=page_size, pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tax_amount = (payload.subtotal - payload.discount_amount) * (payload.tax_rate / 100)
    total = payload.subtotal - payload.discount_amount + tax_amount
    invoice = Invoice(
        **payload.model_dump(),
        invoice_number=generate_invoice_number(),
        tax_amount=tax_amount,
        total=total,
        amount_due=total,
        created_by_id=current_user.id,
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/pay")
async def record_payment(
    invoice_id: int, payload: PaymentCreate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = r.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    payment = Payment(
        invoice_id=invoice_id,
        amount=payload.amount,
        method=payload.method,
        reference=payload.reference,
        notes=payload.notes,
        processed_by_id=current_user.id,
    )
    invoice.amount_paid += payload.amount
    invoice.amount_due = max(Decimal("0"), invoice.total - invoice.amount_paid)
    if invoice.amount_due == 0:
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.now(timezone.utc)
    elif invoice.amount_paid > 0:
        invoice.status = InvoiceStatus.PARTIAL

    db.add(payment)
    await db.commit()
    return {"message": "Payment recorded", "amount_due": str(invoice.amount_due)}
