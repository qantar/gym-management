from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, Numeric, Text, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class MembershipStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    FROZEN = "frozen"
    CANCELLED = "cancelled"
    PENDING = "pending"


class Membership(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "memberships"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    status = Column(SAEnum(MembershipStatus), default=MembershipStatus.ACTIVE)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    price_paid = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), default=0)
    freeze_days_used = Column(Integer, default=0)
    freeze_start = Column(Date, nullable=True)
    freeze_end = Column(Date, nullable=True)
    freeze_reason = Column(String(255), nullable=True)
    auto_renew = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    sold_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    contract_signed = Column(Boolean, default=False)
    contract_url = Column(String(500), nullable=True)

    member = relationship("Member", back_populates="memberships")
    plan = relationship("MembershipPlan")
