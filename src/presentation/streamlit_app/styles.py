import streamlit as st

def load_global_css():
    """
    Centraliza a injeção de CSS da aplicação para garantir que os estilos
    sejam aplicados a cada rerun do Streamlit, evitando perda de estado.
    """
    st.markdown("""
    <style>
        /* --- ESTILOS GERAIS (Migrados do main.py) --- */
        .main-header {font-size: 24px; font-weight: bold; color: #333;}
        .stApp {background-color: #0e1117;}

        /* --- ESTILOS DE FORMULÁRIO / CARTEIRA (Migrados do carteira.py) --- */
        /* BASE */
        div[data-testid="stTextInput"] > div[data-baseweb="input"],
        div[data-testid="stTextArea"] > div[data-baseweb="base-input"] {
            background-color: #223247 !important;
            border: 1px solid #4A5568 !important;
            border-radius: 4px !important;
            transition: all 0.25s ease-in-out;
        }

        /* TEXTO */
        input, textarea {
            color: #FFFFFF !important;
            font-family: 'Source Sans Pro', sans-serif !important;
        }

        textarea::placeholder,
        input::placeholder {
            color: #9CA3AF !important;
        }

        /* FOCO */
        div[data-testid="stTextInput"] > div[data-baseweb="input"]:focus-within,
        div[data-testid="stTextArea"] > div[data-baseweb="base-input"]:focus-within {
            border-color: #00D1FF !important;
            box-shadow: 0 0 8px rgba(0,209,255,0.45) !important;
        }

        /* CAMPO VAZIO */
        div[data-testid="stTextInput"] div[data-baseweb="input"] input:placeholder-shown,
        div[data-testid="stTextArea"] div[data-baseweb="base-input"] textarea:placeholder-shown {
            border: 2px solid #FFA500 !important;
        }

        /* PENHORAS */
        div[data-testid="stTextArea"]:has(textarea[aria-label*="Penhoras"]) {
            border-left: 5px solid #FF4B4B !important;
            padding-left: 5px;
        }
    </style>
    """, unsafe_allow_html=True)