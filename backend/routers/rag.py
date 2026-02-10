from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import Conversa, Mensagem, Usuario
from ..schemas import QueryRequest, QueryResponse
from ..services.rag_engine import embeddings, llm
from ..services.rag_service import (
    carregar_base_vetorial,
    carregar_conversa,
    carregar_historico,
    reformular_pergunta,
    buscar_documentos,
    montar_contexto,
    gerar_resposta,
    registrar_mensagens,
)

router = APIRouter()

@router.post("/pergunta/", response_model=QueryResponse)
async def responder_pergunta(
    query: QueryRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        base_vetorial, _ = carregar_base_vetorial(embeddings)
        conversa_atual = None
        historico_msgs = []

        if query.conversa_id:
            conversa_atual = carregar_conversa(db, query.conversa_id, current_user.id)
            historico_msgs = carregar_historico(conversa_atual, db)

        pergunta_busca = reformular_pergunta(query.pergunta, historico_msgs, llm)
        documentos = buscar_documentos(base_vetorial, pergunta_busca)
        context = montar_contexto(documentos)
        resposta = gerar_resposta(query.pergunta, context, historico_msgs, llm)

        if not conversa_atual:
            conversa_atual = Conversa(titulo=query.pergunta[:50], usuario_id=current_user.id)
            db.add(conversa_atual)
            db.commit()
            db.refresh(conversa_atual)

        registrar_mensagens(db, conversa_atual, query.pergunta, resposta)

        return {
            "resposta": resposta.content,
            "sources": [doc.metadata for doc in documentos],
            "num_docs": len(documentos),
            "conversa_id": conversa_atual.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro: {str(e)}")
