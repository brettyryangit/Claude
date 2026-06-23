import logging
from datetime import datetime, timedelta
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.goal import Goal
from app.models.checkin import CheckIn
from app.models.streak import Streak
from app.services.whatsapp import whatsapp_service
from app.services.claude_ai import generate_check_in_message, generate_weekly_summary
from app.services.quotes import get_quote, get_motivation_image

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


def start_scheduler():
    # Morning motivation — runs every minute, checks each user's local time
    scheduler.add_job(
        send_morning_motivations,
        CronTrigger(minute="*"),
        id="morning_motivations",
        replace_existing=True,
    )

    # Check-in dispatcher — runs every 30 minutes
    scheduler.add_job(
        send_scheduled_check_ins,
        CronTrigger(minute="*/30"),
        id="check_in_dispatcher",
        replace_existing=True,
    )

    # Weekly summaries — every Sunday at midnight UTC
    scheduler.add_job(
        send_weekly_summaries,
        CronTrigger(day_of_week="sun", hour=0, minute=0),
        id="weekly_summaries",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started")


async def send_morning_motivations():
    """Send morning motivation to users whose local time matches their motivation_time."""
    db: Session = SessionLocal()
    try:
        now_utc = datetime.utcnow()
        users = db.query(User).filter(
            User.is_active == True,
            User.onboarding_complete == True,
        ).all()

        for user in users:
            try:
                user_tz = pytz.timezone(user.timezone or "UTC")
                user_local_time = now_utc.replace(tzinfo=pytz.utc).astimezone(user_tz)
                user_time_str = user_local_time.strftime("%H:%M")

                if user_time_str != (user.motivation_time or "07:30"):
                    continue

                # Check not already sent today
                today_start = user_local_time.replace(hour=0, minute=0, second=0, microsecond=0)
                already_sent = db.query(CheckIn).filter(
                    CheckIn.user_id == user.id,
                    CheckIn.check_in_type == "morning_motivation",
                    CheckIn.sent_at >= today_start.astimezone(pytz.utc).replace(tzinfo=None),
                ).first()

                if already_sent:
                    continue

                # Get primary goal for category
                primary_goal = db.query(Goal).filter(
                    Goal.user_id == user.id,
                    Goal.is_primary == True,
                    Goal.active == True,
                ).first()

                category = primary_goal.category if primary_goal else "general"
                streak_obj = db.query(Streak).filter(
                    Streak.user_id == user.id,
                    Streak.goal_id == primary_goal.id if primary_goal else None,
                ).first()
                streak = streak_obj.current_streak if streak_obj else 0

                quote = get_quote(category)
                image_url = get_motivation_image(category)

                await whatsapp_service.send_motivation(
                    user.phone_number,
                    image_url,
                    quote,
                    user.name or "there",
                    streak,
                )

                # Log it
                check_in = CheckIn(
                    user_id=user.id,
                    goal_id=primary_goal.id if primary_goal else None,
                    check_in_type="morning_motivation",
                    scheduled_at=datetime.utcnow(),
                    sent_at=datetime.utcnow(),
                    message_sent=quote,
                    image_url=image_url,
                )
                db.add(check_in)
                db.commit()

            except Exception as e:
                logger.error(f"Morning motivation failed for {user.phone_number}: {e}")

    finally:
        db.close()


async def send_scheduled_check_ins():
    """Send daily check-in messages to users at their configured times."""
    db: Session = SessionLocal()
    try:
        now_utc = datetime.utcnow()
        users = db.query(User).filter(
            User.is_active == True,
            User.onboarding_complete == True,
            User.subscription_status.in_(["trial", "active"]),
        ).all()

        for user in users:
            try:
                user_tz = pytz.timezone(user.timezone or "UTC")
                user_local = now_utc.replace(tzinfo=pytz.utc).astimezone(user_tz)
                user_time_str = user_local.strftime("%H:%M")

                check_in_times = user.check_in_times or ["08:00", "20:00"]
                if user_time_str not in check_in_times:
                    continue

                today_start = user_local.replace(hour=0, minute=0, second=0, microsecond=0)

                # Check this specific check-in not already sent today
                existing = db.query(CheckIn).filter(
                    CheckIn.user_id == user.id,
                    CheckIn.check_in_type == "daily",
                    CheckIn.scheduled_at >= today_start.astimezone(pytz.utc).replace(tzinfo=None),
                    CheckIn.message_sent.isnot(None),
                ).count()

                max_check_ins = user.check_in_frequency or 2
                if existing >= max_check_ins:
                    continue

                primary_goal = db.query(Goal).filter(
                    Goal.user_id == user.id,
                    Goal.is_primary == True,
                    Goal.active == True,
                ).first()

                if not primary_goal:
                    continue

                streak_obj = db.query(Streak).filter(
                    Streak.user_id == user.id,
                    Streak.goal_id == primary_goal.id,
                ).first()
                streak = streak_obj.current_streak if streak_obj else 0

                # Get last reply
                last_check_in = db.query(CheckIn).filter(
                    CheckIn.user_id == user.id,
                    CheckIn.check_in_type == "daily",
                    CheckIn.user_reply.isnot(None),
                ).order_by(CheckIn.reply_received_at.desc()).first()

                last_reply = last_check_in.user_reply if last_check_in else None
                days_since = 0
                if last_check_in and last_check_in.reply_received_at:
                    days_since = (datetime.utcnow() - last_check_in.reply_received_at).days

                time_of_day = "morning" if user_local.hour < 12 else "evening"

                message = await generate_check_in_message(
                    user.name or "there",
                    primary_goal.title,
                    streak,
                    user.message_tone or "adaptive",
                    time_of_day,
                    last_reply,
                    days_since,
                )

                await whatsapp_service.send_text(user.phone_number, message)

                check_in = CheckIn(
                    user_id=user.id,
                    goal_id=primary_goal.id,
                    check_in_type="daily",
                    scheduled_at=datetime.utcnow(),
                    sent_at=datetime.utcnow(),
                    message_sent=message,
                )
                db.add(check_in)
                db.commit()

            except Exception as e:
                logger.error(f"Check-in failed for {user.phone_number}: {e}")

    finally:
        db.close()


async def send_weekly_summaries():
    """Send weekly progress summaries every Sunday."""
    db: Session = SessionLocal()
    try:
        users = db.query(User).filter(
            User.is_active == True,
            User.onboarding_complete == True,
            User.subscription_status.in_(["trial", "active"]),
        ).all()

        week_ago = datetime.utcnow() - timedelta(days=7)

        for user in users:
            try:
                primary_goal = db.query(Goal).filter(
                    Goal.user_id == user.id,
                    Goal.is_primary == True,
                ).first()
                if not primary_goal:
                    continue

                total = db.query(CheckIn).filter(
                    CheckIn.user_id == user.id,
                    CheckIn.check_in_type == "daily",
                    CheckIn.sent_at >= week_ago,
                ).count()

                completed = db.query(CheckIn).filter(
                    CheckIn.user_id == user.id,
                    CheckIn.check_in_type == "daily",
                    CheckIn.sent_at >= week_ago,
                    CheckIn.assessment == "completed",
                ).count()

                streak_obj = db.query(Streak).filter(
                    Streak.user_id == user.id,
                    Streak.goal_id == primary_goal.id,
                ).first()
                streak = streak_obj.current_streak if streak_obj else 0

                summary = await generate_weekly_summary(
                    user.name or "there",
                    primary_goal.title,
                    streak,
                    completed,
                    total,
                )

                await whatsapp_service.send_text(user.phone_number, summary)

                check_in = CheckIn(
                    user_id=user.id,
                    goal_id=primary_goal.id,
                    check_in_type="weekly_summary",
                    scheduled_at=datetime.utcnow(),
                    sent_at=datetime.utcnow(),
                    message_sent=summary,
                )
                db.add(check_in)
                db.commit()

            except Exception as e:
                logger.error(f"Weekly summary failed for {user.phone_number}: {e}")

    finally:
        db.close()
