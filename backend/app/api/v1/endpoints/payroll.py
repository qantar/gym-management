from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timezone
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.payroll import PayrollRun, PaySlip, PayrollStatus
from app.models.staff import Staff, StaffAttendance
from app.models.user import User, UserRole

router = APIRouter()

FINANCE = (UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.ACCOUNTANT, UserRole.HR_MANAGER)


class PayrollRunCreate(BaseModel):
    branch_id: Optional[int] = None
    period_start: date
    period_end: date
    pay_date: date
    notes: Optional[str] = None


class PaySlipUpdate(BaseModel):
    overtime_hours: Optional[Decimal] = None
    overtime_pay: Optional[Decimal] = None
    bonus: Optional[Decimal] = None
    commission: Optional[Decimal] = None
    deduction_other: Optional[Decimal] = None
    notes: Optional[str] = None


@router.get("/runs")
async def list_runs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*FINANCE)),
):
    q = select(PayrollRun)
    if branch_id:
        q = q.where(PayrollRun.branch_id == branch_id)
    q = q.order_by(PayrollRun.period_start.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    r = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return {"items": r.scalars().all(), "total": total, "page": page, "page_size": page_size}


@router.post("/runs", status_code=201)
async def create_run(
    payload: PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*FINANCE)),
):
    """Create a payroll run and auto-generate pay slips for all staff in branch."""
    q = select(Staff).where(Staff.is_deleted == False)
    if payload.branch_id:
        q = q.where(Staff.branch_id == payload.branch_id)
    r = await db.execute(q)
    staff_list = r.scalars().all()

    run = PayrollRun(
        branch_id=payload.branch_id,
        period_start=payload.period_start,
        period_end=payload.period_end,
        pay_date=payload.pay_date,
        notes=payload.notes,
        created_by_id=current_user.id,
    )
    db.add(run)
    await db.flush()

    period_days = (payload.period_end - payload.period_start).days + 1
    total_gross = Decimal("0")
    total_net = Decimal("0")
    total_deductions = Decimal("0")
    total_commissions = Decimal("0")

    for staff in staff_list:
        # Count attendance
        att_r = await db.execute(
            select(func.count(StaffAttendance.id)).where(
                StaffAttendance.staff_id == staff.id,
                StaffAttendance.date >= payload.period_start,
                StaffAttendance.date <= payload.period_end,
                StaffAttendance.status == "present",
            )
        )
        days_worked = att_r.scalar() or period_days  # default full period if no tracking
        days_absent = max(0, period_days - days_worked - 2)  # rough weekend adjustment

        daily_rate = staff.base_salary / Decimal("30")
        absence_deduction = daily_rate * days_absent
        gosi = staff.base_salary * Decimal("0.1")  # 10% GOSI
        gross = staff.base_salary
        total_deduct = absence_deduction + gosi
        net = gross - total_deduct

        slip = PaySlip(
            run_id=run.id,
            staff_id=staff.id,
            base_salary=staff.base_salary,
            days_worked=days_worked,
            days_absent=days_absent,
            commission=Decimal("0"),
            bonus=Decimal("0"),
            gross=gross,
            deduction_gosi=gosi,
            deduction_absence=absence_deduction,
            total_deductions=total_deduct,
            net=net,
        )
        db.add(slip)
        total_gross += gross
        total_net += net
        total_deductions += total_deduct

    run.total_gross = total_gross
    run.total_net = total_net
    run.total_deductions = total_deductions
    run.total_commissions = total_commissions
    await db.commit()
    await db.refresh(run)
    return run


@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles(*FINANCE))):
    r = await db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
    run = r.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Payroll run not found")
    return run


@router.post("/runs/{run_id}/approve")
async def approve_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.ACCOUNTANT)),
):
    r = await db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
    run = r.scalar_one_or_none()
    if not run or run.status != PayrollStatus.DRAFT:
        raise HTTPException(400, "Can only approve draft runs")
    run.status = PayrollStatus.APPROVED
    run.approved_by_id = current_user.id
    await db.commit()
    return {"message": "Payroll run approved", "total_net": str(run.total_net)}


@router.post("/runs/{run_id}/pay")
async def mark_paid(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ACCOUNTANT)),
):
    r = await db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
    run = r.scalar_one_or_none()
    if not run or run.status != PayrollStatus.APPROVED:
        raise HTTPException(400, "Can only pay approved runs")
    run.status = PayrollStatus.PAID
    # Mark all slips as paid
    slips_r = await db.execute(select(PaySlip).where(PaySlip.run_id == run_id))
    for slip in slips_r.scalars().all():
        slip.is_paid = True
        slip.paid_at = date.today()
    await db.commit()
    return {"message": f"Payroll paid — SAR {run.total_net} distributed to {len(run.slips)} employees"}


@router.get("/runs/{run_id}/slips")
async def list_slips(run_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles(*FINANCE))):
    r = await db.execute(select(PaySlip).where(PaySlip.run_id == run_id))
    return r.scalars().all()


@router.put("/runs/{run_id}/slips/{slip_id}")
async def update_slip(
    run_id: int, slip_id: int, payload: PaySlipUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles(*FINANCE)),
):
    r = await db.execute(select(PaySlip).where(PaySlip.id == slip_id, PaySlip.run_id == run_id))
    slip = r.scalar_one_or_none()
    if not slip:
        raise HTTPException(404, "Slip not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(slip, k, v)
    # Recalculate totals
    slip.gross = slip.base_salary + (slip.overtime_pay or 0) + (slip.bonus or 0) + (slip.commission or 0)
    slip.total_deductions = (slip.deduction_gosi or 0) + (slip.deduction_absence or 0) + (slip.deduction_other or 0)
    slip.net = slip.gross - slip.total_deductions
    await db.commit()
    await db.refresh(slip)
    return slip


@router.get("/summary")
async def payroll_summary(
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*FINANCE)),
):
    # Latest paid run
    q = select(PayrollRun).where(PayrollRun.status == PayrollStatus.PAID)
    if branch_id:
        q = q.where(PayrollRun.branch_id == branch_id)
    q = q.order_by(PayrollRun.period_start.desc()).limit(1)
    r = await db.execute(q)
    latest = r.scalar_one_or_none()

    # YTD
    year_start = date.today().replace(month=1, day=1)
    ytd_q = select(func.sum(PayrollRun.total_net)).where(
        PayrollRun.status == PayrollStatus.PAID,
        PayrollRun.period_start >= year_start,
    )
    if branch_id:
        ytd_q = ytd_q.where(PayrollRun.branch_id == branch_id)
    ytd = (await db.execute(ytd_q)).scalar() or 0

    # Staff count
    sc = (await db.execute(select(func.count(Staff.id)).where(Staff.is_deleted == False))).scalar()

    return {
        "headcount": sc,
        "ytd_total": str(ytd),
        "last_run_net": str(latest.total_net) if latest else "0",
        "last_run_date": str(latest.pay_date) if latest else None,
        "last_run_status": latest.status if latest else None,
    }
