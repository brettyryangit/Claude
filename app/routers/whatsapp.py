import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.goal import Goal
from app.models.checkin import CheckIn
from app.models.streak import Streak
from app.models.message_log import MessageLog
from app.services.whatsapp import whatsapp_service
from app.services.onboarding import handle_onboarding_message
from app.services.claude_ai import assess_check_in_reply, handle_free_chat
from app.services.stripe_service import create_checkout_link

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["whatsapp"])

TIER_MAP = {"1": "core", "2": "pro", "3": "elite", "4": "annual"}

WELCOME_MESSAGE = """Hey 👋 Welcome to *Grit* — your personal AI accountability coach.

I'll keep you on track with your goals through daily check-ins, morning motivation, and a personalised 90-day plan built just for you.

You get *7 days completely free* to try this out. No card needed right now.

Ready to start? Just say *yes* and I'll ask you 10 quick questions to set everything up. Takes about 3 minutes. 🔥"""


@router.get("")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return int(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_message(request: Request, db: Session = Depends(get_db)):
    """Handle incoming WhatsApp messages."""
    try:
        body = await request.json()
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        message = messages[0]
        phone_number = message.get("from")
        message_type = message.get("type", "text")

        if message_type == "text":
            text = message.get("text", {}).get("body", "").strip()
        else:
            return {"status": "ok"}

        if not phone_number or not text:
            return {"status": "ok"}

        # Log inbound message
        user = db.query(User).filter(User.phone_number == phone_number).first()

        if user:
            log = MessageLog(
                user_id=user.id,
                direction="inbound",
                message_type="text",
                content=text,
            )
            db.add(log)
            user.last_active_at = datetime.utcnow()

        await _route_message(phone_number, text, user, db)
        db.commit()

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return {"status": "ok"}


async def _route_message(phone: str, text: str, user: User | None, db: Session) -> None:
    """Route incoming message to the correct handler."""
    text_lower = text.lower().strip()

    # New user
    if not user:
        if text_lower in ["yes", "start", "hi", "hello", "hey"]:
            new_user = User(phone_number=phone)
            db.add(new_user)
            db.flush()
            await whatsapp_service.send_text(phone, WELCOME_MESSAGE)
        else:
            await whatsapp_service.send_text(
                phone,
                "Hey! I'm Grit, your accountability coach. Reply *YES* to get started with your free 7-day trial. 🔥"
            )
        return

    # Not yet started onboarding
    if not user.onboarding_complete and user.onboarding_step == 0:
        if text_lower in ["yes", "start", "ok", "sure", "go", "let's go", "lets go"]:
            from app.services.claude_ai import ONBOARDING_QUESTIONS
            user.onboarding_step = 1
            await whatsapp_service.send_text(phone, ONBOARDING_QUESTIONS[0])
            db.commit()
        else:
            await whatsapp_service.send_text(phone, WELCOME_MESSAGE)
        return

    # Mid-onboarding
    if not user.onboarding_complete:
        await handle_onboarding_message(user, text, db)
        return

    # Stripe tier selection
    if text_lower in TIER_MAP and user.subscription_status == "trial":
        tier = TIER_MAP[text_lower]
        try:
            link = create_checkout_link(phone, tier)
            await whatsapp_service.send_text(
                phone,
                f"Perfect choice 💪 Here's your secure payment link:\n\n{link}\n\nTakes 30 seconds. Your coaching continues right after."
            )
        except Exception as e:
            logger.error(f"Stripe link error: {e}")
            await whatsapp_service.send_text(phone, "Sorry, there was a hiccup with the payment link. Try again in a minute.")
        return

    # Streak freeze
    if "freeze" in text_lower and user.streak_freezes_available > 0:
        user.streak_freezes_available -= 1
        await whatsapp_service.send_text(
            phone,
            f"Streak freeze used ❄️ Your streak is protected for today. You have {user.streak_freezes_available} freeze(s) left. Don't make it a habit. 😤"
        )
        db.commit()
        return

    # Check for pending check-in reply
    pending_check_in = db.query(CheckIn).filter(
        CheckIn.user_id == user.id,
        CheckIn.check_in_type == "daily",
        CheckIn.user_reply == None,
        CheckIn.sent_at != None,
    ).order_by(CheckIn.sent_at.desc()).first()

    if pending_check_in:
        pending_check_in.user_reply = text
        pending_check_in.reply_received_at = datetime.utcnow()

        primary_goal = db.query(Goal).filter(
            Goal.user_id == user.id,
            Goal.is_primary == True,
        ).first()

        if primary_goal:
            assessment = await assess_check_in_reply(primary_goal.title, text)
            pending_check_in.assessment = assessment
            pending_check_in.streak_maintained = assessment in ["completed", "partial"]

            streak_obj = db.query(Streak).filter(
                Streak.user_id == user.id,
                Streak.goal_id == primary_goal.id,
            ).first()

            if streak_obj and assessment == "completed":
                streak_obj.current_streak += 1
                streak_obj.total_days_completed += 1
                streak_obj.last_checked_in = datetime.utcnow()
                if streak_obj.current_streak > streak_obj.longest_streak:
                    streak_obj.longest_streak = streak_obj.current_streak

                # Milestone celebration
                if streak_obj.current_streak in [7, 14, 30, 60, 90]:
                    await whatsapp_service.send_text(
                        phone,
                        f"🏆 {streak_obj.current_streak}-DAY STREAK! That's not luck — that's discipline. Most people quit long before this. Keep going."
                    )
                else:
                    await whatsapp_service.send_text(phone, f"Logged ✅ Day {streak_obj.current_streak} in the books.")

            elif streak_obj and assessment == "missed":
                streak_obj.current_streak = 0
                await whatsapp_service.send_text(phone, "Noted. Streak reset. Tomorrow you start again — and that's okay. What matters is you show up. 💪")

            else:
                await whatsapp_service.send_text(phone, "Got it. Every bit counts. Keep moving forward.")

        db.commit()
        return

    # Free-form chat
    primary_goal = db.query(Goal).filter(
        Goal.user_id == user.id,
        Goal.is_primary == True,
    ).first()

    context = user.conversation_context or []
    context.append({"role": "user", "content": text})
    context = context[-20:]

    reply = await handle_free_chat(
        user.name or "there",
        primary_goal.title if primary_goal else "your goal",
        text,
        context,
    )

    context.append({"role": "assistant", "content": reply})
    user.conversation_context = context[-20:]
    db.commit()

    await whatsapp_service.send_text(phone, reply)
