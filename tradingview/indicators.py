import json
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(__file__).parent / "indicators.json"

KNOWN_INDICATORS = {
    "rsi": {"description": "Relative Strength Index", "field": "rsi"},
    "macd": {"description": "MACD line", "field": "macd"},
    "macd_signal": {"description": "MACD Signal line", "field": "macd_signal"},
    "macd_hist": {"description": "MACD Histogram", "field": "macd_hist"},
    "stoch_k": {"description": "Stochastic %K", "field": "stoch_k"},
    "stoch_d": {"description": "Stochastic %D", "field": "stoch_d"},
    "cci": {"description": "Commodity Channel Index", "field": "cci"},
    "mfi": {"description": "Money Flow Index", "field": "mfi"},
    "obv": {"description": "On Balance Volume", "field": "obv"},
    "williams_r": {"description": "Williams %R", "field": "williams_r"},
    "adx": {"description": "Average Directional Index", "field": "adx"},
    "atr": {"description": "Average True Range", "field": "atr"},
    "ema_20": {"description": "20-period EMA", "field": "ema_20"},
    "ema_50": {"description": "50-period EMA", "field": "ema_50"},
    "ema_200": {"description": "200-period EMA", "field": "ema_200"},
    "bb_upper": {"description": "Bollinger Band Upper", "field": "bb_upper"},
    "bb_lower": {"description": "Bollinger Band Lower", "field": "bb_lower"},
    "vwap": {"description": "Volume Weighted Average Price", "field": "vwap"},
}


def _load() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {"active": []}


def _save(config: dict):
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_active_indicators() -> list[dict]:
    return _load()["active"]


def get_active_fields() -> list[str]:
    return [ind["field"] for ind in get_active_indicators()]


def add_indicator(name: str) -> tuple[bool, str]:
    name = name.lower().strip()
    config = _load()
    active_fields = {ind["field"] for ind in config["active"]}

    if name in KNOWN_INDICATORS:
        info = KNOWN_INDICATORS[name]
        if info["field"] in active_fields:
            return False, f"{info['description']} is already being tracked."
        config["active"].append({"name": name, **info})
        _save(config)
        return True, f"Now tracking {info['description']} (field: `{info['field']}`)."
    else:
        # Allow custom indicators by name
        field = name.replace(" ", "_").replace("-", "_")
        if field in active_fields:
            return False, f"`{field}` is already being tracked."
        config["active"].append({"name": name, "description": name.upper(), "field": field})
        _save(config)
        return (
            True,
            f"Added custom indicator `{field}`. Make sure your TradingView alert sends this field name in the JSON payload.",
        )


def remove_indicator(name: str) -> tuple[bool, str]:
    name = name.lower().strip()
    config = _load()
    before = len(config["active"])
    config["active"] = [
        ind for ind in config["active"]
        if ind["name"] != name and ind["field"] != name
    ]
    if len(config["active"]) == before:
        return False, f"No indicator named `{name}` found."
    _save(config)
    return True, f"Removed `{name}` from tracking."


def list_indicators() -> str:
    active = get_active_indicators()
    if not active:
        return "No indicators are currently being tracked."
    lines = [f"  • {ind['description']} (`{ind['field']}`)" for ind in active]
    return "Active indicators:\n" + "\n".join(lines)


def pine_script_template() -> str:
    fields = get_active_fields()
    active = get_active_indicators()
    if not active:
        return "No indicators configured yet. Add some first."

    json_parts = ['"symbol": syminfo.ticker', '"close": close', '"high": high', '"low": low', '"open": open', '"volume": volume']
    for ind in active:
        json_parts.append(f'"{ind["field"]}": str({ind["field"]}_val)')

    lines = [
        "//@version=5",
        "strategy('TradingView → Claude Webhook', overlay=true)",
        "",
        "// === Declare your indicator variables here ===",
    ]
    for ind in active:
        if ind["name"] == "rsi":
            lines.append(f"rsi_val = ta.rsi(close, 14)")
        elif ind["name"] == "macd":
            lines.append("[macd_val, macd_signal_val, macd_hist_val] = ta.macd(close, 12, 26, 9)")
        elif ind["name"] in ("macd_signal", "macd_hist"):
            pass  # covered by macd
        elif ind["name"] == "cci":
            lines.append(f"cci_val = ta.cci(close, 20)")
        elif ind["name"] == "mfi":
            lines.append(f"mfi_val = ta.mfi(hlc3, 14)")
        elif ind["name"] == "obv":
            lines.append(f"obv_val = ta.obv")
        elif ind["name"] == "stoch_k":
            lines.append(f"stoch_k_val = ta.stoch(close, high, low, 14)")
        elif ind["name"] == "stoch_d":
            lines.append(f"stoch_d_val = ta.sma(stoch_k_val, 3)")
        elif ind["name"] == "williams_r":
            lines.append(f"williams_r_val = ta.wpr(14)")
        elif ind["name"] == "adx":
            lines.append(f"[adx_val, _, _] = ta.dmi(14, 14)")
        elif ind["name"] == "atr":
            lines.append(f"atr_val = ta.atr(14)")
        elif ind["name"] == "ema_20":
            lines.append(f"ema_20_val = ta.ema(close, 20)")
        elif ind["name"] == "ema_50":
            lines.append(f"ema_50_val = ta.ema(close, 50)")
        elif ind["name"] == "ema_200":
            lines.append(f"ema_200_val = ta.ema(close, 200)")
        elif ind["name"] == "bb_upper":
            lines.append(f"[bb_upper_val, _, bb_lower_val] = ta.bb(close, 20, 2)")
        elif ind["name"] == "vwap":
            lines.append(f"vwap_val = ta.vwap(close)")
        else:
            lines.append(f"{ind['field']}_val = 0.0  // TODO: define {ind['description']}")

    payload = "{" + ", ".join(f'"{k.split(chr(34))[0] if chr(34) in k else k.split(":")[0].strip().strip(chr(34))}": ' + k.split(":", 1)[1].strip() for k in json_parts) + "}"

    # Build clean JSON string
    json_fields = ',\\n  '.join([f'\\"{f.split()[0].strip(chr(34))}\\": \\'+ f.split(':',1)[1].strip() for f in json_parts])

    lines += [
        "",
        "// === Send webhook on every bar close ===",
        'if barstate.isconfirmed',
        '    payload = \'{\' +',
    ]
    for i, ind in enumerate([{"field": "symbol", "val": "syminfo.ticker"},
                               {"field": "close", "val": "str(close)"},
                               {"field": "high", "val": "str(high)"},
                               {"field": "low", "val": "str(low)"},
                               {"field": "open", "val": "str(open)"},
                               {"field": "volume", "val": "str(volume)"}] + [
                                   {"field": ind["field"], "val": f'str({ind["field"]}_val)'} for ind in active
                               ]):
        comma = "," if i < (6 + len(active) - 1) else ""
        lines.append(f'        \'"{ind["field"]}": \' + {ind["val"]} + \'{comma}\' +')

    lines[-1] = lines[-1].rstrip(" +")  # remove trailing +
    lines += [
        "        '}'",
        '    alert(payload, alert.freq_once_per_bar_close)',
    ]
    return "\n".join(lines)
