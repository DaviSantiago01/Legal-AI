# ⚖️ Legal AI — RAG Jurídico

Sistema RAG para pesquisa inteligente de jurisprudência e análise de precedentes.

---

## ✅ O que este projeto faz

- Upload de PDFs jurídicos
- Indexação em vetores (Chroma)
- Perguntas com RAG + LLM
- Respostas com fontes

---

## 🧱 Arquitetura (visão rápida)

```
PDFs → Text Splitter → Embeddings → ChromaDB
                                         ↓
Pergunta → Busca Vetorial → RAG → LLM → Resposta + Fonte
```

---

## 🧰 Stack

- Backend: FastAPI + LangChain
- Vetores: ChromaDB
- LLM: Groq
- Frontend: Streamlit
- Banco: PostgreSQL

---

## ⚙️ Variáveis de ambiente

Crie um .env baseado em [.env.example](.env.example) e preencha:

- `GROQ_API_KEY` (obrigatório)
- `DATABASE_URL` (já configurado para Docker/local)

---

## ▶️ Como rodar com Docker (recomendado)

Use [docker-compose.yml](docker-compose.yml):

```
docker compose up -d --build
```

Acesse:

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:8501

---

## ▶️ Como rodar localmente (dev)

1. Instale dependências

```
pip install -r requirements.txt
```

2. Inicie o backend

```
uvicorn backend/src.main:app --reload
```

3. Inicie o frontend

```
streamlit run frontend/app.py
```

---

## 🔌 Endpoints principais

- `POST /carregar/` — upload de PDF
- `POST /processar/{filename}` — indexar documento
- `POST /pergunta/` — perguntar ao RAG
- `GET /documentos/` — listar PDFs

---

## 📁 Estrutura principal

- Backend: [backend/src/main.py](backend/src/main.py)
- Frontend: [frontend/app.py](frontend/app.py)
- Docker backend: [backend/Dockerfile](backend/Dockerfile)
- Docker frontend: [frontend/Dockerfile](frontend/Dockerfile)
- Dependências: [requirements.txt](requirements.txt)

---

## ⚠️ Observações

- Não versionar `.env` (já ignorado em [.gitignore](.gitignore))
- PDFs ficam em `backend/data/documentos` (ignorado do git)

---
