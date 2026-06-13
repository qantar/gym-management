from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.membership import Membership, MembershipStatus
from app.models.membership_plan import MembershipPlan
from app.models.user import User
from app.schemas.membership import MembershipCreate, MembershipFreeze, MembershipResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()

CYCLE_DAYS = {"monthly": 30, "quarterly": 90, "semi_annual": 180, "annual": 365, "weekly": 7, "daily": 1}


@router.post("/", response_model=MembershipResponse, status_code=201)
async def create_membership(payload: MembershipCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(MembershipPlan).where(MembershipPlan.id == payload.plan_id))
    plan = r.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    days = CYCLE_DAYS.get(plan.billing_cycle.value, 30)
    end_date = payload.start_date + timedelta(days=days)
    membership = Membership(
        **payload.model_dump(), end_date=end_date, status=MembershipStatus.ACTIVE,
    )
    plan.current_subscribers += 1
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


@router.post("/{membership_id}/freeze")
async def freeze_membership(membership_id: int, payload: MembershipFreeze, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Membership).where(Membership.id == membership_id))
    m = r.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Membership not found")
    freeze_days = (payload.freeze_end - payload.freeze_start).days
    m.status = MembershipStatus.FROZEN
    m.freeze_start = payload.freeze_start
    m.freeze_end = payload.freeze_end
    m.freeze_reason = payload.reason
    m.freeze_days_used += freeze_days
    m.end_date = m.end_date + timedelta(days=freeze_days)
    await db.commit()
    return {"message": "Membership frozen", "new_end_date": str(m.end_date)}


@router.post("/{membership_id}/unfreeze")
async def unfreeze_membership(membership_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Membership).where(Membership.id == membership_id))
    m = r.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Membership not found")
    m.status = MembershipStatus.ACTIVE
    m.freeze_start = None
    m.freeze_end = None
    await db.commit()
    return {"message": "Membership unfrozen"}
