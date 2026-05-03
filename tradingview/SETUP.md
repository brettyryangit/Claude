# TradingView + Claude Integration

## Quick Start

### 1. Install dependencies
```bash
cd tradingview
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Start the webhook server
```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Expose it to the internet using [ngrok](https://ngrok.com/) for local testing:
```bash
ngrok http 8000
# Copy the https URL — e.g. https://abc123.ngrok.io
```

### 4. Start the interactive CLI (in a new terminal)
```bash
python cli.py
```

---

## Using the CLI

### Add indicators to track
```
add rsi
add macd
add stoch_k
add stoch_d
```

Supported built-ins: `rsi`, `macd`, `macd_signal`, `macd_hist`, `stoch_k`, `stoch_d`,
`cci`, `mfi`, `obv`, `williams_r`, `adx`, `atr`, `ema_20`, `ema_50`, `ema_200`,
`bb_upper`, `bb_lower`, `vwap`

You can also add any custom name — it just needs to match the field in your webhook JSON.

### Generate your Pine Script
```
pine script
```
Copy the output into TradingView's Pine Script editor.

### Analyze for divergence
```
analyze BTCUSDT
```
Or just talk naturally:
```
Is there any hidden bullish divergence on ETHUSDT using RSI and MACD?
```

---

## TradingView Setup

1. Open TradingView → open a chart
2. Click **Alerts** → **Create Alert**
3. Set **Condition** to your script or indicator
4. Under **Notifications**, enable **Webhook URL**
5. Paste your server URL: `https://your-server/webhook`
6. Set the **Message** to the JSON payload from the Pine Script template

### Example webhook payload TradingView sends:
```json
{
  "symbol": "BTCUSDT",
  "close": "65000.5",
  "high": "65800.0",
  "low": "64200.0",
  "open": "64500.0",
  "volume": "1234.56",
  "rsi": "62.5",
  "macd": "150.2",
  "macd_signal": "140.1"
}
```

---

## Architecture

```
TradingView Alert
      │
      ▼ HTTP POST /webhook
 server.py (FastAPI)
      │
      ▼ stores candles + indicator values
   store.py (SQLite)
      │
      ▼ reads data on demand
 analyzer.py (Claude API + tool use)
      │
      ▼ interactive conversation
    cli.py (Rich terminal UI)
```
