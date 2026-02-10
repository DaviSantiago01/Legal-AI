import os
import logging
from fastapi import HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from ..utils import get_vector_count, limpar_chroma_db

logger = logging.getLogger(__name__)

def validar_upload_pdf(file, max_bytes: int):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado ou o nome está vazio.")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas PDFs são permitidos.")
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > max_bytes:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 10MB)")

async def salvar_pdf(file, docs_dir: str):
    os.makedirs(docs_dir, exist_ok=True)
    caminho_arquivo = os.path.join(docs_dir, file.filename)
    try:
        content = await file.read()
        with open(caminho_arquivo, "wb") as f:
            f.write(content)
        return caminho_arquivo, content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")

def restaurar_pdf_se_necessario(caminho_pdf: str, documento_registro, docs_dir: str):
    if os.path.exists(caminho_pdf):
        return
    if documento_registro.conteudo_binario:
        os.makedirs(docs_dir, exist_ok=True)
        with open(caminho_pdf, "wb") as f:
            f.write(documento_registro.conteudo_binario)
        return
    raise HTTPException(status_code=404, detail="Arquivo físico não encontrado e sem backup no banco.")

def carregar_paginas_pdf(caminho_pdf: str):
    loader = PyPDFLoader(caminho_pdf)
    paginas_pdf = loader.load()
    if not paginas_pdf or all(not doc.page_content.strip() for doc in paginas_pdf):
        raise HTTPException(
            status_code=400,
            detail="O PDF está vazio ou não contém texto extraível. Se for um documento escaneado, ele precisa de OCR."
        )
    return paginas_pdf

def splitar_paginas(paginas_pdf, chunk_size: int, chunk_overlap: int, separators: list[str]):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators
    )
    blocos = splitter.split_documents(paginas_pdf)
    blocos = [c for c in blocos if c.page_content.strip()]
    if not blocos:
        raise HTTPException(status_code=400, detail="Não foi possível extrair blocos de texto significativos deste documento.")
    return blocos

def criar_ou_validar_base(embeddings, chroma_dir: str):
    try:
        base_vetorial = Chroma(persist_directory=chroma_dir, embedding_function=embeddings)
        total = get_vector_count(base_vetorial)
        return base_vetorial, total
    except Exception as e:
        if "dimension" in str(e).lower():
            logger.warning(f"⚠️ Erro de dimensão detectado. Resetando índice: {e}")
            limpar_chroma_db()
            raise
        logger.error(f"Erro inesperado no Chroma: {e}")
        raise

def persistir_blocos(blocos, embeddings, chroma_dir: str):
    try:
        base_vetorial = Chroma.from_documents(
            documents=blocos,
            embedding=embeddings,
            persist_directory=chroma_dir
        )
    except Exception as e:
        if "dimension" in str(e).lower():
            logger.warning("⚠️ Erro de dimensão ao salvar. Limpando e tentando novamente...")
            limpar_chroma_db()
            base_vetorial = Chroma.from_documents(
                documents=blocos,
                embedding=embeddings,
                persist_directory=chroma_dir
            )
        else:
            raise e
    base_vetorial.persist()
    return base_vetorial
