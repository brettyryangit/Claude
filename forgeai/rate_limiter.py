import psycopg2
from datetime import datetime
from config import DATABASE_URL, RATE_LIMITS


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def check_rate_limit(user_id: str, tier: str) -> dict:
    limit = RATE_LIMITS.get(tier, 10)
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now()
    window_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    c.execute("SELECT message_count, window_start FROM rate_limits WHERE user_id = %s", (user_id,))
    row = c.fetchone()

    if not row:
        c.execute(
            "INSERT INTO rate_limits (user_id, message_count, window_start, last_message) VALUES (%s, 1, %s, %s)",
            (user_id, window_start, now)
        )
        conn.commit()
        conn.close()
        return {"allowed": True, "count": 1, "limit": limit}

    count, stored_window = row

    if stored_window.date() < now.date():
        c.execute(
            "UPDATE rate_limits SET message_count = 1, window_start = %s, last_message = %s WHERE user_id = %s",
            (window_start, now, user_id)
        )
        conn.commit()
        conn.close()
        return {"allowed": True, "count": 1, "limit": limit}

    if count >= limit:
        conn.close()
        return {"allowed": False, "count": count, "limit": limit}

    c.execute(
        "UPDATE rate_limits SET message_count = message_count + 1, last_message = %s WHERE user_id = %s",
        (now, user_id)
    )
    conn.commit()
    conn.close()
    return {"allowed": True, "count": count + 1, "limit": limit}


def get_rate_limit_response(tier: str) -> str:
    if tier in ["trial", "free"]:
        return """You have reached today's message limit on the free plan.

Upgrade to Pro at $29 per month for 30 daily messages and full accountability coaching.

Your check-in will resume tomorrow morning."""
    return """You have sent a lot of messages today. ForgeAI works best for focused daily check-ins.

I will be here for your check-in tomorrow morning. Rest up."""
