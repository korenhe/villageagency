import requests
from .config import SUPABASE_URL, SUPABASE_KEY
import logging

logger = logging.getLogger(__name__)


HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# basic interface: insert/select
def db_insert(table: str, payload: dict):
    url = f"{SUPABASE_URL}/{table}"

    try:
        r = requests.post(url, headers=HEADERS, json=payload)

        logger.debug(f"INSERT {table} | status={r.status_code}")

        if r.status_code not in (200, 201):
            logger.error(f"INSERT FAILED [{table}]:", r.text)
            return False

        return True

    except Exception as e:
        logger.error(f"INSERT EXCEPTION [{table}]:", e)
        return False


def db_select(table: str, filters: str = "", select: str = ""):
    url = f"{SUPABASE_URL}/{table}?"

    parts = []

    if filters:
        parts.append(filters)

    if select:
        parts.append(f"select={select}")

    url += "&".join(parts)

    try:
        r = requests.get(url, headers=HEADERS)

        logger.debug("SELECT %s | status=%s", table, r.status_code)

        if r.status_code != 200:
            logger.error("SELECT FAILED [%s]: %s", table, r.text)
            return []

        data = r.json()
        return data if isinstance(data, list) else []

    except Exception:
        logger.exception("SELECT EXCEPTION [%s]", table)
        return []


# get group
def get_memory(agent_id):
    data = db_select("living_memory", filters=f"agent_id=eq.{agent_id}", select="text")
    return [x["text"] for x in data]


def get_agent(agent_id):
    data = db_select("living_agents", filters=f"id=eq.{agent_id}", select="name,bio")

    if not data:
        return {"name": "Agent", "bio": ""}

    return data[0]


def get_agent_identity(agent_id: str):
    data = db_select("living_agents", filters=f"id=eq.{agent_id}")

    if not data:
        return {}

    agent = data[0]

    return {
        "id": agent.get("id", ""),
        "name": agent.get("name", "Agent"),
        "bio": agent.get("bio", ""),
        "avatar_url": agent.get("avatar_url", ""),
        "emoji": agent.get("emoji", ""),
    }


def get_all_agents():
    return db_select("living_agents")


def parse_time(ts: str):
    if not ts:
        return 0

    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def get_logs(agent_id, limit=20):
    filters = f"agent_id=eq.{agent_id}" f"&order=created_at.desc" f"&limit={limit}"

    data = db_select("living_log", filters=filters)

    for x in data:
        x["created_at_ts"] = parse_time(x.get("created_at"))

    return data


def get_recent_diaries(agent_id, limit=20):
    filters = f"agent_id=eq.{agent_id}" f"&order=created_at.desc" f"&limit={limit}"

    data = db_select("living_diary", filters=filters)

    for x in data:
        x["created_at_ts"] = parse_time(x.get("created_at"))

    return data


# save group
def save_memory(agent_id, text):
    return db_insert("living_memory", {"agent_id": agent_id, "text": text})


def save_log(agent_id, text):
    return db_insert("living_log", {"agent_id": agent_id, "text": text})


def save_diary(agent_id: str, content: str):
    return db_insert("living_diary", {"agent_id": agent_id, "text": content})
