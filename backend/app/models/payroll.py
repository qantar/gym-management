from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Date, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin


class PayrollStatus(str, enum.Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class PayrollRun(TimestampMixin, Base):
    __tablename__ = "payroll_runs"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    status = Column(SAEnum(PayrollStatus), default=PayrollStatus.DRAFT)
    total_gross = Column(Numeric(10, 2), default=0)
    total_deductions = Column(Numeric(10, 2), default=0)
    total_net = Column(Numeric(10, 2), default=0)
    total_commissions = Column(Numeric(10, 2), default=0)
    notes = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    slips = relationship("PaySlip", back_populates="run", lazy="joined")


class PaySlip(TimestampMixin, Base):
    __tablename__ = "pay_slips"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("payroll_runs.id"), nullable=False)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=False)
    base_salary = Column(Numeric(10, 2), nullable=False)
    days_worked = Column(Integer, default=0)
    days_absent = Column(Integer, default=0)
    overtime_hours = Column(Numeric(5, 2), default=0)
    overtime_pay = Column(Numeric(10, 2), default=0)
    commission = Column(Numeric(10, 2), default=0)
    bonus = Column(Numeric(10, 2), default=0)
    gross = Column(Numeric(10, 2), nullable=False)
    deduction_gosi = Column(Numeric(10, 2), default=0)
    deduction_absence = Column(Numeric(10, 2), default=0)
    deduction_other = Column(Numeric(10, 2), default=0)
    total_deductions = Column(Numeric(10, 2), default=0)
    net = Column(Numeric(10, 2), nullable=False)
    is_paid = Column(Boolean, default=False)
    paid_at = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    run = relationship("PayrollRun", back_populates="slips")
