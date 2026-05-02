from db import UserDB
from claude_agent import generate_pattern_insight, generate_weekly_review

db = UserDB()


def run_pattern_analysis(user_id: str, goal_id: str, goal_title: str) -> str | None:
    history = db.get_checkin_history(user_id, goal_id, days=30)
    if len(history) < 7:
        return None
    return generate_pattern_insight(goal_title, history)


def run_weekly_review(user_id: str, goal_id: str, goal_title: str) -> str | None:
    history = db.get_checkin_history(user_id, goal_id, days=7)
    if not history:
        return None
    return generate_weekly_review(goal_title, history)
