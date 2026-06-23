import stripe
import logging
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.models.referral import Referral
from app.services.whatsapp import whatsapp_service
from app.services.referral import record_commission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/stripe", tags=["stripe"])

TIER_MESSAGES = {
    "core": "You're on Core 💪 3 goals, 2 check-ins a day. Let's get to work.",
    "pro": "You're on Pro 🔥 Unlimited goals, 3 daily check-ins, full streak analytics. This is where transformation happens.",
    "elite": "You're on Elite 👑 The full package. I'll be with you every step. No excuses now.",
    "annual": "You're locked in for a full year 🏆 Best decision you've made. Let's make it count.",
}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    db: Session = SessionLocal()
    try:
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            phone = session.get("metadata", {}).get("phone_number")
            tier = session.get("metadata", {}).get("tier", "pro")
            customer_id = session.get("customer")

            if phone:
                user = db.query(User).filter(User.phone_number == phone).first()
                if user:
                    user.subscription_status = "active"
                    user.subscription_tier = tier
                    user.stripe_customer_id = customer_id
                    db.commit()

                    message = TIER_MESSAGES.get(tier, "You're all set! Let's go. 🔥")
                    await whatsapp_service.send_text(phone, f"Payment confirmed ✅ {message}")

                    # Fire referral commission if this user was referred
                    if user.referred_by_code:
                        referral = db.query(Referral).filter(
                            Referral.referred_user_id == user.id,
                        ).first()
                        if referral and referral.status != "converted":
                            referral.status = "converted"
                            referral.converted_at = datetime.utcnow()

                        # Calculate commission from invoice amount
                        invoice_amount = session.get("amount_total", 0) / 100  # pence to pounds
                        commission = round(invoice_amount * referral.commission_rate, 2) if referral else 0
                        if commission > 0 and referral:
                            month = datetime.utcnow().strftime("%Y-%m")
                            record_commission(referral.referrer_user_id, referral.id, commission, month, db)
                            # Notify referrer
                            referrer = db.query(User).filter(User.id == referral.referrer_user_id).first()
                            if referrer:
                                await whatsapp_service.send_text(
                                    referrer.phone_number,
                                    f"💰 Commission earned! Someone you referred just subscribed. "
                                    f"£{commission:.2f} added to your wallet. "
                                    f"You'll earn this every month they stay subscribed. "
                                    f"Reply *WALLET* to see your balance."
                                )

        elif event["type"] == "customer.subscription.deleted":
            customer_id = event["data"]["object"].get("customer")
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                user.subscription_status = "cancelled"
                db.commit()
                await whatsapp_service.send_text(
                    user.phone_number,
                    "Your subscription has been cancelled. If you change your mind, just reply *restart* and I'll get you back on track. Good luck out there. 💪"
                )

        elif event["type"] == "invoice.payment_failed":
            customer_id = event["data"]["object"].get("customer")
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                await whatsapp_service.send_text(
                    user.phone_number,
                    "Hey — your payment didn't go through. Update your card details to keep your streak and goals intact 👇\n\nReply *billing* and I'll send you the link."
                )

    finally:
        db.close()

    return {"status": "ok"}
