import streamlit as st
import pandas as pd
import plotly.express as px

from datetime import datetime, time
from src.presentation.streamlit_app.views.auditoria_v2 import render_auditoria_v2
from src.domain.models import EvaluationStatus, NoBidReason

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

    # Calcula o valor máximo para o slider de forma dinâmica
    all_values = [i.valor_2_praca for i in all_items if i.valor_2_praca and i.valor_2_praca > 0]
    max_slider_value = int(max(all_values)) if all_values else 1000000

    # Categorização baseada no EvaluationStatus
    items_analisar = [i for i in all_items if i.status_carteira == 'ANALISAR']
    items_participar = [i for i in all_items if i.status_carteira == 'PARTICIPAR']
    items_finalizados = [i for i in all_items if i.status_carteira in ('NO_BID', 'OUTBID')]

    tabs = st.tabs([
        f"📥 A Analisar ({len(items_analisar)})",
        f"🚀 Participar ({len(items_participar)})",
        f"🏁 Finalizados ({len(items_finalizados)})"
    ])

    with tabs[0]:
        if not items_analisar:
            st.info("Sua esteira de análise está vazia.")
        else:
            with st.container(border=True):
                filters = _render_filters("analisar", max_slider_value, allow_sorting=True)

            filtered_items = _apply_filters(items_analisar, filters, max_slider_value)
            st.caption(f"Exibindo {len(filtered_items)} de {len(items_analisar)} leilões.")

            for auction in filtered_items:
                _render_card(auction, suffix="analisar")

    with tabs[1]:
        if not items_participar:
            st.info("Nenhum leilão na fase de participação.")
        else:
            with st.container(border=True):
                filters = _render_filters("participar", max_slider_value, allow_sorting=True)

            filtered_items = _apply_filters(items_participar, filters, max_slider_value)
            st.caption(f"Exibindo {len(filtered_items)} de {len(items_participar)} leilões.")

            for auction in filtered_items:
                _render_card(auction, suffix="participar", is_participating=True, services=services, user_id=user_id)

    with tabs[2]:
        if not items_finalizados:
            st.info("Nenhum leilão finalizado (descartado ou com disputa perdida).")
        else:
            # --- INÍCIO DA SEÇÃO DE INDICADORES ---
            df_finalizados = pd.DataFrame([vars(a) for a in items_finalizados])

            with st.container(border=True):
                st.markdown("#### 📊 Painel de Análise de Desempenho")
                
                # 1. KPIs
                total_finalizados = len(df_finalizados)
                no_bid_count = df_finalizados[df_finalizados['status_carteira'] == 'NO_BID'].shape[0]
                outbid_count = df_finalizados[df_finalizados['status_carteira'] == 'OUTBID'].shape[0]
                
                taxa_no_bid = (no_bid_count / total_finalizados * 100) if total_finalizados > 0 else 0
                taxa_outbid = (outbid_count / total_finalizados * 100) if total_finalizados > 0 else 0
                
                capital_evitado_series = df_finalizados.loc[df_finalizados['status_carteira'] == 'NO_BID', 'valor_2_praca']
                capital_evitado = pd.to_numeric(capital_evitado_series, errors='coerce').sum()

                kpi_cols = st.columns(4)
                kpi_cols[0].metric("Total Finalizados", f"{total_finalizados}")
                kpi_cols[1].metric("Taxa de 'NO BID'", f"{taxa_no_bid:.1f}%")
                kpi_cols[2].metric("Taxa de 'OUTBID'", f"{taxa_outbid:.1f}%")
                kpi_cols[3].metric("Capital Evitado", f"R$ {capital_evitado/1_000_000:.2f}M")

                st.divider()

                # 2. Gráficos
                chart_cols = st.columns(2)
                with chart_cols[0]:
                    st.markdown("##### Motivos de Descarte ('NO BID')")
                    
                    def get_reason_display_name(reason):
                        if hasattr(reason, 'value'): return reason.value
                        elif isinstance(reason, str) and reason: return reason
                        return "Não especificado"

                    df_nobid = df_finalizados[df_finalizados['status_carteira'] == 'NO_BID'].copy()
                    if not df_nobid.empty:
                        df_nobid['no_bid_reason_str'] = df_nobid['no_bid_reason'].apply(get_reason_display_name)
                        reason_counts = df_nobid['no_bid_reason_str'].value_counts().reset_index()
                        reason_counts.columns = ['Motivo', 'Quantidade']

                        # Filtra a categoria "Não especificado" para um gráfico mais limpo
                        reason_counts = reason_counts[reason_counts['Motivo'] != 'Não especificado']

                        if not reason_counts.empty:
                            fig_reasons = px.pie(
                                reason_counts,
                                names='Motivo',
                                values='Quantidade',
                                hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Pastel
                            )
                            fig_reasons.update_layout(height=350, margin=dict(l=20, r=20, t=5, b=20), showlegend=True)
                            st.plotly_chart(fig_reasons, use_container_width=True)
                        else:
                            st.caption("Nenhum motivo de descarte foi especificado.")
                    else:
                        st.caption("Nenhum leilão 'NO BID' registrado.")

                with chart_cols[1]:
                    st.markdown("##### Status dos Finalizados")
                    if not df_finalizados.empty:
                        status_counts = df_finalizados['status_carteira'].value_counts().reset_index()
                        status_counts.columns = ['Status', 'Quantidade']
                        fig_status = px.pie(status_counts, names='Status', values='Quantidade', hole=0.4, color_discrete_map={'NO_BID': '#EF553B', 'OUTBID': '#636EFA'})
                        fig_status.update_layout(height=350, margin=dict(l=20, r=20, t=5, b=20))
                        st.plotly_chart(fig_status, use_container_width=True)
            
            st.divider()
            # --- FIM DA SEÇÃO DE INDICADORES ---

            with st.container(border=True):
                reason_options = [reason.value for reason in NoBidReason]
                status_options = ['NO_BID', 'OUTBID']
                filters = _render_filters(
                    "descartados", 
                    max_slider_value, 
                    allow_sorting=False, 
                    no_bid_reason_options=reason_options,
                    status_options=status_options
                )

            filtered_items = _apply_filters(items_finalizados, filters, max_slider_value)
            st.caption(f"Exibindo {len(filtered_items)} de {len(items_finalizados)} leilões.")

            for auction in filtered_items:
                _render_card(auction, suffix="finalizado", is_readonly=True)


def _render_filters(prefix: str, max_value: int, allow_sorting: bool = True, no_bid_reason_options: list = None, status_options: list = None):
    """Renderiza um conjunto de filtros padronizados."""
    filters = {}
    st.markdown("##### Filtros e Ordenação")
    c1, c2 = st.columns([2, 1])
    with c1:
        filters['search'] = st.text_input("🔎 Buscar por Título ou ID", key=f"search_{prefix}")
        
        if no_bid_reason_options:
            filters['no_bid_reasons'] = st.multiselect(
                "Filtrar por Motivo de Descarte",
                options=no_bid_reason_options,
                key=f"reason_filter_{prefix}"
            )

        if status_options:
            filters['statuses'] = st.multiselect(
                "Filtrar por Status Final",
                options=status_options,
                key=f"status_filter_{prefix}"
            )

    with c2:
        if allow_sorting:
            filters['sort_date'] = st.checkbox("Ordenar por data do leilão", value=True, key=f"sort_{prefix}")
    
    # Slider fora das colunas para ocupar a largura total
        min_val, max_val = st.slider(
            "💰 Filtrar por Valor (2ª Praça)",
            min_value=0,
            max_value=max_value,
            value=(0, max_value),
            step=10000,
            key=f"val_slider_{prefix}",
            format="R$ %d"
        )
        filters['min_val'] = min_val
        filters['max_val'] = max_val

    return filters


def _apply_filters(items, filters, max_slider_value):
    """Aplica os filtros a uma lista de leilões."""
    filtered = items

    search_term = filters.get('search', '').lower()
    if search_term:
        filtered = [i for i in filtered if
                    (i.titulo and search_term in i.titulo.lower()) or
                    (i.id_leilao and search_term in i.id_leilao.lower())]

    selected_reasons = filters.get('no_bid_reasons')
    if selected_reasons:
        def get_reason_value(reason):
            if isinstance(reason, NoBidReason):
                return reason.value
            return reason

        filtered = [
            i for i in filtered if
            i.no_bid_reason and get_reason_value(i.no_bid_reason) in selected_reasons
        ]

    selected_statuses = filters.get('statuses')
    if selected_statuses:
        filtered = [i for i in filtered if i.status_carteira in selected_statuses]

    min_val = filters.get('min_val', 0)
    max_val = filters.get('max_val', float('inf'))
    if min_val > 0 or max_val < max_slider_value:
        filtered = [i for i in filtered if i.valor_2_praca and min_val <= i.valor_2_praca <= max_val]

    if filters.get('sort_date', False):
        # Usa sorted() para retornar uma nova lista ordenada, sem modificar a original
        filtered = sorted(filtered, key=lambda x: x.data_2_praca if x.data_2_praca else datetime(9999, 1, 1))

    return filtered


def _render_card(auction, suffix, is_participating=False, is_readonly=False, services=None, user_id=None):
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

            # Exibe o motivo do descarte ou status final
            if is_readonly:
                if auction.status_carteira == 'NO_BID' and auction.no_bid_reason:
                    st.info(f"**Motivo do Descarte:** {auction.no_bid_reason}", icon="🗑️")
                elif auction.status_carteira == 'OUTBID':
                    st.warning("**Status:** Disputa Perdida", icon="🥊")

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

            # Botão para marcar como disputa perdida
            if is_participating:
                if st.button("Marcar como Perdido 🥊", key=f"btn_lost_{auction.id_leilao}_{suffix}", use_container_width=True):
                    services["repository"].update_status(user_id, auction.site, auction.id_leilao, EvaluationStatus.OUTBID)
                    st.toast("Leilão movido para 'Finalizados' como Disputa Perdida.")
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