import os
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from ..config import DOCS_DIR, CHROMA_DIR
from ..database import get_db
from ..deps import get_current_user
from ..models import Documento, Usuario
from ..schemas import DocumentoResponse
from ..services.rag_engine import embeddings, CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_SEPARATORS
from ..services.documentos_service import (
    validar_upload_pdf,
    salvar_pdf,
    restaurar_pdf_se_necessario,
    carregar_paginas_pdf,
    splitar_paginas,
    persistir_blocos,
    criar_ou_validar_base,
)

router = APIRouter()

MAX_FILE_BYTES = 10 * 1024 * 1024

@router.post("/carregar/", response_model=DocumentoResponse)
async def carregar_documentos(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
) -> DocumentoResponse:
    validar_upload_pdf(file, MAX_FILE_BYTES)
    caminho_arquivo, content = await salvar_pdf(file, DOCS_DIR)

    documento_existente = db.query(Documento).filter(Documento.nome_arquivo == file.filename).first()
    if documento_existente:
        documento_existente.conteudo_binario = content
        documento_existente.preprocessado = False
        documento_existente.numero_chunks = 0
        db.commit()
        db.refresh(documento_existente)
        return documento_existente

    doc = Documento(
        nome_arquivo=file.filename,
        nome_original=file.filename,
        caminho_arquivo=caminho_arquivo,
        conteudo_binario=content
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

@router.post("/processar/{filename}")
async def processar_documento(
    filename: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    caminho_pdf = os.path.join(DOCS_DIR, filename)

    documento_registro = db.query(Documento).filter(Documento.nome_arquivo == filename).first()
    if not documento_registro:
        raise HTTPException(status_code=404, detail="Documento não registrado no banco de dados.")

    if documento_registro.preprocessado:
        try:
            _, total = criar_ou_validar_base(embeddings, CHROMA_DIR)
            if total > 0:
                return {
                    "message": "Documento já processado e verificado.",
                    "filename": filename,
                    "numero_chunks": documento_registro.numero_chunks,
                }
        except Exception:
            pass

    restaurar_pdf_se_necessario(caminho_pdf, documento_registro, DOCS_DIR)

    try:
        paginas_pdf = carregar_paginas_pdf(caminho_pdf)
        blocos = splitar_paginas(paginas_pdf, CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_SEPARATORS)
        persistir_blocos(blocos, embeddings, CHROMA_DIR)

        documento_registro.preprocessado = True
        documento_registro.numero_chunks = len(blocos)
        db.commit()

        return {
            "message": "Documento processado e armazenado com sucesso.",
            "filename": filename,
            "numero_chunks": len(blocos)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar: {str(e)}")

@router.get("/documentos/")
async def listar_documentos(current_user: Usuario = Depends(get_current_user)):
    try:
        if not os.path.exists(DOCS_DIR):
            return {"documentos": [], "total": 0}
        documentos = [f for f in os.listdir(DOCS_DIR) if f.endswith('.pdf')]
        return {"documentos": documentos, "total": len(documentos)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro {str(e)}")
