import streamlit as st
import requests

st.set_page_config(page_title="Legal AI", page_icon="⚖️")

st.title("⚖️ Legal AI - Sistema RAG Jurídico")
st.markdown("---")

st.subheader("📄 Upload de Documentos")
uploaded_file = st.file_uploader("Escolha um PDF", type="pdf")

if uploaded_file and st.button("📤 Enviar Documento"):
    with st.spinner("Processando..."):
        try:
            files = {"file": uploaded_file}
            response = requests.post("http://localhost:8000/carregar/", files=files)
            
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ {data['message']}")
                st.info(f"**Arquivo:** {data['filename']}")
            
            elif response.status_code == 400:
                error = response.json()
                st.error(f"❌ Erro de validação: {error['detail']}")
            
            elif response.status_code == 500:
                error = response.json()
                st.error(f"❌ Erro no servidor: {error['detail']}")
            
            else:
                st.error(f"❌ Erro inesperado ({response.status_code})")
        
        except requests.exceptions.ConnectionError:
            st.error("❌ Não foi possível conectar ao servidor. Certifique-se que a API está rodando.")
        
        except Exception as e:
            st.error(f"❌ Erro: {str(e)}")