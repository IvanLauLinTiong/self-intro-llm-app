import chainlit as cl
import requests
import uuid


BASE_URL = "http://chatservice:80/chatservice"


def generate_chat_id():
    return str(uuid.uuid4())


@cl.on_chat_start
async def init():
    chat_id = generate_chat_id()

    response = requests.get(f"{BASE_URL}/{chat_id}")
    response.raise_for_status()
    response = response.json()

    if "greeting_msg" in response:
        await cl.Message(content=response["greeting_msg"]).send()

    cl.user_session.set("chat_id", chat_id)


@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()

    chat_id = cl.user_session.get("chat_id")
    payload = {"message": message.content}

    response = requests.post(f"{BASE_URL}/{chat_id}", json=payload)
    response.raise_for_status()
    msg.content = response.json()["answer"]

    await msg.update()
