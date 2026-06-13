"""
Kiosk mode — unauthenticated check-in terminal.
Rate limited: max 10 attempts per IP per minute.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timezone
from pydantic import BaseModel
from typing import Optional
from collections import defaultdict
import time

from app.core.database import get_db
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.attendance import AttendanceLog, CheckinMethod
from app.core.websocket import ws_manager

router = APIRouter()

# Simple in-memory rate limiter: ip -> list of timestamps
_rate_store: dict[str, list[float]] = defaultdict(list)
_RATE_LIMIT = 20       # max attempts
_RATE_WINDOW = 60.0    # per second window


def _check_rate_limit(ip: str) -> None:
    now = time.monotonic()
    timestamps = _rate_store[ip]
    # Prune old
    _rate_store[ip] = [t for t in timestamps if now - t < _RATE_WINDOW]
    if len(_rate_store[ip]) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many check-in attempts. Please wait a minute.",
        )
    _rate_store[ip].append(now)


class KioskCheckin(BaseModel):
    branch_id: int
    identifier: str
    method: str = "qr"   # qr, rfid, pin, manual


def _method_enum(method: str) -> CheckinMethod:
    return {
        "qr": CheckinMethod.QR,
        "rfid": CheckinMethod.RFID,
        "pin": CheckinMethod.PIN,
    }.get(method, CheckinMethod.MANUAL)


@router.post("/checkin")
async def kiosk_checkin(
    payload: KioskCheckin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Public kiosk check-in endpoint with rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    # Resolve member
    member = None
    if payload.method == "qr":
        r = await db.execute(select(Member).where(Member.qr_code == payload.identifier))
        member = r.scalar_one_or_none()
    elif payload.method == "rfid":
        r = await db.execute(select(Member).where(Member.rfid_tag == payload.identifier))
        member = r.scalar_one_or_none()
    elif payload.method == "pin":
        r = await db.execute(select(Member).where(
            Member.pin_code == payload.identifier,
            Member.branch_id == payload.branch_id,
        ))
        member = r.scalar_one_or_none()
    else:  # manual — try member_id string
        r = await db.execute(select(Member).where(Member.member_id == payload.identifier))
        member = r.scalar_one_or_none()
        if not member:
            try:
                mid = int(payload.identifier)
                r2 = await db.execute(select(Member).where(Member.id == mid))
                member = r2.scalar_one_or_none()
            except ValueError:
                pass

    if not member:
        return {"success": False, "type": "error", "message": "Member not found. Please see front desk."}

    if member.status != MemberStatus.ACTIVE:
        return {
            "success": False, "type": "warning",
            "message": f"Your membership is {member.status.value}. Please see front desk.",
            "member_name": f"{member.first_name} {member.last_name}",
        }

    # Active membership check
    ms = (await db.execute(
        select(Membership).where(
            Membership.member_id == member.id,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )).scalar_one_or_none()

    if not ms:
        return {
            "success": False, "type": "warning",
            "message": "No active membership found. Please see front desk.",
            "member_name": f"{member.first_name} {member.last_name}",
        }

    # Already checked in today?
    today = date.today()
    existing = (await db.execute(
        select(AttendanceLog).where(
            AttendanceLog.member_id == member.id,
            AttendanceLog.branch_id == payload.branch_id,
            AttendanceLog.check_out == None,
            func.date(AttendanceLog.check_in) == today,
        )
    )).scalar_one_or_none()

    if existing:
        return {
            "success": True, "type": "info",
            "message": f"Welcome back, {member.first_name}! Already checked in.",
            "member_name": f"{member.first_name} {member.last_name}",
            "member_id": member.member_id,
        }

    # Create log
    log = AttendanceLog(
        member_id=member.id,
        branch_id=payload.branch_id,
        check_in=datetime.now(timezone.utc),
        method=_method_enum(payload.method),
    )
    member.total_checkins += 1
    db.add(log)
    await db.commit()
    await db.refresh(log)

    # Broadcast to dashboard
    await ws_manager.broadcast_to_branch(payload.branch_id, "checkin", {
        "member_id": member.id,
        "member_name": f"{member.first_name} {member.last_name}",
        "method": payload.method,
        "has_active_membership": True,
        "log_id": log.id,
        "check_in": log.check_in.isoformat(),
    })

    return {
        "success": True, "type": "success",
        "message": f"Welcome, {member.first_name}! 👋",
        "member_name": f"{member.first_name} {member.last_name}",
        "member_id": member.member_id,
        "photo_url": member.photo_url,
        "membership_expires": str(ms.end_date),
        "total_checkins": member.total_checkins,
    }


@router.get("/stats/{branch_id}")
async def kiosk_stats(branch_id: int, db: AsyncSession = Depends(get_db)):
    """Public stats for kiosk display header."""
    today = date.today()
    total = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.branch_id == branch_id,
            func.date(AttendanceLog.check_in) == today,
        )
    )).scalar() or 0
    in_gym = (await db.execute(
        select(func.count(AttendanceLog.id)).where(
            AttendanceLog.branch_id == branch_id,
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.check_out == None,
        )
    )).scalar() or 0
    return {"checkins_today": total, "in_gym_now": in_gym, "date": str(today)}
