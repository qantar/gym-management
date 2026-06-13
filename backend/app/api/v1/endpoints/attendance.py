from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timezone, date
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.attendance import AttendanceLog, CheckinMethod
from app.models.member import Member
from app.models.user import User
from app.schemas.attendance import CheckinRequest, AttendanceResponse

router = APIRouter()


@router.post("/checkin", response_model=AttendanceResponse)
async def checkin(
    payload: CheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = None
    if payload.qr_code:
        r = await db.execute(select(Member).where(Member.qr_code == payload.qr_code))
        member = r.scalar_one_or_none()
    elif payload.rfid_tag:
        r = await db.execute(select(Member).where(Member.rfid_tag == payload.rfid_tag))
        member = r.scalar_one_or_none()
    elif payload.member_id:
        r = await db.execute(select(Member).where(Member.id == payload.member_id))
        member = r.scalar_one_or_none()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    log = AttendanceLog(
        member_id=member.id,
        branch_id=payload.branch_id,
        check_in=datetime.now(timezone.utc),
        method=payload.method,
        processed_by_id=current_user.id,
    )
    member.total_checkins += 1
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.post("/checkout/{log_id}")
async def checkout(log_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(AttendanceLog).where(AttendanceLog.id == log_id))
    log = r.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    log.check_out = datetime.now(timezone.utc)
    await db.commit()
    return {"message": "Checked out", "duration_minutes": int((log.check_out - log.check_in).total_seconds() / 60)}


@router.get("/today")
async def today_stats(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    today = date.today()
    r = await db.execute(
        select(func.count()).where(
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.branch_id == branch_id,
        )
    )
    total = r.scalar()
    r2 = await db.execute(
        select(func.count()).where(
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.branch_id == branch_id,
            AttendanceLog.check_out == None,
        )
    )
    in_gym = r2.scalar()
    return {"total_checkins": total, "in_gym_now": in_gym, "date": str(today)}
