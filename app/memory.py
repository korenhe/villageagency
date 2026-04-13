import json
from .llm import chat
import logging

logger = logging.getLogger(__name__)


def extract_memory(message: str):
    prompt = f"""
Extract personal facts worth remembering from this message.

RULES:
- Only extract stable facts (identity, preferences, relationships)
- Ignore small talk
- If nothing useful, return empty list

Return ONLY valid JSON array of strings.

Message:
{message}
"""

    raw = chat(prompt, message="")

    logger.debug("raw memory output:", raw)

    import json

    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except:
        pass

    return []
