import anthropic
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

ONBOARDING_QUESTIONS = [
    "What's your name? I want to make this feel personal from day one.",
    "What's the ONE thing — your biggest goal — that if you nailed it, would change everything for you? Don't overthink it.",
    "How long have you been putting this off, and what keeps getting in the way?",
    "On a scale of 1–10, how serious are you right now about actually doing this?",
    "What does success look like for you in 90 days? Paint me a picture.",
    "How many days a week are you realistically able to commit to working on this goal?",
    "What time do you usually wake up, and what time zone are you in?",
    "Have you tried to achieve this before? What happened?",
    "Who in your life knows about this goal — or is this between you and me?",
    "Last one: what do you want me to do if you go quiet and miss a few check-ins — go easy on you, or hold you accountable hard?",
]


async def get_onboarding_response(step: int, user_answer: str, conversation_history: list) -> str:
    """Generate the next onboarding question or transition message."""
    system = """You are Grit — a no-nonsense but warm personal accountability coach on WhatsApp.
You're setting up a new user. Your job is to:
1. Acknowledge their answer warmly and briefly (1 sentence max)
2. Ask the next question naturally, like a real conversation
Keep responses short. No bullet points. No lists. Just talk like a human coach."""

    messages = conversation_history.copy()
    messages.append({"role": "user", "content": user_answer})

    if step < len(ONBOARDING_QUESTIONS):
        next_question = ONBOARDING_QUESTIONS[step]
        messages.append({
            "role": "user",
            "content": f"[SYSTEM: Acknowledge their answer briefly, then ask this next: {next_question}]"
        })

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system,
        messages=messages,
    )
    return response.content[0].text


async def generate_goal_plan(user_name: str, goal: str, answers: dict) -> str:
    """Generate a full personalised plan based on onboarding answers."""
    system = """You are an expert coach creating a highly personalised 90-day action plan.
Structure the plan with:
1. Goal Summary
2. Why This Matters (based on what they said)
3. Weekly Schedule (specific days/times based on availability they gave)
4. Week-by-Week Progression (weeks 1-4, 5-8, 9-12)
5. Daily Habits Checklist
6. Warning Signs to Watch For
7. How to Measure Success

Be specific. Use their exact words back at them. Make it feel written just for them."""

    prompt = f"""Create a 90-day personalised plan for {user_name}.

Their goal: {goal}

Their onboarding answers:
{json.dumps(answers, indent=2)}

Write the full plan now."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


async def generate_check_in_message(
    user_name: str,
    goal: str,
    streak: int,
    tone: str,
    time_of_day: str,
    last_reply: str = None,
    days_since_reply: int = 0,
) -> str:
    """Generate a personalised daily check-in message."""
    system = f"""You are Grit, a personal accountability coach texting {user_name} on WhatsApp.
Tone: {tone}. Adaptive means: warm when they're doing well, direct when they're slipping.
Current streak: {streak} days.
Time of day: {time_of_day}.
Keep messages SHORT — 2-4 sentences max. Conversational. No emojis overload. End with a simple yes/no question or action prompt."""

    context = f"Their goal: {goal}\nCurrent streak: {streak} days\n"
    if last_reply:
        context += f"Last thing they told me: {last_reply}\n"
    if days_since_reply > 1:
        context += f"They haven't replied in {days_since_reply} days.\n"

    urgency = ""
    if days_since_reply >= 3:
        urgency = "They've gone quiet. Call them out directly but don't be harsh."
    elif streak >= 7 and streak % 7 == 0:
        urgency = f"Celebrate their {streak}-day streak milestone."
    elif streak == 0:
        urgency = "They're starting fresh today. Be encouraging."

    prompt = f"{context}\n{urgency}\n\nWrite the check-in message now."

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


async def assess_check_in_reply(goal: str, message: str) -> str:
    """Assess whether a user completed their goal based on their reply."""
    prompt = f"""Goal: {goal}
User replied: "{message}"

Assess this reply. Return ONLY one word: completed, partial, missed, or unclear."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )
    result = response.content[0].text.strip().lower()
    if result not in ["completed", "partial", "missed", "unclear"]:
        return "unclear"
    return result


async def generate_weekly_summary(user_name: str, goal: str, streak: int, completions: int, total: int) -> str:
    """Generate a weekly progress summary."""
    system = "You are Grit, a personal accountability coach. Write a weekly summary WhatsApp message. Keep it under 100 words. Be direct, warm, and motivating."

    prompt = f"""{user_name}'s week:
Goal: {goal}
Check-ins completed: {completions}/{total}
Current streak: {streak} days

Write their weekly summary now."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


async def handle_free_chat(user_name: str, goal: str, message: str, conversation_history: list) -> str:
    """Handle free-form messages from users outside of check-ins."""
    system = f"""You are Grit, {user_name}'s personal accountability coach on WhatsApp.
Their primary goal: {goal}
Keep responses conversational, short (under 150 words), and always anchor back to their goal when relevant.
Never break character. You are their coach, not an AI assistant."""

    messages = conversation_history[-10:] + [{"role": "user", "content": message}]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=system,
        messages=messages,
    )
    return response.content[0].text
