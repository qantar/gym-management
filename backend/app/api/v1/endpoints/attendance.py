from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, date
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.websocket import ws_manager
from app.models.attendance import AttendanceLog, CheckinMethod
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.user import User
from app.schemas.attendance import CheckinRequest, AttendanceResponse

router = APIRouter()


async def _resolve_member(payload: CheckinRequest, db: AsyncSession) -> Member:
    """Resolve member from QR/RFID/PIN/ID."""
    member = None
    if payload.qr_code:
        r = await db.execute(select(Member).where(Member.qr_code == payload.qr_code))
        member = r.scalar_one_or_none()
    elif payload.rfid_tag:
        r = await db.execute(select(Member).where(Member.rfid_tag == payload.rfid_tag))
        member = r.scalar_one_or_none()
    elif payload.pin_code:
        r = await db.execute(select(Member).where(Member.pin_code == payload.pin_code))
        member = r.scalar_one_or_none()
    elif payload.member_id:
        r = await db.execute(select(Member).where(Member.id == payload.member_id))
        member = r.scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")
    return member


@router.post("/checkin", response_model=AttendanceResponse)
async def checkin(
    payload: CheckinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = await _resolve_member(payload, db)

    # Check active membership
    r = await db.execute(
        select(Membership).where(
            Membership.member_id == member.id,
            Membership.status == MembershipStatus.ACTIVE,
        )
    )
    membership = r.scalar_one_or_none()

    # Check already checked in
    r2 = await db.execute(
        select(AttendanceLog).where(
            AttendanceLog.member_id == member.id,
            AttendanceLog.branch_id == payload.branch_id,
            AttendanceLog.check_out == None,
            func.date(AttendanceLog.check_in) == date.today(),
        )
    )
    existing = r2.scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Member already checked in. Use /checkout.")

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

    # Broadcast live event
    await ws_manager.broadcast_to_branch(payload.branch_id, "checkin", {
        "member_id": member.id,
        "member_name": f"{member.first_name} {member.last_name}",
        "member_photo": member.photo_url,
        "method": payload.method.value,
        "has_active_membership": membership is not None,
        "log_id": log.id,
        "check_in": log.check_in.isoformat(),
    })

    return log


@router.post("/checkout/{log_id}")
async def checkout(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(AttendanceLog).where(AttendanceLog.id == log_id))
    log = r.scalar_one_or_none()
    if not log:
        raise HTTPException(404, "Log not found")
    if log.check_out:
        raise HTTPException(400, "Already checked out")
    log.check_out = datetime.now(timezone.utc)
    # Ensure timezone-aware comparison
    check_in = log.check_in
    if check_in.tzinfo is None:
        check_in = check_in.replace(tzinfo=timezone.utc)
    duration = int((log.check_out - check_in).total_seconds() / 60)
    await db.commit()

    await ws_manager.broadcast_to_branch(log.branch_id, "checkout", {
        "log_id": log.id, "member_id": log.member_id, "duration_minutes": duration,
    })

    return {"message": "Checked out", "duration_minutes": duration}


@router.get("/live/{branch_id}")
async def live_stats(
    branch_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    total_r = await db.execute(
        select(func.count()).where(
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.branch_id == branch_id,
        )
    )
    in_gym_r = await db.execute(
        select(func.count()).where(
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.branch_id == branch_id,
            AttendanceLog.check_out == None,
        )
    )
    # Recent logs
    recent_r = await db.execute(
        select(AttendanceLog).where(
            func.date(AttendanceLog.check_in) == today,
            AttendanceLog.branch_id == branch_id,
        ).order_by(AttendanceLog.check_in.desc()).limit(20)
    )
    return {
        "total_today": total_r.scalar(),
        "in_gym_now": in_gym_r.scalar(),
        "recent_logs": [
            {
                "id": l.id, "member_id": l.member_id,
                "check_in": l.check_in.isoformat(),
                "check_out": l.check_out.isoformat() if l.check_out else None,
                "method": l.method.value,
            }
            for l in recent_r.scalars().all()
        ],
    }


@router.websocket("/ws/{branch_id}")
async def attendance_ws(websocket: WebSocket, branch_id: int):
    """Real-time attendance feed. Connect and receive JSON events."""
    await ws_manager.connect(websocket, branch_id)
    try:
        await websocket.send_text('{"event":"connected","data":{"branch_id":' + str(branch_id) + '}}')
        while True:
            # Keep-alive ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, branch_id)


@router.get("/history")
async def member_history(
    member_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AttendanceLog).where(
        AttendanceLog.member_id == member_id
    ).order_by(AttendanceLog.check_in.desc()).offset((page-1)*page_size).limit(page_size)
    r = await db.execute(query)
    logs = r.scalars().all()
    return [
        {
            "id": l.id, "branch_id": l.branch_id,
            "check_in": l.check_in.isoformat(),
            "check_out": l.check_out.isoformat() if l.check_out else None,
            "method": l.method.value,
            "duration_minutes": int((l.check_out - l.check_in).total_seconds() / 60) if l.check_out else None,
        }
        for l in logs
    ]
