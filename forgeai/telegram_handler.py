import tempfile
import os
import requests
from config import TELEGRAM_BOT_TOKEN

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
TELEGRAM_FILE_API = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_message(chat_id: str, text: str):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")


def get_telegram_voice_url(file_id: str) -> str:
    resp = requests.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id}, timeout=10)
    file_path = resp.json()["result"]["file_path"]
    return f"{TELEGRAM_FILE_API}/{file_path}"


def transcribe_telegram_voice(file_id: str) -> str:
    from whisper_transcribe import transcribe_audio_url
    audio_url = get_telegram_voice_url(file_id)
    return transcribe_audio_url(audio_url)


def parse_telegram_update(data: dict) -> dict | None:
    """Extract the fields we need from a Telegram Update object."""
    message = data.get("message") or data.get("edited_message")
    if not message:
        return None

    chat_id = str(message["chat"]["id"])
    user = message.get("from", {})
    username = user.get("first_name") or user.get("username") or "there"

    voice = message.get("voice")
    text = message.get("text", "")

    return {
        "chat_id": chat_id,
        "username": username,
        "voice_file_id": voice["file_id"] if voice else None,
        "text": text,
    }


def set_webhook(webhook_url: str):
    resp = requests.post(
        f"{TELEGRAM_API}/setWebhook",
        json={"url": webhook_url},
        timeout=10
    )
    return resp.json()


def delete_webhook():
    resp = requests.post(f"{TELEGRAM_API}/deleteWebhook", timeout=10)
    return resp.json()
