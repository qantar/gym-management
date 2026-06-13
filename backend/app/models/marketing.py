from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Numeric, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class CampaignType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    MULTI = "multi"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class TargetSegment(str, enum.Enum):
    ALL_MEMBERS = "all_members"
    ACTIVE = "active"
    EXPIRING_7D = "expiring_7d"
    EXPIRING_30D = "expiring_30d"
    EXPIRED = "expired"
    FROZEN = "frozen"
    INACTIVE_30D = "inactive_30d"
    INACTIVE_60D = "inactive_60d"
    NEW_THIS_MONTH = "new_this_month"
    PREMIUM_ONLY = "premium_only"
    CUSTOM = "custom"


class Campaign(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(SAEnum(CampaignType), nullable=False, default=CampaignType.SMS)
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    target_segment = Column(SAEnum(TargetSegment), default=TargetSegment.ALL_MEMBERS)
    subject = Column(String(255), nullable=True)       # email subject
    message_body = Column(Text, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    recipient_count = Column(Integer, default=0)
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    converted_count = Column(Integer, default=0)
    bounced_count = Column(Integer, default=0)
    cost = Column(Numeric(10, 2), default=0)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    logs = relationship("CampaignLog", back_populates="campaign", lazy="dynamic")


class CampaignLog(TimestampMixin, Base):
    __tablename__ = "campaign_logs"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=True)
    recipient = Column(String(255), nullable=False)   # phone or email
    status = Column(String(20), default="pending")    # pending/sent/delivered/opened/clicked/bounced
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(String(255), nullable=True)

    campaign = relationship("Campaign", back_populates="logs")


class Coupon(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    discount_type = Column(String(20), default="percentage")  # percentage / fixed
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_purchase = Column(Numeric(10, 2), default=0)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    plan_id = Column(Integer, ForeignKey("membership_plans.id"), nullable=True)
