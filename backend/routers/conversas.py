from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import Conversa, Mensagem, Usuario
from ..schemas import ConversaResponse, MensagemResponse

router = APIRouter()

@router.get("/conversas/", response_model=list[ConversaResponse])
async def listar_conversas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    conversas = db.query(Conversa).filter(Conversa.usuario_id == current_user.id).order_by(Conversa.criado_em.desc()).all()
    return conversas

@router.get("/conversas/{conversa_id}/mensagens/", response_model=list[MensagemResponse])
async def listar_mensagens(
    conversa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    conversa = db.query(Conversa).filter(Conversa.id == conversa_id, Conversa.usuario_id == current_user.id).first()
    if not conversa:
        raise HTTPException(status_code=404, detail="Conversa não encontrada ou acesso negado")

    mensagens = db.query(Mensagem).filter(Mensagem.conversa_id == conversa_id).order_by(Mensagem.criado_em.asc()).all()
    return mensagens
