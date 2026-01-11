import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
        /* Força altura da linha */
        div[data-testid="stDataEditor"] table {
            --row-height: 150px !important;
        }
        div[data-testid="stDataEditor"] td {
            vertical-align: middle !important;
            font-size: 16px;
        }
        /* Ajuste de container para remover espaços brancos sobrando */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 98% !important;
        }
        div[data-testid="stDataEditor"] th {
            background-color: #f0f2f6;
            min-height: 40px;
            font-size: 15px;
        }
    </style>
    """, unsafe_allow_html=True)
