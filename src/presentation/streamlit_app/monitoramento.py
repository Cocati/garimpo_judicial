import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def render_monitoramento(services):
    """
    Renderiza a página de monitoramento das execuções dos scrapers.
    """
    st.title("📊 Monitoramento de Scrapers")
    st.caption("Acompanhe a saúde e o desempenho dos robôs de coleta de dados.")

    # --- 1. FILTROS ---
    try:
        all_sources = services['get_scraper_sources'].execute()
        all_statuses = ['SUCCESS', 'FAILED', 'IN_PROGRESS']
    except Exception as e:
        st.error(f"Não foi possível carregar as opções de filtro: {e}")
        return

    with st.container(border=True):
        st.markdown("#####  Filtros")
        c1, c2, c3, c4 = st.columns(4)
        start_date = c1.date_input("Data Início", value=datetime.now() - timedelta(days=7))
        end_date = c2.date_input("Data Fim", value=datetime.now())
        selected_sources = c3.multiselect("Fontes (Scrapers)", options=all_sources, default=all_sources)
        selected_statuses = c4.multiselect("Status", options=all_statuses, default=all_statuses)

    # --- 2. BUSCA DE DADOS ---
    try:
        runs_data = services['get_scraper_runs'].execute(
            start_date=start_date,
            end_date=end_date,
            sources=selected_sources,
            statuses=selected_statuses
        )
        df = pd.DataFrame([vars(r) for r in runs_data])
    except Exception as e:
        st.error(f"Erro ao buscar dados das execuções: {e}")
        return

    if df.empty:
        st.info("Nenhuma execução encontrada para os filtros selecionados.")
        return

    # Conversão de tipos para análise
    df['execution_start_time'] = pd.to_datetime(df['execution_start_time'])
    df['date'] = df['execution_start_time'].dt.date

    # --- 3. KPIs ---
    st.markdown("---")
    st.markdown("#### Indicadores do Período")
    
    total_runs = len(df)
    success_runs = df[df['run_status'] == 'SUCCESS'].shape[0]
    success_rate = (success_runs / total_runs * 100) if total_runs > 0 else 0
    total_collected = df['raw_items_collected'].sum()
    total_mapped = df['mapped_items_count'].sum()
    avg_duration = df[df['run_status'] == 'SUCCESS']['duration_seconds'].mean()

    kpi_cols = st.columns(5)
    kpi_cols[0].metric("Total de Execuções", f"{total_runs}")
    kpi_cols[1].metric("Taxa de Sucesso", f"{success_rate:.1f}%")
    kpi_cols[2].metric("Itens Coletados", f"{int(total_collected)}")
    kpi_cols[3].metric("Itens Mapeados", f"{int(total_mapped)}")
    kpi_cols[4].metric("Duração Média (s)", f"{avg_duration:.2f}" if not pd.isna(avg_duration) else "N/A")

    # --- 4. GRÁFICOS ---
    st.markdown("---")
    st.markdown("#### Análise Visual")
    
    chart_cols = st.columns(2)

    with chart_cols[0]:
        st.markdown("##### Execuções por Dia e Status")
        runs_by_day = df.groupby(['date', 'run_status']).size().reset_index(name='count')
        fig_runs = px.bar(runs_by_day, x='date', y='count', color='run_status',
                          title="Volume de Execuções Diárias",
                          labels={'date': 'Data', 'count': 'Nº de Execuções'},
                          color_discrete_map={'SUCCESS': '#2ca02c', 'FAILED': '#d62728', 'IN_PROGRESS': '#1f77b4'})
        st.plotly_chart(fig_runs, use_container_width=True)

    with chart_cols[1]:
        st.markdown("##### Itens Coletados vs. Mapeados por Fonte")
        items_by_source = df.groupby('source_name')[['raw_items_collected', 'mapped_items_count']].sum().reset_index()
        items_by_source = items_by_source.melt(id_vars='source_name', var_name='tipo', value_name='quantidade')
        
        fig_items = px.bar(items_by_source, x='source_name', y='quantidade', color='tipo', barmode='group',
                           title="Eficiência de Mapeamento por Fonte",
                           labels={'source_name': 'Fonte', 'quantidade': 'Nº de Itens'},
                           color_discrete_map={'raw_items_collected': '#1f77b4', 'mapped_items_count': '#ff7f0e'})
        st.plotly_chart(fig_items, use_container_width=True)

    # --- 5. TABELA DE DADOS ---
    st.markdown("---")
    st.markdown("#### Detalhes das Execuções")
    
    with st.expander("Clique para ver a tabela de dados brutos"):
        st.dataframe(df[[
            'execution_start_time',
            'source_name',
            'run_status',
            'duration_seconds',
            'raw_items_collected',
            'mapped_items_count',
            'error_details'
        ]].sort_values(by='execution_start_time', ascending=False), use_container_width=True)