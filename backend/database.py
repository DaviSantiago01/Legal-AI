import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import load_env

# Configuração de Logs
logger = logging.getLogger(__name__)
load_env()

# Configuração da URL do Banco de Dados 
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada")

# Inicialização do Engine 
# (Engine é a interface de comunicação com o banco de dados)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    connect_args={"connect_timeout": 5}, # Timeout de conexão em segundos
    pool_size=5,  # Número de conexões mantidas no pool
    max_overflow=10  # Conexões extras permitidas além do pool_size
)

# Criação da Sessão Local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para Models
Base = declarative_base()

def get_db():
    """Dependency para FastAPI fornecer a sessão do banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Cria as tabelas no PostgreSQL."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas PostgreSQL verificadas/criadas com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise
