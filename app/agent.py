from .db import get_memory, save_log, save_memory, get_agent
from .llm import chat
from .memory import extract_memory

import logging

logger = logging.getLogger(__name__)


def filter_memory(memory, message):
    keywords = message.lower().split()
    return [m for m in memory if any(k in m.lower() for k in keywords)]


def handle_message(agent_id: str, user_type: str, message: str):
    # llm
    reply, memories = chat(agent_id, user_type, message)

    # log
    save_log(agent_id, f"user: {message}")
    save_log(agent_id, f"agent: {reply}")

    # memory extraction (only owner)
    if user_type == "owner":
        logger.info("memories extracted: %s", memories)
        for m in memories:
            save_memory(agent_id, m)

    return reply
