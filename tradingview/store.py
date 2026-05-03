import aiosqlite
import asyncio
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                indicators TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_candles_symbol_ts
            ON candles (symbol, timestamp)
        """)
        await db.commit()


async def insert_candle(symbol: str, timestamp: str, ohlcv: dict, indicators: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO candles (symbol, timestamp, open, high, low, close, volume, indicators)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT DO NOTHING
        """, (
            symbol,
            timestamp,
            ohlcv.get("open"),
            ohlcv.get("high"),
            ohlcv.get("low"),
            ohlcv.get("close"),
            ohlcv.get("volume"),
            json.dumps(indicators),
        ))
        await db.commit()


async def get_candles(symbol: str, limit: int = 100) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM candles
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (symbol, limit)) as cursor:
            rows = await cursor.fetchall()

    result = []
    for row in reversed(rows):
        entry = dict(row)
        entry["indicators"] = json.loads(entry["indicators"] or "{}")
        result.append(entry)
    return result


async def get_symbols() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT DISTINCT symbol FROM candles ORDER BY symbol") as cursor:
            rows = await cursor.fetchall()
    return [r[0] for r in rows]


async def get_candle_count(symbol: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM candles WHERE symbol = ?", (symbol,)
        ) as cursor:
            row = await cursor.fetchone()
    return row[0] if row else 0
