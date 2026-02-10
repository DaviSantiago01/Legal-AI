from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    nome: Optional[str] = None

class UserResponse(UserBase):
    id: int
    nome: Optional[str] = None
    criado_em: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
