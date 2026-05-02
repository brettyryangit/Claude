import uuid
from db import get_connection, UserDB
from config import AFFILIATE_COMMISSION, PAYOUT_THRESHOLD

db = UserDB()


def get_referral_stats(user_id: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT clicks_count, earnings_total, converted FROM referrals WHERE referrer_id = %s",
        (user_id,)
    )
    rows = c.fetchall()
    conn.close()

    total_clicks = sum(r[0] for r in rows)
    total_earnings = sum(r[1] for r in rows)
    conversions = sum(1 for r in rows if r[2])

    return {
        "clicks": total_clicks,
        "conversions": conversions,
        "earnings": total_earnings,
        "payout_eligible": total_earnings >= PAYOUT_THRESHOLD
    }


def record_referral_click(referral_code: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "UPDATE referrals SET clicks_count = clicks_count + 1 WHERE referral_code = %s",
        (referral_code,)
    )
    conn.commit()
    conn.close()


def convert_referral(referred_user_id: str, referral_code: str, subscription_amount: int):
    conn = get_connection()
    c = conn.cursor()
    commission = (subscription_amount / 100) * AFFILIATE_COMMISSION
    c.execute(
        """UPDATE referrals
           SET converted = TRUE, conversion_date = NOW(),
               referred_user_id = %s,
               earnings_total = earnings_total + %s
           WHERE referral_code = %s""",
        (referred_user_id, commission, referral_code)
    )
    conn.commit()
    conn.close()


def format_referral_message(user_id: str) -> str:
    user = db.get_user(user_id)
    code = user.get('referral_code', '')
    stats = get_referral_stats(user_id)

    return f"""Your referral link: https://forgeai.app/ref/{code}

Stats:
- Clicks: {stats['clicks']}
- Sign-ups: {stats['conversions']}
- Earnings: ${stats['earnings']:.2f}

You earn 30% commission on every paying user you refer. Payouts go out when you hit $20."""
