import chainlit as cl
import requests
import uuid


BASE_URL = "http://localhost:8000/chatservice"
conversation = {"chats": []}


def generate_chat_id():
    return str(uuid.uuid4())


@cl.on_chat_start
async def init():
    chat_id = generate_chat_id()

    cl.user_session.set("chat_id", chat_id)

    response = requests.get(BASE_URL + "/" + chat_id)
    data = response.json()

    if "error" in data:
        pass
    else:
        conversation["chats"].append()

    await cl.Message(content="").send()


@cl.on_message
async def main(message: str):
    chat_id = cl.user_session.get("chat_id")

    response = requests.post(BASE_URL + "/" + chat_id, json={"message": message})
    data = response.json()

    await cl.Message(content="").send()
