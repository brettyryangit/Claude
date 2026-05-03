"""
FastAPI webhook server that receives TradingView alerts and stores them.

Start with:
    uvicorn server:app --host 0.0.0.0 --port 8000

Then point your TradingView alert webhook to:
    http://<your-server>:8000/webhook
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

import store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await store.init_db()
    yield


app = FastAPI(title="TradingView → Claude Bridge", lifespan=lifespan)


@app.post("/webhook")
async def receive_alert(request: Request):
    """
    Accepts JSON payloads from TradingView alerts.

    Expected fields (all optional except symbol and close):
        symbol, open, high, low, close, volume, timestamp
        + any indicator fields (rsi, macd, macd_signal, ...)
    """
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    symbol = data.get("symbol", "UNKNOWN").upper()
    timestamp = data.get("timestamp") or datetime.now(timezone.utc).isoformat()

    ohlcv = {
        "open": _to_float(data.get("open")),
        "high": _to_float(data.get("high")),
        "low": _to_float(data.get("low")),
        "close": _to_float(data.get("close")),
        "volume": _to_float(data.get("volume")),
    }

    # Everything that isn't a standard field is treated as an indicator
    standard_fields = {"symbol", "open", "high", "low", "close", "volume", "timestamp"}
    indicators = {
        k: _to_float(v)
        for k, v in data.items()
        if k not in standard_fields
    }

    await store.insert_candle(symbol, timestamp, ohlcv, indicators)

    count = await store.get_candle_count(symbol)
    return JSONResponse({"status": "ok", "symbol": symbol, "candles_stored": count})


@app.get("/status")
async def status():
    symbols = await store.get_symbols()
    counts = {s: await store.get_candle_count(s) for s in symbols}
    return {"symbols": counts}


@app.get("/data/{symbol}")
async def get_data(symbol: str, limit: int = 50):
    candles = await store.get_candles(symbol.upper(), limit=limit)
    return {"symbol": symbol.upper(), "candles": candles}


def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
