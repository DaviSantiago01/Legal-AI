import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DOCS_DIR = os.path.join(BASE_DIR, "data", "documentos")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)

def load_env():
    in_docker = os.path.exists("/.dockerenv")
    load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"), override=not in_docker, encoding="utf-8")

def get_cors_origins():
    origins = os.getenv("CORS_ORIGINS", "http://localhost:8501")
    return [origin.strip() for origin in origins.split(",") if origin.strip()]
