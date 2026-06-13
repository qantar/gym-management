from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.attendance import CheckinMethod


class CheckinRequest(BaseModel):
    member_id: Optional[int] = None
    qr_code: Optional[str] = None
    rfid_tag: Optional[str] = None
    pin_code: Optional[str] = None
    branch_id: int
    method: CheckinMethod = CheckinMethod.MANUAL


class CheckoutRequest(BaseModel):
    attendance_log_id: int


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    member_id: int
    branch_id: int
    check_in: datetime
    check_out: Optional[datetime] = None
    method: CheckinMethod
