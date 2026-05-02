from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from db import UserDB
from checkin import format_checkin_message

db = UserDB()
scheduler = AsyncIOScheduler()


async def send_morning_checkins(send_message_func):
    users = db.get_all_active_users_for_checkin()
    for user in users:
        try:
            targets = db.get_targets_for_goal(user['goal_id'])
            streak = db.get_current_streak(user['user_id'], user['goal_id'])
            message = format_checkin_message(
                name=user.get('username', 'there'),
                targets=targets,
                streak=streak
            )
            await send_message_func(user['phone_number'], message)
        except Exception as e:
            print(f"Failed checkin for {user['user_id']}: {e}")


def start_scheduler(send_message_func):
    scheduler.add_job(
        send_morning_checkins,
        CronTrigger(hour=8, minute=0),
        args=[send_message_func],
        id='morning_checkins',
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler running")
