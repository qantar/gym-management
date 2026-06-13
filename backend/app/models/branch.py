from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Branch(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    city = Column(String(100), nullable=False)
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    capacity = Column(Integer, default=500)
    is_active = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    opening_time = Column(String(5), default="06:00")
    closing_time = Column(String(5), default="23:00")

    members = relationship("Member", back_populates="branch", lazy="dynamic")
    staff = relationship("Staff", back_populates="branch", lazy="dynamic")
    schedules = relationship("ClassSchedule", back_populates="branch", lazy="dynamic")
