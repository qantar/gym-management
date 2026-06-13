from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class MemberStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FROZEN = "frozen"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Member(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(String(20), unique=True, index=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(SAEnum(Gender), nullable=True)
    national_id = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relation = Column(String(50), nullable=True)
    photo_url = Column(String(500), nullable=True)
    qr_code = Column(String(255), unique=True, nullable=True)
    rfid_tag = Column(String(100), unique=True, nullable=True)
    pin_code = Column(String(6), nullable=True)
    status = Column(SAEnum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    medical_notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    referred_by_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    total_checkins = Column(Integer, default=0)
    lifetime_value = Column(Integer, default=0)

    branch = relationship("Branch", back_populates="members")
    memberships = relationship("Membership", back_populates="member", lazy="dynamic")
    invoices = relationship("Invoice", back_populates="member", lazy="dynamic")
    attendance_logs = relationship("AttendanceLog", back_populates="member", lazy="dynamic")
