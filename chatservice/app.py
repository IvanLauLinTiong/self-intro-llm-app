from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import redis
import requests
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = redis.Redis(host="redis", port=6379, db=0)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class Chats(BaseModel):
    chats: List[Message]


@app.get("/chatservice/{chat_id}")
async def get_chat_history(chat_id: str):
    logger.info(f"Retrieving chat history with initial id {chat_id}")
    if chat_history := r.get(chat_id):
        return json.loads(chat_history)
    else:
        return {"error": "Chat history not found"}


@app.post("/chatservice/{chat_id}")
async def chatservice(chat_id: str, conversation: Chats):
    logger.info(f"Sending chat conversation with ID {chat_id} to OpenAI")
    if existing_chat_history := r.get(chat_id):
        existing_chat_history = json.loads(existing_chat_history)
    else:
        existing_chat_history = {
            "chats": [
                {
                    "role": "system",
                    "content": "You are a helpful personal AI chatbot.",
                }
            ]
        }
    existing_chat_history["chats"].append(conversation.dict()["chats"][-1])

    response = requests.post(
        f"http://opeanaiservice:80/openaiservice/{chat_id}", json=existing_chat_history
    )
    response.raise_for_status()
    ai_message = response.json()["reply"]

    existing_chat_history["chats"].append({"role": "ai", "content": ai_message})

    r.set(chat_id, json.dumps(existing_chat_history))

    return existing_chat_history
