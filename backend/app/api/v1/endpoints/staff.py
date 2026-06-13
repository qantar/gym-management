from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.staff import Staff, StaffAttendance
from app.models.user import User, UserRole
from pydantic import BaseModel
from decimal import Decimal
from typing import Optional as Opt

router = APIRouter()


class StaffCreate(BaseModel):
    user_id: int
    branch_id: int
    employee_id: str
    department: Opt[str] = None
    designation: Opt[str] = None
    employment_type: str = "full_time"
    base_salary: Decimal = Decimal("0")
    commission_rate: Decimal = Decimal("0")
    hire_date: date
    national_id: Opt[str] = None
    certifications: Opt[str] = None


class StaffUpdate(BaseModel):
    department: Opt[str] = None
    designation: Opt[str] = None
    base_salary: Opt[Decimal] = None
    commission_rate: Opt[Decimal] = None
    kpi_score: Opt[Decimal] = None
    certifications: Opt[str] = None


@router.get("/")
async def list_staff(
    branch_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Staff).where(Staff.is_deleted == False)
    if branch_id:
        query = query.where(Staff.branch_id == branch_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return {"items": result.scalars().all(), "total": total, "page": page, "page_size": page_size}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: StaffCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.OWNER)),
):
    staff = Staff(**payload.model_dump())
    db.add(staff)
    await db.commit()
    await db.refresh(staff)
    return staff


@router.get("/{staff_id}")
async def get_staff(staff_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Staff).where(Staff.id == staff_id, Staff.is_deleted == False))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Staff not found")
    return s


@router.put("/{staff_id}")
async def update_staff(
    staff_id: int, payload: StaffUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.BRANCH_MANAGER)),
):
    r = await db.execute(select(Staff).where(Staff.id == staff_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Staff not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.HR_MANAGER)),
):
    r = await db.execute(select(Staff).where(Staff.id == staff_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Staff not found")
    s.is_deleted = True
    await db.commit()
    return {"message": "Staff deleted"}


@router.post("/{staff_id}/attendance")
async def record_attendance(
    staff_id: int,
    action: str = Query(..., pattern="^(checkin|checkout)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone
    today = date.today()
    r = await db.execute(select(StaffAttendance).where(StaffAttendance.staff_id == staff_id, StaffAttendance.date == today))
    att = r.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if action == "checkin":
        if att:
            raise HTTPException(400, "Already checked in today")
        att = StaffAttendance(staff_id=staff_id, date=today, check_in=now, status="present")
        db.add(att)
    else:
        if not att or not att.check_in:
            raise HTTPException(400, "No check-in found for today")
        att.check_out = now
    await db.commit()
    return {"message": f"Staff {action} recorded", "time": now.isoformat()}


@router.get("/payroll/summary")
async def payroll_summary(
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ACCOUNTANT, UserRole.HR_MANAGER, UserRole.OWNER)),
):
    q = select(func.sum(Staff.base_salary), func.count(Staff.id)).where(Staff.is_deleted == False)
    if branch_id:
        q = q.where(Staff.branch_id == branch_id)
    r = await db.execute(q)
    total_salary, count = r.one()
    return {
        "total_base_salary": str(total_salary or 0),
        "headcount": count,
        "estimated_monthly": str((total_salary or 0)),
    }
