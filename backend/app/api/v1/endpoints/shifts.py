from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.shift import StaffShift, ShiftStatus
from app.models.user import User, UserRole

router = APIRouter()

MANAGE = (UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.HR_MANAGER, UserRole.BRANCH_MANAGER)


class ShiftCreate(BaseModel):
    staff_id: int
    branch_id: int
    shift_date: date
    start_time: str   # "08:00"
    end_time: str     # "16:00"
    notes: Optional[str] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None


class ShiftUpdate(BaseModel):
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    status: Optional[ShiftStatus] = None
    notes: Optional[str] = None


@router.get("/")
async def list_shifts(
    branch_id: int,
    week_start: Optional[date] = None,
    staff_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    week_start = week_start or date.today()
    week_end = week_start + timedelta(days=7)
    q = select(StaffShift).where(
        StaffShift.branch_id == branch_id,
        StaffShift.shift_date >= week_start,
        StaffShift.shift_date < week_end,
    )
    if staff_id:
        q = q.where(StaffShift.staff_id == staff_id)
    q = q.order_by(StaffShift.shift_date, StaffShift.start_time)
    r = await db.execute(q)
    shifts = r.scalars().all()
    return [
        {
            "id": s.id, "staff_id": s.staff_id, "branch_id": s.branch_id,
            "shift_date": str(s.shift_date), "start_time": s.start_time,
            "end_time": s.end_time, "status": s.status.value, "notes": s.notes,
        }
        for s in shifts
    ]


@router.post("/", status_code=201)
async def create_shift(
    payload: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGE)),
):
    shifts_to_create = []

    if payload.is_recurring and payload.recurrence_rule in ("weekly", "biweekly"):
        weeks = 4 if payload.recurrence_rule == "weekly" else 2
        interval = 1 if payload.recurrence_rule == "weekly" else 2
        for w in range(weeks):
            shifts_to_create.append(StaffShift(
                staff_id=payload.staff_id, branch_id=payload.branch_id,
                shift_date=payload.shift_date + timedelta(weeks=w * interval),
                start_time=payload.start_time, end_time=payload.end_time,
                notes=payload.notes, is_recurring=True,
                recurrence_rule=payload.recurrence_rule,
                created_by_id=current_user.id,
            ))
    else:
        shifts_to_create.append(StaffShift(
            staff_id=payload.staff_id, branch_id=payload.branch_id,
            shift_date=payload.shift_date, start_time=payload.start_time,
            end_time=payload.end_time, notes=payload.notes,
            created_by_id=current_user.id,
        ))

    for s in shifts_to_create:
        db.add(s)
    await db.commit()
    return {"created": len(shifts_to_create), "first_date": str(payload.shift_date)}


@router.put("/{shift_id}")
async def update_shift(
    shift_id: int, payload: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGE)),
):
    r = await db.execute(select(StaffShift).where(StaffShift.id == shift_id))
    shift = r.scalar_one_or_none()
    if not shift:
        raise HTTPException(404, "Shift not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(shift, k, v)
    await db.commit()
    return {"message": "Shift updated"}


@router.delete("/{shift_id}")
async def delete_shift(
    shift_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*MANAGE)),
):
    r = await db.execute(select(StaffShift).where(StaffShift.id == shift_id))
    shift = r.scalar_one_or_none()
    if not shift:
        raise HTTPException(404, "Shift not found")
    await db.delete(shift)
    await db.commit()
    return {"message": "Shift deleted"}


@router.get("/weekly-summary")
async def weekly_summary(
    branch_id: int,
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    week_start = week_start or date.today()
    week_end = week_start + timedelta(days=7)
    r = await db.execute(
        select(StaffShift.staff_id, func.count(StaffShift.id).label("shifts"))
        .where(StaffShift.branch_id == branch_id, StaffShift.shift_date >= week_start, StaffShift.shift_date < week_end)
        .group_by(StaffShift.staff_id)
    )
    return {"week": str(week_start), "staff_coverage": [{"staff_id": row.staff_id, "shifts": row.shifts} for row in r.all()]}
