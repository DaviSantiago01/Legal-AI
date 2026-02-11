import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import load_env, get_cors_origins
from .database import create_tables
from .routers import auth_router, documentos_router, rag_router, conversas_router

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
load_env()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # As tabelas agora são gerenciadas via Alembic migrations
    yield   

app = FastAPI(title="Projeto RAG", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_cors_origins(), allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
app.include_router(documentos_router)
app.include_router(rag_router)
app.include_router(conversas_router)
