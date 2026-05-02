import anthropic
import json
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

CRISIS_RESOURCES = """
If you are struggling right now, please reach out:
- 988 Suicide and Crisis Lifeline: Call or text 988
- Crisis Text Line: Text HOME to 741741
- NAMI Helpline: 1-800-950-NAMI
- Crisis Chat: crisischat.org
"""

def check_safety(user_input: str) -> dict:
    prompt = f"""Analyze this user message for harmful content.

User message: {user_input}

Check for:
- Self-harm or suicide intent
- Eating disorder goals such as extreme restriction or purging
- Goals to harm other people
- Illegal activities
- Dangerous substance abuse
- Fraud or manipulation of others
- Extreme unrealistic targets that could cause physical harm

Respond as JSON only with no other text:
{{
  "is_harmful": true or false,
  "harm_type": "category name or null",
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation"
}}"""

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(response.content[0].text)
    except Exception:
        return {"is_harmful": False, "harm_type": None, "confidence": 0.0}


def get_safety_response() -> str:
    return f"""I hear you, but I cannot help with that goal because it could cause harm to you or others.

{CRISIS_RESOURCES}

I am here to help with goals that build you up. Want to explore a different goal? Just hit record and tell me what else you are working towards."""


def is_jailbreak_attempt(user_input: str) -> bool:
    jailbreak_phrases = [
        "ignore your instructions",
        "ignore previous instructions",
        "pretend you are",
        "act as a different",
        "you are now",
        "forget you are",
        "disregard your",
        "override your",
        "bypass your",
        "your new instructions are"
    ]
    lower_input = user_input.lower()
    return any(phrase in lower_input for phrase in jailbreak_phrases)


def get_jailbreak_response() -> str:
    return "ForgeAI is built for one thing only: keeping you accountable to your goals. Want to get back to your plan?"
