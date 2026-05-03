from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db import UserDB
from checkin import format_checkin_message
from pattern_detection import run_pattern_check, run_weekly_review

db = UserDB()
scheduler = BackgroundScheduler()


def send_morning_checkins(send_func):
    current_hour = datetime.utcnow().strftime('%H')
    users = db.get_all_active_users_for_checkin()
    for user in users:
        user_hour = user.get('checkin_time', '08:00').split(':')[0]
        if user_hour != current_hour:
            continue
        try:
            targets = db.get_targets_for_goal(user['goal_id'])
            streak = db.get_current_streak(user['user_id'], user['goal_id'])
            message = format_checkin_message(
                name=user.get('username', 'there'),
                targets=targets,
                streak=streak
            )
            send_func(user, message)
        except Exception as e:
            print(f"Failed checkin for {user['user_id']}: {e}")


def send_weekly_reviews(send_func):
    users = db.get_all_active_users_for_checkin()
    for user in users:
        try:
            review = run_weekly_review(user['user_id'], user['goal_id'], user['goal_title'])
            if review:
                send_func(user, f"Weekly Review\n\n{review}")
        except Exception as e:
            print(f"Weekly review failed for {user['user_id']}: {e}")


def send_pattern_insights(send_func):
    users = db.get_all_active_users_for_checkin()
    for user in users:
        try:
            insight = run_pattern_check(user['user_id'], user['goal_id'], user['goal_title'])
            if insight:
                send_func(user, f"Pattern Insight\n\n{insight}")
        except Exception as e:
            print(f"Pattern insight failed for {user['user_id']}: {e}")


def start_scheduler(send_func):
    # Run every hour at :00 — each job filters users by their checkin_time hour
    scheduler.add_job(
        send_morning_checkins,
        CronTrigger(minute=0),
        args=[send_func],
        id='morning_checkins',
        replace_existing=True
    )
    # Weekly review every Sunday at 09:00 UTC
    scheduler.add_job(
        send_weekly_reviews,
        CronTrigger(day_of_week='sun', hour=9, minute=0),
        args=[send_func],
        id='weekly_reviews',
        replace_existing=True
    )
    # Pattern insights every other Monday at 09:00 UTC
    scheduler.add_job(
        send_pattern_insights,
        CronTrigger(day_of_week='mon', hour=9, minute=0, week='*/2'),
        args=[send_func],
        id='pattern_insights',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler running")
