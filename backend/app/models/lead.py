from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, Enum as SAEnum, DateTime
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class LeadStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    TRIAL = "trial"
    PROPOSAL = "proposal"
    WON = "won"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    WALK_IN = "walk_in"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE = "google"
    REFERRAL = "referral"
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    OTHER = "other"


class Lead(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    source = Column(SAEnum(LeadSource), default=LeadSource.WALK_IN)
    status = Column(SAEnum(LeadStatus), default=LeadStatus.NEW)
    interest_plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=True)
    expected_value = Column(Numeric(10, 2), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    next_follow_up = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    lost_reason = Column(String(255), nullable=True)
    converted_member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)

    interest_plan = relationship("MembershipPlan")
