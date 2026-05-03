import psycopg2cffi as psycopg2
import psycopg2.extras
import uuid
from datetime import datetime, timedelta
from config import DATABASE_URL, TRIAL_DAYS


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR PRIMARY KEY,
            platform VARCHAR NOT NULL,
            phone_number VARCHAR,
            username VARCHAR,
            created_at TIMESTAMP DEFAULT NOW(),
            subscription_tier VARCHAR DEFAULT 'trial',
            trial_ends_at TIMESTAMP,
            subscription_started_at TIMESTAMP,
            subscription_expires_at TIMESTAMP,
            stripe_customer_id VARCHAR,
            timezone VARCHAR DEFAULT 'UTC',
            checkin_time VARCHAR DEFAULT '08:00',
            referral_code VARCHAR UNIQUE,
            referred_by VARCHAR,
            onboarded BOOLEAN DEFAULT FALSE,
            safety_flagged BOOLEAN DEFAULT FALSE,
            safety_flag_count INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT TRUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            goal_id VARCHAR PRIMARY KEY,
            user_id VARCHAR REFERENCES users(user_id),
            title VARCHAR NOT NULL,
            macro_goal TEXT,
            difficulty_rating INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            active BOOLEAN DEFAULT TRUE,
            last_checkin_date TIMESTAMP,
            initial_voice_transcript TEXT,
            extracted_data JSONB
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS targets (
            target_id VARCHAR PRIMARY KEY,
            goal_id VARCHAR REFERENCES goals(goal_id),
            action_description TEXT NOT NULL,
            barrier_type VARCHAR,
            frequency VARCHAR DEFAULT 'daily',
            duration_minutes INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            active BOOLEAN DEFAULT TRUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            checkin_id VARCHAR PRIMARY KEY,
            user_id VARCHAR REFERENCES users(user_id),
            goal_id VARCHAR REFERENCES goals(goal_id),
            checkin_date TIMESTAMP DEFAULT NOW(),
            status VARCHAR,
            user_voice_transcript TEXT,
            streak INTEGER DEFAULT 0,
            feedback TEXT,
            ai_extracted_context JSONB,
            targets_completed INTEGER DEFAULT 0,
            targets_total INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            subscription_id VARCHAR PRIMARY KEY,
            user_id VARCHAR REFERENCES users(user_id),
            tier VARCHAR NOT NULL,
            started_at TIMESTAMP DEFAULT NOW(),
            renewal_date TIMESTAMP,
            stripe_subscription_id VARCHAR,
            active BOOLEAN DEFAULT TRUE,
            cancelled_at TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id VARCHAR PRIMARY KEY,
            referrer_id VARCHAR REFERENCES users(user_id),
            referral_code VARCHAR NOT NULL,
            referred_user_id VARCHAR,
            created_at TIMESTAMP DEFAULT NOW(),
            converted BOOLEAN DEFAULT FALSE,
            conversion_date TIMESTAMP,
            clicks_count INTEGER DEFAULT 0,
            earnings_total FLOAT DEFAULT 0.0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS safety_flags (
            flag_id VARCHAR PRIMARY KEY,
            user_id VARCHAR REFERENCES users(user_id),
            flagged_at TIMESTAMP DEFAULT NOW(),
            goal_attempt TEXT,
            flag_reason VARCHAR,
            action_taken VARCHAR
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS rate_limits (
            user_id VARCHAR PRIMARY KEY,
            message_count INTEGER DEFAULT 0,
            window_start TIMESTAMP DEFAULT NOW(),
            last_message TIMESTAMP DEFAULT NOW()
        )
    """)

    conn.commit()
    conn.close()
    print("Database ready")


class UserDB:

    def get_or_create_user(self, user_id: str, platform: str, phone: str = None, username: str = None) -> dict:
        conn = get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = c.fetchone()

        if not user:
            referral_code = str(uuid.uuid4())[:8].upper()
            trial_ends = datetime.now() + timedelta(days=TRIAL_DAYS)
            c.execute(
                """INSERT INTO users (user_id, platform, phone_number, username, referral_code, trial_ends_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, platform, phone, username, referral_code, trial_ends)
            )
            conn.commit()
            c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            user = c.fetchone()

        conn.close()
        return dict(user)

    def update_user(self, user_id: str, **kwargs):
        conn = get_connection()
        c = conn.cursor()
        set_clause = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [user_id]
        c.execute(f"UPDATE users SET {set_clause} WHERE user_id = %s", values)
        conn.commit()
        conn.close()

    def get_user(self, user_id: str) -> dict:
        conn = get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = c.fetchone()
        conn.close()
        return dict(user) if user else None

    def save_goal(self, user_id: str, extracted_data: dict, transcript: str) -> str:
        conn = get_connection()
        c = conn.cursor()
        goal_id = str(uuid.uuid4())
        goal = extracted_data.get('goal', {})
        c.execute(
            """INSERT INTO goals (goal_id, user_id, title, macro_goal, difficulty_rating, initial_voice_transcript, extracted_data)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                goal_id, user_id,
                goal.get('primary', 'My Goal'),
                extracted_data.get('macro_goal_30_days', ''),
                extracted_data.get('difficulty_rating', 5),
                transcript,
                psycopg2.extras.Json(extracted_data)
            )
        )
        conn.commit()
        conn.close()
        return goal_id

    def save_targets(self, goal_id: str, targets: list):
        conn = get_connection()
        c = conn.cursor()
        for target in targets:
            c.execute(
                """INSERT INTO targets (target_id, goal_id, action_description, barrier_type, frequency, duration_minutes)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    str(uuid.uuid4()), goal_id,
                    target.get('action', ''),
                    target.get('barrier_addressed', ''),
                    target.get('frequency', 'daily'),
                    target.get('duration_mins', 15)
                )
            )
        conn.commit()
        conn.close()

    def save_checkin(self, user_id: str, goal_id: str, status: str, transcript: str,
                     streak: int, feedback: str, targets_completed: int, targets_total: int) -> str:
        conn = get_connection()
        c = conn.cursor()
        checkin_id = str(uuid.uuid4())
        c.execute(
            """INSERT INTO checkins (checkin_id, user_id, goal_id, status, user_voice_transcript,
                                     streak, feedback, targets_completed, targets_total)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (checkin_id, user_id, goal_id, status, transcript, streak, feedback, targets_completed, targets_total)
        )
        c.execute("UPDATE goals SET last_checkin_date = NOW() WHERE goal_id = %s", (goal_id,))
        conn.commit()
        conn.close()
        return checkin_id

    def get_current_streak(self, user_id: str, goal_id: str) -> int:
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "SELECT streak FROM checkins WHERE user_id = %s AND goal_id = %s ORDER BY checkin_date DESC LIMIT 1",
            (user_id, goal_id)
        )
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

    def get_checkin_history(self, user_id: str, goal_id: str, days: int = 30) -> list:
        conn = get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute(
            """SELECT * FROM checkins WHERE user_id = %s AND goal_id = %s
               AND checkin_date > NOW() - INTERVAL '%s days'
               ORDER BY checkin_date DESC""",
            (user_id, goal_id, days)
        )
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_active_goals(self, user_id: str) -> list:
        conn = get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM goals WHERE user_id = %s AND active = TRUE", (user_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_targets_for_goal(self, goal_id: str) -> list:
        conn = get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("SELECT * FROM targets WHERE goal_id = %s AND active = TRUE", (goal_id,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def flag_safety(self, user_id: str, goal_attempt: str, flag_reason: str, action_taken: str):
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO safety_flags (flag_id, user_id, goal_attempt, flag_reason, action_taken) VALUES (%s, %s, %s, %s, %s)",
            (str(uuid.uuid4()), user_id, goal_attempt, flag_reason, action_taken)
        )
        c.execute(
            "UPDATE users SET safety_flag_count = safety_flag_count + 1 WHERE user_id = %s",
            (user_id,)
        )
        conn.commit()
        conn.close()

    def get_all_active_users_for_checkin(self) -> list:
        conn = get_connection()
        c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        c.execute("""
            SELECT u.*, g.goal_id, g.title as goal_title
            FROM users u
            JOIN goals g ON u.user_id = g.user_id
            WHERE u.active = TRUE
            AND u.onboarded = TRUE
            AND g.active = TRUE
            AND u.safety_flagged = FALSE
        """)
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]
