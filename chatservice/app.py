from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import find_dotenv, load_dotenv

from langchain.chains import ConversationalRetrievalChain
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


PERSIST_DIR = "./chroma_db"
GREETING_MSESSAGE = """Hello World!👋I'm personal chatbot assistant for LinTiong Lau. Feel free to \
ask me any questions about his background and experience.🤖"""


load_dotenv(find_dotenv())
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Message(BaseModel):
    message: str


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tracked LLM chains
llm_chains = {}


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


def generate_llm_chain(chat_id: str) -> ConversationalRetrievalChain:
    embedding = OpenAIEmbeddings()
    llm = ChatOpenAI(temperature=0)
    vectordb = Chroma(persist_directory=PERSIST_DIR, embedding_function=embedding)
    retriever = vectordb.as_retriever(search_kwargs={"k": 2})

    message_history = RedisChatMessageHistory(
        session_id=chat_id,
        url="redis://redis:6379/0",
    )
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        output_key="answer",
        chat_memory=message_history,
        return_messages=True,
    )

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        chain_type="stuff",
        combine_docs_chain_kwargs={"prompt": prompt},
        retriever=retriever,
        memory=memory,
    )

    return chain


@app.get("/health")
async def health():
    return {"status": "OK"}


@app.get("/chatservice/{chat_id}")
async def chatservice(chat_id: str):
    if chat_id in llm_chains:
        return {"chat_id": chat_id}

    chain = generate_llm_chain(chat_id)
    llm_chains[chat_id] = chain

    return {"chat_id": chat_id, "greeting_msg": GREETING_MSESSAGE}


@app.post("/chatservice/{chat_id}")
async def chatservice(chat_id: str, message: Message):

    chain = llm_chains[chat_id]

    res = await chain.ainvoke(message.message)  # maybe cadd asynlangchaincallback ?

    answer = res["answer"]

    return {"chat_id": chat_id, "answer": answer}
