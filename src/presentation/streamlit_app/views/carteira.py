import streamlit as st

from datetime import datetime, time
from src.presentation.streamlit_app.views.auditoria_v2 import render_auditoria_v2

def render_carteira(services, user_id):
    """
    Ponto de entrada da Carteira. 
    Gerencia o roteamento entre Listagem, Edição de Dados e Auditoria V2.0.
    """
    st.title("📁 Minha Carteira de Oportunidades")

    # Inicialização de estados de navegação
    if "page" not in st.session_state:
        st.session_state.page = "listagem"
    if "selected_auction" not in st.session_state:
        st.session_state.selected_auction = None

    # ROTEAMENTO (Router)
    if st.session_state.page == "auditoria_v2" and st.session_state.selected_auction:
        # Chama a tela de Auditoria
        auction_ref = st.session_state.selected_auction
        
        # Botão flutuante de voltar (UX)
        if st.button("⬅️ Voltar para Carteira"):
            st.session_state.page = "listagem"
            st.session_state.selected_auction = None
            st.rerun()
            
        render_auditoria_v2(
            services, 
            user_id, 
            auction_ref["site"], 
            auction_ref["id_leilao"]
        )
        
    elif st.session_state.page == "editar_dados_brutos":
        _render_edit_source_data(services)
        
    else:
        _render_portfolio_list(services, user_id)

def _render_portfolio_list(services, user_id):
    """Renderiza a listagem segmentada por abas."""
    # Garante que temos o caso de uso correto
    all_items = services["get_portfolio_auctions"].execute(user_id)
    
    # Categorização baseada no EvaluationStatus
    items_analisar = [i for i in all_items if i.status_carteira == 'ANALISAR']
    items_participar = [i for i in all_items if i.status_carteira == 'PARTICIPAR']
    items_descartados = [i for i in all_items if i.status_carteira == 'NO_BID']

    tabs = st.tabs([
        f"📥 A Analisar ({len(items_analisar)})", 
        f"🚀 Participar ({len(items_participar)})", 
        f"🗑️ Descartados ({len(items_descartados)})"
    ])

    with tabs[0]:
        if not items_analisar:
            st.info("Sua esteira de análise está vazia.")
        for auction in items_analisar:
            _render_card(auction, suffix="analisar") 

    with tabs[1]:
        for auction in items_participar:
            _render_card(auction, suffix="participar", is_participating=True)

    with tabs[2]:
        for auction in items_descartados:
            _render_card(auction, suffix="descartado", is_readonly=True)

def _render_card(auction, suffix, is_participating=False, is_readonly=False):
    """Card de visualização do leilão com botões de ação únicos."""
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 1])
        
        with c1:
            if auction.imagem_capa:
                # CORREÇÃO DO ERRO DE WIDTH
                st.image(auction.imagem_capa, use_container_width=True)
            else:
                st.markdown("📷 *Sem Foto*")
        
        with c2:
            col_t1, col_t2 = st.columns([0.9, 0.1])
            col_t1.subheader(auction.titulo)
            
            # Botão de Edição Rápida
            if col_t2.button("✏️", key=f"edit_raw_{auction.id_leilao}_{suffix}"):
                st.session_state.page = "editar_dados_brutos"
                st.session_state.selected_auction = {"site": auction.site, "id_leilao": auction.id_leilao, "obj": auction}
                st.rerun()

            st.caption(f"📍 {auction.cidade}/{auction.uf} | 🏛️ {auction.site}")
            
            c_d1, c_d2 = st.columns(2)
            
            # Formatação segura de datas
            d1_str = auction.data_1_praca.strftime("%d/%m/%Y") if auction.data_1_praca else "S/D"
            d2_str = auction.data_2_praca.strftime("%d/%m/%Y") if auction.data_2_praca else "S/D"
            
            c_d1.metric("1ª Praça", f"R$ {auction.valor_1_praca:,.2f}", d1_str)
            c_d2.metric("2ª Praça", f"R$ {auction.valor_2_praca:,.2f}", d2_str, delta_color="normal")

        with c3:
            btn_label = "Avaliar 📝"
            if is_participating: btn_label = "Ver Detalhes 🔍"
            elif is_readonly: btn_label = "Revisar 📂"

            if st.button(btn_label, key=f"btn_go_{auction.id_leilao}_{suffix}", use_container_width=True):
                st.session_state.page = "auditoria_v2"
                st.session_state.selected_auction = {"site": auction.site, "id_leilao": auction.id_leilao}
                st.rerun()

def _render_edit_source_data(services):
    """Formulário para correção de dados de scraping."""
    auction_data = st.session_state.selected_auction["obj"]
    
    # 1. BOTÃO VOLTAR (Restaurado)
    if st.button("⬅️ Cancelar e Voltar", key="btn_back_edit"):
        st.session_state.page = "listagem"
        st.rerun()

    st.subheader(f"✏️ Corrigir Dados Estruturais: {auction_data.id_leilao}")
    st.info("Edite os dados principais caso o scraping tenha trazido informações incorretas.")
    
    with st.form("edit_raw_form"):
        new_title = st.text_input("Título", value=auction_data.titulo)
        
        c1, c2 = st.columns(2)
        
        # COLUNA 1: DADOS DA 1ª PRAÇA
        with c1:
            st.markdown("### 1ª Praça")
            v1 = st.number_input("Valor R$", value=float(auction_data.valor_1_praca or 0.0))
            
            # Tratamento de Data (Restaurado)
            val_d1 = auction_data.data_1_praca.date() if auction_data.data_1_praca else datetime.now().date()
            d1_input = st.date_input("Data", value=val_d1, key="d1_input")

        # COLUNA 2: DADOS DA 2ª PRAÇA
        with c2:
            st.markdown("### 2ª Praça")
            v2 = st.number_input("Valor R$", value=float(auction_data.valor_2_praca or 0.0))
            
            # Tratamento de Data (Restaurado)
            val_d2 = auction_data.data_2_praca.date() if auction_data.data_2_praca else datetime.now().date()
            d2_input = st.date_input("Data", value=val_d2, key="d2_input")
        
        st.markdown("---")
        
        if st.form_submit_button("💾 Salvar Correções", use_container_width=True):
            # Conversão de date -> datetime para compatibilidade com o modelo
            new_dt1 = datetime.combine(d1_input, time.min)
            new_dt2 = datetime.combine(d2_input, time.min)
            
            updates = {
                "titulo": new_title, 
                "valor_1_praca": v1, 
                "valor_2_praca": v2,
                "data_1_praca": new_dt1, # Adicionado
                "data_2_praca": new_dt2  # Adicionado
            }
            
            # Chama o repositório (Agora funcionará pois corrigimos o dependencies.py)
            services["repository"].update_auction_core_data(auction_data.site, auction_data.id_leilao, updates)
            
            st.success("Dados corrigidos com sucesso!")
            st.session_state.page = "listagem"
            st.rerun()