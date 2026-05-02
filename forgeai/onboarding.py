from db import UserDB
from claude_agent import extract_onboarding_data
from safety import check_safety, get_safety_response, is_jailbreak_attempt

db = UserDB()

WELCOME_MESSAGE = """Hey {name} Welcome to ForgeAI.

I am your accountability coach. No forms, no questionnaires. Just talk.

Hit the mic button and talk for 2 to 4 minutes. Tell me:
- What goal you are chasing
- What has stopped you before
- Your daily schedule
- Sleep, diet, energy levels
- What success looks like in 30 days

Be honest. The more real you are, the better I coach you."""

CHECKLIST_MESSAGE = """While you are recording, cover these points. Just talk naturally, do not memorize them:

- Main goal such as gym, trading, career, sobriety
- Why do you actually care about this goal
- What has blocked you before
- How much time can you commit daily
- When do you wake up and go to bed
- Current sleep hours per night
- Diet situation honestly
- Work and stress situation
- Energy levels lately
- Any health issues or limitations
- What you know you should do but keep avoiding
- What success looks like in 30 days

Hit record when you are ready."""


def format_plan_message(extracted: dict) -> str:
    goal = extracted.get('goal', {})
    barriers = extracted.get('barriers', [])
    targets = extracted.get('daily_targets', [])
    macro = extracted.get('macro_goal_30_days', '')
    difficulty = extracted.get('difficulty_rating', 5)
    note = extracted.get('coach_note', '')
    questions = extracted.get('clarification_questions', [])

    barrier_text = "\n".join([f"- {b['name']}: {b['evidence']}" for b in barriers])
    target_text = "\n".join([
        f"- {t['action']} ({t['duration_mins']} mins, {t['frequency']})"
        for t in targets
    ])

    message = f"""Got it. Here is what I heard and your plan:

YOUR BARRIERS:
{barrier_text}

YOUR DAILY TARGETS:
{target_text}

30-DAY GOAL: {macro}
Difficulty: {difficulty} out of 10

COACH NOTE: {note}"""

    if questions:
        question_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        message += f"""

Quick clarifications needed:
{question_text}

Reply with voice or text."""
    else:
        message += """

Does this plan work for you? Reply YES to lock it in or tell me what to adjust."""

    return message


def handle_onboarding_voice(user_id: str, transcript: str) -> tuple:
    if is_jailbreak_attempt(transcript):
        return "ForgeAI is here to help you hit your goals, nothing else. What is the goal you are working towards?", None

    safety = check_safety(transcript)
    if safety.get('is_harmful') and safety.get('confidence', 0) > 0.7:
        db.flag_safety(user_id, transcript, safety.get('harm_type'), 'refused_plan')
        return get_safety_response(), None

    extracted = extract_onboarding_data(transcript)

    if extracted.get('is_harmful'):
        db.flag_safety(user_id, transcript, extracted.get('harm_type'), 'refused_plan')
        return get_safety_response(), None

    if extracted.get('error'):
        return "I did not quite catch all of that. Could you send another voice note? Tell me your goal and what has been stopping you.", None

    return format_plan_message(extracted), extracted
