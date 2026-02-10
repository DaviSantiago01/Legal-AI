import os
import shutil
import logging
from .config import CHROMA_DIR

logger = logging.getLogger(__name__)

def get_vector_count(vector_store):
    """
    Retorna a contagem de documentos no Vector Store de forma segura.
    Tenta usar métodos internos mais rápidos, com fallback para métodos públicos.
    """
    try:
        # Tenta usar a API interna do Chroma (mais rápida: O(1))
        return vector_store._collection.count()
    except Exception as e:
        # Se for erro de dimensão, propaga para ser tratado e limpar o banco
        if "dimension" in str(e).lower():
            raise
        try:
            # Fallback: carrega IDs para contar (menos eficiente: O(N))
            # Usado apenas se a API interna falhar ou mudar
            return len(vector_store.get()['ids'])
        except Exception:
            return 0

def limpar_chroma_db():
    """
    Reseta o diretório do ChromaDB com segurança.
    Remove toda a pasta e recria, garantindo um estado limpo.
    """
    if os.path.exists(CHROMA_DIR):
        logger.warning(f"🧹 Resetando base vetorial: {CHROMA_DIR}")
        try:
            # Remove a árvore de diretórios recursivamente
            shutil.rmtree(CHROMA_DIR)
        except PermissionError:
            logger.error("❌ Erro de permissão ao limpar ChromaDB. O arquivo pode estar em uso pelo sistema.")
        except Exception as e:
            logger.error(f"❌ Erro ao limpar ChromaDB: {e}")
    
    # Recria o diretório vazio
    os.makedirs(CHROMA_DIR, exist_ok=True)
