# ⚖️ Legal AI - Assistente Jurídico com RAG

Sistema RAG para pesquisa inteligente de jurisprudência e análise de precedentes.

---

## 💡 Ideia

Advogados gastam horas buscando precedentes manualmente. Este sistema usa RAG (Retrieval-Augmented Generation) para buscar e analisar jurisprudência automaticamente, economizando tempo e aumentando precisão.

---

## 🎯 MVP - Funcionalidades

✅ Upload de PDFs jurídicos (decisões, leis, contratos)  
✅ Busca híbrida (semântica + keywords)  
✅ Chat inteligente com memória de contexto  
✅ Citações automáticas com fonte

---

## 🏗️ Arquitetura

```
PDFs → Text Splitter → Embeddings → ChromaDB
                                         ↓
Pergunta → Busca BM25 + Vetores → RAG → LLM → Resposta + Fonte
```

---

## 🛠️ Stack Técnico

- **Backend:** Python + LangChain
- **Busca:** BM25 + Vector Search
- **Interface:** Streamlit
---

**🔨 Em desenvolvimento - MVP**
