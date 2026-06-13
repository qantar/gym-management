from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.member import Member, MemberStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.attendance import AttendanceLog
from app.models.lead import Lead
from app.models.user import User

router = APIRouter()


@router.get("/kpis")
async def dashboard_kpis(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    month_start = today.replace(day=1)

    async def count(model, *conditions):
        q = select(func.count(model.id)).where(*conditions)
        return (await db.execute(q)).scalar()

    async def sum_col(model, col, *conditions):
        q = select(func.sum(col)).where(*conditions)
        return (await db.execute(q)).scalar() or 0

    branch_filter = [Member.branch_id == branch_id] if branch_id else []
    inv_branch = [Invoice.branch_id == branch_id] if branch_id else []

    active_members = await count(Member, Member.status == MemberStatus.ACTIVE, Member.is_deleted == False, *branch_filter)
    new_members_month = await count(Member, func.date(Member.created_at) >= month_start, Member.is_deleted == False, *branch_filter)
    expiring_7d = await count(Member, Member.status == MemberStatus.ACTIVE, *branch_filter)
    overdue_invoices = await count(Invoice, Invoice.status == InvoiceStatus.OVERDUE, *inv_branch)
    checkins_today = await count(AttendanceLog, func.date(AttendanceLog.check_in) == today)
    revenue_today = await sum_col(Invoice, Invoice.total, Invoice.status == InvoiceStatus.PAID, func.date(Invoice.paid_at) == today, *inv_branch)
    revenue_month = await sum_col(Invoice, Invoice.total, Invoice.status == InvoiceStatus.PAID, func.date(Invoice.paid_at) >= month_start, *inv_branch)

    return {
        "active_members": active_members,
        "new_members_month": new_members_month,
        "expiring_7d": expiring_7d,
        "overdue_invoices": overdue_invoices,
        "checkins_today": checkins_today,
        "revenue_today": str(revenue_today),
        "revenue_month": str(revenue_month),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
