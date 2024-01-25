from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import find_dotenv, load_dotenv

from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage


ROLE_CLASS_MAP = {"ai": AIMessage, "user": HumanMessage, "system": SystemMessage}
PERSIST_DIR = "./chroma_db"
load_dotenv(find_dotenv())


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Message(BaseModel):
    role: str
    content: str


class Chats(BaseModel):
    chats: List[Message]


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM chain
embedding = OpenAIEmbeddings()
chat = ChatOpenAI(temperature=0)
vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=embedding)
retriever = vectordb.as_retriever()


# Templates
system_template = r"""
    You are a helpful personal assistant who answers to users questions based on the contexts given to you.
    The contexts are personal details for LinTiong Lau (Ivan) which describes his employment history, education,
    skills, projects, etc. If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Context: {context}
    Chat History: {chat_history}"""

human_template = "{question}"

prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(system_template),
        HumanMessagePromptTemplate.from_template(human_template),
    ]
)


def create_messages(conversation):
    return [
        ROLE_CLASS_MAP[message.role](content=message.content)
        for message in conversation
    ]


def format_docs(docs):
    formatted_docs = []
    for doc in docs:
        formatted_doc = "Source: " + doc.metadata["source"]
        formatted_docs.append(formatted_doc)
    return "\n".join(formatted_docs)


@app.post("/openaiservice/{chat_id}")
async def openaiservice(chat_id: str, conversation: Chats):
    query = conversation.chats[-1].content

    docs = retriever.get_relevant_documents(query=query)
    docs = format_docs(docs=docs)

    prompt = system_message_prompt.format(context=docs)
    messages = [prompt] + create_messages(conversation=conversation.chats)

    result = chat(messages)

    return {"id": chat_id, "reply": result.content}
