from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ChatMessageHistory, ConversationBufferMemory
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from pathlib import Path
import chainlit as cl

load_dotenv()


@cl.on_chat_start
async def on_chat_start():
    msg = cl.Message(content="")
    await msg.send()

    system_template = r"""
    You are a helpful personal assistant who answers to users questions based on the contexts given to you.
    The contexts are personal details for LinTiong Lau (Ivan) which describes his employment history, education,
    skills, projects, etc. If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Context: {context}
    Chat History: {chat_history}
    Your Response:"""

    human_template = "{question}"

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template),
        ]
    )

    persist_directory = "./chroma_db"
    embedding = OpenAIEmbeddings()
    if Path(persist_directory).exists():
        print("Loading existing db")
        # Load existing chroma db
        vectordb = Chroma(
            persist_directory=persist_directory, embedding_function=embedding
        )
    else:
        print("Creating new db...")
        # Load and Process document
        loader = DirectoryLoader(
            "./personal_docs/", glob="./*.pdf", loader_cls=PyPDFLoader
        )
        documents = loader.load()

        # Create persistent chroma DB if not exist
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=24)
        texts = text_splitter.split_documents(documents)
        vectordb = Chroma.from_documents(
            documents=texts, embedding=embedding, persist_directory=persist_directory
        )

    # Create a chain that uses the Chroma vector store
    message_history = ChatMessageHistory()
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
        retriever=vectordb.as_retriever(search_kwargs={"k": 2}),
        memory=memory,
        # return_source_documents=True,
    )

    msg.content = """Hello World!👋I'm personal chatbot assistant for LinTiong Lau. Feel free to ask me any questions
    about his background and experience.🤖"""

    await msg.update()

    cl.user_session.set("chain", chain)


@cl.on_message
async def on_message(message: cl.Message):
    msg = cl.Message(content="")
    await msg.send()

    chain = cl.user_session.get("chain")
    cb = cl.AsyncLangchainCallbackHandler()

    response = await chain.ainvoke(message.content, callbacks=[cb])

    answer = response["answer"]
    await cl.Message(content=answer).send()
