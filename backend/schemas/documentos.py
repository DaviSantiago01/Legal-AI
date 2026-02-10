from datetime import datetime
from pydantic import BaseModel

class DocumentoResponse(BaseModel):
    id: int
    nome_arquivo: str
    nome_original: str
    caminho_arquivo: str
    preprocessado: bool
    numero_chunks: int
    criado_em: datetime

    class Config:
        from_attributes = True
