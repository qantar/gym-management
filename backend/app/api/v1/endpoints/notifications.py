from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.user import User
from app.services.notification_service import (
    send_membership_expiry_reminder, send_invoice_notification, send_bulk_campaign
)

router = APIRouter()


class BulkNotificationRequest(BaseModel):
    channel: str           # sms, email, whatsapp
    template: str
    subject: str = ""
    segment: str = "all_members"
    branch_id: Optional[int] = None


@router.post("/send/expiry-reminders")
async def send_expiry_reminders(
    days_ahead: int = Query(7, ge=1, le=30),
    branch_id: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send expiry reminders to members expiring within N days."""
    target_date = date.today() + timedelta(days=days_ahead)
    q = select(Membership, Member).join(Member, Membership.member_id == Member.id).where(
        Membership.status == MembershipStatus.ACTIVE,
        Membership.end_date <= target_date,
        Membership.end_date >= date.today(),
        Member.is_deleted == False,
    )
    if branch_id:
        q = q.where(Member.branch_id == branch_id)
    r = await db.execute(q)
    pairs = r.all()

    results = []
    for membership, member in pairs:
        result_list = await send_membership_expiry_reminder(
            phone=member.phone,
            email=member.email,
            name=f"{member.first_name} {member.last_name}",
            plan=str(membership.plan_id),
            expiry_date=str(membership.end_date),
        )
        results.append({
            "member_id": member.member_id,
            "member_name": f"{member.first_name} {member.last_name}",
            "expiry": str(membership.end_date),
            "channels_sent": len(result_list),
            "success": all(r.success for r in result_list),
        })

    return {
        "reminders_sent": len(results),
        "days_ahead": days_ahead,
        "results": results,
    }


@router.post("/send/invoice-reminders")
async def send_invoice_reminders(
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send reminders for all overdue invoices."""
    q = select(Invoice, Member).join(Member, Invoice.member_id == Member.id).where(
        Invoice.status.in_([InvoiceStatus.OVERDUE, InvoiceStatus.PENDING]),
        Member.is_deleted == False,
    )
    if branch_id:
        q = q.where(Invoice.branch_id == branch_id)
    r = await db.execute(q)
    pairs = r.all()

    sent = 0
    for invoice, member in pairs:
        await send_invoice_notification(
            phone=member.phone, email=member.email,
            name=f"{member.first_name} {member.last_name}",
            invoice_number=invoice.invoice_number,
            amount=str(invoice.amount_due),
            due_date=str(invoice.due_date)[:10],
        )
        sent += 1

    return {"reminders_sent": sent}


@router.post("/send/bulk")
async def send_bulk_notification(
    payload: BulkNotificationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send bulk notification to a member segment."""
    q = select(Member).where(Member.is_deleted == False, Member.status == MemberStatus.ACTIVE)
    if payload.branch_id:
        q = q.where(Member.branch_id == payload.branch_id)
    r = await db.execute(q.limit(10000))
    members = r.scalars().all()

    recipients = [
        {
            "name": f"{m.first_name} {m.last_name}",
            "phone": m.phone,
            "email": m.email or "",
            "plan": "",
        }
        for m in members
    ]

    result = await send_bulk_campaign(
        recipients=recipients,
        channel=payload.channel,
        template=payload.template,
        subject=payload.subject,
    )
    return {
        "total_recipients": len(recipients),
        "sent": result["sent"],
        "failed": result["failed"],
        "channel": payload.channel,
    }


@router.get("/preview-template")
async def preview_template(
    template: str,
    name: str = "Ahmed Al-Rashid",
    plan: str = "Premium Annual",
    expiry_date: str = "2026-12-31",
):
    """Preview a template with sample variables."""
    from app.services.notification_service import _render_template
    rendered = _render_template(template, {
        "name": name, "plan": plan, "date": expiry_date,
        "amount": "SAR 2,400.00", "invoice_id": "INV-SAMPLE",
        "branch": "+966-11-XXX-XXXX",
    })
    return {"original": template, "rendered": rendered, "char_count": len(rendered)}
