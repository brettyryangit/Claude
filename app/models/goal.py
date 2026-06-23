from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # fitness, finance, career, wellness, learning, personal
    is_primary = Column(Boolean, default=False)  # the "candlestick mover"

    target_frequency = Column(String, default="daily")  # daily, weekly, custom
    target_count = Column(Integer, default=1)            # e.g. 3 times per week

    # Generated plan
    plan_generated = Column(Boolean, default=False)
    plan_content = Column(Text, nullable=True)    # full Claude-generated plan text
    plan_pdf_url = Column(String, nullable=True)  # Cloudflare R2 URL

    start_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")
    check_ins = relationship("CheckIn", back_populates="goal", cascade="all, delete-orphan")
    streak = relationship("Streak", back_populates="goal", uselist=False, cascade="all, delete-orphan")
