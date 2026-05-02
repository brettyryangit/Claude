import stripe
import uuid
from flask import request, jsonify
from db import UserDB, get_connection
from config import STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, SUBSCRIPTION_PRICES

stripe.api_key = STRIPE_SECRET_KEY
db = UserDB()


def create_checkout_session(user_id: str, tier: str, phone: str) -> str:
    price_amount = SUBSCRIPTION_PRICES.get(tier)
    if not price_amount:
        raise ValueError(f"Unknown tier: {tier}")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"ForgeAI {tier.capitalize()}"},
                "unit_amount": price_amount,
                "recurring": {"interval": "month"},
            },
            "quantity": 1,
        }],
        mode="subscription",
        success_url="https://forgeai.app/success",
        cancel_url="https://forgeai.app/cancel",
        metadata={"user_id": user_id, "tier": tier, "phone": phone},
    )
    return session.url


def handle_stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return jsonify({"error": "invalid signature"}), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        tier = session["metadata"]["tier"]
        stripe_sub_id = session.get("subscription")
        _activate_subscription(user_id, tier, stripe_sub_id)

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        _cancel_subscription_by_stripe_id(sub["id"])

    return jsonify({"status": "ok"})


def _activate_subscription(user_id: str, tier: str, stripe_subscription_id: str):
    conn = get_connection()
    c = conn.cursor()
    sub_id = str(uuid.uuid4())
    c.execute(
        """INSERT INTO subscriptions (subscription_id, user_id, tier, stripe_subscription_id)
           VALUES (%s, %s, %s, %s)""",
        (sub_id, user_id, tier, stripe_subscription_id)
    )
    c.execute(
        "UPDATE users SET subscription_tier = %s, subscription_started_at = NOW() WHERE user_id = %s",
        (tier, user_id)
    )
    conn.commit()
    conn.close()


def _cancel_subscription_by_stripe_id(stripe_subscription_id: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE subscriptions SET active = FALSE, cancelled_at = NOW() WHERE stripe_subscription_id = %s",
        (stripe_subscription_id,)
    )
    c.execute("""
        UPDATE users SET subscription_tier = 'free'
        WHERE user_id = (
            SELECT user_id FROM subscriptions WHERE stripe_subscription_id = %s
        )
    """, (stripe_subscription_id,))
    conn.commit()
    conn.close()
