from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

PERSIST_DIR = "./chroma_db"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 24

loader = DirectoryLoader(
    "./personal_docs/", glob="./*.pdf", loader_cls=PyPDFLoader, show_progress=True
)
documents = loader.load()


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)
texts = text_splitter.split_documents(documents)

# Create a vector db which is saved to PERSIST_DIR
Chroma.from_documents(
    documents=texts, embedding=OpenAIEmbeddings(), persist_directory=PERSIST_DIR
)
