from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    OWNER = "owner"
    REGIONAL_MANAGER = "regional_manager"
    BRANCH_MANAGER = "branch_manager"
    FRONT_DESK = "front_desk"
    TRAINER = "trainer"
    ACCOUNTANT = "accountant"
    SALES_REP = "sales_rep"
    INVENTORY_MANAGER = "inventory_manager"
    HR_MANAGER = "hr_manager"


class User(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), nullable=False, default=UserRole.FRONT_DESK)
    branch_id = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    avatar_url = Column(String(500), nullable=True)

    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")
