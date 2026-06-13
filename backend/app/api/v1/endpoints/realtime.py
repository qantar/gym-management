"""
Real-time WebSocket endpoints for live dashboard KPI streaming.
Auth: token passed as query param ?token=<jwt> (WebSocket can't send headers).
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select, func
import asyncio
import json
from datetime import datetime, timezone, date
from typing import Set, Dict

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.member import Member, MemberStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.attendance import AttendanceLog

router = APIRouter()

# branch_id → set of connected websockets
_clients: Dict[int, Set[WebSocket]] = {}


async def _authenticate_ws(websocket: WebSocket, token: str | None) -> bool:
    """Validate JWT token for WS connection. Close with 4001 if invalid."""
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return False
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        return True
    except (ValueError, Exception):
        await websocket.close(code=4001, reason="Invalid token")
        return False


async def _fetch_kpis(branch_id: int) -> dict:
    async with AsyncSessionLocal() as db:
        today = date.today()
        month_start = today.replace(day=1)

        active = (await db.execute(
            select(func.count(Member.id)).where(
                Member.branch_id == branch_id,
                Member.status == MemberStatus.ACTIVE,
                Member.is_deleted == False,
            )
        )).scalar() or 0

        checkins = (await db.execute(
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

        revenue_today = (await db.execute(
            select(func.sum(Invoice.total)).where(
                Invoice.branch_id == branch_id,
                Invoice.status == InvoiceStatus.PAID,
                func.date(Invoice.paid_at) == today,
            )
        )).scalar() or 0

        overdue = (await db.execute(
            select(func.count(Invoice.id)).where(
                Invoice.branch_id == branch_id,
                Invoice.status == InvoiceStatus.OVERDUE,
            )
        )).scalar() or 0

        new_month = (await db.execute(
            select(func.count(Member.id)).where(
                Member.branch_id == branch_id,
                func.date(Member.created_at) >= month_start,
                Member.is_deleted == False,
            )
        )).scalar() or 0

    return {
        "active_members": active,
        "checkins_today": checkins,
        "in_gym_now": in_gym,
        "revenue_today": str(revenue_today),
        "overdue_invoices": overdue,
        "new_members_month": new_month,
    }


@router.websocket("/dashboard/{branch_id}")
async def dashboard_ws(
    websocket: WebSocket,
    branch_id: int,
    token: str | None = Query(default=None),
):
    """
    Stream live KPI updates every 10 seconds.
    Connect with: ws://host/api/v1/realtime/dashboard/{branch_id}?token=<jwt>
    """
    await websocket.accept()

    if not await _authenticate_ws(websocket, token):
        return  # already closed

    if branch_id not in _clients:
        _clients[branch_id] = set()
    _clients[branch_id].add(websocket)

    try:
        # Send initial data immediately
        kpis = await _fetch_kpis(branch_id)
        await websocket.send_text(json.dumps({
            "event": "kpi_update",
            "ts": datetime.now(timezone.utc).isoformat(),
            "data": kpis,
        }))

        while True:
            # Wait 10s, then send update (or exit on disconnect)
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
                if msg == "ping":
                    await websocket.send_text('{"event":"pong"}')
            except asyncio.TimeoutError:
                pass  # Send scheduled update
            except Exception:
                break

            try:
                kpis = await _fetch_kpis(branch_id)
                await websocket.send_text(json.dumps({
                    "event": "kpi_update",
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "data": kpis,
                }))
            except Exception:
                break

    except WebSocketDisconnect:
        pass
    finally:
        _clients.get(branch_id, set()).discard(websocket)


async def broadcast_kpi_update(branch_id: int):
    """Push immediate KPI update to all connected dashboard clients for a branch."""
    if branch_id not in _clients or not _clients[branch_id]:
        return
    try:
        kpis = await _fetch_kpis(branch_id)
        payload = json.dumps({
            "event": "kpi_update",
            "ts": datetime.now(timezone.utc).isoformat(),
            "data": kpis,
        })
        dead = set()
        for ws in _clients[branch_id]:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        _clients[branch_id] -= dead
    except Exception:
        pass
