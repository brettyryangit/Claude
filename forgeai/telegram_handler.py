import asyncio
import os
import tempfile
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from db import init_db, UserDB
from onboarding import handle_onboarding_voice, WELCOME_MESSAGE, CHECKLIST_MESSAGE
from checkin import process_checkin_response
from whisper_transcribe import transcribe_audio_url
from safety import is_jailbreak_attempt
from rate_limiter import check_rate_limit, get_rate_limit_response
from config import TELEGRAM_BOT_TOKEN

db = UserDB()
pending_onboarding = {}
pending_plan_data = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = f"tg_{user.id}"
    name = user.first_name or "there"

    db.get_or_create_user(user_id, 'telegram', phone=None, username=name)

    await update.message.reply_text(WELCOME_MESSAGE.format(name=name))
    await update.message.reply_text(CHECKLIST_MESSAGE)
    pending_onboarding[user_id] = True


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = f"tg_{user.id}"
    name = user.first_name or "there"
    text = update.message.text.strip()

    db_user = db.get_or_create_user(user_id, 'telegram', phone=None, username=name)

    rate_check = check_rate_limit(user_id, db_user.get('subscription_tier', 'trial'))
    if not rate_check['allowed']:
        await update.message.reply_text(get_rate_limit_response(db_user.get('subscription_tier')))
        return

    if is_jailbreak_attempt(text):
        await update.message.reply_text("ForgeAI is here to keep you accountable to your goals only. What is your goal?")
        return

    await _process_input(update, user_id, name, db_user, text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = f"tg_{user.id}"
    name = user.first_name or "there"

    db_user = db.get_or_create_user(user_id, 'telegram', phone=None, username=name)

    rate_check = check_rate_limit(user_id, db_user.get('subscription_tier', 'trial'))
    if not rate_check['allowed']:
        await update.message.reply_text(get_rate_limit_response(db_user.get('subscription_tier')))
        return

    await update.message.reply_text("Got your voice note, transcribing now...")

    try:
        voice = update.message.voice or update.message.audio
        tg_file = await context.bot.get_file(voice.file_id)
        transcript = await _transcribe_telegram_voice(tg_file.file_path, context.bot.token)
    except Exception as e:
        await update.message.reply_text("Could not transcribe that. Try again or send a text message.")
        print(f"Transcription error: {e}")
        return

    if not transcript:
        await update.message.reply_text("I did not catch that. Try again or send a text message.")
        return

    if is_jailbreak_attempt(transcript):
        await update.message.reply_text("ForgeAI is here to keep you accountable to your goals only. What is your goal?")
        return

    await _process_input(update, user_id, name, db_user, transcript)


async def _transcribe_telegram_voice(file_path: str, bot_token: str) -> str:
    import openai
    from config import OPENAI_API_KEY

    openai.api_key = OPENAI_API_KEY

    url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
    response = requests.get(url)

    suffix = ".ogg" if file_path.endswith(".oga") or file_path.endswith(".ogg") else ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        return transcript
    finally:
        os.unlink(tmp_path)


async def _process_input(update: Update, user_id: str, name: str, db_user: dict, text: str):
    if not db_user.get('onboarded'):
        if user_id not in pending_onboarding:
            pending_onboarding[user_id] = True
            await update.message.reply_text(WELCOME_MESSAGE.format(name=name))
            await update.message.reply_text(CHECKLIST_MESSAGE)
            return

        if text.lower() == 'yes' and user_id in pending_plan_data:
            extracted = pending_plan_data.pop(user_id)
            transcript_saved = extracted.pop('transcript', '')
            goal_id = db.save_goal(user_id, extracted, transcript_saved)
            db.save_targets(goal_id, extracted.get('daily_targets', []))
            db.update_user(user_id, onboarded=True)
            pending_onboarding.pop(user_id, None)
            await update.message.reply_text("Plan locked in. Your first check-in is tomorrow morning. Let us go.")
            return

        response_text, extracted_data = handle_onboarding_voice(user_id, text)
        await update.message.reply_text(response_text)

        if extracted_data:
            pending_plan_data[user_id] = extracted_data
            pending_plan_data[user_id]['transcript'] = text
        return

    active_goals = db.get_active_goals(user_id)

    if not active_goals:
        await update.message.reply_text("You do not have an active goal. Type /start to set one up.")
        return

    goal_id = active_goals[0]['goal_id']
    response = process_checkin_response(user_id, goal_id, text)
    await update.message.reply_text(response)


def main():
    init_db()

    if not TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in .env")
        return

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("ForgeAI Telegram bot running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
