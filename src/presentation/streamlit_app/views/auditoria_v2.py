import streamlit as st

from datetime import date
from src.domain.models import (
    DetailedAnalysis, ConjugeStatus, NaturezaExecucao, 
    EspecieCredito, RiskLevel
)
from src.domain.isj_calculator import IsjCalculator
from src.presentation.streamlit_app.components.alertas_engine import AlertasEngine
from src.presentation.streamlit_app.components.isj_gauge import render_isj_gauge


def render_auditoria_v2(services, user_id: str, site: str, id_leilao: str):
    """
    Formulário de Auditoria Jurídica V2.0 - Final.
    Integração completa com regras de domínio, validação de nulidades e persistência.
    """
    
    # 1. Carregamento Inicial (Singleton no Session State)
    if "current_analysis" not in st.session_state or \
       st.session_state.current_analysis.id_leilao != id_leilao or \
       st.session_state.current_analysis.site != site:
        
        analysis = services['repository'].get_detailed_analysis(site, id_leilao, user_id)
        if not analysis:
            analysis = DetailedAnalysis(site=site, id_leilao=id_leilao, usuario_id=user_id)
        st.session_state.current_analysis = analysis

    # Referência local para facilitar leitura
    analysis = st.session_state.current_analysis
    auction_data = services['repository'].get_auction(site, id_leilao)
    
    # Helpers de UI (Definidos localmente para manter contexto)
    def map_na_option(choice):
        mapping = {"Sim": True, "Não": False, "N/A": None}
        return mapping.get(choice)

    def get_na_index(value):
        if value is True: return 0
        if value is False: return 1
        return 2 # N/A

    # 2. CABEÇALHO (Resumo Visual)
    if auction_data:
        with st.container(border=True):
            col_img, col_info = st.columns([1, 4])
            
            # Coluna da Imagem
            with col_img:
                if auction_data.imagem_capa:
                    st.image(auction_data.imagem_capa, use_container_width=True)
                else:
                    st.info("📷 Sem foto")
                    
            # Coluna de Informações (Dados reestruturados em 3 linhas)
            with col_info:
                st.subheader(f"📍 {auction_data.titulo or 'Leilão Identificado'}")
                
                # Linha 1: Datas das Praças
                c_data1, c_data2 = st.columns(2)
                data_1_str = auction_data.data_1_praca.strftime('%d/%m/%Y') if auction_data.data_1_praca else '-'
                data_2_str = auction_data.data_2_praca.strftime('%d/%m/%Y') if auction_data.data_2_praca else '-'
                c_data1.markdown(f"**Data 1ª Praça:** {data_1_str}")
                c_data2.markdown(f"**Data 2ª Praça:** {data_2_str}")
                
                # Linha 2: Valores das Praças
                c_val1, c_val2 = st.columns(2)
                c_val1.markdown(f"**Valor 1ª Praça:** R$ {auction_data.valor_1_praca:,.2f}")
                c_val2.markdown(f"**Valor 2ª Praça:** R$ {auction_data.valor_2_praca:,.2f}")
                
                # Linha 3: Link do Edital
                st.markdown(f"🔗 [Acesse o Edital]({auction_data.link_detalhe})")
    # 3. Layout Principal
    col_form, col_stats = st.columns([3, 1])

    with col_form:
        tabs = st.tabs([
            "⚖️ 1. Processo", "📜 2. Matrícula", "📝 3. Edital", 
            "🏠 4. Situação", "💰 5. Financeiro", "🤖 6. Parecer"
        ])

        # --- TAB 1: PROCESSO JUDICIAL (Foco da Refatoração) ---
        with tabs[0]:
            st.markdown("Análise do Processo Judicial e Riscos Processuais")
            
            # Bloco A: Dados Básicos e Executados
            c1, c2 = st.columns([1, 1])
            with c1:
                analysis.proc_num = st.text_input("Nº Processo", value=analysis.proc_num or "", key="k_proc_num")
                
                # Tratamento de Lista de Executados (String <-> List)
                executados_str = "\n".join(analysis.proc_executados)
                new_executados = st.text_area(
                    "Executados (um por linha)", 
                    value=executados_str, 
                    height=100,
                    key="k_proc_execs",
                    help="Insira o nome dos executados, um por linha."
                )
                analysis.proc_executados = [x.strip() for x in new_executados.split('\n') if x.strip()]

            with c2:
                # Natureza da Execução
                options_nat = list(NaturezaExecucao)
                try: idx_nat = options_nat.index(analysis.proc_natureza_execucao)
                except: idx_nat = 0
                analysis.proc_natureza_execucao = st.selectbox(
                    "Natureza da Execução", options=options_nat, 
                    index=idx_nat, key="k_proc_nat", format_func=lambda x: x.value
                )

                # Espécie de Crédito (Novo Campo)
                options_esp = list(EspecieCredito)
                try: idx_esp = options_esp.index(analysis.proc_especie_credito)
                except: idx_esp = 1 # Default Comum
                analysis.proc_especie_credito = st.selectbox(
                    "Espécie de Crédito", options=options_esp,
                    index=idx_esp, key="k_proc_esp", format_func=lambda x: x.value,
                    help="Crédito Comum aumenta risco de impenhorabilidade."
                )

            st.divider()

            # Bloco B: Financeiro do Processo & Proporcionalidade
            c3, c4, c5 = st.columns(3)
            with c3:
                analysis.proc_debito_atualizado = st.number_input(
                    "Débito Total (R$)", value=float(analysis.proc_debito_atualizado or 0.0), key="k_proc_deb"
                )
            with c4:
                # Sincroniza com vlr_avaliacao global para cálculo do ISJ
                analysis.vlr_avaliacao = st.number_input(
                    "Avaliação do Imóvel (R$)", value=float(analysis.vlr_avaliacao or 0.0), key="k_proc_aval"
                )
            with c5:
                # KPI Visual de Proporcionalidade
                if analysis.vlr_avaliacao > 0:
                    prop = (analysis.proc_debito_atualizado / analysis.vlr_avaliacao) * 100
                    st.metric("Proporcionalidade", f"{prop:.1f}%", delta_color="inverse")
                    if prop < 10:
                        st.warning("⚠️ Risco: Preço Vil (<10%)")
                else:
                    st.metric("Proporcionalidade", "0.0%")

            st.divider()

            # Bloco C: Checklist de Nulidades (Flags Críticas)
            st.markdown("#### 🚨 Checklist de Nulidades")
            
            col_chk1, col_chk2 = st.columns(2)
            
            with col_chk1:
                # 1. Citação (CRÍTICO)
                choice_citacao = st.radio(
                    "Réu foi devidamente citado?", options=["Sim", "Não", "N/A"],
                    index=get_na_index(analysis.proc_citacao), horizontal=True, key="k_citacao"
                )
                analysis.proc_citacao = map_na_option(choice_citacao)

                # 2. Cônjuge
                choice_conj = st.radio(
                    "Cônjuge Intimado?", options=["Sim", "Não", "N/A"],
                    index=get_na_index(analysis.proc_conjuge), horizontal=True, key="k_conjuge"
                )
                analysis.proc_citacao = map_na_option(choice_citacao)
                
                # 3. Justiça Gratuita
                analysis.proc_justica_gratuita = st.toggle(
                    "Executado possui Justiça Gratuita?", 
                    value=bool(analysis.proc_justica_gratuita), 
                    key="k_proc_jg",
                    help="Aumenta risco de recursos protelatórios."
                )

            with col_chk2:
                # 4. Credores
                choice_cred = st.radio(
                    "Outros credores intimados?", options=["Sim", "Não", "N/A"],
                    index=get_na_index(analysis.proc_credores), horizontal=True, key="k_cred"
                )
                analysis.proc_credores = map_na_option(choice_cred)

                # 5. Coproprietários
                choice_coprop = st.radio(
                    "Coproprietário intimado?", options=["Sim", "Não", "N/A"],
                    index=get_na_index(analysis.proc_coproprietario_intimado), horizontal=True, key="k_coprop"
                )
                analysis.proc_coproprietario_intimado = map_na_option(choice_coprop)

                # 6. Avaliação Integral
                analysis.proc_avaliacao_imovel = st.checkbox(
                    "Avaliação abrange 100% do imóvel?", 
                    value=bool(analysis.proc_avaliacao_imovel), 
                    key="k_aval_full"
                )

            # Recursos
            analysis.proc_recursos = st.toggle("Existem recursos pendentes?", value=bool(analysis.proc_recursos), key="k_rec")
            if analysis.proc_recursos:
                analysis.proc_recursos_obs = st.text_area("Detalhe os recursos", value=analysis.proc_recursos_obs or "")

        # --- TAB 2: MATRÍCULA (Refatorada para Padronização de Experiência) ---
    with tabs[1]:
        st.markdown("Análise Registral e Verificação de Matrícula")
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            analysis.mat_num = st.text_input(
                "Nº Matrícula", 
                value=analysis.mat_num or "", 
                key="k_mat_num"
            )
             # Lista de Proprietários
            prop_text = st.text_area(
                "Proprietários (um por linha)",
                value="\n".join(analysis.mat_proprietario),
                height=100,
                key="input_mat_proprietario"
            )
            # Converte string multilinhas para lista, removendo vazios
            analysis.mat_proprietario = [p.strip() for p in prop_text.split('\n') if p.strip()]

             # Lista de Documentos
            docs_text = st.text_area(
            "Documentos dos Proprietários (CPF/CNPJ - um por linha)",
            value="\n".join(analysis.mat_documentos_proprietarios),
            height=100,
            key="input_mat_docs"
        )
            analysis.mat_documentos_proprietarios = [d.strip() for d in docs_text.split('\n') if d.strip()]

            # Lista de Penhoras (Full width)
            penhoras_text = st.text_area(
            "Penhoras e Averbações Ativas (uma por linha)",
            value="\n".join(analysis.mat_penhoras),
            help="Liste as penhoras (R-X) ou averbações (Av-X) que constam na matrícula.",
            key="input_mat_penhoras"
        )
            analysis.mat_penhoras = [p.strip() for p in penhoras_text.split('\n') if p.strip()]


        with c2:
           #st.markdown("**Ônus Relevantes**")
   
            # Padronização: Proprietário == Executado
            choice_prop = st.radio(
            "Proprietário coincide com o Executado?",
            options=["Sim", "Não", "N/A"],
            index=get_na_index(analysis.mat_prop_confere),
            horizontal=True,
            key="k_mat_conf_radio"
        )
            analysis.mat_prop_confere = map_na_option(choice_prop)
                
            # Padronização: Penhora Averbada
            choice_pen = st.radio(
            "Penhora averbada na matrícula?",
            options=["Sim", "Não", "N/A"],
            index=get_na_index(analysis.mat_penhora_averbada),
            horizontal=True,
            key="k_pen_av_radio"
        )
            analysis.mat_penhora_averbada = map_na_option(choice_pen)
             # Padronização: Usufruto
            choice_usu = st.radio(
            "Possui Usufruto?",
            options=["Sim", "Não", "N/A"],
            index=get_na_index(analysis.mat_usufruto),
            horizontal=True,
            key="k_usu_radio"
        )
            analysis.mat_usufruto = map_na_option(choice_usu)

        with c3:
            
            # Padronização: Cônjuge
            choice_conj = st.radio(
            "Proprietário tem conjugue??",
            options=["Sim", "Não", "N/A"],
            index=get_na_index(analysis.mat_conjugue),
            horizontal=True,
            key="k_mat_conj_radio"
        )
            analysis.mat_conjugue = map_na_option(choice_conj)
            
            # Padronização: Proprietário PJ
            choice_pj = st.radio(
            "Proprietário é Pessoa Jurídica (PJ)?",
            options=["Sim", "Não", "N/A"],
            index=get_na_index(analysis.mat_proprietario_pj),
            horizontal=True,
            key="k_mat_pj_radio"
        )
            analysis.mat_proprietario_pj = map_na_option(choice_pj)
        
            # Padronização: Indisponibilidade
            choice_ind = st.radio(
            "Possui Indisponibilidade?",
            options=["Sim", "Não", "N/A"],
            index=get_na_index(analysis.mat_indisp),
            horizontal=True,
            key="k_ind_radio"
        )
            analysis.mat_indisp = map_na_option(choice_ind)


        # --- TAB 3: EDITAL ---
        with tabs[2]:
            st.markdown("Regras e Condições")
            c1, c2 = st.columns(2)
            with c1:
                analysis.edt_objeto = st.text_input("Descrição do Objeto", value=analysis.edt_objeto or "", key="k_edt_obj")
                # Nota: Este campo é visual, o cálculo usa analysis.vlr_avaliacao (Tab 1)
                st.info(f"Avaliação Base: R$ {analysis.vlr_avaliacao:,.2f}") 
                analysis.edt_data_avaliacao = st.date_input("Data Avaliação", value=analysis.edt_data_avaliacao or date.today(), key="k_edt_dt")
            with c2:
                analysis.edt_parcelamento = st.toggle("Permite Parcelamento?", value=bool(analysis.edt_parcelamento), key="k_edt_parc")
                analysis.edt_iptu_subroga = st.toggle("IPTU Sub-roga no preço?", value=bool(analysis.edt_iptu_subroga), key="k_edt_iptu")
                analysis.edt_condo_claro = st.toggle("Dívida Condomínio Clara?", value=bool(analysis.edt_condo_claro), key="k_edt_condo")
                analysis.edt_percentual_minimo = st.number_input("% Mínimo 2ª Praça", value=float(analysis.edt_percentual_minimo or 50.0), key="k_edt_perc")

        # --- TAB 4: SITUAÇÃO ---
        with tabs[3]:
            st.markdown("Ocupação e Conservação")
            c1, c2 = st.columns(2)
            with c1:
                analysis.edt_posse_status = st.selectbox(
                    "Status Ocupação", 
                    options=["Vago", "Ocupado", "Desconhecido"],
                    index=["Vago", "Ocupado", "Desconhecido"].index(analysis.edt_posse_status) if analysis.edt_posse_status in ["Vago", "Ocupado", "Desconhecido"] else 0,
                    key="k_posse_st"
                )
                analysis.custo_reforma = st.number_input("Est. Reforma (R$)", value=float(analysis.custo_reforma or 0.0), key="k_ref")
            with c2:
                analysis.custo_desocupacao = st.number_input("Est. Desocupação (R$)", value=float(analysis.custo_desocupacao or 0.0), key="k_desoc")
            
            #analysis.edt_posse_estrategia = st.text_area("Estratégia de Posse", value=analysis.edt_posse_estrategia or "", key="k_posse_est")

        # --- TAB 5: FINANCEIRO ---
        with tabs[4]:
            st.markdown("Viabilidade Econômica")
            c1, c2 = st.columns(2)
            with c1:
                analysis.fin_lance = st.number_input("Lance Máximo Planejado (R$)", value=float(analysis.fin_lance or 0.0), key="k_fin_lance")
                analysis.valor_venda_estimado = st.number_input("Valor de Venda (R$)", value=float(analysis.valor_venda_estimado or 0.0), key="k_fin_venda")
            with c2:
                analysis.fin_itbi = st.number_input("Custos ITBI/Cartório (R$)", value=float(analysis.fin_itbi or 0.0), key="k_fin_itbi")
                analysis.divida_condominio = st.number_input("Dívida Condomínio (R$)", value=float(analysis.divida_condominio or 0.0), key="k_fin_div_c")
                analysis.divida_iptu = st.number_input("Dívida IPTU (R$)", value=float(analysis.divida_iptu or 0.0), key="k_fin_div_i")

        # --- TAB 6: PARECER ---
        with tabs[5]:
            st.markdown("Conclusão do Especialista")
            options_risk = list(RiskLevel)
            try: idx_risk = options_risk.index(analysis.risco_judicial)
            except: idx_risk = 0
            
            analysis.risco_judicial = st.selectbox(
                "Nível de Risco Global", options=options_risk, 
                index=idx_risk, key="k_risco", format_func=lambda x: x.value
            )
            analysis.analise_ia = st.text_area(
                "Parecer Final & Próximos Passos", 
                value=analysis.analise_ia or "", height=250, key="k_parecer"
            )

    # 4. Cálculos Finais (Reativos)
    # Recalcula ISJ e KPIs com base nos dados recém inseridos na UI
    alertas = AlertasEngine.avaliar(analysis)
    kpis = IsjCalculator.calculate_financial_kpis(analysis)
    isj_score = IsjCalculator.calculate(analysis)

    # 5. Sidebar de Estatísticas e Ações
    with col_stats:
        st.markdown("### 📊 Resultado")
        render_isj_gauge(isj_score, alertas)
        
        st.divider()
        st.markdown("**Viabilidade**")
        
        # Colorir métricas baseadas no resultado
        delta_lucro = "normal" if kpis['lucro_liquido'] > 0 else "off"
        st.metric("Lucro Líquido", f"R$ {kpis['lucro_liquido']:,.2f}", delta_color=delta_lucro)
        
        st.metric("ROI Estimado", f"{kpis['roi_nominal']:.1f}%")
        st.metric("Investimento Total", f"R$ {kpis['investimento_total']:,.2f}")
        
        st.divider()
        
        # Lógica de Bloqueio (AC-4)
        bloqueado = analysis.proc_citacao is False or analysis.mat_prop_confere is False
        if bloqueado:
             st.error("🚫 **BLOQUEADO**\n\nNulidade crítica detectada (Citação ou Propriedade).")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("💾 Salvar", use_container_width=True, key="k_btn_save"):
                 services['save_rascunho'].execute(analysis)
                 st.toast("Rascunho salvo com sucesso!", icon="💾")

        with col_btn2:
            if st.button("🚀 Finalizar", type="primary", disabled=bloqueado, use_container_width=True, key="k_btn_fin"):
                services['finalizar_auditoria'].execute(analysis,user_id)
                st.balloons()
                st.success("Auditoria finalizada!")
                # Idealmente redirecionar ou limpar estado aqui

       
        with col_btn3:
            # O botão de descartar NÃO usa 'disabled=bloqueado', pois nulidades são justamente o motivo de descarte.
            if st.button("🗑️ OUT", use_container_width=True, key="k_btn_desc"):
                # Invoca o Caso de Uso que criamos nas etapas anteriores
                services['descartar_auditoria'].execute(analysis, user_id)
                st.warning("Auditoria descartada e leilão rejeitado.", icon="🗑️")
                
                # Limpa o estado atual e força o recarregamento da tela para evitar dados fantasmas
                if "current_analysis" in st.session_state:
                    del st.session_state.current_analysis
                
                # 2. Limpa os dados da sessão para não causar vazamento de estado (State Leak)
                if "current_analysis" in st.session_state:
                    del st.session_state.current_analysis
                
                # 3. Pausa rápida para a mensagem de feedback ser lida pelo usuário
                import time
                time.sleep(1.5)
                
                # 4. Roteamento: Define a página de destino e força o reload
                st.session_state.page = "listagem"
                st.rerun()
                
    # 6. Auto-save Silencioso (Background)
    # Executa a cada interação para garantir que nada se perca
    try:
        services['save_rascunho'].execute(analysis)
    except Exception:
        pass # Falhas silenciosas no autosave não devem travar a UI