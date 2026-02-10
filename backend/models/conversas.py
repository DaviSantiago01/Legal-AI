from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from ..database import Base

class Conversa(Base):
    __tablename__ = "conversas"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    mensagens = relationship("Mensagem", back_populates="conversa", cascade="all, delete-orphan")
    usuario = relationship("Usuario", back_populates="conversas")

class Mensagem(Base):
    __tablename__ = "mensagens"

    id = Column(Integer, primary_key=True, index=True)
    conversa_id = Column(Integer, ForeignKey("conversas.id"), nullable=False)
    conteudo = Column(Text, nullable=False)
    remetente = Column(String, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow)

    conversa = relationship("Conversa", back_populates="mensagens")
