from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Grit"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Database
    DATABASE_URL: str = "postgresql://localhost/grit"

    # Anthropic
    ANTHROPIC_API_KEY: str = ""

    # WhatsApp / Meta
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "grit-verify-token"
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v19.0"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_CORE: str = ""      # £4.99/month price ID
    STRIPE_PRICE_PRO: str = ""       # £9.99/month price ID
    STRIPE_PRICE_ELITE: str = ""     # £19.99/month price ID
    STRIPE_PRICE_ANNUAL: str = ""    # £59.99/year price ID

    # Cloudflare R2
    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_R2_ACCESS_KEY: str = ""
    CLOUDFLARE_R2_SECRET_KEY: str = ""
    CLOUDFLARE_R2_BUCKET: str = "grit-assets"
    CLOUDFLARE_R2_PUBLIC_URL: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
