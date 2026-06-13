from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Boolean, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin


class ShiftStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    ABSENT    = "absent"
    CANCELLED = "cancelled"


class StaffShift(TimestampMixin, Base):
    __tablename__ = "staff_shifts"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    shift_date = Column(Date, nullable=False)
    start_time = Column(String(5), nullable=False)   # "08:00"
    end_time = Column(String(5), nullable=False)     # "16:00"
    status = Column(SAEnum(ShiftStatus), default=ShiftStatus.SCHEDULED)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(50), nullable=True)  # "weekly", "biweekly"
