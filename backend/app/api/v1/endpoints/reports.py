from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.invoice import Invoice, InvoiceStatus
from app.models.member import Member, MemberStatus
from app.models.attendance import AttendanceLog
from app.models.lead import Lead, LeadStatus
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/revenue")
async def revenue_report(
    branch_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.ACCOUNTANT, UserRole.BRANCH_MANAGER)),
):
    date_from = date_from or (date.today() - timedelta(days=30))
    date_to = date_to or date.today()
    query = select(func.sum(Invoice.total), func.count(Invoice.id)).where(
        Invoice.status == InvoiceStatus.PAID,
        func.date(Invoice.paid_at) >= date_from,
        func.date(Invoice.paid_at) <= date_to,
    )
    if branch_id:
        query = query.where(Invoice.branch_id == branch_id)
    r = await db.execute(query)
    total_revenue, invoice_count = r.one()
    return {"total_revenue": str(total_revenue or 0), "invoice_count": invoice_count, "period": {"from": str(date_from), "to": str(date_to)}}


@router.get("/membership-summary")
async def membership_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    statuses = [MemberStatus.ACTIVE, MemberStatus.EXPIRED, MemberStatus.FROZEN, MemberStatus.SUSPENDED]
    result = {}
    for s in statuses:
        q = select(func.count(Member.id)).where(Member.status == s, Member.is_deleted == False)
        if branch_id:
            q = q.where(Member.branch_id == branch_id)
        r = await db.execute(q)
        result[s.value] = r.scalar()
    return result


@router.get("/attendance-summary")
async def attendance_summary(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    week_ago = today - timedelta(days=7)
    r = await db.execute(
        select(func.date(AttendanceLog.check_in), func.count()).where(
            AttendanceLog.branch_id == branch_id,
            func.date(AttendanceLog.check_in) >= week_ago,
        ).group_by(func.date(AttendanceLog.check_in)).order_by(func.date(AttendanceLog.check_in))
    )
    return [{"date": str(row[0]), "count": row[1]} for row in r.all()]


@router.get("/crm-summary")
async def crm_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    statuses = [LeadStatus.NEW, LeadStatus.CONTACTED, LeadStatus.TRIAL, LeadStatus.PROPOSAL, LeadStatus.WON, LeadStatus.LOST]
    result = {}
    for s in statuses:
        q = select(func.count(Lead.id)).where(Lead.status == s, Lead.is_deleted == False)
        if branch_id:
            q = q.where(Lead.branch_id == branch_id)
        r = await db.execute(q)
        result[s.value] = r.scalar()
    total = result.get("won", 0) + result.get("lost", 0)
    result["conversion_rate"] = round((result.get("won", 0) / total * 100), 1) if total > 0 else 0
    return result
