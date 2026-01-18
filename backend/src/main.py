# Imports Gerais
import os
import shutil
import logging
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import DOCS_DIR, CHROMA_DIR
from contextlib import asynccontextmanager

# LangChain e IA
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage

# Database
from sqlalchemy.orm import Session
from .database import get_db, create_tables
from .models import Documento, Conversa, Mensagem
from .schemas import DocumentoResponse, QueryRequest, QueryResponse

# Deixamos o formato simples para o terminal ficar limpo
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Setup de Ambiente 
in_docker = os.path.exists("/.dockerenv")
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=not in_docker)

# Inicialização dos Modelos de IA
embeddings = GoogleGenerativeAIEmbeddings(model="text-embedding-004")
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# --- Funções Auxiliares ---
def _get_vector_count(vector_store):
    """Retorna a contagem de documentos no Vector Store de forma segura."""
    try:
        # Tenta usar a API interna do Chroma (mais rápida)
        return vector_store._collection.count()
    except Exception as e:
        # Se for erro de dimensão, levanta para ser tratado pelo chamador
        if "dimension" in str(e).lower():
            raise
        try:
            # Fallback para busca vazia (API pública)
            return len(vector_store.get()['ids'])
        except Exception:
            return 0

def _limpar_chroma():
    """Remove o diretório do ChromaDB se houver erro de compatibilidade."""
    os.makedirs(CHROMA_DIR, exist_ok=True)
    logger.warning(f"🧹 Limpando conteúdo do Chroma: {CHROMA_DIR}")
    for nome in os.listdir(CHROMA_DIR):
        caminho = os.path.join(CHROMA_DIR, nome)
        if os.path.isdir(caminho):
            shutil.rmtree(caminho)
        else:
            os.remove(caminho)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield   

app = FastAPI(title="Legal AI RAG", lifespan=lifespan)

# CORS
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/carregar/", response_model=DocumentoResponse)
async def carregar_documentos(file: UploadFile, db: Session = Depends(get_db)):
    """Recebe e salva PDF no servidor"""

    # Valida se o nome existe
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nenhum arquivo foi enviado ou o nome está vazio.")

    # Valida se é um PDF (case-insensitive)
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Apenas PDFs são permitidos.")
    
    # Verifica o tamanho do arquivo
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 10MB)")

    os.makedirs(DOCS_DIR, exist_ok=True)
    caminho_arquivo = os.path.join(DOCS_DIR, file.filename)

    try:
        content = await file.read()
        with open(caminho_arquivo, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar: {str(e)}")

    documento_existente = db.query(Documento).filter(Documento.nome_arquivo == file.filename).first()
    if documento_existente:
        documento_existente.conteudo_binario = content
        documento_existente.preprocessado = False
        documento_existente.numero_chuncks = 0
        db.commit()
        db.refresh(documento_existente)
        return documento_existente

    doc = Documento(
        nome_arquivo=file.filename,
        nome_original=file.filename,
        caminho_arquivo=caminho_arquivo,
        conteudo_binario=content
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

# API: Processar e indexar PDF
@app.post("/processar/{filename}")
async def processar_documento(filename: str, db: Session = Depends(get_db)):
    """Carrega PDF, faz chunking e salva no vector store"""

    caminho_arquivo = os.path.join(DOCS_DIR, filename)
    
    # Busca o documento no banco de dados para garantir que temos o binário
    documento_db = db.query(Documento).filter(Documento.nome_arquivo == filename).first()
    if not documento_db:
        raise HTTPException(status_code=404, detail="Documento não registrado no banco de dados.")

    # Se já estiver preprocessado, tenta verificar o Chroma
    if documento_db.preprocessado:
        try:
            vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
            if _get_vector_count(vectordb) > 0:
                return {
                    "message": "Documento já processado e verificado.",
                    "filename": filename,
                    "num_chunks": documento_db.numero_chuncks,
                }
        except Exception as e:
            if "dimension" in str(e).lower():
                logger.warning(f"⚠️ Erro de dimensão detectado. Resetando índice: {e}")
                _limpar_chroma()
            else:
                logger.error(f"Erro inesperado no Chroma: {e}")

    # Se o arquivo não existir no disco (ex: reiniciou o container), restaura do banco
    if not os.path.exists(caminho_arquivo):
        if documento_db.conteudo_binario:
            os.makedirs(DOCS_DIR, exist_ok=True)
            with open(caminho_arquivo, "wb") as f:
                f.write(documento_db.conteudo_binario)
        else:
            raise HTTPException(status_code=404, detail="Arquivo físico não encontrado e sem backup no banco.")

    try:
        # Carregar PDF
        loader = PyPDFLoader(caminho_arquivo)
        documento = loader.load()

        # Dividir em chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(documento)

        # Salvar no ChromaDB
        try:
            vectordb = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=CHROMA_DIR
            )
        except Exception as e:
            if "dimension" in str(e).lower():
                logger.warning("⚠️ Erro de dimensão ao salvar. Limpando e tentando novamente...")
                _limpar_chroma()
                vectordb = Chroma.from_documents(
                    documents=chunks,
                    embedding=embeddings,
                    persist_directory=CHROMA_DIR
                )
            else:
                raise e

        # Força persistência (necessário em algumas versões do Chroma/Docker)
        vectordb.persist() 
        
        # Atualiza status no banco
        documento_db.preprocessado = True
        documento_db.numero_chuncks = len(chunks)
        db.commit()

        return {
            "message": "Documento processado e armazenado com sucesso.",
            "filename": filename,
            "num_chunks": len(chunks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

# API: Fazer pergunta ao RAG
@app.post("/pergunta/", response_model=QueryResponse)
async def responder_pergunta(query: QueryRequest, db: Session = Depends(get_db)):
    """Busca documentos relevantes e gera resposta com LLM"""
    try:
        # Carregar vector store
        try:
            vectordb = Chroma(
                persist_directory=CHROMA_DIR,
                embedding_function=embeddings
            )
            # Tenta um count para validar dimensões
            _get_vector_count(vectordb)
        except Exception as e:
            if "dimension" in str(e).lower():
                logger.error(f"❌ Erro de dimensão no Chroma: {e}")
                _limpar_chroma()
                raise HTTPException(
                    status_code=400, 
                    detail="A base de dados era incompatível e foi resetada. Por favor, processe o documento novamente."
                )
            logger.error(f"Erro ao carregar ChromaDB: {e}")
            raise HTTPException(status_code=500, detail="Erro ao carregar base de dados. Re-processe o documento.")

        # Validar se há documentos na base
        count = _get_vector_count(vectordb)

        if count == 0:
            raise HTTPException(status_code=404, detail="Nenhum documento indexado. Por favor, processe um documento primeiro.")
        
        # Buscar documentos similares
        try:
            docs = vectordb.similarity_search(query.pergunta, k=3)
        except Exception as e:
            if "dimension" in str(e).lower():
                _limpar_chroma()
                raise HTTPException(
                    status_code=400, 
                    detail="Erro de compatibilidade detectado. A base foi limpa. Processe o documento novamente."
                )
            raise e

        # Montar contexto
        context_parts = []
        for doc in docs:
            fonte = doc.metadata.get('source', 'N/A')
            context_parts.append(f"Fonte: {fonte}\n{doc.page_content}")
        context = "\n\n---\n\n".join(context_parts)

        # Criar prompt
        messages = [
            SystemMessage(content="Você é um assistente jurídico que responde com base APENAS no contexto fornecido. Cite as fontes."),
            HumanMessage(content=f"Contexto:\n{context}\n\nPergunta: {query.pergunta}")
        ]   
             
        #  Gerar resposta
        resposta = llm.invoke(messages)

        conversa = Conversa(titulo=query.pergunta[:50])
        db.add(conversa)
        db.commit()

        msg_user = Mensagem(
            conversa_id=conversa.id,
            conteudo=query.pergunta,
            remetente="user"
        )
        msg_ia = Mensagem(
            conversa_id=conversa.id,
            conteudo=resposta.content,
            remetente="ia"
        )
        db.add(msg_user)
        db.add(msg_ia)      
        db.commit()

        return {
            "resposta": resposta.content,
            "sources": [doc.metadata for doc in docs],
            "num_docs": len(docs)
        }
    except HTTPException:
        # Re-levanta erros do FastAPI para evitar que virem 500
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
    
@app.get("/documentos/")
async def listar_documentos():
    """Lista os documentos carregados no servidor"""
    try:
        # Verifica o diretório de documentos, se nao existir, retorna lista vazia
        if not os.path.exists(DOCS_DIR):
            return {
                "documentos": [],
                "total": 0
            }

        # Lista os arquivos PDF no diretório, list comprehension para filtrar apenas PDFs
        documentos = [f for f in os.listdir(DOCS_DIR) if f.endswith('.pdf')] 

        return {
            "documentos": documentos,
            "total": len(documentos)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro {str(e)}")
