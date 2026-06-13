from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from decimal import Decimal
from datetime import datetime, timezone, date, timedelta
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.invoice import Invoice, Payment, InvoiceStatus, PaymentMethod
from app.models.member import Member
from app.models.user import User, UserRole
from app.schemas.invoice import InvoiceCreate, PaymentCreate, InvoiceResponse
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter()


def gen_invoice_number() -> str:
    return f"INV-{str(uuid.uuid4())[:8].upper()}"


@router.get("/", response_model=PaginatedResponse[InvoiceResponse])
async def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[InvoiceStatus] = None,
    member_id: Optional[int] = None,
    branch_id: Optional[int] = None,
    overdue_only: bool = False,
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
    if overdue_only:
        query = query.where(
            Invoice.status == InvoiceStatus.PENDING,
            Invoice.due_date < datetime.now(timezone.utc),
        )
    query = query.order_by(Invoice.created_at.desc())
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
        invoice_number=gen_invoice_number(),
        tax_amount=tax_amount,
        total=total,
        amount_due=total,
        created_by_id=current_user.id,
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = r.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    return inv


@router.post("/{invoice_id}/pay")
async def record_payment(
    invoice_id: int, payload: PaymentCreate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = r.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    if invoice.status in (InvoiceStatus.PAID, InvoiceStatus.CANCELLED):
        raise HTTPException(400, f"Cannot pay a {invoice.status} invoice")
    if payload.amount > invoice.amount_due:
        raise HTTPException(400, "Payment exceeds amount due")

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
    return {"message": "Payment recorded", "amount_due": str(invoice.amount_due), "status": invoice.status}


@router.post("/{invoice_id}/cancel", response_model=MessageResponse)
async def cancel_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ACCOUNTANT, UserRole.BRANCH_MANAGER)),
):
    r = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = r.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if inv.status == InvoiceStatus.PAID:
        raise HTTPException(400, "Cannot cancel a paid invoice — issue a refund instead")
    inv.status = InvoiceStatus.CANCELLED
    await db.commit()
    return MessageResponse(message="Invoice cancelled")


@router.post("/{invoice_id}/refund", response_model=MessageResponse)
async def refund_invoice(
    invoice_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ACCOUNTANT)),
):
    r = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    inv = r.scalar_one_or_none()
    if not inv or inv.status != InvoiceStatus.PAID:
        raise HTTPException(400, "Can only refund paid invoices")
    inv.status = InvoiceStatus.REFUNDED
    await db.commit()
    return MessageResponse(message="Invoice refunded")


@router.get("/summary/overdue")
async def overdue_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    q = select(func.count(Invoice.id), func.sum(Invoice.amount_due)).where(
        Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]),
        Invoice.due_date < now,
    )
    if branch_id:
        q = q.where(Invoice.branch_id == branch_id)
    r = await db.execute(q)
    count, total = r.one()
    return {"overdue_count": count, "overdue_total": str(total or 0)}


@router.post("/run-collections")
async def run_collections(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mark all past-due pending invoices as OVERDUE."""
    now = datetime.now(timezone.utc)
    q = (
        update(Invoice)
        .where(Invoice.status == InvoiceStatus.PENDING, Invoice.due_date < now)
        .values(status=InvoiceStatus.OVERDUE)
    )
    if branch_id:
        q = q.where(Invoice.branch_id == branch_id)
    result = await db.execute(q)
    await db.commit()
    return {"updated": result.rowcount, "message": f"{result.rowcount} invoices marked overdue"}
