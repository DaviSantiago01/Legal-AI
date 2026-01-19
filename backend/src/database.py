import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Configuração de Logs
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), encoding="utf-8")

# Configuração da URL do Banco de Dados 
DATABASE_URL = os.getenv("DATABASE_URL")

# Inicialização do Engine 
# (Engine é a interface de comunicação com o banco de dados)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica conexões antes de usar
    connect_args={"connect_timeout": 5},
    pool_size=5,  # Número de conexões mantidas no pool
    max_overflow=10  # Conexões extras permitidas além do pool_size
)

# Criação da Sessão Local
# (SessionLocal é uma factory que cria sessões de banco de dados)
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
