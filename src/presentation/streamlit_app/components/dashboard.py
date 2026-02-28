import streamlit as st
import pandas as pd
import plotly.express as px  # Nova importação para gráficos bonitos

def render_dashboard(df: pd.DataFrame, stats_history: dict = None):
    """
    Renderiza o painel de indicadores com gráficos de Pizza/Donut.
    """
    if not stats_history:
        stats_history = {'analisar': 0, 'descartar': 0}

    st.markdown("### 📊 Visão Geral")

    # --- LINHA 1: KPIs GERAIS (Métricas continuam iguais) ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        total_pendente = len(df)
        st.metric("📌 Pendentes", total_pendente, help="Fila de espera")
    
    with c2:
        vol_total = df['valor_1_praca'].sum() if not df.empty and 'valor_1_praca' in df.columns else 0
        st.metric("💰 Volume (1ª Praça)", f"R$ {vol_total/1_000_000:.1f}M")

    with c3:
        st.metric("🗑️ Descartados", stats_history.get('descartar', 0))
        
    with c4:
        count_analisar = stats_history.get('analisar', 0)
        total_proc = stats_history.get('total_processado', 1) or 1
        st.metric("⭐ Para Análise", count_analisar, delta=f"{(count_analisar/total_proc)*100:.0f}% Aprov")

    st.markdown("---")

    # --- LINHA 2: GRÁFICOS DE PIZZA (DONUT) ---
    if not df.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        # --- GRÁFICO 1: TIPO DE BEM ---
        with col_chart1:
            if 'tipo_bem' in df.columns:
                # Prepara os dados: Conta quantos de cada tipo
                counts_tipo = df['tipo_bem'].value_counts().reset_index()
                counts_tipo.columns = ['Tipo', 'Qtd']
                
                # Cria o gráfico Donut
                fig_tipo = px.pie(
                    counts_tipo, 
                    names='Tipo', 
                    values='Qtd', 
                    title='🏢 Distribuição por Tipo',
                    hole=0.4, # Faz o buraco no meio (Donut)
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                # Ajustes visuais (fundo transparente para combinar com tema dark)
                fig_tipo.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_tipo, use_container_width=True)

        # --- GRÁFICO 2: TOP LEILOEIROS ---
        with col_chart2:
            if 'site' in df.columns:
                # Prepara os dados: Conta quantos de cada site
                counts_site = df['site'].value_counts().reset_index()
                counts_site.columns = ['Site', 'Qtd']
                
                # Se tiver muitos sites, pega o Top 5 e agrupa o resto em "Outros" (Opcional, mas recomendado)
                if len(counts_site) > 6:
                    top_5 = counts_site.head(5)
                    outros = pd.DataFrame([['Outros', counts_site.iloc[5:]['Qtd'].sum()]], columns=['Site', 'Qtd'])
                    counts_site = pd.concat([top_5, outros])

                # Cria o gráfico Donut
                fig_site = px.pie(
                    counts_site, 
                    names='Site', 
                    values='Qtd', 
                    title='⚖️ Top Leiloeiros',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_site.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_site, use_container_width=True)
    
    st.markdown("---")
