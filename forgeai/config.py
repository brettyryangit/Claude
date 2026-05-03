import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WATI_API_KEY = os.getenv("WATI_API_KEY")
WATI_API_URL = os.getenv("WATI_API_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PHONE_NUMBER = os.getenv("ADMIN_PHONE_NUMBER")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

CLAUDE_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1000
TRIAL_DAYS = 7
AFFILIATE_COMMISSION = 0.30
PAYOUT_THRESHOLD = 20.00

RATE_LIMITS = {
    "trial": 10,
    "free": 10,
    "pro": 30,
    "elite": 999
}

SUBSCRIPTION_PRICES = {
    "pro": 2900,
    "elite": 9900
}
