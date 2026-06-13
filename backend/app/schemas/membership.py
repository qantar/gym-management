from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal
from app.models.membership import MembershipStatus


class MembershipCreate(BaseModel):
    member_id: int
    plan_id: int
    branch_id: int
    start_date: date
    price_paid: Decimal
    discount_amount: Decimal = Decimal("0")
    auto_renew: bool = True
    notes: Optional[str] = None


class MembershipFreeze(BaseModel):
    freeze_start: date
    freeze_end: date
    reason: str


class MembershipResponse(BaseModel):
    id: int
    member_id: int
    plan_id: int
    branch_id: int
    status: MembershipStatus
    start_date: date
    end_date: date
    price_paid: Decimal
    discount_amount: Decimal
    freeze_days_used: int
    auto_renew: bool
    created_at: datetime

    class Config:
        from_attributes = True
