from datetime import datetime
from pydantic import BaseModel

class ConversaResponse(BaseModel):
    id: int
    titulo: str
    criado_em: datetime

    class Config:
        from_attributes = True

class MensagemResponse(BaseModel):
    id: int
    conversa_id: int
    conteudo: str
    remetente: str
    criado_em: datetime

    class Config:
        from_attributes = True
