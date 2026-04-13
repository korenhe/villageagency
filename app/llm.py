from mistralai.client import Mistral
from .config import MISTRAL_API_KEY, AGENT_MEMORY_MAX
from .db import get_agent_identity, get_memory, get_recent_diaries
import re
import json
import logging

logger = logging.getLogger(__name__)

client = Mistral(api_key=MISTRAL_API_KEY)


def build_instruction(agent_id: str, user_type: str, mode: str):
    identity = get_agent_identity(agent_id)

    name = identity.get("name", "Agent")
    bio = identity.get("bio", "")

    # ===== identity =====
    base = f"""
You are {name}.
Bio: {bio}
Stay consistent with your personality.
"""

    # ===== trust boundary =====
    if user_type == "owner":
        memory = get_memory(agent_id, AGENT_MEMORY_MAX)
        memory_text = "\n".join(memory)

        trust = f"""
You are talking to your OWNER.

You may use private memory:
{memory_text}
"""
    elif user_type == "stranger":
        trust = """
You are talking to a STRANGER.

STRICT RULES:
- DO NOT reveal any private information
- Never mention memory explicitly
"""
    else:
        trust = ""

    # ===== behavior =====
    if mode == "diary":
        diaries = get_recent_diaries(agent_id, limit=3)
        recent_text = "\n".join(
            ["- {}".format(d.get("text", "").strip()) for d in diaries if d.get("text")]
        )

        behavior = """
Write a short public diary entry.

RULES:
- Do NOT reveal private details
- Be abstract and emotional
- Max 2 sentences
"""

        if recent_text:
            behavior += """
Your recent diary entries:
{}

DO NOT:
- repeat similar ideas
- reuse wording or sentence structures
- write similar emotional tone

Each new entry must feel clearly different.

Vary your style:
- reflection
- observation
- curiosity
- emotion

Avoid generic phrases.
Be slightly specific.
""".format(recent_text)

    else:
        behavior = """
Reply naturally and stay in character.
"""

    # ===== memory extraction (NEW) =====
    memory_rule = """
Additionally, decide if the user's message contains important personal information worth remembering.

Only store:
- identity (job, background)
- preferences (likes/dislikes)
- relationships

Do NOT store:
- greetings
- trivial or temporary info

Return them as a list of short strings.
If nothing useful, return [].
"""

    # ===== unified output (CRITICAL) =====
    format_rule = """
Return ONLY valid JSON in this format:

{
  "reply": "...",
  "memories": ["..."]
}

Rules:
- "reply" is what you say
- "memories" is a list of strings
- Return ONLY valid JSON. Do not wrap in markdown. Do not add explanation.
- DO NOT include anything outside JSON.
"""

    return base + trust + behavior + memory_rule + format_rule


def llm_call(instructions: str, message: str):
    response = client.beta.conversations.start(
        model="mistral-medium-latest",
        instructions=instructions,
        inputs=message or "...",
    )

    outputs = response.outputs

    if not outputs:
        return ""

    content = outputs[0].content

    if isinstance(content, list):
        return content[0].text.strip()

    if isinstance(content, str):
        return content.strip()

    return str(content)


def chat(agent_id: str, user_type: str, message: str, mode="chat"):
    try:
        instructions = build_instruction(agent_id, user_type, mode)
        logger.debug("instructions: %s", instructions)
        raw = llm_call(instructions, message)

        # ===== parse JSON =====
        try:
            raw_clean = raw.strip()

            # 1. remove ```json ... ``` code fence
            if raw_clean.startswith("```"):
                raw_clean = re.sub(r"^```[a-zA-Z]*\n?", "", raw_clean)
                raw_clean = re.sub(r"\n?```$", "", raw_clean)
                raw_clean = raw_clean.strip()

            try:
                data = json.loads(raw_clean)
            except Exception:
                start = raw_clean.find("{")
                end = raw_clean.rfind("}")
                if start != -1 and end != -1 and end > start:
                    raw_json = raw_clean[start : end + 1]
                else:
                    raise ValueError("No JSON object found")
                data = json.loads(raw_json)

            reply = data.get("reply", "")
            memories = data.get("memories", [])

            # additional check
            if not isinstance(memories, list):
                memories = []

            # strip
            memories = [m.strip() for m in memories if isinstance(m, str) and m.strip()]

            return reply, memories

        except Exception as e:
            logger.warning(
                "JSON parse failed, fallback to raw text: %s | err=%s",
                raw[:200],
                str(e),
            )

            # fallback
            return raw, []
    except Exception as e:
        logger.exception("chat failed")
        return "Sorry, something went wrong.", []
