import asyncio
from flask import Flask, request, jsonify
from db import init_db, UserDB
from onboarding import handle_onboarding_voice, WELCOME_MESSAGE, CHECKLIST_MESSAGE
from checkin import process_checkin_response
from whisper_transcribe import transcribe_audio_url
from safety import is_jailbreak_attempt
from rate_limiter import check_rate_limit, get_rate_limit_response
from scheduler import start_scheduler
from stripe_handler import handle_stripe_webhook, create_checkout_session
from admin import admin_bp
import requests
from config import WATI_API_KEY, WATI_API_URL

app = Flask(__name__)
app.register_blueprint(admin_bp)
db = UserDB()

pending_onboarding = {}
pending_plan_data = {}


def send_whatsapp_message(phone: str, message: str):
    headers = {
        "Authorization": f"Bearer {WATI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "receivers": [{"whatsappNumber": phone}],
        "message": message
    }
    try:
        requests.post(f"{WATI_API_URL}/api/v1/sendSessionMessage", headers=headers, json=payload)
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")


@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    phone = data.get('waId', '')
    message_type = data.get('type', 'text')
    user_name = data.get('senderName', 'there')
    user_id = f"wa_{phone}"

    user = db.get_or_create_user(user_id, 'whatsapp', phone, user_name)

    rate_check = check_rate_limit(user_id, user.get('subscription_tier', 'trial'))
    if not rate_check['allowed']:
        send_whatsapp_message(phone, get_rate_limit_response(user.get('subscription_tier')))
        return jsonify({"status": "rate_limited"})

    if message_type == 'audio':
        audio_url = data.get('data', {}).get('url', '')
        transcript = transcribe_audio_url(audio_url)
    else:
        transcript = data.get('text', {}).get('body', '')

    if not transcript:
        send_whatsapp_message(phone, "I did not catch that. Try sending a voice note or a text message.")
        return jsonify({"status": "no_input"})

    if is_jailbreak_attempt(transcript):
        send_whatsapp_message(phone, "ForgeAI is here to keep you accountable to your goals only. What is your goal?")
        return jsonify({"status": "blocked"})

    if not user.get('onboarded'):
        if user_id not in pending_onboarding:
            pending_onboarding[user_id] = True
            send_whatsapp_message(phone, WELCOME_MESSAGE.format(name=user_name))
            send_whatsapp_message(phone, CHECKLIST_MESSAGE)
            return jsonify({"status": "welcome_sent"})
        else:
            response_text, extracted_data = handle_onboarding_voice(user_id, transcript)
            send_whatsapp_message(phone, response_text)

            if extracted_data:
                pending_plan_data[user_id] = extracted_data
                pending_plan_data[user_id]['transcript'] = transcript

    else:
        active_goals = db.get_active_goals(user_id)

        if transcript.strip().lower() == 'yes' and user_id in pending_plan_data:
            extracted = pending_plan_data.pop(user_id)
            transcript_saved = extracted.pop('transcript', '')
            goal_id = db.save_goal(user_id, extracted, transcript_saved)
            db.save_targets(goal_id, extracted.get('daily_targets', []))
            db.update_user(user_id, onboarded=True)
            pending_onboarding.pop(user_id, None)
            send_whatsapp_message(phone, "Plan locked in. Your first check-in is tomorrow morning. Let us go.")
            return jsonify({"status": "plan_saved"})

        if not active_goals:
            send_whatsapp_message(phone, "You do not have an active goal. Say new goal to set one up.")
            return jsonify({"status": "no_goals"})

        goal_id = active_goals[0]['goal_id']
        response = process_checkin_response(user_id, goal_id, transcript)
        send_whatsapp_message(phone, response)

    return jsonify({"status": "ok"})


@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    return handle_stripe_webhook()


@app.route('/upgrade/<tier>', methods=['GET'])
def upgrade(tier: str):
    phone = request.args.get('phone', '')
    user_id = f"wa_{phone}"
    try:
        url = create_checkout_session(user_id, tier, phone)
        return jsonify({"checkout_url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ForgeAI running"})


if __name__ == '__main__':
    init_db()
    start_scheduler(send_whatsapp_message)
    app.run(host='0.0.0.0', port=8080, debug=False)
