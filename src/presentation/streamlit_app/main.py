import sys
import os
import streamlit as st
import time
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Garimpo Judicial",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SETUP PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS ---
try:
    from src.domain.models import EvaluationStatus
    from src.presentation.streamlit_app.dependencies import get_services
    # Importa os componentes da Triagem (Antigo)
    from src.presentation.streamlit_app.components import (
        render_sidebar, 
        render_dashboard, 
        render_triage_cards
    )
    # Importa a Nova Página
    from src.presentation.streamlit_app.views.carteira import render_carteira
    from src.presentation.streamlit_app.styles import load_global_css
except ImportError as e:
    st.error(f"Erro de Importação: {e}")
    st.stop()

def main():
    # 0. Carrega Estilos Globais
    load_global_css()

    # 1. Inicializa Serviços
    services = get_services()
    
    # Mock User ID (Em prod viria do Auth)
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = "Julio"
    user_id = st.session_state["user_id"]

    # 2. Navegação Lateral (Sidebar Menu)
    with st.sidebar:
        # st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=50) # Placeholder Logo
        st.markdown("### Garimpo Judicial")
        
        # Menu de Opções
        page = st.radio(
            "Navegação", 
            ["🔍 Triagem Rápida", "📁 Minha Carteira"],
            index=0
        )
        
        st.divider()
        # Stats Rápidos na Sidebar
        # Nota: get_stats pode falhar se a tabela não estiver populada ainda, então usamos try/except silencioso ou mock se preferir
        try:
            stats = services["get_stats"].execute(user_id)
            st.caption("📊 Produtividade Hoje")
            st.write(f"Analisados: **{stats.get('total_processado', 0)}**")
            st.write(f"Salvos: **{stats.get('analisar', 0)}**")
        except:
            st.caption("Carregando stats...")

    # 3. Roteamento de Páginas
    
    # --- ROTA: TRIAGEM ---
    if page == "🔍 Triagem Rápida":
        run_triage_page(services, user_id)
        
    # --- ROTA: CARTEIRA ---
    elif page == "📁 Minha Carteira":
        render_carteira(services, user_id)

# =========================================
# LÓGICA DA PÁGINA DE TRIAGEM (Refatorada)
# =========================================
def run_triage_page(services, user_id):
    st.title("🔍 Triagem de Oportunidades")
    
    # 1. Busca as opções disponíveis no banco primeiro
    filter_options = services["get_filters"].execute()
    
    # 2. Passa as listas explícitas para o render_sidebar
    # CORREÇÃO AQUI: Passamos os argumentos nomeados corretos
    filters = render_sidebar(
        unique_ufs=filter_options.get("ufs", []),
        unique_cities=filter_options.get("cidades", []),
        unique_types=filter_options.get("tipos", []),
        unique_sites=filter_options.get("sites", []),
        unique_status=filter_options.get("status_imovel", [])
    )
    
    # 3. Busca Leilões com os filtros aplicados
    # Nota: Lembre-se que agora filters['uf'] retorna uma lista, e o repo já espera lista
    auctions_data = services["get_auctions"].execute(
        user_id=user_id,
        uf=filters.get('uf'),
        cidade=filters.get('cidade'),
        tipo_bem=filters.get('tipo_bem'),
        site=filters.get('site'),
        status_imovel=filters.get('status_imovel')
    )
    
    # Converte para DataFrame para visualização
    df_auctions = pd.DataFrame([vars(a) for a in auctions_data]) if auctions_data else pd.DataFrame()

    # Dashboard Topo
    render_dashboard(df_auctions)
    
    st.divider()

    # Cards de Triagem
    if not df_auctions.empty:
        decisions = render_triage_cards(df_auctions)

        # Botão Flutuante/Fixo de Ação
        if decisions:
            count = len(decisions)
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button(f"Processar Lote ({count}) ⚡", type="primary", use_container_width=True):
                    _process_batch(services, decisions)
    else:
        st.info("Nenhum leilão encontrado com estes filtros.")

def _process_batch(services, decisions_dict):
    try:
        to_analyze = []
        to_discard = []

        for item in decisions_dict.values():
            payload = {'site': item['site'], 'id_leilao': item['id_leilao']}
            
            if item['decisao'] == "Analisar":
                to_analyze.append(payload)
            elif item['decisao'] == "Descartar":
                to_discard.append(payload)

        user_id = st.session_state["user_id"]

        if to_discard:
            services["submit_eval"].execute(user_id, to_discard, EvaluationStatus.DESCARTAR)
        
        if to_analyze:
            services["submit_eval"].execute(user_id, to_analyze, EvaluationStatus.ANALISAR)

        st.toast("🚀 Decisões salvas com sucesso!", icon="✅")
        
        # Limpa o session state das decisões antigas
        for key in list(st.session_state.keys()):
            if key.startswith("decision_"):
                del st.session_state[key]

        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

if __name__ == "__main__":
    main()
