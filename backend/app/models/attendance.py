from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin


class CheckinMethod(str, enum.Enum):
    QR = "qr"
    RFID = "rfid"
    PIN = "pin"
    MANUAL = "manual"
    FACE = "face"


class AttendanceLog(TimestampMixin, Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=False)
    check_out = Column(DateTime(timezone=True), nullable=True)
    method = Column(SAEnum(CheckinMethod), default=CheckinMethod.QR)
    processed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(String(255), nullable=True)

    member = relationship("Member", back_populates="attendance_logs")
