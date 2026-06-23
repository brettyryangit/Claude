import random
import string
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.referral import ReferralCode, Referral, ReferralEarning
from app.services.whatsapp import whatsapp_service

logger = logging.getLogger(__name__)

COMMISSION_RATE = 0.20          # 20% of whatever referred user pays each month
REFERRAL_TRIAL_DAYS = 30        # referred user gets 30 days instead of 7
REFERRAL_FIRST_MONTH_DISCOUNT = 0.20   # 20% off their first paid month

SHARE_MESSAGE_TEMPLATES = {
    "fitness": (
        "Hey! I've been using this AI accountability coach called Grit and it's actually keeping me on track "
        "with my fitness goals 💪 It texts me every day on WhatsApp, gave me a personalised 90-day plan as a PDF, "
        "and tracks my streak. You get a FREE 30-day trial (instead of the usual 7) plus 20% off your first month "
        "if you use my link.\n\nNo app to download — just WhatsApp 👇\n\n{link}\n\nSeriously try it, it's changed my routine."
    ),
    "finance": (
        "Have you heard of Grit? It's an AI accountability coach on WhatsApp — I've been using it for my savings goals "
        "and it checks in with me every day to make sure I'm on track 📈 You get a FREE 30-day trial and 20% off "
        "your first month with my link.\n\nNo app needed — just WhatsApp 👇\n\n{link}"
    ),
    "general": (
        "I want to share something that's actually been helping me stay accountable to my goals. "
        "It's called Grit — an AI coach that texts you every day on WhatsApp, builds you a personalised plan, "
        "and tracks your streak. Because you're getting it through me, you get a FREE 30-day trial "
        "plus 20% off your first month 🎁\n\nNo app to download — just tap this link 👇\n\n{link}\n\nLet me know how you get on!"
    ),
}


def generate_referral_code(name: str, db: Session) -> str:
    """Generate a unique referral code like BRETT-X7K2."""
    base = name.upper()[:5].replace(" ", "")
    while True:
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        code = f"{base}-{suffix}"
        exists = db.query(ReferralCode).filter(ReferralCode.code == code).first()
        if not exists:
            return code


def get_or_create_referral_code(user: User, db: Session) -> ReferralCode:
    """Get existing referral code or create a new one for the user."""
    if user.referral_code:
        return user.referral_code

    code = generate_referral_code(user.name or "GRIT", db)
    ref_code = ReferralCode(user_id=user.id, code=code)
    db.add(ref_code)
    db.commit()
    db.refresh(ref_code)
    return ref_code


def get_share_link(code: str) -> str:
    """Build the WhatsApp deep link that pre-fills a message to the Grit number."""
    # When clicked on mobile, opens WhatsApp and starts a chat with Grit
    # The ?ref= param is captured in the webhook and stored against the new user
    return f"https://wa.me/61XXXXXXXXXX?text=START%20{code}"


def get_share_message(user: User, db: Session) -> str:
    """Get a ready-to-forward WhatsApp message for the user to share."""
    ref_code = get_or_create_referral_code(user, db)
    link = get_share_link(ref_code.code)

    # Pick template based on their primary goal category
    from app.models.goal import Goal
    primary_goal = db.query(Goal).filter(
        Goal.user_id == user.id,
        Goal.is_primary == True,
    ).first()
    category = primary_goal.category if primary_goal else "general"
    template = SHARE_MESSAGE_TEMPLATES.get(category, SHARE_MESSAGE_TEMPLATES["general"])
    return template.format(link=link)


def record_referral_click(code: str, new_phone: str, db: Session) -> Referral | None:
    """Record when someone clicks a referral link and starts onboarding."""
    ref_code = db.query(ReferralCode).filter(ReferralCode.code == code).first()
    if not ref_code:
        return None

    # Don't double-record if they've clicked before
    existing = db.query(Referral).filter(
        Referral.referral_code_id == ref_code.id,
        Referral.referred_phone == new_phone,
    ).first()
    if existing:
        return existing

    referral = Referral(
        referral_code_id=ref_code.id,
        referrer_user_id=ref_code.user_id,
        referred_phone=new_phone,
        status="clicked",
        commission_rate=COMMISSION_RATE,
    )
    db.add(referral)
    db.commit()
    return referral


def confirm_referral_signup(new_user: User, db: Session) -> None:
    """Mark referral as signed up when new user completes onboarding."""
    referral = db.query(Referral).filter(
        Referral.referred_phone == new_user.phone_number,
        Referral.status == "clicked",
    ).first()
    if not referral:
        return

    referral.referred_user_id = new_user.id
    referral.status = "trial"
    referral.signed_up_at = datetime.utcnow()
    new_user.referred_by_code = referral.referral_code.code
    db.commit()

    # Notify the referrer
    referrer = db.query(User).filter(User.id == referral.referrer_user_id).first()
    if referrer:
        import asyncio
        asyncio.create_task(whatsapp_service.send_text(
            referrer.phone_number,
            f"🎉 Someone just signed up using your referral link! "
            f"When they become a paying member you'll earn 20% of their subscription every month — automatically. "
            f"Keep sharing 👊"
        ))


def record_commission(referrer_user_id, referral_id, amount: float, month: str, db: Session) -> None:
    """Record a commission earning for a referrer."""
    earning = ReferralEarning(
        referrer_user_id=referrer_user_id,
        referral_id=referral_id,
        amount=round(amount, 2),
        month=month,
    )
    db.add(earning)

    referrer = db.query(User).filter(User.id == referrer_user_id).first()
    if referrer:
        referrer.referral_wallet_balance = round(
            (referrer.referral_wallet_balance or 0) + amount, 2
        )
    db.commit()


async def send_referral_stats(user: User, db: Session) -> None:
    """Send the user their referral stats and share link on request."""
    ref_code = get_or_create_referral_code(user, db)
    link = get_share_link(ref_code.code)

    total_referrals = db.query(Referral).filter(
        Referral.referrer_user_id == user.id,
    ).count()

    converted = db.query(Referral).filter(
        Referral.referrer_user_id == user.id,
        Referral.status == "converted",
    ).count()

    wallet = user.referral_wallet_balance or 0
    paid_out = user.referral_wallet_paid or 0

    message = (
        f"*Your Grit Referral Dashboard* 📊\n\n"
        f"🔗 Your link: {link}\n"
        f"👥 Total sign-ups: {total_referrals}\n"
        f"💳 Paying members: {converted}\n"
        f"💰 Wallet balance: £{wallet:.2f}\n"
        f"✅ Total paid out: £{paid_out:.2f}\n\n"
        f"You earn *20% every month* for each person who stays subscribed. "
        f"Share your link and watch it compound 🚀\n\n"
        f"Reply *SHARE* and I'll send you a ready-to-forward message for your contacts."
    )
    await whatsapp_service.send_text(user.phone_number, message)


async def send_share_message_to_user(user: User, db: Session) -> None:
    """Send the user a pre-written message they can copy and forward."""
    message = get_share_message(user, db)
    await whatsapp_service.send_text(
        user.phone_number,
        f"Here's your ready-to-forward message 👇 Just copy and paste it into any chat:\n\n"
        f"─────────────────\n{message}\n─────────────────\n\n"
        f"Every person who signs up through your link and becomes a paying member earns you "
        f"20% of their subscription every single month. It compounds fast. 💰"
    )
