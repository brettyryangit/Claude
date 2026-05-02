from db import UserDB
from claude_agent import generate_checkin_feedback
from safety import is_jailbreak_attempt, check_safety, get_safety_response

db = UserDB()

CHECKIN_MESSAGE = """Good morning {name}. Day {day_number}.

Today's targets:
{targets}

How did you do? Hit record and give me a quick update."""

MISSED_CHECKIN_MESSAGE = """Hey {name}. You missed your check-in yesterday.

No update from you means I count it as a miss.

Streak reset to 0.

Today's targets are the same. Hit record when you are ready to get back on it."""


def format_checkin_message(name: str, targets: list, streak: int) -> str:
    target_text = "\n".join([f"- {t['action_description']}" for t in targets])
    day_num = streak + 1
    return CHECKIN_MESSAGE.format(name=name, day_number=day_num, targets=target_text)


def process_checkin_response(user_id: str, goal_id: str, transcript: str) -> str:
    if is_jailbreak_attempt(transcript):
        return "Let us stay focused on your goals. How did your targets go today?"

    safety = check_safety(transcript)
    if safety.get('is_harmful') and safety.get('confidence', 0) > 0.8:
        db.flag_safety(user_id, transcript, safety.get('harm_type'), 'checkin_concern')
        return get_safety_response()

    targets = db.get_targets_for_goal(goal_id)
    target_descriptions = [t['action_description'] for t in targets]
    current_streak = db.get_current_streak(user_id, goal_id)

    transcript_lower = transcript.lower()
    yes_words = ['yes', 'yeah', 'yep', 'done', 'completed', 'hit', 'did it', 'finished', 'nailed']
    no_words = ['no', 'nope', 'missed', 'skipped', 'failed', "didn't", 'did not', "couldn't"]
    partial_words = ['partial', 'some', 'half', 'most', 'almost', 'nearly', 'part of']

    if any(word in transcript_lower for word in partial_words):
        status = 'partial'
        targets_completed = max(1, len(targets) // 2)
    elif any(word in transcript_lower for word in no_words):
        status = 'no'
        targets_completed = 0
    else:
        status = 'yes'
        targets_completed = len(targets)

    new_streak = current_streak + 1 if status in ['yes', 'partial'] else 0

    history = db.get_checkin_history(user_id, goal_id, days=30)
    pattern_context = ""
    if len(history) >= 14:
        miss_count = sum(1 for h in history if h['status'] == 'no')
        if miss_count > 3:
            pattern_context = f"This user has missed {miss_count} of the last {len(history)} check-ins."

    feedback = generate_checkin_feedback(
        target_descriptions=target_descriptions,
        transcript=transcript,
        status=status,
        streak=new_streak,
        targets_hit=targets_completed,
        targets_total=len(targets),
        historical_patterns=pattern_context
    )

    db.save_checkin(
        user_id=user_id,
        goal_id=goal_id,
        status=status,
        transcript=transcript,
        streak=new_streak,
        feedback=feedback,
        targets_completed=targets_completed,
        targets_total=len(targets)
    )

    streak_line = f"\nStreak: {new_streak} days" if new_streak > 0 else "\nStreak reset. Back to Day 0."
    return feedback + streak_line
