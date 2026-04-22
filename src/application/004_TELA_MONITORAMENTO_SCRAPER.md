# Especificação Técnica: Tela de Monitoramento de Scrapers

**ID:** 004
**Autor:** Gemini Code Assist
**Data:** 22/04/2026
**Status:** Proposta

---

## 1. Introdução e Objetivos

Esta especificação detalha a criação de uma nova tela no painel administrativo "Garimpo Judicial" chamada **"📊 Monitoramento"**. O objetivo principal desta tela é fornecer uma visão clara e centralizada sobre a saúde, performance e resultados das execuções dos scrapers (robôs de coleta de dados).

Os principais objetivos são:
- **Monitorar a Saúde:** Identificar rapidamente se os scrapers estão executando com sucesso ou falhando.
- **Analisar a Performance:** Acompanhar métricas como duração, latência e volume de requisições.
- **Verificar a Qualidade dos Dados:** Quantificar o número de itens brutos coletados e quantos foram mapeados com sucesso para o sistema.
- **Facilitar o Diagnóstico:** Permitir a filtragem por data, fonte (site do leiloeiro) e status para investigar problemas específicos.

## 2. Fonte de Dados

A tela será alimentada exclusivamente pela tabela `public.scraper_runs`, cuja estrutura é a seguinte:

```sql
CREATE TABLE public.scraper_runs (
    id bigserial NOT NULL,
    execution_id uuid NOT NULL,
    source_name varchar(100) NOT NULL,
    run_type varchar(50) NOT NULL,
    execution_start_time timestamptz NOT NULL,
    execution_end_time timestamptz NULL,
    duration_seconds int4 NULL,
    run_status varchar(50) NOT NULL, -- 'SUCCESS', 'FAILED', 'IN_PROGRESS'
    total_requests int4 NULL,
    successful_requests int4 NULL,
    failed_requests int4 NULL,
    raw_items_collected int4 NULL,
    mapped_items_count int4 NULL,
    error_details text NULL,
    created_at timestamptz DEFAULT now() NULL,
    CONSTRAINT scraper_runs_pkey PRIMARY KEY (id)
);
```

## 3. Design da Interface (UI/UX)

A nova tela será acessível através de um novo item no menu de navegação principal na sidebar.

### 3.1. Layout Geral

A página será dividida em três seções principais:
1.  **Painel de Filtros:** No topo, permitindo ao usuário segmentar os dados.
2.  **Painel de KPIs (Indicadores Chave):** Logo abaixo dos filtros, com métricas agregadas do período selecionado.
3.  **Visualizações e Dados Brutos:** Uma área com gráficos e uma tabela detalhada das execuções.

### 3.2. Componentes da Tela

#### a. Painel de Filtros
- **Seletor de Período:** Um `st.date_input` para selecionar o intervalo de datas (início e fim). O padrão será os últimos 7 dias.
- **Seletor de Fonte (Scraper):** Um `st.multiselect` para filtrar por um ou mais `source_name`.
- **Seletor de Status:** Um `st.multiselect` para filtrar por `run_status` (ex: SUCCESS, FAILED).

#### b. Painel de KPIs
Será uma grade de `st.metric` exibindo os seguintes indicadores (calculados com base nos filtros aplicados):
- **Total de Execuções:** Contagem total de runs no período.
- **Taxa de Sucesso:** Percentual de runs com status `SUCCESS`.
- **Itens Coletados:** Soma de `raw_items_collected`.
- **Itens Mapeados:** Soma de `mapped_items_count`.
- **Duração Média:** Média de `duration_seconds` das execuções bem-sucedidas.

#### c. Gráficos
Dois gráficos principais serão exibidos lado a lado:
- **Gráfico 1: Execuções por Dia (Gráfico de Barras)**
    - **Eixo X:** Data.
    - **Eixo Y:** Contagem de execuções.
    - **Cores:** Barras empilhadas por `run_status` (verde para `SUCCESS`, vermelho para `FAILED`).
- **Gráfico 2: Itens Coletados vs. Mapeados por Fonte (Gráfico de Barras)**
    - **Eixo X:** Nome da Fonte (`source_name`).
    - **Eixo Y:** Contagem de itens.
    - **Barras:** Duas barras para cada fonte: uma para `raw_items_collected` e outra para `mapped_items_count`. Isso evidencia problemas de mapeamento.

#### d. Tabela de Execuções
- Uma `st.dataframe` exibindo as últimas 100 execuções (respeitando os filtros).
- **Colunas:** `execution_start_time`, `source_name`, `run_status`, `duration_seconds`, `raw_items_collected`, `mapped_items_count`.
- A tabela permitirá ordenação por qualquer coluna.

---

## 4. Plano de Implementação (Backend)

### 4.1. Domain Layer (`src/domain/models.py`)
- Criar um novo dataclass `ScraperRun` para representar uma execução de forma agnóstica à tecnologia.
- Criar um dataclass `ScraperRunFilter` para encapsular os filtros da tela.

### 4.2. Infrastructure Layer (`src/infra/`)
- **`database/models_sql.py`**: Adicionar um novo modelo SQLAlchemy `ScraperRunModel` que mapeia a tabela `scraper_runs`.
- **`repositories/postgres_repo.py`**:
    - Implementar um novo método `get_scraper_runs(self, filters: ScraperRunFilter) -> List[ScraperRun]`.
    - Este método irá consultar a tabela `scraper_runs` usando o `ScraperRunModel`, aplicar os filtros e mapear os resultados para uma lista de objetos `ScraperRun`.

### 4.3. Application Layer (`src/application/`)
- **`interfaces.py`**: Adicionar a assinatura do método `get_scraper_runs` à interface `AuctionRepository`.
    - *Nota de Design:* Idealmente, poderia ser criado um `ScraperRepository` separado. No entanto, para manter a simplicidade do projeto neste estágio, o método será adicionado ao repositório existente.
- **`use_cases.py`**: Criar um novo `GetScraperRunsUseCase` que recebe os filtros, os encapsula no `ScraperRunFilter` e chama o método correspondente do repositório.

## 5. Plano de Implementação (Frontend)

### 5.1. Nova View (`src/presentation/streamlit_app/views/`)
- Criar o arquivo `monitoramento.py`.
- Este arquivo conterá uma função principal `render_monitoramento(services)`.
- A função irá:
    1.  Instanciar e chamar o `GetScraperRunsUseCase`.
    2.  Renderizar os filtros da UI.
    3.  Processar os dados retornados com Pandas para calcular os KPIs e preparar os dados para os gráficos.
    4.  Renderizar os componentes da tela (KPIs, gráficos, tabela) usando Streamlit.

### 5.2. Roteamento (`src/presentation/streamlit_app/main.py`)
- Adicionar a opção **"📊 Monitoramento"** ao `st.radio` na sidebar.
- Adicionar uma nova condição `elif page == "📊 Monitoramento":` para chamar a função `render_monitoramento(services)`.

### 5.3. Dependências (`src/presentation/streamlit_app/dependencies.py`)
- Registrar o novo `GetScraperRunsUseCase` no container de serviços para que possa ser injetado na `main.py`.

---

## 6. Exemplo de Código (View)

Um trecho de como a view `monitoramento.py` poderia ser estruturada:

```python
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_monitoramento(services):
    st.title("📊 Monitoramento de Scrapers")

    # 1. Obter dados e renderizar filtros
    all_sources = services['get_scraper_sources'].execute() # Supõe um novo use case

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        start_date = c1.date_input("Data Início", value=datetime.now() - timedelta(days=7))
        end_date = c2.date_input("Data Fim", value=datetime.now())
        selected_sources = c3.multiselect("Fontes", options=all_sources)

    # 2. Chamar use case com filtros
    runs_data = services['get_scraper_runs'].execute(
        start_date=start_date,
        end_date=end_date,
        sources=selected_sources
    )
    df = pd.DataFrame([vars(r) for r in runs_data])

    if df.empty:
        st.info("Nenhuma execução encontrada para os filtros selecionados.")
        return

    # 3. Calcular e renderizar KPIs, gráficos e tabela...
    # ... (lógica de UI com st.metric, st.bar_chart, st.dataframe)
```