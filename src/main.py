# Imports Gerais
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from typing import List

# LangChain - Loaders, Splitters, Embeddings, Vector Stores, Chains, Memory
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.tools import tool
from langchain.agents import create_agent

# Busca Híbrida
from langchain_community.retrievers import BM25Retriever

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

app = FastAPI(title="Legal AI RAG")

agent = create_agent(
    model="gemini-1.5-pro", 
    temperature=0, 
    api_key=api_key
)


