from fastapi import FastAPI
from pydantic import BaseModel
from .agent import handle_message
from .diary import generate_diary
from .scheduler import start_scheduler
import logging
from app.config import ENABLE_SCHEDULER

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
)

app = FastAPI()


class MessageReq(BaseModel):
    agent_id: str
    user_type: str
    message: str


@app.post("/message")
def message(req: MessageReq):
    reply = handle_message(req.agent_id, req.user_type, req.message)
    return {"reply": reply}


@app.post("/diary/{agent_id}")
def diary(agent_id: str):
    d = generate_diary(agent_id)
    return {"diary": d}


@app.on_event("startup")
def startup_event():
    if ENABLE_SCHEDULER:
        start_scheduler()
