import streamlit as st
from datetime import date
from src.domain.models import DetailedAnalysis, ConjugeStatus, NaturezaExecucao, EspecieCredito, RiskLevel, OccupationStatus
from src.domain.isj_calculator import IsjCalculator
from src.presentation.streamlit_app.components.alertas_engine import AlertasEngine
from src.presentation.streamlit_app.components.isj_gauge import render_isj_gauge

def render_auditoria_v2(services, user_id: str, site: str, id_leilao: str):
    """
    Formulário principal de Auditoria Jurídica V2.0.
    Implementa 6 seções completas, Auto-save, Alertas e KPIs em tempo real.
    """
    
    # 1. Carregamento Inicial ou Recuperação do Estado
    if "current_analysis" not in st.session_state or \
       st.session_state.current_analysis.id_leilao != id_leilao:
        
        # Carrega do banco
        analysis = services['repository'].get_detailed_analysis(site, id_leilao, user_id)
        
        # Se não existir, cria um objeto vazio
        if not analysis:
            analysis = DetailedAnalysis(site=site, id_leilao=id_leilao, usuario_id=user_id)
            
        st.session_state.current_analysis = analysis

    # Referência curta para facilitar a escrita
    analysis = st.session_state.current_analysis

    # 2. Motores de Cálculo (Tempo Real)
    alertas = AlertasEngine.avaliar(analysis)
    isj_score = IsjCalculator.calculate(analysis)
    kpis = IsjCalculator.calculate_financial_kpis(analysis)

    # 3. Layout: Banner de Alertas Críticos
    criticos = [a for a in alertas if a.nivel == "critico"]
    if criticos:
        st.error(f"⚠️ Atenção: {len(criticos)} Pontos Críticos identificados!")
        for alerta in criticos:
            st.caption(f"• {alerta.mensagem}")

    # 4. Layout Principal: Colunas (Formulário vs Sidebar de Stats)
    col_form, col_stats = st.columns([3, 1])

    with col_form:
        tabs = st.tabs([
            "⚖️ 1. Processo", "📜 2. Matrícula", "📝 3. Edital", 
            "🏠 4. Situação", "💰 5. Financeiro", "🤖 6. Parecer IA"
        ])

        # --- TAB 1: PROCESSO ---
        with tabs[0]:
            st.caption("Análise do Processo Judicial e Rito de Execução")
            c1, c2 = st.columns(2)
            with c1:
                analysis.proc_num = st.text_input("Nº Processo", value=analysis.proc_num)
                analysis.proc_natureza_execucao = st.selectbox(
                    "Natureza da Execução", 
                    options=list(NaturezaExecucao),
                    format_func=lambda x: x.value if x else "Selecione",
                    index=list(NaturezaExecucao).index(analysis.proc_natureza_execucao) if analysis.proc_natureza_execucao else 0
                )
                analysis.proc_debito_atualizado = st.number_input("Débito Total Atualizado (R$)", value=analysis.proc_debito_atualizado or 0.0)

            with c2:
                st.markdown("**Checklist de Nulidades**")
                analysis.proc_citacao = st.checkbox("Réu citado corretamente?", value=analysis.proc_citacao)
                analysis.proc_credores = st.checkbox("Outros credores intimados?", value=analysis.proc_credores)
                analysis.proc_coproprietario_intimado = st.checkbox("Coproprietário intimado?", value=analysis.proc_coproprietario_intimado)
                analysis.proc_recursos = st.toggle("Existem recursos pendentes?", value=analysis.proc_recursos)
            
            if analysis.proc_recursos:
                analysis.proc_recursos_obs = st.text_area("Detalhe os recursos pendentes", value=analysis.proc_recursos_obs)

        # --- TAB 2: MATRÍCULA ---
        with tabs[1]:
            st.caption("Análise Registral e Gravames")
            c1, c2 = st.columns(2)
            with c1:
                analysis.mat_num = st.text_input("Nº Matrícula", value=analysis.mat_num)
                analysis.mat_prop_confere = st.checkbox("Proprietário Matrícula == Executado?", value=analysis.mat_prop_confere)
                analysis.mat_proprietario_pj = st.checkbox("Proprietário é Pessoa Jurídica?", value=analysis.mat_proprietario_pj)
            
            with c2:
                st.markdown("**Ônus na Matrícula**")
                analysis.mat_usufruto = st.checkbox("Possui Usufruto?", value=analysis.mat_usufruto)
                analysis.mat_indisp = st.checkbox("Possui Indisponibilidade?", value=analysis.mat_indisp)
                analysis.mat_penhora_averbada = st.checkbox("Penhora do leilão averbada?", value=analysis.mat_penhora_averbada)

        # --- TAB 3: EDITAL (PREENCHIDO) ---
        with tabs[2]:
            st.caption("Regras do Leilão e Dados do Bem")
            c1, c2 = st.columns(2)
            with c1:
                analysis.edt_objeto = st.text_input("Descrição do Objeto (Resumida)", value=analysis.edt_objeto)
                analysis.edt_vlr_avaliacao = st.number_input("Valor da Avaliação (Edital)", value=analysis.edt_vlr_avaliacao or 0.0)
                analysis.edt_data_avaliacao = st.date_input("Data da Avaliação", value=analysis.edt_data_avaliacao)
            
            with c2:
                st.markdown("**Condições de Pagamento e Dívidas**")
                analysis.edt_parcelamento = st.toggle("Permite Parcelamento?", value=analysis.edt_parcelamento)
                analysis.edt_iptu_subroga = st.toggle("IPTU Sub-roga no preço (Art. 130)?", value=analysis.edt_iptu_subroga)
                analysis.edt_condo_claro = st.toggle("Dívida de Condomínio clara no edital?", value=analysis.edt_condo_claro)
                analysis.edt_percentual_minimo = st.number_input("% Mínimo 2ª Praça", value=analysis.edt_percentual_minimo or 50.0)

        # --- TAB 4: SITUAÇÃO FÍSICA (PREENCHIDO) ---
        with tabs[3]:
            st.caption("Ocupação e Estado de Conservação")
            
            analysis.edt_posse_status = st.text_input(
                "Status da Ocupação (Vago/Ocupado)", 
                value=analysis.edt_posse_status
            )
            # Dica: Poderíamos usar um selectbox se OccupationStatus fosse um Enum estrito
            
            col_custos1, col_custos2 = st.columns(2)
            with col_custos1:
                analysis.custo_reforma = st.number_input("Estimativa de Reforma (R$)", value=analysis.custo_reforma or 0.0)
                analysis.custo_desocupacao = st.number_input("Custo de Desocupação (Adv + Custo)", value=analysis.custo_desocupacao or 0.0)
            
            with col_custos2:
                 analysis.edt_posse_estrategia = st.text_area("Estratégia de Desocupação", value=analysis.edt_posse_estrategia, height=100, placeholder="Ex: Acordo amigável, Imissão na Posse...")

        # --- TAB 5: FINANCEIRO ---
        with tabs[4]:
            st.caption("Viabilidade Econômica")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("### Entradas")
                analysis.fin_lance = st.number_input("Lance Máximo Pretendido (R$)", value=analysis.fin_lance or 0.0)
                analysis.valor_venda_estimado = st.number_input("Valor de Venda (Saída) (R$)", value=analysis.valor_venda_estimado or 0.0)
            
            with c2:
                st.markdown("### Custos Adicionais")
                analysis.fin_itbi = st.number_input("ITBI + Cartório (R$)", value=analysis.fin_itbi or 0.0)
                analysis.divida_condominio = st.number_input("Dívida Condomínio (se houver)", value=analysis.divida_condominio or 0.0)
                analysis.divida_iptu = st.number_input("Dívida IPTU (se houver)", value=analysis.divida_iptu or 0.0)

        # --- TAB 6: PARECER (PREENCHIDO) ---
        with tabs[5]:
            st.caption("Conclusão e Parecer Final")
            
            # Seção de Risco
            col_risco, col_rec = st.columns([1, 2])
            with col_risco:
                analysis.risco_judicial = st.selectbox(
                    "Nível de Risco Judicial",
                    options=list(RiskLevel),
                    format_func=lambda x: x.value,
                    index=list(RiskLevel).index(analysis.risco_judicial) if analysis.risco_judicial else 0
                )
            with col_rec:
                if analysis.recomendacao_ia:
                    st.info(f"💡 **Sugestão da IA:** {analysis.recomendacao_ia}")
            
            st.divider()
            st.markdown("**Parecer Jurídico do Advogado**")
            analysis.analise_ia = st.text_area(
                "Escreva aqui sua análise final...", 
                value=analysis.analise_ia,
                height=300
            )

    # 5. Coluna Lateral: Score e KPIs (AC-5)
    with col_stats:
        st.markdown("### Resultado")
        render_isj_gauge(isj_score, alertas)
        
        st.divider()
        st.markdown("#### 💰 KPIs Estimados")
        st.metric("Lucro Líquido", f"R$ {kpis['lucro_liquido']:,.2f}")
        st.metric("ROI Estimado", f"{kpis['roi_nominal']:.1f}%", delta_color="normal")
        st.caption(f"Investimento Total: R$ {kpis['investimento_total']:,.2f}")
        
        st.divider()
        
        # Botão Finalizar com Bloqueio (AC-4)
        bloqueado = analysis.proc_citacao is False or analysis.mat_prop_confere is False
        
        # Botão de Salvar Rascunho Manual (Opcional, pois já tem auto-save)
        if st.button("💾 Salvar Rascunho", use_container_width=True):
             services['save_rascunho'].execute(analysis)
             st.toast("Rascunho salvo!")

        if st.button("🚀 Finalizar Auditoria", type="primary", disabled=bloqueado, use_container_width=True):
            novo_status = services['finalizar_auditoria'].execute(analysis, user_id)
            st.success(f"Finalizado! Status: {novo_status}")
            st.rerun()
        
        if bloqueado:
            st.error("🚫 Finalização bloqueada: Verifique Nulidades (Citação ou Propriedade).")

    # 6. Lógica de Auto-save (AC-6)
    # Executa sempre que houver interação (Rerun do Streamlit)
    try:
        services['save_rascunho'].execute(analysis)
        # st.toast("Auto-save ativo", icon="☁️") # Comentado para não poluir a tela
    except Exception as e:
        st.error(f"Erro no auto-save: {e}")