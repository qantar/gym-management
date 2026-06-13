from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    password: str
    role: UserRole = UserRole.FRONT_DESK
    branch_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    phone: Optional[str] = None
    full_name: str
    role: UserRole
    branch_id: Optional[int] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
