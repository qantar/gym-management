from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.member import Member
from app.models.membership import Membership
from app.models.invoice import Invoice, InvoiceStatus
from app.models.attendance import AttendanceLog
from app.models.class_schedule import ClassBooking
from app.models.branch import Branch
from app.models.user import User

router = APIRouter()


@router.get("/{member_id}/profile")
async def member_full_profile(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Full member profile — memberships, invoices, attendance, bookings."""
    r = await db.execute(select(Member).where(Member.id == member_id, Member.is_deleted == False))
    member = r.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")

    # Active membership
    ms_r = await db.execute(
        select(Membership).where(Membership.member_id == member_id, Membership.status == "active")
        .order_by(Membership.end_date.desc()).limit(1)
    )
    active_membership = ms_r.scalar_one_or_none()

    # All memberships
    all_ms = await db.execute(
        select(Membership).where(Membership.member_id == member_id).order_by(Membership.created_at.desc())
    )
    memberships = all_ms.scalars().all()

    # Outstanding balance
    bal_r = await db.execute(
        select(func.sum(Invoice.amount_due)).where(
            Invoice.member_id == member_id,
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE, InvoiceStatus.PARTIAL])
        )
    )
    outstanding = bal_r.scalar() or 0

    # Last 10 invoices
    inv_r = await db.execute(
        select(Invoice).where(Invoice.member_id == member_id)
        .order_by(Invoice.created_at.desc()).limit(10)
    )
    invoices = inv_r.scalars().all()

    # Attendance stats
    today = date.today()
    month_start = today.replace(day=1)
    checkins_month = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.member_id == member_id,
            func.date(AttendanceLog.check_in) >= month_start,
        )
    )).scalar()

    checkins_year = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.member_id == member_id,
            func.date(AttendanceLog.check_in) >= today.replace(month=1, day=1),
        )
    )).scalar()

    # Recent attendance
    att_r = await db.execute(
        select(AttendanceLog).where(AttendanceLog.member_id == member_id)
        .order_by(AttendanceLog.check_in.desc()).limit(20)
    )
    recent_attendance = att_r.scalars().all()

    # Class bookings
    bk_r = await db.execute(
        select(ClassBooking).where(ClassBooking.member_id == member_id)
        .order_by(ClassBooking.created_at.desc()).limit(10)
    )
    bookings = bk_r.scalars().all()

    def ms_dict(m):
        return {
            "id": m.id, "plan_id": m.plan_id, "status": m.status,
            "start_date": str(m.start_date), "end_date": str(m.end_date),
            "price_paid": str(m.price_paid), "freeze_days_used": m.freeze_days_used,
            "auto_renew": m.auto_renew,
        }

    def inv_dict(i):
        return {
            "id": i.id, "invoice_number": i.invoice_number, "status": i.status,
            "total": str(i.total), "amount_due": str(i.amount_due),
            "due_date": i.due_date.isoformat() if i.due_date else None,
            "paid_at": i.paid_at.isoformat() if i.paid_at else None,
        }

    def att_dict(a):
        duration = None
        if a.check_out and a.check_in:
            duration = int((a.check_out - a.check_in).total_seconds() / 60)
        return {
            "id": a.id, "check_in": a.check_in.isoformat(),
            "check_out": a.check_out.isoformat() if a.check_out else None,
            "method": a.method.value, "duration_minutes": duration,
        }

    return {
        "member": {
            "id": member.id, "member_id": member.member_id,
            "first_name": member.first_name, "last_name": member.last_name,
            "email": member.email, "phone": member.phone,
            "date_of_birth": str(member.date_of_birth) if member.date_of_birth else None,
            "gender": member.gender.value if member.gender else None,
            "status": member.status.value,
            "photo_url": member.photo_url,
            "qr_code": member.qr_code,
            "rfid_tag": member.rfid_tag,
            "medical_notes": member.medical_notes,
            "notes": member.notes,
            "emergency_contact_name": member.emergency_contact_name,
            "emergency_contact_phone": member.emergency_contact_phone,
            "emergency_contact_relation": member.emergency_contact_relation,
            "total_checkins": member.total_checkins,
            "lifetime_value": member.lifetime_value,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "branch_id": member.branch_id,
        },
        "active_membership": ms_dict(active_membership) if active_membership else None,
        "all_memberships": [ms_dict(m) for m in memberships],
        "outstanding_balance": str(outstanding),
        "recent_invoices": [inv_dict(i) for i in invoices],
        "attendance_stats": {
            "total_all_time": member.total_checkins,
            "this_month": checkins_month,
            "this_year": checkins_year,
        },
        "recent_attendance": [att_dict(a) for a in recent_attendance],
        "recent_bookings": [
            {"id": b.id, "schedule_id": b.schedule_id, "status": b.status, "attended": b.attended}
            for b in bookings
        ],
    }


@router.get("/{member_id}/pdf")
async def member_pdf_report(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download member profile as PDF."""
    from app.services.pdf_service import generate_members_report_pdf
    r = await db.execute(select(Member).where(Member.id == member_id, Member.is_deleted == False))
    member = r.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")
    branch_r = await db.execute(select(Branch).where(Branch.id == member.branch_id))
    branch = branch_r.scalar_one_or_none()
    branch_name = branch.name if branch else "GymOS"
    m_dict = {k: getattr(member, k, None) for k in ["id","member_id","first_name","last_name","email","phone","status","total_checkins","lifetime_value","created_at"]}
    m_dict["status"] = m_dict["status"].value if m_dict["status"] else ""
    m_dict["created_at"] = str(m_dict["created_at"] or "")
    pdf_bytes = generate_members_report_pdf([m_dict], branch_name)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=member_{member.member_id}.pdf"},
    )
