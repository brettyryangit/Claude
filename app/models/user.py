from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    timezone = Column(String, default="UTC")

    # Onboarding
    onboarding_complete = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)
    onboarding_answers = Column(JSON, default=dict)

    # Subscription
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, default="trial")  # trial, active, cancelled, expired
    subscription_tier = Column(String, default="trial")    # trial, core, pro, elite
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_ends_at = Column(DateTime, nullable=True)

    # Preferences
    check_in_times = Column(JSON, default=lambda: ["08:00", "20:00"])
    motivation_time = Column(String, default="07:30")
    message_tone = Column(String, default="adaptive")
    check_in_frequency = Column(Integer, default=2)

    # Streak freeze
    streak_freezes_available = Column(Integer, default=1)

    # Conversation context (last N messages for Claude)
    conversation_context = Column(JSON, default=list)

    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    check_ins = relationship("CheckIn", back_populates="user", cascade="all, delete-orphan")
    streaks = relationship("Streak", back_populates="user", cascade="all, delete-orphan")
    message_logs = relationship("MessageLog", back_populates="user", cascade="all, delete-orphan")
