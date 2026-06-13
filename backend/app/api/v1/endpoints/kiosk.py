"""
Kiosk mode endpoints — optimized for full-screen self-service check-in terminal.
Returns minimal data for fast display.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timezone
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.attendance import AttendanceLog, CheckinMethod
from app.core.websocket import ws_manager

router = APIRouter()


class KioskCheckin(BaseModel):
    branch_id: int
    identifier: str          # QR code, RFID, or member_id string
    method: str = "qr"       # qr, rfid, pin, manual


@router.post("/checkin")
async def kiosk_checkin(payload: KioskCheckin, db: AsyncSession = Depends(get_db)):
    """Unauthenticated kiosk check-in — returns member greeting card."""
    member = None
    method = payload.method

    if method in ("qr", "manual"):
        r = await db.execute(select(Member).where(Member.qr_code == payload.identifier))
        member = r.scalar_one_or_none()
        if not member and method == "manual":
            # Try member_id string
            r2 = await db.execute(select(Member).where(Member.member_id == payload.identifier))
            member = r2.scalar_one_or_none()
    elif method == "rfid":
        r = await db.execute(select(Member).where(Member.rfid_tag == payload.identifier))
        member = r.scalar_one_or_none()
    elif method == "pin":
        r = await db.execute(select(Member).where(Member.pin_code == payload.identifier, Member.branch_id == payload.branch_id))
        member = r.scalar_one_or_none()

    if not member:
        return {"success": False, "message": "Member not found", "type": "error"}

    if member.status != MemberStatus.ACTIVE:
        return {
            "success": False,
            "message": f"Membership is {member.status.value}",
            "type": "warning",
            "member_name": f"{member.first_name} {member.last_name}",
        }

    # Check active membership
    ms_r = await db.execute(
        select(Membership).where(Membership.member_id == member.id, Membership.status == MembershipStatus.ACTIVE)
    )
    membership = ms_r.scalar_one_or_none()
    if not membership:
        return {
            "success": False,
            "message": "No active membership",
            "type": "warning",
            "member_name": f"{member.first_name} {member.last_name}",
        }

    # Duplicate check
    today = date.today()
    dup = await db.execute(
        select(AttendanceLog).where(
            AttendanceLog.member_id == member.id,
            AttendanceLog.branch_id == payload.branch_id,
            AttendanceLog.check_out == None,
            func.date(AttendanceLog.check_in) == today,
        )
    )
    if dup.scalar_one_or_none():
        return {
            "success": True,
            "message": "Already checked in",
            "type": "info",
            "member_name": f"{member.first_name} {member.last_name}",
            "member_id": member.member_id,
        }

    log = AttendanceLog(
        member_id=member.id, branch_id=payload.branch_id,
        check_in=datetime.now(timezone.utc),
        method=CheckinMethod.QR if method == "qr" else CheckinMethod.RFID if method == "rfid" else CheckinMethod.PIN if method == "pin" else CheckinMethod.MANUAL,
    )
    member.total_checkins += 1
    db.add(log)
    await db.commit()

    # Broadcast to dashboard
    await ws_manager.broadcast_to_branch(payload.branch_id, "checkin", {
        "member_id": member.id, "member_name": f"{member.first_name} {member.last_name}",
        "method": method, "has_active_membership": True, "log_id": log.id,
        "check_in": log.check_in.isoformat(),
    })

    return {
        "success": True,
        "type": "success",
        "message": f"Welcome, {member.first_name}! 👋",
        "member_name": f"{member.first_name} {member.last_name}",
        "member_id": member.member_id,
        "photo_url": member.photo_url,
        "membership_expires": str(membership.end_date),
        "total_checkins": member.total_checkins,
    }


@router.get("/stats/{branch_id}")
async def kiosk_stats(branch_id: int, db: AsyncSession = Depends(get_db)):
    """Public stats for kiosk display."""
    today = date.today()
    count = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.branch_id == branch_id, func.date(AttendanceLog.check_in) == today,
        )
    )).scalar()
    in_gym = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.branch_id == branch_id, func.date(AttendanceLog.check_in) == today, AttendanceLog.check_out == None,
        )
    )).scalar()
    return {"checkins_today": count or 0, "in_gym_now": in_gym or 0, "date": str(today)}
