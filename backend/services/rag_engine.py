from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from ..config import load_env

load_env()

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
CHUNK_SEPARATORS = ["\n\n", "\n", " ", ""]

embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
