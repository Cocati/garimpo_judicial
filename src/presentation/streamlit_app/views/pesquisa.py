import streamlit as st
import pandas as pd
from src.domain.models import EvaluationStatus, Auction
from typing import List

def _render_single_card(auction: Auction, services, user_id: str):
    """Renderiza um único card de resultado de busca."""
    with st.container():
        col_img, col_info, col_action = st.columns([1.2, 2.3, 1])

        with col_img:
            img_url = auction.imagem_capa
            if not img_url or pd.isna(img_url):
                img_url = "https://via.placeholder.com/300x220?text=Sem+Foto"
            st.markdown(
                f'<img src="{img_url}" style="width: 100%; height: 220px; object-fit: cover; border-radius: 8px;" alt="Foto do bem">',
                unsafe_allow_html=True
            )
            st.caption(f"ID: {auction.id_leilao} | {auction.site}")

        with col_info:
            st.markdown(f"<div class='big-font'>{auction.titulo}</div>", unsafe_allow_html=True)
            if auction.status_imovel and pd.notna(auction.status_imovel):
                st.markdown(f"<span class='status-badge'>{auction.status_imovel}</span>", unsafe_allow_html=True)

            v1 = float(auction.valor_1_praca or 0)
            v2 = float(auction.valor_2_praca or 0)
            c_v1, c_v2 = st.columns(2)
            with c_v1:
                st.markdown("<span class='price-label'>1ª Praça:</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='price-value'>R$ {v1:,.2f}</div>", unsafe_allow_html=True)
            with c_v2:
                st.markdown("<span class='price-label'>2ª Praça:</span>", unsafe_allow_html=True)
                st.markdown(f"<div class='price-value-2'>📉 R$ {v2:,.2f}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown(f"🔗 <a href='{auction.link_detalhe}' target='_blank' class='link-edital'>Ver Edital no Site</a>", unsafe_allow_html=True)

        with col_action:
            st.write("**Status Atual**")
            status_val = auction.status_carteira
            status_display = status_val.replace('_', ' ').capitalize()
            st.markdown(f"<div class='search-status-badge status-{status_val}'>{status_display}</div>", unsafe_allow_html=True)

            if status_val == EvaluationStatus.DESCARTAR.value:
                revert_key = f"revert_{auction.unique_id}"
                if st.button("↩️ Reverter para Análise", key=revert_key, use_container_width=True):
                    try:
                        services["update_status"].execute(
                            user_id=user_id,
                            site=auction.site,
                            id_leilao=auction.id_leilao,
                            new_status=EvaluationStatus.ANALISAR
                        )
                        st.toast(f"Leilão {auction.id_leilao} revertido para análise!", icon="✅")
                        if 'search_results' in st.session_state:
                            del st.session_state['search_results']
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao reverter: {e}")
        st.write("---")

def render_pesquisa(services):
    st.title("🔎 Pesquisa Global de Leilões")
    st.caption("Encontre qualquer leilão, independentemente do status (pendente, descartado, etc).")

    # Styles copied from triage_cards.py for consistency
    st.markdown("""
    <style>
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            border: 1px solid #444; border-radius: 12px; padding: 15px; background-color: #262730;
        }
        .status-badge { display: inline-block; padding: 3px 10px; font-size: 12px; font-weight: bold; color: white; background-color: #555; border-radius: 12px; margin-bottom: 8px; }
        .big-font { font-size: 16px !important; font-weight: 600; line-height: 1.4; margin-bottom: 10px;}
        .price-label { font-size: 12px; color: #aaa; }
        .price-value { font-size: 15px; font-weight: bold; }
        .price-value-2 { font-size: 15px; font-weight: bold; color: #4CAF50; }
        .link-edital { font-size: 13px; text-decoration: none; color: #4da6ff !important; }
        .search-status-badge { display: inline-block; padding: 4px 12px; font-size: 13px; font-weight: bold; text-align: center; color: white; border-radius: 15px; margin-bottom: 10px; width: 100%; }
        .status-DESCARTAR { background-color: #a63434; }
        .status-ANALISAR { background-color: #3465a4; }
        .status-PARTICIPAR { background-color: #46a434; }
        .status-PENDING { background-color: #555753; }
        .status-NO_BID { background-color: #888a85; }
        .status-OUTBID { background-color: #f57900; }
    </style>
    """, unsafe_allow_html=True)

    if 'search_results' not in st.session_state:
        st.session_state['search_results'] = None
    if 'search_performed' not in st.session_state:
        st.session_state['search_performed'] = False

    user_id = st.session_state.get("user_id", "Julio")

    with st.form(key="search_form"):
        st.markdown("##### Filtros de Pesquisa")
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("Buscar por Título ou ID do Leilão", placeholder="Ex: Apartamento em Copacabana ou 12345")
        with col2:
            status_options = [s for s in EvaluationStatus]
            selected_status = st.multiselect("Status", options=status_options, format_func=lambda x: x.value)
        
        submitted = st.form_submit_button("Buscar Leilões", use_container_width=True, type="primary")

    if submitted:
        with st.spinner("Buscando..."):
            results = services["search_auctions"].execute(
                user_id=user_id,
                search_term=search_term if search_term else None,
                status=selected_status if selected_status else None
            )
            st.session_state['search_results'] = results
            st.session_state['search_performed'] = True
    
    if st.session_state['search_performed']:
        results: List[Auction] = st.session_state['search_results']
        st.divider()
        if results:
            st.success(f"Exibindo {len(results)} resultado(s) (limitado aos 100 mais recentes).")
            for auction in results:
                _render_single_card(auction, services, user_id)
        else:
            st.info("Nenhum resultado encontrado para os critérios informados.")