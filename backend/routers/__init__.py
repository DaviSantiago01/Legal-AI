from .auth import router as auth_router
from .documentos import router as documentos_router
from .rag import router as rag_router
from .conversas import router as conversas_router

__all__ = ["auth_router", "documentos_router", "rag_router", "conversas_router"]
