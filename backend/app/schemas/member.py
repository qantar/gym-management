from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date, datetime
from app.models.member import MemberStatus, Gender


class MemberCreate(BaseModel):
    branch_id: int
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: str
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    national_id: Optional[str] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relation: Optional[str] = None
    medical_notes: Optional[str] = None
    notes: Optional[str] = None


class MemberUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    medical_notes: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[MemberStatus] = None


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: str
    branch_id: int
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    status: MemberStatus
    total_checkins: int
    lifetime_value: int
    qr_code: Optional[str] = None
    notes: Optional[str] = None
    medical_notes: Optional[str] = None
    created_at: datetime
