from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.marketing import Campaign, CampaignLog, Coupon, CampaignType, CampaignStatus, TargetSegment
from app.models.member import Member, MemberStatus
from app.models.user import User

router = APIRouter()


class CampaignCreate(BaseModel):
    branch_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    campaign_type: CampaignType = CampaignType.SMS
    target_segment: TargetSegment = TargetSegment.ALL_MEMBERS
    subject: Optional[str] = None
    message_body: str
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    message_body: Optional[str] = None
    subject: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[CampaignStatus] = None


class CouponCreate(BaseModel):
    code: str
    description: Optional[str] = None
    discount_type: str = "percentage"
    discount_value: Decimal
    min_purchase: Decimal = Decimal("0")
    max_uses: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    branch_id: Optional[int] = None
    plan_id: Optional[int] = None


async def _segment_count(segment: TargetSegment, branch_id: Optional[int], db: AsyncSession) -> int:
    from datetime import date, timedelta
    from app.models.attendance import AttendanceLog
    q = select(func.count(Member.id)).where(Member.is_deleted == False)
    if branch_id:
        q = q.where(Member.branch_id == branch_id)
    if segment == TargetSegment.ACTIVE:
        q = q.where(Member.status == MemberStatus.ACTIVE)
    elif segment == TargetSegment.EXPIRED:
        q = q.where(Member.status == MemberStatus.EXPIRED)
    elif segment == TargetSegment.FROZEN:
        q = q.where(Member.status == MemberStatus.FROZEN)
    elif segment == TargetSegment.NEW_THIS_MONTH:
        q = q.where(func.date(Member.created_at) >= date.today().replace(day=1))
    return (await db.execute(q)).scalar() or 0


@router.get("/campaigns")
async def list_campaigns(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    campaign_type: Optional[CampaignType] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    q = select(Campaign).where(Campaign.is_deleted == False)
    if status:
        q = q.where(Campaign.status == status)
    if campaign_type:
        q = q.where(Campaign.campaign_type == campaign_type)
    q = q.order_by(Campaign.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    r = await db.execute(q.offset((page - 1) * page_size).limit(page_size))
    return {"items": r.scalars().all(), "total": total, "page": page, "page_size": page_size}


@router.post("/campaigns", status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    recipient_count = await _segment_count(payload.target_segment, payload.branch_id, db)
    campaign = Campaign(
        **payload.model_dump(),
        recipient_count=recipient_count,
        created_by_id=current_user.id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    return c


@router.put("/campaigns/{campaign_id}")
async def update_campaign(
    campaign_id: int, payload: CampaignUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    r = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    if c.status in (CampaignStatus.SENT, CampaignStatus.SENDING):
        raise HTTPException(400, "Cannot edit a sent/sending campaign")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(c, k, v)
    await db.commit()
    await db.refresh(c)
    return c


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    """Trigger campaign send. In production this enqueues a Celery task."""
    r = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    if c.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED):
        raise HTTPException(400, f"Cannot send a {c.status} campaign")
    c.status = CampaignStatus.SENT
    c.sent_at = datetime.now(timezone.utc)
    c.sent_count = c.recipient_count
    c.delivered_count = int(c.recipient_count * 0.97)  # simulated delivery rate
    await db.commit()
    return {"message": f"Campaign sent to {c.sent_count} recipients", "delivered": c.delivered_count}


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(campaign_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = r.scalar_one_or_none()
    if not c or c.status == CampaignStatus.SENT:
        raise HTTPException(400, "Cannot cancel")
    c.status = CampaignStatus.CANCELLED
    await db.commit()
    return {"message": "Campaign cancelled"}


@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(404, "Campaign not found")
    c.is_deleted = True
    await db.commit()
    return {"message": "Campaign deleted"}


@router.get("/campaigns/stats/overview")
async def campaign_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(
        select(
            func.count(Campaign.id).label("total"),
            func.sum(Campaign.sent_count).label("total_sent"),
            func.sum(Campaign.delivered_count).label("total_delivered"),
            func.sum(Campaign.opened_count).label("total_opened"),
            func.sum(Campaign.converted_count).label("total_converted"),
        ).where(Campaign.is_deleted == False, Campaign.status == CampaignStatus.SENT)
    )
    row = r.one()
    total_sent = row.total_sent or 0
    return {
        "total_campaigns": row.total,
        "total_sent": total_sent,
        "total_delivered": row.total_delivered or 0,
        "delivery_rate": round((row.total_delivered or 0) / max(total_sent, 1) * 100, 1),
        "open_rate": round((row.total_opened or 0) / max(total_sent, 1) * 100, 1),
        "conversion_rate": round((row.total_converted or 0) / max(total_sent, 1) * 100, 1),
    }


# ── Coupons ────────────────────────────────────────────────────────────────
@router.get("/coupons")
async def list_coupons(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Coupon).where(Coupon.is_deleted == False).order_by(Coupon.created_at.desc()))
    return r.scalars().all()


@router.post("/coupons", status_code=201)
async def create_coupon(payload: CouponCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = await db.execute(select(Coupon).where(Coupon.code == payload.code.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Coupon code '{payload.code}' already exists")
    data = payload.model_dump()
    data['code'] = payload.code.upper()
    coupon = Coupon(**data)
    db.add(coupon)
    await db.commit()
    await db.refresh(coupon)
    return coupon


@router.post("/coupons/validate")
async def validate_coupon(code: str, amount: Decimal, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    r = await db.execute(select(Coupon).where(Coupon.code == code.upper(), Coupon.is_deleted == False, Coupon.is_active == True))
    coupon = r.scalar_one_or_none()
    if not coupon:
        raise HTTPException(404, "Coupon not found or inactive")
    if coupon.valid_until and coupon.valid_until < now:
        raise HTTPException(400, "Coupon expired")
    if coupon.valid_from and coupon.valid_from > now:
        raise HTTPException(400, "Coupon not yet valid")
    if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
        raise HTTPException(400, "Coupon usage limit reached")
    if amount < coupon.min_purchase:
        raise HTTPException(400, f"Minimum purchase SAR {coupon.min_purchase} required")
    if coupon.discount_type == "percentage":
        discount = amount * (coupon.discount_value / 100)
    else:
        discount = min(coupon.discount_value, amount)
    return {"valid": True, "code": coupon.code, "discount_type": coupon.discount_type, "discount_value": str(coupon.discount_value), "discount_amount": str(discount), "final_amount": str(amount - discount)}


@router.get("/segments/count")
async def segment_count(
    segment: TargetSegment, branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    count = await _segment_count(segment, branch_id, db)
    return {"segment": segment, "count": count}
