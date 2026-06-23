from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class ReferralCode(Base):
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    code = Column(String, unique=True, nullable=False, index=True)  # e.g. BRETT-X7K2
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="referral_code")
    referrals = relationship("Referral", back_populates="referral_code")


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id"), nullable=False)
    referrer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referred_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    referred_phone = Column(String, nullable=False)

    # Status tracking
    status = Column(String, default="clicked")  # clicked, signed_up, trial, converted, churned

    # Commission
    commission_rate = Column(Float, default=0.20)   # 20% of what referred user pays
    total_earned = Column(Float, default=0.0)        # lifetime earnings from this referral
    total_paid_out = Column(Float, default=0.0)

    clicked_at = Column(DateTime, default=datetime.utcnow)
    signed_up_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)   # when they became a paying user

    referral_code = relationship("ReferralCode", back_populates="referrals")
    referrer = relationship("User", foreign_keys=[referrer_user_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_user_id], back_populates="referred_by")


class ReferralEarning(Base):
    __tablename__ = "referral_earnings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referral_id = Column(UUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False)

    amount = Column(Float, nullable=False)           # e.g. 1.998 (20% of £9.99)
    currency = Column(String, default="GBP")
    month = Column(String, nullable=False)           # e.g. "2026-06"
    paid_out = Column(Boolean, default=False)
    paid_out_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    referrer = relationship("User", back_populates="referral_earnings")
