from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract
from datetime import datetime, date, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.invoice import Invoice, InvoiceStatus
from app.models.member import Member, MemberStatus
from app.models.attendance import AttendanceLog
from app.models.lead import Lead, LeadStatus
from app.models.pos import Sale, SaleStatus
from app.models.staff import Staff
from app.models.inventory import Product
from app.models.user import User, UserRole

router = APIRouter()

FINANCE_ROLES = (UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.ACCOUNTANT, UserRole.BRANCH_MANAGER, UserRole.REGIONAL_MANAGER)


@router.get("/revenue")
async def revenue_report(
    branch_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    group_by: str = Query("month", regex="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*FINANCE_ROLES)),
):
    date_from = date_from or (date.today() - timedelta(days=180))
    date_to = date_to or date.today()

    if group_by == "month":
        trunc = func.date_trunc("month", Invoice.paid_at)
    elif group_by == "week":
        trunc = func.date_trunc("week", Invoice.paid_at)
    else:
        trunc = func.date(Invoice.paid_at)

    q = select(trunc.label("period"), func.sum(Invoice.total).label("revenue"), func.count(Invoice.id).label("invoices")).where(
        Invoice.status == InvoiceStatus.PAID,
        func.date(Invoice.paid_at) >= date_from,
        func.date(Invoice.paid_at) <= date_to,
    ).group_by("period").order_by("period")
    if branch_id:
        q = q.where(Invoice.branch_id == branch_id)
    r = await db.execute(q)
    rows = r.all()

    total_q = select(func.sum(Invoice.total), func.count(Invoice.id)).where(Invoice.status == InvoiceStatus.PAID, func.date(Invoice.paid_at) >= date_from, func.date(Invoice.paid_at) <= date_to)
    if branch_id:
        total_q = total_q.where(Invoice.branch_id == branch_id)
    total_r = await db.execute(total_q)
    total_rev, total_inv = total_r.one()

    return {
        "period": {"from": str(date_from), "to": str(date_to)},
        "total_revenue": str(total_rev or 0),
        "total_invoices": total_inv,
        "data": [{"period": str(r.period), "revenue": str(r.revenue), "invoices": r.invoices} for r in rows],
    }


@router.get("/membership-summary")
async def membership_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = {}
    for s in MemberStatus:
        q = select(func.count(Member.id)).where(Member.status == s, Member.is_deleted == False)
        if branch_id:
            q = q.where(Member.branch_id == branch_id)
        result[s.value] = (await db.execute(q)).scalar()

    # New this month
    month_start = date.today().replace(day=1)
    q = select(func.count(Member.id)).where(func.date(Member.created_at) >= month_start, Member.is_deleted == False)
    if branch_id:
        q = q.where(Member.branch_id == branch_id)
    result["new_this_month"] = (await db.execute(q)).scalar()
    return result


@router.get("/attendance-heatmap")
async def attendance_heatmap(branch_id: int, days: int = 30, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    date_from = date.today() - timedelta(days=days)
    r = await db.execute(
        select(
            extract("dow", AttendanceLog.check_in).label("dow"),
            extract("hour", AttendanceLog.check_in).label("hour"),
            func.count().label("count"),
        ).where(AttendanceLog.branch_id == branch_id, func.date(AttendanceLog.check_in) >= date_from)
        .group_by("dow", "hour").order_by("dow", "hour")
    )
    return [{"day": int(row.dow), "hour": int(row.hour), "count": row.count} for row in r.all()]


@router.get("/crm-summary")
async def crm_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = {}
    for s in LeadStatus:
        q = select(func.count(Lead.id)).where(Lead.status == s, Lead.is_deleted == False)
        if branch_id:
            q = q.where(Lead.branch_id == branch_id)
        result[s.value] = (await db.execute(q)).scalar()
    closed = (result.get("won", 0) or 0) + (result.get("lost", 0) or 0)
    result["conversion_rate"] = round(((result.get("won", 0) or 0) / closed * 100), 1) if closed > 0 else 0

    # Won revenue
    q = select(func.sum(Lead.expected_value)).where(Lead.status == LeadStatus.WON, Lead.is_deleted == False)
    if branch_id:
        q = q.where(Lead.branch_id == branch_id)
    result["won_revenue"] = str((await db.execute(q)).scalar() or 0)
    return result


@router.get("/pos-summary")
async def pos_summary(
    branch_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_from = date_from or date.today().replace(day=1)
    date_to = date_to or date.today()
    q = select(func.sum(Sale.total), func.count(Sale.id)).where(
        Sale.status == SaleStatus.COMPLETED,
        func.date(Sale.created_at) >= date_from,
        func.date(Sale.created_at) <= date_to,
    )
    if branch_id:
        q = q.where(Sale.branch_id == branch_id)
    r = await db.execute(q)
    total, count = r.one()
    return {"total_revenue": str(total or 0), "transaction_count": count, "period": {"from": str(date_from), "to": str(date_to)}}


@router.get("/retention")
async def retention_report(branch_id: Optional[int] = None, months: int = 6, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = []
    for i in range(months, 0, -1):
        month_start = (date.today().replace(day=1) - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        active_q = select(func.count(Member.id)).where(Member.status == MemberStatus.ACTIVE, Member.is_deleted == False, func.date(Member.created_at) <= month_end)
        if branch_id:
            active_q = active_q.where(Member.branch_id == branch_id)
        active = (await db.execute(active_q)).scalar()
        result.append({"month": month_start.strftime("%b %Y"), "active": active})
    return result


@router.get("/staff-summary")
async def staff_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = select(func.count(Staff.id), func.sum(Staff.base_salary), func.avg(Staff.kpi_score)).where(Staff.is_deleted == False)
    if branch_id:
        q = q.where(Staff.branch_id == branch_id)
    r = await db.execute(q)
    count, total_salary, avg_kpi = r.one()
    return {"headcount": count, "total_monthly_salary": str(total_salary or 0), "avg_kpi_score": str(round(float(avg_kpi or 0), 1))}


@router.get("/inventory-summary")
async def inventory_summary(branch_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q_total = select(func.count(Product.id), func.sum(Product.stock_quantity * Product.cost_price)).where(Product.is_deleted == False)
    q_low = select(func.count(Product.id)).where(Product.is_deleted == False, Product.stock_quantity <= Product.reorder_level)
    q_out = select(func.count(Product.id)).where(Product.is_deleted == False, Product.stock_quantity == 0)
    if branch_id:
        q_total = q_total.where(Product.branch_id == branch_id)
        q_low = q_low.where(Product.branch_id == branch_id)
        q_out = q_out.where(Product.branch_id == branch_id)
    sku_count, inv_value = (await db.execute(q_total)).one()
    low = (await db.execute(q_low)).scalar()
    out = (await db.execute(q_out)).scalar()
    return {"sku_count": sku_count, "inventory_value": str(inv_value or 0), "low_stock_items": low, "out_of_stock_items": out}


@router.get("/export/members")
async def export_members(
    format: str = "xlsx",
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export members as Excel or CSV."""
    from fastapi.responses import Response
    from app.services.export_service import export_members_excel, export_members_csv
    from app.models.member import Member

    q = select(Member).where(Member.is_deleted == False)
    if branch_id:
        q = q.where(Member.branch_id == branch_id)
    r = await db.execute(q.order_by(Member.created_at.desc()))
    members = r.scalars().all()
    data = [
        {k: getattr(m, k, None) for k in ["member_id","first_name","last_name","email","phone","total_checkins","lifetime_value","created_at"]}
        | {"status": m.status.value}
        for m in members
    ]
    if format == "csv":
        content = export_members_csv(data).encode()
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=members.csv"})
    content = export_members_excel(data)
    return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=members.xlsx"})


@router.get("/export/invoices")
async def export_invoices_report(
    format: str = "xlsx",
    branch_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export invoices as Excel or CSV."""
    from fastapi.responses import Response
    from app.services.export_service import export_invoices_excel, export_invoices_csv
    from app.models.invoice import Invoice

    q = select(Invoice)
    if branch_id:
        q = q.where(Invoice.branch_id == branch_id)
    if status:
        q = q.where(Invoice.status == status)
    r = await db.execute(q.order_by(Invoice.created_at.desc()).limit(5000))
    invoices = r.scalars().all()
    data = [
        {
            "invoice_number": i.invoice_number, "member_id": i.member_id,
            "description": i.description or "", "subtotal": str(i.subtotal),
            "discount_amount": str(i.discount_amount), "tax_amount": str(i.tax_amount),
            "total": str(i.total), "amount_paid": str(i.amount_paid),
            "amount_due": str(i.amount_due), "status": i.status.value,
            "due_date": i.due_date.isoformat() if i.due_date else "",
            "paid_at": i.paid_at.isoformat() if i.paid_at else "",
        }
        for i in invoices
    ]
    if format == "csv":
        content = export_invoices_csv(data).encode()
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=invoices.csv"})
    content = export_invoices_excel(data)
    return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=invoices.xlsx"})


@router.get("/export/members/pdf")
async def export_members_pdf(
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export members as PDF."""
    from fastapi.responses import Response
    from app.services.pdf_service import generate_members_report_pdf
    from app.models.member import Member
    from app.models.branch import Branch

    q = select(Member).where(Member.is_deleted == False)
    if branch_id:
        q = q.where(Member.branch_id == branch_id)
    r = await db.execute(q.limit(500))
    members = r.scalars().all()
    data = [
        {"member_id": m.member_id, "first_name": m.first_name, "last_name": m.last_name,
         "phone": m.phone, "email": m.email or "", "status": m.status.value,
         "total_checkins": m.total_checkins, "created_at": str(m.created_at or "")}
        for m in members
    ]
    bname = "All Branches"
    if branch_id:
        br = (await db.execute(select(Branch).where(Branch.id == branch_id))).scalar_one_or_none()
        if br:
            bname = br.name
    pdf = generate_members_report_pdf(data, bname)
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=members_report.pdf"})
