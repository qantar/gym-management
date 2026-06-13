from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ClassSchedule(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "class_schedules"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("staff.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    room = Column(String(100), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    capacity = Column(Integer, default=20)
    enrolled = Column(Integer, default=0)
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    color = Column(String(7), default="#6c63ff")

    branch = relationship("Branch", back_populates="schedules")
    bookings = relationship("ClassBooking", back_populates="schedule", lazy="dynamic")


class ClassBooking(TimestampMixin, Base):
    __tablename__ = "class_bookings"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("class_schedules.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    status = Column(String(20), default="booked")
    attended = Column(Boolean, default=False)
    waitlist_position = Column(Integer, nullable=True)

    schedule = relationship("ClassSchedule", back_populates="bookings")
