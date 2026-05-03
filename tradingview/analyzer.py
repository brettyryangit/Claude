"""
Claude-powered analyzer. Uses tool use so Claude can fetch data itself
and produce a divergence analysis with full context.
"""

import asyncio
import json
import os
from typing import Any

import anthropic

import store
import indicators as ind_manager

MODEL = "claude-sonnet-4-6"

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

TOOLS: list[dict] = [
    {
        "name": "get_price_and_indicator_data",
        "description": (
            "Fetch recent OHLCV candle data and all indicator values for a given symbol. "
            "Returns a list of candles ordered oldest to newest."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Trading symbol e.g. BTCUSDT"},
                "limit": {
                    "type": "integer",
                    "description": "Number of recent candles to fetch (default 100)",
                    "default": 100,
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "list_tracked_indicators",
        "description": "Returns the list of indicators currently configured for tracking.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_available_symbols",
        "description": "Returns the symbols that have data stored in the database.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

SYSTEM_PROMPT = """You are a professional technical analyst specializing in divergence detection and momentum analysis.

When analyzing data:
1. **Regular Bullish Divergence**: Price makes a lower low, but the indicator makes a higher low → potential reversal up.
2. **Regular Bearish Divergence**: Price makes a higher high, but the indicator makes a lower high → potential reversal down.
3. **Hidden Bullish Divergence**: Price makes a higher low, indicator makes a lower low → continuation of uptrend.
4. **Hidden Bearish Divergence**: Price makes a lower high, indicator makes a higher high → continuation of downtrend.

When identifying divergences:
- Look at the last 2-5 swing highs/lows for confirmation.
- State which candles (by index or timestamp) form the divergence pattern.
- Rate conviction: Low / Medium / High based on how clean the pattern is.
- Note if divergence aligns across multiple indicators (confluence).
- Flag if the indicator is in overbought/oversold territory (RSI > 70 / < 30, etc.).

Always be specific: quote the actual price and indicator values that form the pattern."""


async def _run_tool(name: str, inputs: dict) -> Any:
    if name == "get_price_and_indicator_data":
        symbol = inputs["symbol"].upper()
        limit = inputs.get("limit", 100)
        candles = await store.get_candles(symbol, limit=limit)
        return candles
    elif name == "list_tracked_indicators":
        return ind_manager.get_active_indicators()
    elif name == "list_available_symbols":
        return await store.get_symbols()
    return {"error": f"Unknown tool: {name}"}


async def analyze(user_message: str, conversation_history: list[dict]) -> str:
    """
    Send a message to Claude with the full conversation history.
    Claude may call tools to fetch data before responding.
    Returns Claude's final text response.
    """
    messages = conversation_history + [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Extract text from response
            text_parts = [block.text for block in response.content if hasattr(block, "text")]
            return "\n".join(text_parts)

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await _run_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result, default=str),
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return "Analysis complete."
