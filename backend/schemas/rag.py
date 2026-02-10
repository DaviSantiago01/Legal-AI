from typing import Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    pergunta: str
    conversa_id: Optional[int] = None

class QueryResponse(BaseModel):
    resposta: str
    sources: list[dict]
    num_docs: int
    conversa_id: Optional[int] = None
