import stripe
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

TIER_PRICES = {
    "core": settings.STRIPE_PRICE_CORE,
    "pro": settings.STRIPE_PRICE_PRO,
    "elite": settings.STRIPE_PRICE_ELITE,
    "annual": settings.STRIPE_PRICE_ANNUAL,
}

TIER_NAMES = {
    "core": "Core — £4.99/month",
    "pro": "Pro — £9.99/month",
    "elite": "Elite — £19.99/month",
    "annual": "Annual — £59.99/year",
}


def create_checkout_link(user_phone: str, tier: str = "pro") -> str:
    """Create a Stripe payment link for the given tier."""
    price_id = TIER_PRICES.get(tier)
    if not price_id:
        raise ValueError(f"Unknown tier: {tier}")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"phone_number": user_phone, "tier": tier},
        success_url="https://grit.app/success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://grit.app/cancel",
    )
    return session.url


def get_subscription_tier_from_event(event: dict) -> tuple[str, str]:
    """Extract phone number and tier from Stripe webhook event."""
    session = event["data"]["object"]
    metadata = session.get("metadata", {})
    phone = metadata.get("phone_number", "")
    tier = metadata.get("tier", "pro")
    return phone, tier


def cancel_subscription(stripe_customer_id: str) -> bool:
    try:
        subscriptions = stripe.Subscription.list(customer=stripe_customer_id, status="active")
        for sub in subscriptions.auto_paging_iter():
            stripe.Subscription.cancel(sub.id)
        return True
    except stripe.StripeError as e:
        logger.error(f"Stripe cancel error: {e}")
        return False
