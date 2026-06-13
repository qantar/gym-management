from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.audit import AuditLog
from app.models.user import User, UserRole

router = APIRouter()

ADMIN = (UserRole.SUPER_ADMIN, UserRole.OWNER, UserRole.BRANCH_MANAGER)


@router.get("/")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    branch_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN)),
):
    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if action:
        q = q.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    if branch_id:
        q = q.where(AuditLog.branch_id == branch_id)
    if date_from:
        q = q.where(AuditLog.created_at >= date_from)
    if date_to:
        q = q.where(AuditLog.created_at <= date_to)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    logs = result.scalars().all()
    return {
        "items": [
            {
                "id": l.id,
                "user_id": l.user_id,
                "branch_id": l.branch_id,
                "action": l.action,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "description": l.description,
                "ip_address": l.ip_address,
                "status": l.status,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/summary")
async def audit_summary(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(*ADMIN)),
):
    since = datetime.utcnow() - timedelta(days=days)
    total = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.created_at >= since))).scalar()
    failures = (await db.execute(select(func.count(AuditLog.id)).where(AuditLog.created_at >= since, AuditLog.status == "failure"))).scalar()

    # Top actions
    actions_r = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("cnt"))
        .where(AuditLog.created_at >= since)
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(10)
    )
    return {
        "period_days": days,
        "total_events": total,
        "failures": failures,
        "top_actions": [{"action": r.action, "count": r.cnt} for r in actions_r.all()],
    }


@router.post("/log")
async def write_audit_log(
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    log = AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        status="success",
    )
    db.add(log)
    await db.commit()
    return {"message": "Logged"}
