# Imports Gerais
import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List

# LangChain - Loaders, Splitters, Embeddings, Vector Stores
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

@app.post("/carregar/")
async def carregar_documentos(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas PDFs são permitidos.")
    
    os.makedirs("data/documents/", exist_ok=True)

    caminho_arquivo = f"data/documents/{file.filename}"

    try:
        with open(caminho_arquivo, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")

    return {
        "message": "Arquivo carregado com sucesso.",
        "filename": file.filename,
        "path": caminho_arquivo
    }
