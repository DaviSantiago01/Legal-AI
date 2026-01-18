import os
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
 from sqlalchemy.exc import OperationalError

# Configuração de Logs
logger = logging.getLogger(__name__)

# Caminho para o .env (Legal_AI/.env)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
dotenv_path = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=dotenv_path, encoding="utf-8")

DATABASE_URL = os.getenv("DATABASE_URL")    

in_docker = os.path.exists("/.dockerenv")

if not DATABASE_URL:
    sqlite_path = os.path.join(BASE_DIR, "backend", "data", "legal_ai.db")
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    DATABASE_URL = f"sqlite:///{sqlite_path}"
elif not in_docker and "@postgres:5432" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("@postgres:5432", "@localhost:5433")

# Argumentos para o engine (ex: pool_pre_ping para evitar conexões perdidas)
def _build_engine(url: str):
    engine_args = {"pool_pre_ping": True}
    if url.startswith("postgresql"):
        engine_args["connect_args"] = {"connect_timeout": 5}
    elif url.startswith("sqlite"):
        engine_args["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **engine_args, echo=False)

engine = _build_engine(DATABASE_URL)

if not in_docker and DATABASE_URL.startswith("postgresql"):
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except OperationalError:
        sqlite_path = os.path.join(BASE_DIR, "backend", "data", "legal_ai.db")
        os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
        DATABASE_URL = f"sqlite:///{sqlite_path}"
        engine = _build_engine(DATABASE_URL)

# Criar sessão com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para os modelos ORM
Base = declarative_base()

# Dependency - Função helper para FastAPI
def get_db():
    """
    Cria uma sessão do banco para cada requisição.
    Fecha automaticamente quando terminar.
    """
    db = SessionLocal()
    try:
        yield db  # Entrega a sessão
    finally:
        db.close()  # Fecha quando terminar

# Função para criar todas as tabelas
def create_tables():
    """
    Cria todas as tabelas definidas nos models.
    Roda apenas uma vez no início.
    """
    # Import local para evitar importação circular
    from . import models
    
    Base.metadata.create_all(bind=engine)
    
    if engine.dialect.name == "postgresql":
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE documentos ADD COLUMN IF NOT EXISTS conteudo_binario BYTEA"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Nota: Coluna conteudo_binario já existe ou erro ao adicionar: {e}")
