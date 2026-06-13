from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.class_schedule import ClassSchedule, ClassBooking
from app.models.user import User

router = APIRouter()


@router.get("/")
async def list_schedules(
    branch_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ClassSchedule).where(ClassSchedule.branch_id == branch_id, ClassSchedule.is_deleted == False)
    if date_from:
        query = query.where(ClassSchedule.start_time >= date_from)
    if date_to:
        query = query.where(ClassSchedule.end_time <= date_to)
    result = await db.execute(query.order_by(ClassSchedule.start_time))
    return result.scalars().all()


@router.post("/book/{schedule_id}")
async def book_class(schedule_id: int, member_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(ClassSchedule).where(ClassSchedule.id == schedule_id))
    schedule = r.scalar_one_or_none()
    if not schedule:
        raise HTTPException(status_code=404, detail="Class not found")
    if schedule.enrolled >= schedule.capacity:
        booking = ClassBooking(schedule_id=schedule_id, member_id=member_id, status="waitlist", waitlist_position=1)
        db.add(booking)
        await db.commit()
        return {"message": "Added to waitlist"}
    booking = ClassBooking(schedule_id=schedule_id, member_id=member_id, status="booked")
    schedule.enrolled += 1
    db.add(booking)
    await db.commit()
    return {"message": "Booked successfully"}
