from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Streak(Base):
    __tablename__ = "streaks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)

    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_days_completed = Column(Integer, default=0)
    last_checked_in = Column(DateTime, nullable=True)
    freeze_used_today = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="streaks")
    goal = relationship("Goal", back_populates="streak")
