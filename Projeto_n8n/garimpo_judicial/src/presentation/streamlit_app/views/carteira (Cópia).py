import streamlit as st
import pandas as pd
from src.domain.models import DetailedAnalysis, RiskLevel, OccupationStatus

def render_carteira(services, user_id):
    st.title("📁 Minha Carteira de Oportunidades")
    
    # 1. Carrega os itens salvos ("Analisar")
    portfolio = services["get_portfolio"].execute(user_id)
    
    if not portfolio:
        st.info("Sua carteira está vazia. Vá para a 'Triagem' para encontrar oportunidades.")
        return

    # 2. Seletor de Imóvel (Master View)
    # Cria uma lista formatada para o Selectbox
    options = {f"{p.id_leilao} | {p.titulo} ({p.site})": p for p in portfolio}
    selected_label = st.selectbox("Selecione o imóvel para realizar o Deep Dive:", options.keys())
    
    # Recupera o objeto Auction selecionado
    auction = options[selected_label]
    
    st.divider()

    # 3. Busca a Análise Detalhada existente (ou cria nova)
    analysis = services["get_analysis"].execute(user_id, auction.site, auction.id_leilao)

    # Layout: Coluna Esquerda (Resumo Imóvel) | Coluna Direita (Ferramentas de Análise)
    col_left, col_right = st.columns([1, 2])

    # --- COLUNA ESQUERDA: DADOS ESTÁTICOS ---
    with col_left:
        if auction.imagem_capa:
            st.image(auction.imagem_capa, use_container_width=True)
        
        st.subheader("Dados do Edital")
        st.markdown(f"**1ª Praça:** R$ {auction.valor_1_praca:,.2f}")
        st.markdown(f"**2ª Praça:** R$ {auction.valor_2_praca:,.2f}")
        st.markdown(f"**Cidade:** {auction.cidade}/{auction.uf}")
        
        st.markdown("---")
        st.markdown(f"[🔗 Abrir Edital Original]({auction.link_detalhe})")

    # --- COLUNA DIREITA: FORMULÁRIO DE ANÁLISE ---
    with col_right:
        tab_juridico, tab_financeiro = st.tabs(["⚖️ Análise Jurídica", "💰 Calculadora de ROI"])

        # ==========================
        # ABA JURÍDICA
        # ==========================
        with tab_juridico:
            st.caption("Preencha o checklist para validar a segurança jurídica.")
            
            with st.form("form_juridico"):
                c1, c2 = st.columns(2)
                with c1:
                    new_parecer = st.text_area("Parecer Jurídico (Resumo)", value=analysis.parecer_juridico or "")
                    new_risco = st.selectbox(
                        "Risco Jurídico", 
                        options=[e.value for e in RiskLevel], 
                        index=[e.value for e in RiskLevel].index(analysis.risco_judicial.value)
                    )
                with c2:
                    st.write("**Checklist de Nulidades**")
                    new_reu_citado = st.checkbox("Réu Citado Corretamente?", value=analysis.reu_citado)
                    new_intimacao = st.checkbox("Credores Intimados?", value=analysis.intimacao_credores)
                    
                    if not new_reu_citado:
                        st.error("⚠️ ALERTA: Falta de citação é risco de Nulidade Fatal!")

                st.markdown("#### Passivo do Imóvel")
                c3, c4, c5 = st.columns(3)
                with c3:
                    new_div_condo = st.number_input("Dívida Condomínio (R$)", value=analysis.divida_condominio, step=100.0)
                with c4:
                    new_div_iptu = st.number_input("Dívida IPTU (R$)", value=analysis.divida_iptu, step=100.0)
                with c5:
                    new_subroga = st.checkbox("Dívida Sub-roga?", value=analysis.divida_subroga, help="Se marcado, a dívida morre com o leilão. Se desmarcado, você paga.")

                st.markdown("#### Ocupação")
                new_ocupacao = st.selectbox(
                    "Situação Física", 
                    options=[e.value for e in OccupationStatus],
                    index=[e.value for e in OccupationStatus].index(analysis.ocupacao_status.value)
                )

                submit_juridico = st.form_submit_button("💾 Salvar Análise Jurídica")
                
                if submit_juridico:
                    # Atualiza o objeto analysis
                    analysis.parecer_juridico = new_parecer
                    analysis.risco_judicial = RiskLevel(new_risco)
                    analysis.reu_citado = new_reu_citado
                    analysis.intimacao_credores = new_intimacao
                    analysis.divida_condominio = new_div_condo
                    analysis.divida_iptu = new_div_iptu
                    analysis.divida_subroga = new_subroga
                    analysis.ocupacao_status = OccupationStatus(new_ocupacao)
                    
                    services["save_analysis"].execute(analysis)
                    st.success("Dados jurídicos atualizados!")
                    st.rerun()

        # ==========================
        # ABA FINANCEIRA (ROI)
        # ==========================
        with tab_financeiro:
            st.caption("Simule a viabilidade econômica do arremate.")
            
            # INPUTS
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                st.markdown("**Custos Variáveis**")
                val_mercado = st.number_input("Valor de Venda Estimado (Mercado)", value=analysis.valor_venda_estimado or 0.0, step=1000.0)
                custo_obra = st.number_input("Estimativa de Reforma", value=analysis.custo_reforma, step=500.0)
                custo_desoc = st.number_input("Custo Desocupação", value=analysis.custo_desocupacao, step=500.0)
            
            with col_in2:
                st.markdown("**Parâmetros do Leilão**")
                # Se a dívida não sub-roga, ela soma no custo!
                divida_total = 0.0
                if not analysis.divida_subroga:
                    divida_total = analysis.divida_condominio + analysis.divida_iptu
                    st.warning(f"⚠️ Dívidas (R$ {divida_total:,.2f}) somadas ao custo (Não Sub-roga)")
                
                lance_base = st.number_input("Simular Valor de Lance", value=auction.valor_2_praca, step=1000.0)

            # CÁLCULOS
            comissao = lance_base * 0.05
            itbi_registro = lance_base * 0.04 # Estimativa 4%
            custo_aquisicao = lance_base + comissao + itbi_registro + divida_total + custo_obra + custo_desoc
            
            lucro_bruto = val_mercado - custo_aquisicao
            roi_perc = (lucro_bruto / custo_aquisicao * 100) if custo_aquisicao > 0 else 0

            st.divider()
            
            # RESULTADOS (Métricas Grandes)
            m1, m2, m3 = st.columns(3)
            m1.metric("Custo Total Aquisição", f"R$ {custo_aquisicao:,.2f}")
            m2.metric("Lucro Líquido Previsto", f"R$ {lucro_bruto:,.2f}", delta_color="normal")
            m3.metric("ROI Estimado", f"{roi_perc:.1f}%", delta_color="normal" if roi_perc > 0 else "inverse")

            # Botão Salvar Financeiro
            if st.button("💾 Atualizar Financeiro"):
                analysis.valor_venda_estimado = val_mercado
                analysis.custo_reforma = custo_obra
                analysis.custo_desocupacao = custo_desoc
                # Campos calculados não salvamos no banco, apenas os inputs
                services["save_analysis"].execute(analysis)
                st.toast("Premissas financeiras salvas!", icon="💰")
