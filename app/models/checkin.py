from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class CheckIn(Base):
    __tablename__ = "check_ins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=True)

    check_in_type = Column(String, default="daily")  # daily, morning_motivation, weekly_summary, milestone

    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    message_sent = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)

    user_reply = Column(Text, nullable=True)
    reply_received_at = Column(DateTime, nullable=True)

    # AI assessment of the reply
    assessment = Column(String, nullable=True)  # completed, partial, missed, no_reply
    streak_maintained = Column(Boolean, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="check_ins")
    goal = relationship("Goal", back_populates="check_ins")
