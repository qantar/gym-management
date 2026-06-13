from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date, timedelta
from typing import Optional, List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.class_schedule import ClassSchedule, ClassBooking
from app.models.member import Member
from app.models.user import User

router = APIRouter()


class ScheduleCreate(BaseModel):
    branch_id: int
    trainer_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    room: Optional[str] = None
    start_time: datetime
    end_time: datetime
    capacity: int = 20
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    color: str = "#6c63ff"


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    trainer_id: Optional[int] = None
    room: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    capacity: Optional[int] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_schedules(
    branch_id: int,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    trainer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    date_from = date_from or datetime.utcnow().replace(hour=0, minute=0, second=0)
    date_to = date_to or (date_from + timedelta(days=7))
    q = select(ClassSchedule).where(
        ClassSchedule.branch_id == branch_id,
        ClassSchedule.is_deleted == False,
        ClassSchedule.is_active == True,
        ClassSchedule.start_time >= date_from,
        ClassSchedule.start_time <= date_to,
    )
    if trainer_id:
        q = q.where(ClassSchedule.trainer_id == trainer_id)
    q = q.order_by(ClassSchedule.start_time)
    r = await db.execute(q)
    schedules = r.scalars().all()
    return [
        {
            "id": s.id, "name": s.name, "description": s.description,
            "branch_id": s.branch_id, "trainer_id": s.trainer_id,
            "room": s.room, "start_time": s.start_time.isoformat(),
            "end_time": s.end_time.isoformat(), "capacity": s.capacity,
            "enrolled": s.enrolled, "spots_left": max(0, s.capacity - s.enrolled),
            "is_full": s.enrolled >= s.capacity, "color": s.color,
        }
        for s in schedules
    ]


@router.post("/", status_code=201)
async def create_schedule(
    payload: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Conflict check: same room same time
    if payload.room:
        conflict = await db.execute(
            select(ClassSchedule).where(
                ClassSchedule.branch_id == payload.branch_id,
                ClassSchedule.room == payload.room,
                ClassSchedule.is_deleted == False,
                ClassSchedule.start_time < payload.end_time,
                ClassSchedule.end_time > payload.start_time,
            )
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(400, f"Room '{payload.room}' is already booked in that time slot")

    schedule = ClassSchedule(**payload.model_dump())

    # If recurring, generate next 4 weeks
    instances = [schedule]
    if payload.is_recurring and payload.recurrence_rule == "weekly":
        for week in range(1, 5):
            delta = timedelta(weeks=week)
            inst = ClassSchedule(
                **{k: v for k, v in payload.model_dump().items()},
                start_time=payload.start_time + delta,
                end_time=payload.end_time + delta,
            )
            instances.append(inst)

    for inst in instances:
        db.add(inst)
    await db.commit()
    await db.refresh(schedule)
    return {"created": len(instances), "first": {"id": schedule.id, "name": schedule.name, "start_time": schedule.start_time.isoformat()}}


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: int, payload: ScheduleUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(ClassSchedule).where(ClassSchedule.id == schedule_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Schedule not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(s, k, v)
    await db.commit()
    await db.refresh(s)
    return s


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(ClassSchedule).where(ClassSchedule.id == schedule_id))
    s = r.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Schedule not found")
    s.is_deleted = True
    await db.commit()
    return {"message": "Schedule deleted"}


@router.post("/{schedule_id}/book")
async def book_class(
    schedule_id: int, member_id: int,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(ClassSchedule).where(ClassSchedule.id == schedule_id))
    schedule = r.scalar_one_or_none()
    if not schedule:
        raise HTTPException(404, "Class not found")

    # Duplicate booking check
    dup = await db.execute(select(ClassBooking).where(ClassBooking.schedule_id == schedule_id, ClassBooking.member_id == member_id, ClassBooking.status != "cancelled"))
    if dup.scalar_one_or_none():
        raise HTTPException(400, "Member already booked this class")

    if schedule.enrolled >= schedule.capacity:
        booking = ClassBooking(schedule_id=schedule_id, member_id=member_id, status="waitlist", waitlist_position=schedule.enrolled - schedule.capacity + 1)
        db.add(booking)
        await db.commit()
        return {"status": "waitlist", "position": booking.waitlist_position}

    booking = ClassBooking(schedule_id=schedule_id, member_id=member_id, status="booked")
    schedule.enrolled += 1
    db.add(booking)
    await db.commit()
    return {"status": "booked", "schedule": schedule.name, "start_time": schedule.start_time.isoformat()}


@router.post("/{schedule_id}/cancel-booking")
async def cancel_booking(
    schedule_id: int, member_id: int,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(ClassBooking).where(ClassBooking.schedule_id == schedule_id, ClassBooking.member_id == member_id, ClassBooking.status == "booked"))
    booking = r.scalar_one_or_none()
    if not booking:
        raise HTTPException(404, "Booking not found")
    booking.status = "cancelled"
    # Decrement enrolled, promote first waitlisted
    s_r = await db.execute(select(ClassSchedule).where(ClassSchedule.id == schedule_id))
    schedule = s_r.scalar_one_or_none()
    if schedule:
        schedule.enrolled = max(0, schedule.enrolled - 1)
        wl = await db.execute(select(ClassBooking).where(ClassBooking.schedule_id == schedule_id, ClassBooking.status == "waitlist").order_by(ClassBooking.waitlist_position).limit(1))
        next_up = wl.scalar_one_or_none()
        if next_up:
            next_up.status = "booked"
            next_up.waitlist_position = None
            schedule.enrolled += 1
    await db.commit()
    return {"message": "Booking cancelled"}


@router.get("/{schedule_id}/bookings")
async def get_bookings(schedule_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(ClassBooking).where(ClassBooking.schedule_id == schedule_id).order_by(ClassBooking.created_at))
    return r.scalars().all()


@router.post("/{schedule_id}/mark-attendance")
async def mark_attendance(
    schedule_id: int, member_ids: List[int],
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(ClassBooking).where(ClassBooking.schedule_id == schedule_id, ClassBooking.member_id.in_(member_ids)))
    bookings = r.scalars().all()
    for b in bookings:
        b.attended = True
    await db.commit()
    return {"marked": len(bookings)}


@router.get("/trainer/{trainer_id}/availability")
async def trainer_availability(
    trainer_id: int,
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    week_start = week_start or date.today()
    week_end = week_start + timedelta(days=7)
    r = await db.execute(
        select(ClassSchedule).where(
            ClassSchedule.trainer_id == trainer_id,
            ClassSchedule.is_deleted == False,
            ClassSchedule.is_active == True,
            func.date(ClassSchedule.start_time) >= week_start,
            func.date(ClassSchedule.start_time) < week_end,
        ).order_by(ClassSchedule.start_time)
    )
    busy = r.scalars().all()
    return {
        "trainer_id": trainer_id,
        "week": {"start": str(week_start), "end": str(week_end)},
        "busy_slots": [{"day": s.start_time.strftime("%A"), "start": s.start_time.isoformat(), "end": s.end_time.isoformat(), "class": s.name} for s in busy],
        "classes_this_week": len(busy),
    }
