import streamlit as st
import pandas as pd
from datetime import datetime

def render_carteira(services, user_id):
    st.title("📁 Minha Carteira de Oportunidades")

    # 1. Gestão de Estado da Visualização
    if "editing_auction_id" not in st.session_state:
        st.session_state["editing_auction_id"] = None

    # Se tiver um ID selecionado, mostra a tela de ANÁLISE PROFUNDA
    if st.session_state["editing_auction_id"]:
        _render_detailed_analysis(services, user_id)
    else:
        # Senão, mostra a LISTAGEM com ABAS
        _render_portfolio_list(services, user_id)

def _render_portfolio_list(services, user_id):
    # 1. Busca todos os itens já com o status mapeado
    all_items = services["get_portfolio_auctions"].execute(user_id)
    
    # 2. Filtra as listas baseado no status
    items_analisar = [i for i in all_items if i.status_carteira == 'ANALISAR']
    items_participar = [i for i in all_items if i.status_carteira == 'PARTICIPAR']
    items_descartados = [i for i in all_items if i.status_carteira == 'NO_BID']

    # 3. Cria as abas
    tab1, tab2, tab3 = st.tabs([
        f"📥 A Analisar ({len(items_analisar)})", 
        f"🚀 Participar ({len(items_participar)})", 
        f"🗑️ Descartados ({len(items_descartados)})"
    ])

    with tab1:
        if not items_analisar:
            st.info("Sua esteira de análise está vazia. Volte para a Triagem!")
        for auction in items_analisar:
            _render_card(auction) 

    with tab2:
        if not items_participar:
            st.info("Nenhum imóvel aprovado para leilão ainda.")
        for auction in items_participar:
            _render_card(auction, is_participating=True)

    with tab3:
        if not items_descartados:
            st.info("Lixeira vazia.")
        for auction in items_descartados:
            _render_card(auction, is_readonly=True)

def _render_card(auction, is_participating=False, is_readonly=False):
    """
    Função auxiliar que desenha o card do imóvel na lista.
    """
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 1])
        
        # Coluna 1: Imagem
        with c1:
            if auction.imagem_capa:
                st.image(auction.imagem_capa, width="stretch")
            else:
                st.markdown("📷 *Sem Foto*")
        
        # Coluna 2: Dados e Datas
        with c2:
            st.subheader(f"{auction.titulo}")
            st.caption(f"📍 {auction.cidade} - {auction.uf} | 🏛️ {auction.site}")
            
            # Helper para formatar data
            def fmt_date(dt):
                return dt.strftime("%d/%m/%Y") if dt else "--/--/--"

            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.markdown(f"**1ª Praça** ({fmt_date(auction.data_1_praca)})")
                st.markdown(f"💰 R$ {auction.valor_1_praca:,.2f}")
            
            with col_p2:
                st.markdown(f"**2ª Praça** ({fmt_date(auction.data_2_praca)})")
                val_2 = auction.valor_2_praca
                st.markdown(f":green[**📉 R$ {val_2:,.2f}**]")
        
        # Coluna 3: Ação
        with c3:
            st.write("") # Espaçamento
            
            # Define o texto do botão baseado no contexto
            btn_label = "Avaliar 📝"
            if is_participating:
                btn_label = "Ver Detalhes 🔍"
            elif is_readonly:
                btn_label = "Revisar 📂"

            # Atualizado para evitar warning: use_container_width -> width="stretch" (ainda suportado)
            # ou width='stretch' se seu streamlit for muito novo.
            if st.button(btn_label, key=f"btn_{auction.id_leilao}", width="stretch"):
                # Salva o contexto na sessão
                st.session_state["editing_auction_id"] = auction.id_leilao
                st.session_state["editing_auction_site"] = auction.site
                st.session_state["current_auction_obj"] = auction
                st.rerun()

def _render_detailed_analysis(services, user_id):
    """
    Tela de Imersão: Análise Jurídica e Financeira.
    """
    id_leilao = st.session_state["editing_auction_id"]
    site = st.session_state["editing_auction_site"]
    auction_obj = st.session_state.get("current_auction_obj")

    # Busca dados detalhados do banco
    analysis_data = services["repo"].get_detailed_analysis(user_id, site, id_leilao)
    
    # --- 1. CABEÇALHO DE NAVEGAÇÃO ---
    c_back, c_title = st.columns([1, 10])
    with c_back:
        if st.button("⬅️"):
            st.session_state["editing_auction_id"] = None
            st.session_state["current_auction_obj"] = None
            st.rerun()
    with c_title:
        st.subheader(f"Análise: {id_leilao}")

    # --- 2. CARD DE CONTEXTO ---
    if auction_obj:
        with st.expander("🔎 Dados do Edital (Clique para recolher)", expanded=True):
            c_img, c_info, c_dates = st.columns([1, 2, 2])
            
            with c_img:
                if auction_obj.imagem_capa:
                    st.image(auction_obj.imagem_capa, width="stretch")
                else:
                    st.markdown("📷 *Sem Foto*")
            
            with c_info:
                st.markdown(f"**{auction_obj.titulo}**")
                st.caption(f"📍 {auction_obj.cidade}/{auction_obj.uf}")
                st.markdown(f"🔗 [Abrir Edital no Site]({auction_obj.link_detalhe})")

            with c_dates:
                def fmt(dt): return dt.strftime("%d/%m/%Y") if dt else "--"
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown("**1ª Praça**")
                    st.caption(fmt(auction_obj.data_1_praca))
                    st.markdown(f"R$ {auction_obj.valor_1_praca:,.2f}")
                with col_d2:
                    st.markdown("**2ª Praça**")
                    st.caption(fmt(auction_obj.data_2_praca))
                    st.markdown(f":green[**R$ {auction_obj.valor_2_praca:,.2f}**]")

    st.divider()

    # --- 3. ÁREA DE TRABALHO (FORMULÁRIOS) ---
    col_jur, col_fin = st.columns(2)
    
    with col_jur:
        st.markdown("### ⚖️ Análise Jurídica")
        
        parecer = st.text_area("Parecer Jurídico (Resumo)", value=analysis_data.parecer_juridico or "", height=150)
        
        # --- CORREÇÃO DO ERRO DO SELECTBOX (RISCO) ---
        opcoes_risco = ["Baixo", "Médio", "Alto"]
        
        # Verifica se é Enum ou String para evitar erro
        valor_atual_risco = analysis_data.risco_judicial
        if hasattr(valor_atual_risco, 'value'): 
            valor_atual_risco = valor_atual_risco.value
        
        # Garante que o valor existe na lista, senão usa o padrão
        if valor_atual_risco not in opcoes_risco:
            valor_atual_risco = "Baixo"
            
        risco = st.selectbox("Risco Jurídico", opcoes_risco, index=opcoes_risco.index(valor_atual_risco))

        st.markdown("**Checklist de Nulidades**")
        chk_reu = st.checkbox("Réu Citado Corretamente?", value=analysis_data.reu_citado)
        chk_credores = st.checkbox("Credores Intimados?", value=analysis_data.intimacao_credores)
        
        st.markdown("---")
        
        # --- CORREÇÃO DO ERRO DO SELECTBOX (OCUPAÇÃO) ---
        opcoes_ocupacao = ["Vago", "Ocupado (Proprietário)", "Ocupado (Inquilino)", "Desconhecido"]
        
        # Verifica se é Enum ou String
        valor_atual_ocupacao = analysis_data.ocupacao_status
        if hasattr(valor_atual_ocupacao, 'value'):
            valor_atual_ocupacao = valor_atual_ocupacao.value
        
        # Garante que valor existe na lista
        if valor_atual_ocupacao not in opcoes_ocupacao:
            valor_atual_ocupacao = "Vago"

        # Passamos o INDEX (número inteiro) e não uma lista
        idx_ocupacao = opcoes_ocupacao.index(valor_atual_ocupacao)
        ocupacao = st.selectbox("Situação Física", opcoes_ocupacao, index=idx_ocupacao)

    with col_fin:
        st.markdown("### 💰 Estudo de Viabilidade (ROI)")
        
        venda_estimada = st.number_input("Valor de Venda (Mercado)", value=float(analysis_data.valor_venda_estimado or 0.0))
        
        c1, c2 = st.columns(2)
        div_cond = c1.number_input("Dívida Condomínio", value=float(analysis_data.divida_condominio or 0.0))
        div_iptu = c2.number_input("Dívida IPTU", value=float(analysis_data.divida_iptu or 0.0))
        
        custo_ref = st.number_input("Custo Reforma/Desoc.", value=float(analysis_data.custo_reforma or 0.0))
        
        # Cálculo Simples em Tempo Real
        custo_total_dividas = div_cond + div_iptu + custo_ref
        st.info(f"Passivo Total Levantado: **R$ {custo_total_dividas:,.2f}**")

    st.markdown("---")
    
    # --- BARRA DE AÇÃO (DECISÃO) ---
    col_save, col_approve, col_reject = st.columns([2, 2, 2])
    
    # 1. Salvar Rascunho
    with col_save:
        if st.button("💾 Salvar Progresso", width="stretch"):
            _save_analysis(services, analysis_data, parecer, risco, chk_reu, chk_credores, ocupacao, venda_estimada, div_cond, div_iptu, custo_ref)
            st.toast("Dados salvos com sucesso!")

    # 2. Aprovar (Mover para Participar)
    with col_approve:
        if st.button("🟢 APROVAR P/ LEILÃO", type="primary", width="stretch"):
            # Salva
            _save_analysis(services, analysis_data, parecer, risco, chk_reu, chk_credores, ocupacao, venda_estimada, div_cond, div_iptu, custo_ref)
            # Atualiza Status
            services["repo"].update_status(user_id, site, id_leilao, "PARTICIPAR")
            
            st.balloons()
            st.success("Imóvel movido para a aba PARTICIPAR!")
            st.session_state["editing_auction_id"] = None
            st.rerun()

    # 3. Descartar (Mover para Lixeira)
    with col_reject:
        if st.button("🔴 DESCARTAR / NO-BID", width="stretch"):
             _save_analysis(services, analysis_data, parecer, risco, chk_reu, chk_credores, ocupacao, venda_estimada, div_cond, div_iptu, custo_ref)
             
             # Atualiza Status
             services["repo"].update_status(user_id, site, id_leilao, "NO_BID")
             
             st.error("Imóvel descartado.")
             st.session_state["editing_auction_id"] = None
             st.rerun()

def _save_analysis(services, original_obj, parecer, risco, reu, credores, ocupacao, venda, cond, iptu, reforma):
    """Helper para montar o objeto e salvar"""
    original_obj.parecer_juridico = parecer
    original_obj.risco_judicial = risco
    original_obj.reu_citado = reu
    original_obj.intimacao_credores = credores
    original_obj.ocupacao_status = ocupacao
    original_obj.valor_venda_estimado = venda
    original_obj.divida_condominio = cond
    original_obj.divida_iptu = iptu
    original_obj.custo_reforma = reforma
    
    services["repo"].save_detailed_analysis(original_obj)