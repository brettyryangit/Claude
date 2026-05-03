from functools import wraps
from flask import Blueprint, request, jsonify
from db import get_connection, UserDB
from config import ADMIN_PHONE_NUMBER, ADMIN_API_KEY

admin_bp = Blueprint('admin', __name__)
db = UserDB()


def is_admin(phone: str) -> bool:
    return phone == ADMIN_PHONE_NUMBER


def require_admin_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-Admin-Key') or request.args.get('admin_key')
        if not ADMIN_API_KEY or key != ADMIN_API_KEY:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin/stats', methods=['GET'])
@require_admin_key
def get_stats():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users WHERE active = TRUE")
    total_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE subscription_tier IN ('pro', 'elite') AND active = TRUE")
    paying_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM checkins WHERE checkin_date > NOW() - INTERVAL '24 hours'")
    checkins_today = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE safety_flagged = TRUE")
    flagged_users = c.fetchone()[0]

    conn.close()

    return jsonify({
        "total_users": total_users,
        "paying_users": paying_users,
        "checkins_today": checkins_today,
        "flagged_users": flagged_users,
        "mrr_estimate": paying_users * 29
    })


@admin_bp.route('/admin/flag_user', methods=['POST'])
@require_admin_key
def flag_user():
    data = request.json
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    db.update_user(user_id, safety_flagged=True, active=False)
    return jsonify({"status": "user flagged and deactivated"})


@admin_bp.route('/admin/users', methods=['GET'])
@require_admin_key
def list_users():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user_id, platform, phone_number, username, subscription_tier,
               onboarded, safety_flagged, created_at
        FROM users ORDER BY created_at DESC LIMIT 100
    """)
    rows = c.fetchall()
    conn.close()
    users = [
        {
            "user_id": r[0], "platform": r[1], "phone": r[2],
            "username": r[3], "tier": r[4], "onboarded": r[5],
            "flagged": r[6], "created_at": str(r[7])
        }
        for r in rows
    ]
    return jsonify({"users": users})
