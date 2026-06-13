from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.branch import Branch
from app.models.member import Member, MemberStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.attendance import AttendanceLog
from app.models.user import User, UserRole

router = APIRouter()


class BranchCreate(BaseModel):
    name: str
    code: str
    city: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[int] = None
    capacity: int = 500
    opening_time: str = "06:00"
    closing_time: str = "23:00"


class BranchUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[int] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_branches(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Branch).where(Branch.is_deleted == False).order_by(Branch.name))
    return r.scalars().all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_branch(
    payload: BranchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER)),
):
    existing = await db.execute(select(Branch).where(Branch.code == payload.code))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Branch code '{payload.code}' already exists")
    branch = Branch(**payload.model_dump())
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch


@router.get("/{branch_id}")
async def get_branch(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Branch).where(Branch.id == branch_id, Branch.is_deleted == False))
    b = r.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Branch not found")
    return b


@router.put("/{branch_id}")
async def update_branch(
    branch_id: int, payload: BranchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.REGIONAL_MANAGER)),
):
    r = await db.execute(select(Branch).where(Branch.id == branch_id))
    b = r.scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Branch not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(b, k, v)
    await db.commit()
    await db.refresh(b)
    return b


@router.get("/{branch_id}/stats")
async def branch_stats(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import date
    today = date.today()
    month_start = today.replace(day=1)

    active_members = (await db.execute(
        select(func.count(Member.id)).where(Member.branch_id == branch_id, Member.status == MemberStatus.ACTIVE, Member.is_deleted == False)
    )).scalar()

    revenue_month = (await db.execute(
        select(func.sum(Invoice.total)).where(
            Invoice.branch_id == branch_id, Invoice.status == InvoiceStatus.PAID,
            func.date(Invoice.paid_at) >= month_start,
        )
    )).scalar()

    checkins_today = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.branch_id == branch_id, func.date(AttendanceLog.check_in) == today,
        )
    )).scalar()

    in_gym = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.branch_id == branch_id,
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.check_out == None,
        )
    )).scalar()

    return {
        "branch_id": branch_id,
        "active_members": active_members,
        "revenue_month": str(revenue_month or 0),
        "checkins_today": checkins_today,
        "in_gym_now": in_gym,
    }
