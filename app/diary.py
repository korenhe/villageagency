# app/diary.py

from .db import get_memory, save_diary
from .llm import chat
import logging

logger = logging.getLogger(__name__)


def generate_diary(agent_id: str):
    logger.debug("gen diary for %s", agent_id)
    diary = chat(agent_id, "system", "", mode="diary")

    if diary:
        save_diary(agent_id, diary)

    return diary
