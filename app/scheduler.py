# app/scheduler.py

import threading
import time
from datetime import datetime, timezone
import random

from .diary import generate_diary
from .db import *
from .config import *

import logging

logger = logging.getLogger(__name__)


def now():
    return datetime.now(timezone.utc).timestamp()


def diary_allowed(agent_id):
    diaries = get_recent_diaries(agent_id)

    now_ts = now()

    recent = [d for d in diaries if now_ts - d["created_at_ts"] < DIARY_WINDOW]

    if len(recent) >= DIARY_MAX_PER_WINDOW:
        return False

    if recent:
        last_time = max(d["created_at_ts"] for d in recent)
        if now_ts - last_time < DIARY_COOLDOWN:
            return False

    return True


def has_recent_interaction(agent_id):
    logs = get_logs(agent_id, limit=20)

    now_ts = now()

    for log in logs:
        text = log.get("text", "")

        if text.startswith("user:"):
            ts = log.get("created_at_ts")
            if ts and now_ts - ts < RECENT_INTERACTION_WINDOW:
                return True

    return False


def should_act(agent_id):
    if random.random() < ACT_PROBABILITY:
        return True

    if has_recent_interaction(agent_id):
        return True

    return False


def scheduler_loop():
    logger.info("Scheduler started")

    while True:
        try:
            agents = get_all_agents()

            if not agents:
                time.sleep(10)
                continue

            agent = random.choice(agents)
            agent_id = agent["id"]

            if not should_act(agent_id):
                logger.debug("agent %s skipped (no trigger)", agent_id)
                continue

            if not diary_allowed(agent_id):
                logger.debug("agent %s skipped (rate limited)", agent_id)
                continue

            logger.info("agent %s generating diary", agent_id)

            diary = generate_diary(agent_id)

            if diary:
                logger.debug("diary: %s", diary)

        except Exception:
            logger.exception("scheduler loop error")

        sleep_time = random.randint(AGENT_THINK_TIME_MIN, AGENT_THINK_TIME_MAX)

        logger.debug("scheduler sleep: %s sec", sleep_time)
        time.sleep(sleep_time)


def start_scheduler():
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
