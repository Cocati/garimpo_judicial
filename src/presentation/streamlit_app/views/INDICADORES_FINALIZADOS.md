# Proposta de Implementação de Indicadores na Aba "Finalizados"

## Introdução

A aba "Finalizados" atualmente serve como um arquivo de leilões que foram ativamente descartados (`NO_BID`) ou perdidos em disputa (`OUTBID`). Esses dados, no entanto, representam uma fonte valiosa de inteligência de negócio. A análise agregada desses resultados pode revelar padrões, validar a eficácia da estratégia de triagem e fornecer insights para otimizar futuras decisões de investimento.

Esta proposta detalha a implementação de um painel de indicadores e gráficos nesta aba para transformar dados brutos em conhecimento estratégico.

## Objetivos

*   **Identificar** os principais motivos que levam à decisão de "NO BID".
*   **Analisar** a performance em disputas (`OUTBID`).
*   **Quantificar** o volume de capital "protegido" ao evitar leilões de alto risco.
*   **Detectar** padrões geográficos ou de risco nos leilões descartados.

---

## Proposta de Indicadores e Gráficos

A sugestão é adicionar um `st.container` no topo da aba "Finalizados" que conterá os seguintes componentes visuais:

### 1. Painel de KPIs (Indicadores Chave)

Um resumo rápido com os números mais importantes para dar um panorama instantâneo do desempenho.

*   **Total de Leilões Finalizados:** Número total de itens na aba.
*   **Taxa de Descarte (NO BID):** Percentual de leilões que foram `NO_BID` em relação ao total.
*   **Taxa de Disputa Perdida (OUTBID):** Percentual de leilões que foram `OUTBID`.
*   **Capital Evitado:** Soma do `valor_2_praca` de todos os leilões `NO_BID`, representando o montante que não foi alocado em operações de risco.

**Exemplo Visual (usando `st.metric`):**

!Exemplo de KPIs

```
[ Total Finalizados ]  [ Taxa de NO BID ]  [ Taxa de OUTBID ]  [ Capital Evitado ]
[       150         ]  [      85%       ]  [       15%      ]  [   R$ 12.5M      ]
```

### 2. Gráfico: Principais Motivos para "NO BID"

Este é o indicador mais importante para o feedback estratégico, mostrando *por que* as oportunidades estão sendo descartadas.

*   **Tipo de Gráfico:** Gráfico de Barras Horizontais.
*   **Eixo Y:** Os motivos listados no enum `NoBidReason` (ex: "Risco Jurídico/Processual", "Condição Financeira/Pagamento", etc.).
*   **Eixo X:** A contagem de leilões para cada motivo.
*   **Insight:** Permite identificar rapidamente quais categorias de risco estão mais impactando as decisões. Se "Condição Financeira" for o principal motivo, pode indicar que os critérios de ROI estão muito rígidos. Se for "Risco Jurídico", pode ser um sinal para refinar a fase de triagem inicial.

### 3. Gráfico: Distribuição de Finalizados por Estado (UF)

*   **Tipo de Gráfico:** Gráfico de Barras Verticais.
*   **Eixo X:** Sigla do Estado (UF).
*   **Eixo Y:** Contagem de leilões finalizados, com barras empilhadas para `NO_BID` e `OUTBID`.
*   **Insight:** Ajuda a visualizar se há concentração de leilões problemáticos ou disputas mais acirradas em certas regiões do país, auxiliando na alocação de foco e recursos.

---

## Plano de Implementação Simplificado

A implementação pode ser feita diretamente no arquivo `/src/presentation/streamlit_app/views/carteira.py`, dentro da `tabs[2]`.

1.  **Coleta e Preparação dos Dados:** Antes de renderizar os cards, usar a lista `items_finalizados` para criar um DataFrame do Pandas.

2.  **Cálculo dos Indicadores:**
    *   Agrupar o DataFrame por `status_carteira` para contar `NO_BID` vs. `OUTBID`.
    *   Agrupar o DataFrame (filtrado por `NO_BID`) por `no_bid_reason` para o gráfico de motivos.
    *   Agrupar por `uf` para o gráfico geográfico.

3.  **Renderização no Streamlit:**
    *   Usar `st.columns` para criar o layout dos KPIs e `st.metric` para exibi-los.
    *   Usar `st.bar_chart` para renderizar os gráficos de forma simples e direta.

### Exemplo de Código para `_render_portfolio_list` em `carteira.py`:

```python
# Dentro de with tabs:

if not items_finalizados:
    st.info("Nenhum leilão finalizado (descartado ou com disputa perdida).")
else:
    # --- INÍCIO DA NOVA SEÇÃO DE INDICADORES ---
    import pandas as pd

    df_finalizados = pd.DataFrame([vars(a) for a in items_finalizados])

    with st.container(border=True):
        st.markdown("#### 📊 Painel de Análise de Desempenho")
        
        # 1. KPIs
        total_finalizados = len(df_finalizados)
        no_bid_count = df_finalizados[df_finalizados['status_carteira'] == 'NO_BID'].shape
        taxa_no_bid = (no_bid_count / total_finalizados * 100) if total_finalizados > 0 else 0
        capital_evitado = df_finalizados[df_finalizados['status_carteira'] == 'NO_BID']['valor_2_praca'].sum()

        kpi_cols = st.columns(4)
        kpi_cols.metric("Total Finalizados", f"{total_finalizados}")
        kpi_cols.metric("Taxa de 'NO BID'", f"{taxa_no_bid:.1f}%")
        kpi_cols.metric("Taxa de 'OUTBID'", f"{(100-taxa_no_bid):.1f}%")
        kpi_cols.metric("Capital Evitado", f"R$ {capital_evitado/1_000_000:.2f}M")

        # 2. Gráficos
        chart_cols = st.columns(2)
        with chart_cols:
            st.markdown("##### Motivos de 'NO BID'")
            df_finalizados['no_bid_reason_str'] = df_finalizados['no_bid_reason'].apply(lambda x: x.value if x else 'Não especificado')
            reason_counts = df_finalizados[df_finalizados['status_carteira'] == 'NO_BID']['no_bid_reason_str'].value_counts()
            st.bar_chart(reason_counts)

        with chart_cols:
            st.markdown("##### Finalizados por Estado (UF)")
            uf_counts = df_finalizados.groupby('uf')['status_carteira'].value_counts().unstack(fill_value=0)
            st.bar_chart(uf_counts)
    # --- FIM DA NOVA SEÇÃO ---

    # O resto do código (filtros e cards) continua aqui...
```