from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)
    id: int
    branch_id: int
    full_name: str
    phone: str
    email: Optional[str] = None
    source: LeadSource
    status: LeadStatus
    expected_value: Optional[Decimal] = None
    assigned_to_id: Optional[int] = None
    next_follow_up: Optional[datetime] = None
    created_at: datetime
