from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, LargeBinary, String
from ..database import Base

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, unique=True, nullable=False)
    nome_original = Column(String, nullable=False)
    caminho_arquivo = Column(String, nullable=False)
    conteudo_binario = Column(LargeBinary, nullable=True)
    preprocessado = Column(Boolean, default=False)
    numero_chunks = Column("numero_chuncks", Integer, default=0)
    criado_em = Column(DateTime, default=datetime.utcnow)
