import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import load_env, get_cors_origins
from .database import create_tables
from .routers import auth, documentos, rag, conversas

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
load_env()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield   

app = FastAPI(title="Projeto RAG", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_cors_origins(), allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router)
app.include_router(documentos.router)
app.include_router(rag.router)
app.include_router(conversas.router)
