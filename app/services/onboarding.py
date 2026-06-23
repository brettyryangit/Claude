import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.goal import Goal
from app.models.streak import Streak
from app.services.claude_ai import (
    get_onboarding_response,
    generate_goal_plan,
    ONBOARDING_QUESTIONS,
)
from app.services.whatsapp import whatsapp_service
from app.services.pdf_generator import create_and_upload_plan
from app.services.stripe_service import create_checkout_link, TIER_NAMES

logger = logging.getLogger(__name__)

GOAL_CATEGORIES = {
    "gym": "fitness", "fitness": "fitness", "weight": "fitness", "health": "fitness",
    "six pack": "fitness", "muscle": "fitness", "run": "fitness", "sport": "fitness",
    "money": "finance", "save": "finance", "debt": "finance", "invest": "finance",
    "finance": "finance", "budget": "finance", "income": "finance",
    "job": "career", "career": "career", "business": "career", "work": "career",
    "skill": "career", "learn": "career", "study": "career", "exam": "career",
    "anxiety": "wellness", "stress": "wellness", "mental": "wellness", "sleep": "wellness",
    "meditat": "wellness", "mindful": "wellness", "therapy": "wellness",
}


def detect_category(goal_text: str) -> str:
    goal_lower = goal_text.lower()
    for keyword, category in GOAL_CATEGORIES.items():
        if keyword in goal_lower:
            return category
    return "general"


async def handle_onboarding_message(user: User, message: str, db: Session) -> None:
    """Process each step of the onboarding flow."""
    step = user.onboarding_step
    answers = user.onboarding_answers or {}

    # Store the answer
    answer_key = f"q{step}"
    answers[answer_key] = message

    # Extract key info from specific steps
    if step == 0:
        # First answer is their name
        name = message.strip().split()[0].capitalize()
        user.name = name

    if step == 1:
        # Second answer is their primary goal
        answers["primary_goal"] = message
        answers["goal_category"] = detect_category(message)

    if step == 6:
        # Extract timezone from their wake time answer
        tz_hints = {
            "uk": "Europe/London", "london": "Europe/London", "gmt": "Europe/London",
            "new york": "America/New_York", "est": "America/New_York",
            "la": "America/Los_Angeles", "pst": "America/Los_Angeles",
            "australia": "Australia/Sydney", "sydney": "Australia/Sydney",
            "dubai": "Asia/Dubai",
        }
        msg_lower = message.lower()
        for hint, tz in tz_hints.items():
            if hint in msg_lower:
                user.timezone = tz
                break

    user.onboarding_answers = answers
    user.onboarding_step = step + 1

    # Build conversation history for Claude
    history = []
    for i in range(step):
        if i == 0:
            history.append({"role": "assistant", "content": ONBOARDING_QUESTIONS[0]})
        if f"q{i}" in answers:
            history.append({"role": "user", "content": answers[f"q{i}"]})
        if i + 1 < step and i + 1 < len(ONBOARDING_QUESTIONS):
            history.append({"role": "assistant", "content": ONBOARDING_QUESTIONS[i + 1]})

    total_questions = len(ONBOARDING_QUESTIONS)

    if user.onboarding_step >= total_questions:
        # Onboarding complete — generate plan and send payment link
        await _complete_onboarding(user, db)
    else:
        # Send next question
        response = await get_onboarding_response(user.onboarding_step, message, history)
        await whatsapp_service.send_text(user.phone_number, response)

    db.commit()


async def _complete_onboarding(user: User, db: Session) -> None:
    """Wrap up onboarding: create goal, generate plan PDF, send payment link."""
    answers = user.onboarding_answers or {}
    primary_goal = answers.get("primary_goal", "achieve my goal")
    category = answers.get("goal_category", "general")
    name = user.name or "there"

    # Create the primary goal
    goal = Goal(
        user_id=user.id,
        title=primary_goal,
        category=category,
        is_primary=True,
        description=answers.get("q4", ""),
    )
    db.add(goal)
    db.flush()

    # Create streak record
    streak = Streak(user_id=user.id, goal_id=goal.id)
    db.add(streak)

    # Set trial end date
    user.trial_ends_at = datetime.utcnow() + timedelta(days=7)
    user.onboarding_complete = True

    # Tell them we're building their plan
    await whatsapp_service.send_text(
        user.phone_number,
        f"That's everything I need, {name}. Give me 60 seconds — I'm building your personalised 90-day plan right now. 🔨"
    )

    # Generate the plan
    try:
        plan_content = await generate_goal_plan(name, primary_goal, answers)
        goal.plan_content = plan_content
        goal.plan_generated = True
        db.flush()

        # Generate and upload PDF
        pdf_url = await create_and_upload_plan(name, primary_goal, plan_content)
        goal.plan_pdf_url = pdf_url
        db.flush()

        # Send the PDF
        await whatsapp_service.send_document(
            user.phone_number,
            pdf_url,
            f"{name}-90-day-plan.pdf",
            f"Your personalised 90-day plan, {name}. Save this. Refer back to it. This is your roadmap. 🗺️"
        )
    except Exception as e:
        logger.error(f"Plan generation failed for {user.phone_number}: {e}")

    # Send pricing options
    await whatsapp_service.send_text(
        user.phone_number,
        f"""Your 7-day free trial starts now, {name}. I'll check in with you twice a day and send you a morning boost every morning.

After your trial, choose your plan:

1️⃣ *Core* — £4.99/month (3 goals, 2 daily check-ins)
2️⃣ *Pro* — £9.99/month (unlimited goals, 3 check-ins, streak analytics)
3️⃣ *Elite* — £19.99/month (everything + weekly coaching recap)
4️⃣ *Annual* — £59.99/year (Pro features, best value)

Reply with 1, 2, 3, or 4 and I'll send you a secure payment link. Or enjoy the free trial first — no pressure. 👊"""
    )
