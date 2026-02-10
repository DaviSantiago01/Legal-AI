import logging
from fastapi import HTTPException
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from ..config import CHROMA_DIR
from ..models import Conversa, Mensagem
from ..utils import get_vector_count, limpar_chroma_db

logger = logging.getLogger(__name__)

def carregar_base_vetorial(embeddings):
    try:
        base_vetorial = Chroma(
            persist_directory=CHROMA_DIR,
            embedding_function=embeddings
        )
        total_vetores = get_vector_count(base_vetorial)
    except Exception as e:
        if "dimension" in str(e).lower():
            logger.error(f"❌ Erro de dimensão no Chroma: {e}")
            limpar_chroma_db()
            raise HTTPException(
                status_code=400,
                detail="A base de dados era incompatível e foi resetada. Por favor, processe o documento novamente."
            )
        logger.error(f"Erro ao carregar ChromaDB: {e}")
        raise HTTPException(status_code=500, detail="Erro ao carregar base de dados. Re-processe o documento.")
    if total_vetores == 0:
        raise HTTPException(status_code=404, detail="Nenhum documento indexado. Por favor, processe um documento primeiro.")
    return base_vetorial, total_vetores

def carregar_conversa(db, conversa_id: int, usuario_id: int):
    conversa_atual = db.query(Conversa).filter(
        Conversa.id == conversa_id,
        Conversa.usuario_id == usuario_id
    ).first()
    if not conversa_atual:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conversa_atual

def carregar_historico(conversa_atual, db):
    historico_msgs = []
    historico_msgs_db = db.query(Mensagem).filter(
        Mensagem.conversa_id == conversa_atual.id
    ).order_by(Mensagem.criado_em.desc()).limit(6).all()
    historico_msgs_db.reverse()
    for msg in historico_msgs_db:
        if msg.remetente == "user":
            historico_msgs.append(HumanMessage(content=msg.conteudo))
        else:
            historico_msgs.append(AIMessage(content=msg.conteudo))
    return historico_msgs

def reformular_pergunta(pergunta: str, historico_msgs, llm):
    if not historico_msgs:
        return pergunta
    prompt_reform = [
        SystemMessage(content="""Dada a conversa a seguir e uma pergunta de acompanhamento, reformule a pergunta de acompanhamento para que seja uma pergunta independente, capturando todo o contexto necessário da conversa anterior.
Não responda à pergunta, apenas reescreva-a se necessário. Se a pergunta já for independente, retorne-a como está. Mantenha o idioma original."""),
        *historico_msgs,
        HumanMessage(content=pergunta)
    ]
    res_reform = llm.invoke(prompt_reform)
    logger.info(f"Pergunta Original: {pergunta} | Reformulada: {res_reform.content}")
    return res_reform.content

def buscar_documentos(base_vetorial, pergunta_busca: str):
    try:
        return base_vetorial.similarity_search(pergunta_busca, k=4)
    except Exception as e:
        if "dimension" in str(e).lower():
            limpar_chroma_db()
            raise HTTPException(
                status_code=400,
                detail="Erro de compatibilidade detectado. A base foi limpa. Processe o documento novamente."
            )
        raise e

def montar_contexto(documentos):
    context_parts = []
    for doc in documentos:
        fonte = doc.metadata.get("source", "N/A")
        context_parts.append(f"Fonte: {fonte}\n{doc.page_content}")
    return "\n\n---\n\n".join(context_parts)

def gerar_resposta(pergunta: str, context: str, historico_msgs, llm):
    system_prompt_final = """Você é um assistente de IA altamente capaz e profissional, projetado para analisar documentos e responder dúvidas.
Sua missão é responder à pergunta do usuário com base EXCLUSIVAMENTE nas informações fornecidas no Contexto abaixo.

Diretrizes:
1. Responda de forma completa, profissional e direta.
2. Use formatação Markdown para melhorar a leitura (negrito para destaques, listas para tópicos).
3. Se a informação solicitada não estiver no contexto, diga claramente: "Não encontrei essa informação nos documentos analisados."
4. Não invente informações que não estejam no texto.
5. Sempre que possível, cite a fonte ou página de onde tirou a informação."""
    messages_final = [
        SystemMessage(content=system_prompt_final),
        *historico_msgs,
        HumanMessage(content=f"Contexto Recuperado:\n{context}\n\nPergunta do Usuário: {pergunta}")
    ]
    return llm.invoke(messages_final)

def registrar_mensagens(db, conversa_atual, pergunta: str, resposta):
    msg_user = Mensagem(
        conversa_id=conversa_atual.id,
        conteudo=pergunta,
        remetente="user"
    )
    msg_ia = Mensagem(
        conversa_id=conversa_atual.id,
        conteudo=resposta.content,
        remetente="ia"
    )
    db.add(msg_user)
    db.add(msg_ia)
    db.commit()
