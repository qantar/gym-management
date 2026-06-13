from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.lead import LeadStatus, LeadSource


class LeadCreate(BaseModel):
    branch_id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    source: LeadSource = LeadSource.WALK_IN
    interest_plan_id: Optional[int] = None
    expected_value: Optional[Decimal] = None
    assigned_to_id: Optional[int] = None
    next_follow_up: Optional[datetime] = None
    notes: Optional[str] = None


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    assigned_to_id: Optional[int] = None
    next_follow_up: Optional[datetime] = None
    notes: Optional[str] = None
    lost_reason: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    branch_id: int
    full_name: str
    phone: str
    email: Optional[str]
    source: LeadSource
    status: LeadStatus
    expected_value: Optional[Decimal]
    assigned_to_id: Optional[int]
    next_follow_up: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
