from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Numeric, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"


class Staff(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    employee_id = Column(String(20), unique=True, nullable=False)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), nullable=True)
    employment_type = Column(SAEnum(EmploymentType), default=EmploymentType.FULL_TIME)
    base_salary = Column(Numeric(10, 2), nullable=False, default=0)
    commission_rate = Column(Numeric(5, 2), default=0)
    hire_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    national_id = Column(String(20), nullable=True)
    iqama_number = Column(String(20), nullable=True)
    iqama_expiry = Column(Date, nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    certifications = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    kpi_score = Column(Numeric(5, 2), default=0)

    user = relationship("User")
    branch = relationship("Branch", back_populates="staff")
    attendance = relationship("StaffAttendance", back_populates="staff", lazy="dynamic")


class StaffAttendance(TimestampMixin, Base):
    __tablename__ = "staff_attendance"

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="present")
    notes = Column(String(255), nullable=True)

    staff = relationship("Staff", back_populates="attendance")
