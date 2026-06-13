from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import json
from datetime import datetime, timezone, date
from typing import Set

from app.core.database import AsyncSessionLocal
from app.models.member import Member, MemberStatus
from app.models.invoice import Invoice, InvoiceStatus
from app.models.attendance import AttendanceLog

router = APIRouter()

# Connected dashboard clients per branch
_dashboard_clients: dict[int, Set[WebSocket]] = {}


@router.websocket("/dashboard/{branch_id}")
async def dashboard_ws(websocket: WebSocket, branch_id: int):
    """Stream live KPI updates to dashboard every 10 seconds."""
    await websocket.accept()
    if branch_id not in _dashboard_clients:
        _dashboard_clients[branch_id] = set()
    _dashboard_clients[branch_id].add(websocket)

    try:
        while True:
            # Gather KPIs
            async with AsyncSessionLocal() as db:
                today = date.today()
                month_start = today.replace(day=1)

                active = (await db.execute(
                    select(func.count(Member.id)).where(Member.branch_id == branch_id, Member.status == MemberStatus.ACTIVE, Member.is_deleted == False)
                )).scalar()

                checkins = (await db.execute(
                    select(func.count(AttendanceLog.id)).where(
                        AttendanceLog.branch_id == branch_id, func.date(AttendanceLog.check_in) == today,
                    )
                )).scalar()

                in_gym = (await db.execute(
                    select(func.count(AttendanceLog.id)).where(
                        AttendanceLog.branch_id == branch_id, func.date(AttendanceLog.check_in) == today, AttendanceLog.check_out == None,
                    )
                )).scalar()

                revenue_today = (await db.execute(
                    select(func.sum(Invoice.total)).where(
                        Invoice.branch_id == branch_id, Invoice.status == InvoiceStatus.PAID, func.date(Invoice.paid_at) == today,
                    )
                )).scalar()

                overdue = (await db.execute(
                    select(func.count(Invoice.id)).where(Invoice.branch_id == branch_id, Invoice.status == InvoiceStatus.OVERDUE)
                )).scalar()

            payload = json.dumps({
                "event": "kpi_update",
                "ts": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "active_members": active or 0,
                    "checkins_today": checkins or 0,
                    "in_gym_now": in_gym or 0,
                    "revenue_today": str(revenue_today or 0),
                    "overdue_invoices": overdue or 0,
                }
            })

            try:
                await websocket.send_text(payload)
            except Exception:
                break

            # Wait for client ping or 10s interval
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
            except asyncio.TimeoutError:
                pass  # Normal — just continue broadcasting
            except Exception:
                break

    except WebSocketDisconnect:
        pass
    finally:
        _dashboard_clients.get(branch_id, set()).discard(websocket)
