from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, Enum as SAEnum
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class BillingCycle(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"


class PlanType(str, enum.Enum):
    INDIVIDUAL = "individual"
    FAMILY = "family"
    CORPORATE = "corporate"
    STUDENT = "student"
    SENIOR = "senior"


class MembershipPlan(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "membership_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    plan_type = Column(SAEnum(PlanType), default=PlanType.INDIVIDUAL)
    billing_cycle = Column(SAEnum(BillingCycle), default=BillingCycle.MONTHLY)
    price = Column(Numeric(10, 2), nullable=False)
    setup_fee = Column(Numeric(10, 2), default=0)
    max_members = Column(Integer, default=1)
    max_freezes_per_year = Column(Integer, default=2)
    max_freeze_days = Column(Integer, default=30)
    allows_guest = Column(Boolean, default=False)
    guest_passes_per_month = Column(Integer, default=0)
    includes_classes = Column(Boolean, default=True)
    classes_per_month = Column(Integer, nullable=True)
    capacity = Column(Integer, nullable=True)
    current_subscribers = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    features = Column(Text, nullable=True)
    tax_rate = Column(Numeric(5, 2), default=15.0)
