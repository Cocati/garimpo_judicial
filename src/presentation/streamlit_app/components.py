import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List

# ALTERAÇÃO: Agora aceitamos 4 listas como parâmetros
def render_sidebar(unique_ufs: List[str], unique_cities: List[str], unique_types: List[str], unique_sites: List[str]) -> Dict[str, Any]:
    with st.sidebar:
        st.header("🔍 Filtros de Triagem")
        
        # Filtros vindos do Banco
        uf = st.selectbox("Estado (UF)", options=["Todos"] + unique_ufs)
        
        # Dica: Se quiser filtrar cidade baseado na UF selecionada, precisaria de mais lógica, 
        # mas vamos carregar todas por enquanto para simplificar.
        cidade = st.selectbox("Cidade", options=["Todas"] + unique_cities)
        
        tipo_bem = st.multiselect("Tipo de Bem", options=unique_types)
        site = st.multiselect("Leiloeiro", options=unique_sites)
        
        aplicar = st.button("Aplicar Filtros", type="primary", use_container_width=True)
        
        return {
            "uf": None if uf == "Todos" else uf,
            "cidade": None if cidade == "Todas" else cidade,
            "tipo_bem": tipo_bem if tipo_bem else None,
            "site": site if site else None,
            "clicked": aplicar
        }

# ... (Mantenha o render_dashboard igual) ...
def render_dashboard(df: pd.DataFrame):
    if df.empty:
        return

    with st.expander("📊 Ver Estatísticas da Carteira (Clique para expandir)", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'tipo_bem' in df.columns:
                fig_tipo = px.pie(df, names='tipo_bem', title='Tipo Imóvel', hole=0.5)
                fig_tipo.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_tipo, use_container_width=True)

        with col2:
            if 'tipo_leilao' in df.columns:
                fig_mod = px.pie(df, names='tipo_leilao', title='Modalidade', hole=0.5)
                fig_mod.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_mod, use_container_width=True)

        with col3:
            if 'site' in df.columns:
                fig_site = px.pie(df, names='site', title='Leiloeiro', hole=0.5)
                fig_site.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_site, use_container_width=True)
