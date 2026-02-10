from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    senha_hash = Column(String, nullable=False)
    nome = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    conversas = relationship("Conversa", back_populates="usuario")
