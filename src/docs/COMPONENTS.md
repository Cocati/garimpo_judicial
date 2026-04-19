# COMPONENTS.md — Garimpo Judicial

> **Propósito deste documento:** Referência de contexto para desenvolvimento assistido por IA.
> Contém assinaturas exatas, nomes de campos, lógica de negócio e padrões arquiteturais do projeto.
> Mantenha atualizado ao adicionar ou modificar qualquer componente.

---

## VISÃO GERAL

**Projeto:** Garimpo Judicial — sistema de triagem, auditoria e gestão de portfólio de leilões judiciais.
**Stack:** Python · Streamlit · PostgreSQL · SQLAlchemy · Plotly
**Arquitetura:** Clean Architecture (Domain → Application → Infrastructure → Presentation)
**Diretório raiz:** `src/`

### Estrutura de Diretórios

```
src/
├── domain/
│   ├── models.py              # Entidades, enums e value objects
│   └── isj_calculator.py      # Motor de score ISJ
├── application/
│   ├── interfaces.py          # Contrato abstrato do repositório
│   └── use_cases.py           # Casos de uso (lógica de negócio)
├── infra/
│   ├── database/
│   │   ├── config.py          # Engine, SessionLocal, Base
│   │   └── models_sql.py      # Modelos SQLAlchemy (3 tabelas)
│   └── repositories/
│       └── postgres_repo.py   # Implementação PostgreSQL
├── presentation/
│   └── streamlit_app/
│       ├── main.py            # Entry point e roteamento
│       ├── dependencies.py    # Fábrica de serviços (cache)
│       ├── styles.py          # CSS inline
│       ├── components.py      # Sidebar e dashboard legados
│       ├── components/
│       │   ├── sidebar.py         # Filtros de triagem
│       │   ├── dashboard.py       # KPIs e gráficos
│       │   ├── triage_cards.py    # Cards de triagem
│       │   ├── triage_grid.py     # Grid de triagem (tabela)
│       │   ├── alertas_engine.py  # Gerador de alertas jurídicos
│       │   └── isj_gauge.py       # Visualização do score ISJ
│       └── views/
│           ├── carteira.py        # Gestão de portfólio (3 abas)
│           └── auditoria_v2.py    # Formulário de auditoria (6 abas)
└── tests/
    └── unit/
        ├── test_use_cases.py
        └── test_auditoria_use_cases.py
```

---

## 1. CAMADA DE DOMÍNIO (`domain/`)

### `domain/models.py`

Entidades de negócio puras. **Nenhuma dependência de framework.**

---

#### Enums

```python
class EvaluationStatus(str, Enum):
    PENDING    = "PENDING"     # Não avaliado na triagem
    ANALISAR   = "ANALISAR"    # Aprovado na triagem → aguarda auditoria
    PARTICIPAR = "PARTICIPAR"  # Aprovado na auditoria → apto para licitação
    DESCARTAR  = "DESCARTAR"   # Rejeitado na triagem rápida
    NO_BID     = "NO_BID"      # Rejeitado na auditoria detalhada

class RiskLevel(str, Enum):
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO  = "Alto"

class OccupationStatus(str, Enum):
    VAGO                 = "Vago"
    OCUPADO_PROPRIETARIO = "Ocupado (Proprietário)"
    OCUPADO_INQUILINO    = "Ocupado (Inquilino)"
    DESCONHECIDO         = "Desconhecido"

class ConjugeStatus(str, Enum):
    SIM = "S"    # Cônjuge existe e foi citado
    NAO = "N"    # Cônjuge não citado (risco)
    NA  = "N/A"  # Não aplicável

class NaturezaExecucao(str, Enum):
    DEFINITIVA  = "Definitiva"
    PROVISORIA  = "Provisória"   # Penalidade ISJ: −20%

class EspecieCredito(str, Enum):
    CONDOMINIAL = "Condominial"  # Penalidade ISJ: Nenhuma (preferencial)
    COMUM       = "Comum"        # Penalidade ISJ: −15%
    TRABALHISTA = "Trabalhista"  # Penalidade ISJ: Nenhuma (preferencial)
```

---

#### `Auction` (dataclass)

Entidade principal. Representa um leilão importado.

| Campo            | Tipo                        | Obrigatório |
|------------------|-----------------------------|-------------|
| `site`           | `str`                       | Sim         |
| `id_leilao`      | `str`                       | Sim         |
| `titulo`         | `str`                       | Sim         |
| `uf`             | `str`                       | Sim         |
| `cidade`         | `str`                       | Sim         |
| `tipo_leilao`    | `str`                       | Sim         |
| `tipo_bem`       | `str`                       | Sim         |
| `valor_1_praca`  | `float`                     | Sim         |
| `valor_2_praca`  | `float`                     | Sim         |
| `link_detalhe`   | `str`                       | Sim         |
| `imagem_capa`    | `str`                       | Sim         |
| `data_1_praca`   | `Optional[datetime]`        | Não         |
| `data_2_praca`   | `Optional[datetime]`        | Não         |
| `status_carteira`| `Optional[EvaluationStatus]`| Não         |

**Propriedades computadas:**
- `unique_id: str` → `f"{site}_{id_leilao}"`
- `data_ordenacao: datetime` → `max(data_1_praca, data_2_praca)` ou `datetime.max` se ausente

---

#### `AuctionFilter` (dataclass)

Todos os campos são `Optional[List[str]]`, default `None`.
Campos: `uf`, `cidade`, `tipo_bem`, `site`, `tipo_leilao`

---

#### `Evaluation` (dataclass)

Decisão de triagem do usuário.

| Campo          | Tipo                | Obrigatório |
|----------------|---------------------|-------------|
| `usuario_id`   | `str`               | Sim         |
| `site`         | `str`               | Sim         |
| `id_leilao`    | `str`               | Sim         |
| `avaliacao`    | `EvaluationStatus`  | Sim         |
| `data_analise` | `datetime`          | Sim         |

---

#### `DetailedAnalysis` (dataclass)

Auditoria detalhada. Organizada em 6 seções. Todos os campos são opcionais com defaults.

**Identificação:**
- `site: str = ""`, `id_leilao: str = ""`, `usuario_id: str = ""`

**Seção 1 — Processo Judicial** (prefixo `proc_`):

| Campo                       | Tipo                      | Default  | Penalidade ISJ |
|-----------------------------|---------------------------|----------|----------------|
| `proc_num`                  | `str`                     | `""`     | —              |
| `proc_executados`           | `List[str]`               | `[]`     | —              |
| `proc_adv_exec`             | `Optional[bool]`          | `None`   | —              |
| `proc_citacao`              | `bool`                    | `False`  | **Nulidade absoluta: score = 0** |
| `proc_conjuge`              | `ConjugeStatus`           | `NA`     | NAO → −50%     |
| `proc_credores`             | `bool`                    | `False`  | False → −20%   |
| `proc_recursos`             | `bool`                    | `False`  | True → −20%    |
| `proc_recursos_obs`         | `str`                     | `""`     | —              |
| `proc_coproprietario_intimado` | `bool`               | `True`   | False → −40%   |
| `proc_natureza_execucao`    | `NaturezaExecucao`        | `DEFINITIVA` | PROVISORIA → −20% |
| `proc_justica_gratuita`     | `bool`                    | `False`  | True → −10%    |
| `proc_especie_credito`      | `EspecieCredito`          | `CONDOMINIAL` | COMUM → −15% |
| `proc_debito_atualizado`    | `float`                   | `0.0`    | —              |
| `proc_avaliacao_imovel`     | `bool`                    | `True`   | —              |
| `vlr_avaliacao`             | `float`                   | `0.0`    | —              |

**Seção 2 — Matrícula / Registro** (prefixo `mat_`):

| Campo                    | Tipo         | Default  | Penalidade ISJ |
|--------------------------|--------------|----------|----------------|
| `mat_num`                | `str`        | `""`     | —              |
| `mat_proprietario`       | `List[str]`  | `[]`     | —              |
| `mat_documentos_proprietarios` | `List[str]` | `[]` | —              |
| `mat_penhoras`           | `List[str]`  | `[]`     | —              |
| `mat_conjugue`           | `Optional[bool]` | `None`   | —              |
| `mat_prop_confere`       | `bool`       | `True`   | **False → score = 0** |
| `mat_proprietario_pj`    | `bool`       | `False`  | —              |
| `mat_penhora_averbada`   | `bool`       | `True`   | —              |
| `mat_usufruto`           | `bool`       | `False`  | True → −60%    |
| `mat_indisp`             | `bool`       | `False`  | True → −30%    |
| `mat_vagas_mat`          | `Optional[bool]` | `None`   | —              |

**Seção 3 — Edital / Débitos** (prefixo `edt_`):

| Campo                    | Tipo           | Default   | Penalidade ISJ       |
|--------------------------|----------------|-----------|----------------------|
| `edt_objeto`             | `str`          | `""`      | —                    |
| `edt_vlr_avaliacao`      | `float`        | `0.0`     | —                    |
| `edt_percentual_minimo`  | `float`        | `0.0`     | —                    |
| `edt_data_avaliacao`     | `Optional[date]` | `None`  | >1 ano atrás → −10%  |
| `edt_parcelamento`       | `bool`         | `False`   | —                    |
| `edt_iptu_subroga`       | `bool`         | `True`    | False → −20%         |
| `edt_condo_claro`        | `bool`         | `True`    | False → −15%         |

**Seção 4 — Situação Física / Posse:**

| Campo                 | Tipo             | Default        |
|-----------------------|------------------|----------------|
| `edt_posse_status`    | `OccupationStatus` | `DESCONHECIDO` |

**Seção 5 — Financeiro** (prefixo `fin_`):

| Campo                  | Tipo    | Default |
|------------------------|---------|---------|
| `fin_lance`            | `float` | `0.0`   |
| `fin_itbi`             | `float` | `0.0`   |
| `fin_dividas`          | `float` | `0.0`   |
| `recomendacao_ia`      | `str`   | `""`    |

**Seção 6 — Legado / Compatibilidade:**

| Campo                  | Tipo            | Default        |
|------------------------|-----------------|----------------|
| `analise_ia`           | `str`           | `""`           |
| `risco_judicial`       | `RiskLevel`     | `BAIXO`        |
| `valor_venda_estimado` | `float`         | `0.0`          |
| `custo_reforma`        | `float`         | `0.0`          |
| `custo_desocupacao`    | `float`         | `0.0`          |
| `divida_condominio`    | `float`         | `0.0`          |
| `divida_iptu`          | `float`         | `0.0`          |
| `divida_subroga`       | `bool`          | `False`        |

**Propriedades computadas:**
- `reu_citado: bool` → getter de `proc_citacao`
- `intimacao_credores: bool` → getter de `proc_credores`
- `proc_proporcionalidade: float` → `proc_debito_atualizado / vlr_avaliacao` (0 se denominador = 0)

---

### `domain/isj_calculator.py`

**ISJ = Índice de Segurança Jurídica** — score de 0 a 100.

#### `IsjCalculator.calculate(analysis: DetailedAnalysis) -> float`

**Nulidades absolutas** (retorna 0.0 imediatamente):
- `proc_citacao == False`
- `mat_prop_confere == False`

**Sistema de deduções** (aplicadas ao score base 100):

| Condição                                          | Penalidade |
|---------------------------------------------------|------------|
| `proc_conjuge == NAO`                             | −50%       |
| `proc_natureza_execucao == PROVISORIA`            | −20%       |
| `proc_especie_credito == COMUM`                   | −15%       |
| `proc_recursos == True`                           | −20%       |
| `proc_justica_gratuita == True`                   | −10%       |
| `proc_credores == False`                          | −20%       |
| `proc_coproprietario_intimado == False`           | −40%       |
| `proc_proporcionalidade < 0.10`                   | −15%       |
| `mat_indisp == True`                              | −30%       |
| `mat_usufruto == True`                            | −60%       |
| `edt_condo_claro == False`                        | −15%       |
| `edt_iptu_subroga == False`                       | −20%       |
| `edt_data_avaliacao > 1 ano atrás`                | −10%       |

Score final normalizado para intervalo [0, 100].

#### `IsjCalculator.calculate_financial_kpis(analysis: DetailedAnalysis) -> Dict[str, float]`

Retorna:
- `investimento_total`: `fin_lance + fin_itbi + comissao_leilao (5%) + corretagem (6%) + taxa_condo + divida_iptu + custo_reforma + custo_desocupacao`
- `lucro_liquido`: `valor_venda_estimado − investimento_total`
- `roi_nominal`: `lucro_liquido / investimento_total`
- `proporcionalidade_debito`: `proc_debito_atualizado / vlr_avaliacao`

---

## 2. CAMADA DE APLICAÇÃO (`application/`)

### `application/interfaces.py`

```python
class AuctionRepository(ABC):
    def get_pending_auctions(self, user_id: str, filters: AuctionFilter) -> List[Auction]: ...
    def save_evaluations(self, evaluations: List[Evaluation]) -> int: ...
    def get_stats(self, user_id: str) -> dict: ...
    def save_auditoria_rascunho(self, analysis: DetailedAnalysis) -> None: ...
    def get_detailed_analysis(self, site: str, id_leilao: str, user_id: str) -> Optional[DetailedAnalysis]: ...
    def update_status(self, user_id: str, site: str, id_leilao: str, new_status: EvaluationStatus) -> None: ...
```

---

### `application/use_cases.py`

Todos os casos de uso recebem o repositório via construtor.

| Caso de Uso                       | Método `execute()`                                              | Retorno              |
|------------------------------------|-----------------------------------------------------------------|----------------------|
| `GetPendingAuctionsUseCase`        | `(user_id, uf, cidade, tipo_bem, site)`                        | `List[Auction]`      |
| `GetPortfolioAuctionsUseCase`      | `(user_id)`                                                    | `List[Auction]`      |
| `GetDetailedAnalysisUseCase`       | `(user_id, site, id_leilao)`                                   | `DetailedAnalysis`   |
| `SaveDetailedAnalysisUseCase`      | `(analysis: DetailedAnalysis)`                                 | `None`               |
| `SaveAuditoriaRascunhoUseCase`     | `(analysis: DetailedAnalysis)`                                 | `None`               |
| `SubmitBatchEvaluationUseCase`     | `(user_id, items: List[dict], decision: EvaluationStatus)`     | `int` (count)        |
| `GetFilterOptionsUseCase`          | `()`                                                           | `dict`               |
| `GetUserStatsUseCase`              | `(user_id)`                                                    | `Dict[str, int]`     |
| `FinalizarAuditoriaUseCase`        | `(analysis: DetailedAnalysis, user_id: str)`             | `EvaluationStatus`   |
| `DescartarAuditoriaUseCase`        | `(analysis: DetailedAnalysis, user_id: str)`             | `None`               |

**`FinalizarAuditoriaUseCase.execute()` — lógica completa:**
1. Valida nulidades AC-2 (`proc_citacao`) e AC-3 (`mat_prop_confere`)
2. Se nulidade → lança exceção ou retorna `NO_BID`
3. Calcula ISJ via `IsjCalculator.calculate(analysis)`
4. Se ISJ > 60 → status = `PARTICIPAR`; caso contrário → `NO_BID`
5. Chama `repo.update_status(user_id=analysis.user_id, site=analysis.site, id_leilao=analysis.id_leilao, new_status=status)`
6. Retorna o status final

**`GetUserStatsUseCase.execute()` — retorno:**
```python
{"analisar": int, "descartar": int, "total_processado": int}
```

---

## 3. CAMADA DE INFRAESTRUTURA (`infra/`)

### `infra/database/config.py`

```python
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
# ⚠️ Hardcoded — usar variável de ambiente em produção

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

def get_db():  # gerador para injeção de dependência
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### `infra/database/models_sql.py`

#### Tabela `leiloes_analiticos` → `LeilaoAnaliticoModel`

PK: `id_registro_bruto` (Integer, auto-increment)
Campos: `site`, `id_leilao`, `titulo`, `uf`, `cidade`, `tipo_leilao`, `tipo_bem`, `valor_1_praca` (Numeric), `valor_2_praca` (Numeric), `link_detalhe`, `imagem_capa`, `data_1_praca` (DateTime, nullable), `data_2_praca` (DateTime, nullable)

#### Tabela `leiloes_avaliacoes` → `LeilaoAvaliacaoModel`

PK composta: `(usuario_id, site, id_leilao)`
Campos adicionais: `id_registro_bruto` (FK), `avaliacao` (String), `data_analise` (DateTime), `updated_at` (DateTime)

#### Tabela `leiloes_analise_detalhada` → `LeilaoAnaliseDetalhadaModel`

PK composta: `(site, id_leilao, usuario_id)`
Campos: todos os campos de `DetailedAnalysis`
**Campos JSONB** (listas Python → JSON no banco): `proc_executados`, `mat_proprietario`, `mat_penhoras`

---

### `infra/repositories/postgres_repo.py`

#### `PostgresAuctionRepository`

| Método                         | Descrição                                                                           |
|--------------------------------|-------------------------------------------------------------------------------------|
| `get_pending_auctions()`       | LEFT OUTER JOIN exclui avaliados; `LIMIT 100`; ordena por `id_registro_bruto DESC` |
| `save_evaluations()`           | `session.merge()` em lote + `commit()`; retorna count                              |
| `get_filter_options()`         | Queries `DISTINCT` em `leiloes_analiticos`; retorna `{ufs, cidades, tipos, sites}` |
| `get_stats()`                  | `GROUP BY avaliacao`; retorna contagens por status                                 |
| `get_portfolio_auctions()`     | JOIN filtrando `ANALISAR`, `PARTICIPAR`, `NO_BID`                                  |
| `save_auditoria_rascunho()`    | `INSERT ... ON CONFLICT (site, id_leilao, usuario_id) DO UPDATE SET ...`           |
| `get_detailed_analysis()`      | Busca por PK composta; converte enums; faz parse seguro de listas JSON             |
| `get_auction()`                | Busca dados do cabeçalho do leilão por `(site, id_leilao)`                         |
| `update_status()`              | SQL `UPDATE` direto com timestamp                                                  |
| `update_auction_core_data()`   | Corrige `titulo`, `valor_1_praca`, `valor_2_praca`, `data_1_praca`, `data_2_praca` |
| `_map_to_domain()`             | Converte `LeilaoAnaliticoModel` → `Auction`                                        |

---

## 4. CAMADA DE APRESENTAÇÃO (`presentation/streamlit_app/`)

### `main.py` — Entry Point

- **Config Streamlit:** tema dark, layout wide, sidebar expandida
- **Usuário mock:** `st.session_state.user_id = "Julio"` *(⚠️ hardcoded)*
- **Navegação:** radio na sidebar → `"🔍 Triagem Rápida"` | `"📁 Minha Carteira"`
- **Sidebar stats:** exibe `total_processado` e `analisar` count

**Fluxo da página de Triagem:**
1. `get_filters.execute()` → popula dropdowns
2. `render_sidebar()` → retorna filtros selecionados
3. `get_auctions.execute(user_id, **filtros)` → lista de Auction
4. `render_dashboard(df, stats)` → KPIs e gráficos
5. `render_triage_cards(df)` → retorna decisões dict
6. Botão "Processar Lote" → `submit_eval.execute(user_id, items, decision)`

---

### `dependencies.py` — Fábrica de Serviços

Função `get_services()` decorada com `@st.cache_resource`.

```python
{
    "repository":            PostgresAuctionRepository(db),
    "get_filters":           GetFilterOptionsUseCase(repo),
    "get_stats":             GetUserStatsUseCase(repo),
    "get_auctions":          GetPendingAuctionsUseCase(repo),
    "submit_eval":           SubmitBatchEvaluationUseCase(repo),
    "get_portfolio_auctions": GetPortfolioAuctionsUseCase(repo),
    "save_rascunho":         SaveAuditoriaRascunhoUseCase(repo),
    "finalizar_auditoria":   FinalizarAuditoriaUseCase(repo),
}
```

---

### `components/sidebar.py`

```python
def render_sidebar(
    unique_ufs: List[str],
    unique_cities: List[str],
    unique_types: List[str],
    unique_sites: List[str]
) -> Dict[str, Any]:
    # Retorna: {"uf": list|None, "cidade": list|None, "tipo_bem": list|None, "site": list|None}
```

---

### `components/dashboard.py`

```python
def render_dashboard(df: pd.DataFrame, stats_history: dict) -> None:
    # 4 KPIs: Pendentes, Volume (1ª Praça), Descartados, Para Análise
    # 2 Donut charts Plotly: Distribuição por Tipo | Top Leiloeiros
```

---

### `components/triage_cards.py`

```python
def render_triage_cards(df: pd.DataFrame) -> dict:
    # Exibe até 15 cards em layout 3 colunas: [imagem | info | decisão]
    # Cada card: titulo, site, valores, link ao edital
    # Radio: "Pendente" | "Analisar" | "Descartar"
    # Retorna: {id_leilao: "Pendente"|"Analisar"|"Descartar", ...}
```

CSS inline: `height: 220px; object-fit: cover` nas imagens.

---

### `components/triage_grid.py`

```python
def render_triage_grid(df: pd.DataFrame) -> pd.DataFrame:
    # st.data_editor com coluna "decisao" editável (dropdown)
    # Colunas: imagem_capa, titulo, valor_1_praca, valor_2_praca, link_detalhe, site, id_leilao, decisao
    # Altura: (n_rows * 150) + 42 px
    # Retorna DataFrame com coluna "decisao" preenchida
```

---

### `components/alertas_engine.py`

```python
@dataclass
class Alerta:
    nivel: str          # "critico" | "alto" | "medio" | "info"
    mensagem: str
    campo_gatilho: str

class AlertasEngine:
    @staticmethod
    def avaliar(analysis: DetailedAnalysis) -> List[Alerta]:
        # CRÍTICO: proc_citacao=False, mat_prop_confere=False
        # ALTO: mat_usufruto=True, proc_conjuge=NAO, mat_indisp=True
        # MÉDIO: proc_recursos=True, edt_condo_claro=False, proc_justica_gratuita=True
        # INFO: edt_parcelamento=True
```

---

### `components/isj_gauge.py`

```python
def render_isj_gauge(isj_score: float, alertas: List[Alerta]) -> None:
    # Barra de progresso colorida:
    #   verde  se isj_score > 80
    #   laranja se 60 ≤ isj_score ≤ 80
    #   vermelho se isj_score < 60
    # Mostra parecer preliminar e contagem de alertas por nível
```

---

### `views/carteira.py` — Portfólio

```python
def render_carteira(services: dict, user_id: str) -> None:
```

**Estados de navegação interna** (`st.session_state`):
- `st.session_state.carteira_page` → `"listagem"` | `"editar_dados_brutos"` | `"auditoria_v2"`
- `st.session_state.selected_site` / `selected_id_leilao` → leilão em foco

**Funções internas:**

`_render_portfolio_list()` — 3 abas:
| Aba             | Status filtrado   | Botão principal           |
|-----------------|-------------------|---------------------------|
| 📥 A Analisar   | `ANALISAR`        | "Avaliar 📝"              |
| 🚀 Participar   | `PARTICIPAR`      | "Ver Detalhes 🔍"         |
| 🗑️ Descartados  | `NO_BID`          | "Revisar 📂"              |

`_render_card(auction, suffix, is_participating, is_readonly)` — layout 3 colunas:
- Col 1: imagem de capa
- Col 2: titulo, localização (cidade/UF/site), datas e valores das praças
- Col 3: botão ✏️ (editar dados) + botão de ação principal

`_render_edit_source_data()` — formulário de correção de scraping:
- Campos: `titulo`, `valor_1_praca`, `valor_2_praca`, `data_1_praca`, `data_2_praca`
- Link ao edital para verificação
- `repo.update_auction_core_data()` no submit

---

### `views/auditoria_v2.py` — Auditoria Detalhada (6 abas)

```python
def render_auditoria_v2(services: dict, user_id: str, site: str, id_leilao: str) -> None:
```

**Header:** imagem, titulo, datas, valor de avaliação, link ao edital.

**Sidebar durante auditoria:**
- ISJ gauge em tempo real (`IsjCalculator.calculate()`)
- KPIs financeiros: lucro_liquido, roi_nominal, investimento_total
- Botão 💾 "Salvar Rascunho" → `save_rascunho.execute(analysis)`
- Botão ✅ "Finalizar Auditoria" → `finalizar_auditoria.execute(analysis)` (bloqueado se nulidade)

**Abas:**

| Aba | Prefixo | Campos principais |
|-----|---------|-------------------|
| 1 — Processo | `proc_` | num, executados, natureza_execucao, especie_credito, debito_atualizado, vlr_avaliacao, citacao, conjuge, credores, coproprietario, recursos, justica_gratuita |
| 2 — Matrícula | `mat_` | num, proprietario, penhoras, prop_confere, proprietario_pj, usufruto, indisp, penhora_averbada, vagas_mat |
| 3 — Edital | `edt_` | objeto, vlr_avaliacao, data_avaliacao, percentual_minimo, parcelamento, iptu_subroga, condo_claro |
| 4 — Situação | `edt_posse_` | status (OccupationStatus), estrategia; custo_reforma, custo_desocupacao |
| 5 — Financeiro | `fin_` | lance, itbi, dividas, valor_venda_estimado |
| 6 — Parecer | — | risco_judicial (RiskLevel), analise_ia (textarea), recomendacao_ia |

**Auto-save:** cada campo dispara `save_rascunho.execute()` via callback.

---

## 5. BANCO DE DADOS

### Diagrama de Tabelas

```
leiloes_analiticos                leiloes_avaliacoes           leiloes_analise_detalhada
──────────────────                ──────────────────           ─────────────────────────
id_registro_bruto (PK)  ◄──FK──  id_registro_bruto            site          (PK 1/3)
site                              site          (PK 1/3) ──►  id_leilao     (PK 2/3)
id_leilao                         id_leilao     (PK 2/3)      usuario_id    (PK 3/3)
titulo                            usuario_id    (PK 3/3)      [todos campos DetailedAnalysis]
uf                                avaliacao                    [JSONB: proc_executados,
cidade                            data_analise                  mat_proprietario, mat_penhoras]
tipo_leilao                       updated_at
tipo_bem
valor_1_praca
valor_2_praca
data_1_praca
data_2_praca
link_detalhe
imagem_capa
```

### Padrões de Persistência

| Operação        | Padrão                                          | Arquivo                  |
|-----------------|-------------------------------------------------|--------------------------|
| Triagem (batch) | `session.merge()` + `commit()`                  | `postgres_repo.py`       |
| Rascunho audit. | `INSERT ... ON CONFLICT DO UPDATE`              | `postgres_repo.py`       |
| Correção dados  | UPDATE direto via `update_auction_core_data()`  | `postgres_repo.py`       |
| Status change   | UPDATE direto via `update_status()`             | `postgres_repo.py`       |

---

## 6. TESTES

### `tests/unit/test_use_cases.py`

| Teste | O que valida |
|-------|-------------|
| `test_get_pending_auctions_should_call_repository_with_correct_filters` | Filtros repassados corretamente ao repo |
| `test_submit_batch_evaluation_should_create_evaluations_correctly` | Conversão de dict → `Evaluation` |
| `test_get_portfolio_should_isolate_domain_from_infrastructure` | Isolamento do domínio |

### `tests/unit/test_auditoria_use_cases.py`

Testes adicionais cobrindo os casos de uso de auditoria.

**Padrão de todos os testes:** `Mock(spec=AuctionRepository)` + `assert_called_once_with()` / assert em retorno.

## 6. DDL TABLE

### `public.leiloes_analise_detalhada`

```
CREATE TABLE public.leiloes_analise_detalhada (
	site varchar NOT NULL,
	id_leilao varchar NOT NULL,
	usuario_id varchar NOT NULL,
	parecer_juridico text NULL,
	risco_judicial varchar DEFAULT 'Baixo'::character varying NULL,
	reu_citado bool DEFAULT true NULL,
	intimacao_credores bool DEFAULT true NULL,
	divida_condominio float8 DEFAULT 0.0 NULL,
	divida_iptu float8 DEFAULT 0.0 NULL,
	divida_subroga bool DEFAULT true NULL,
	ocupacao_status varchar DEFAULT 'Vago'::character varying NULL,
	valor_venda_estimado float8 DEFAULT 0.0 NULL,
	custo_reforma float8 DEFAULT 0.0 NULL,
	custo_desocupacao float8 DEFAULT 0.0 NULL,
	data_atualizacao timestamp NULL,
	proc_num varchar(50) DEFAULT NULL::character varying NULL,
	proc_executados jsonb DEFAULT '[]'::jsonb NULL,
	proc_adv_exec bool NULL,
	proc_citacao bool NULL,
	proc_conjuge varchar(10) DEFAULT NULL::character varying NULL,
	proc_credores bool NULL,
	proc_recursos bool NULL,
	proc_recursos_obs text NULL,
	proc_coproprietario_intimado bool NULL,
	proc_natureza_execucao varchar(50) DEFAULT NULL::character varying NULL,
	proc_justica_gratuita bool NULL,
	proc_especie_credito varchar(50) DEFAULT NULL::character varying NULL,
	proc_debito_atualizado numeric(15, 2) DEFAULT 0.00 NULL,
	proc_avaliacao_imovel bool NULL,
	
	mat_num varchar(50) DEFAULT NULL::character varying NULL,
	mat_proprietario jsonb DEFAULT '[]'::jsonb NULL,
	mat_penhoras jsonb DEFAULT '[]'::jsonb NULL,
	mat_conjugue bool NULL,
	mat_prop_confere bool NULL,
	mat_proprietario_pj bool NULL,
	mat_penhora_averbada bool NULL,
	mat_usufruto bool NULL,
	mat_indisp bool NULL,
	mat_vagas_mat bool NULL,
	edt_objeto varchar(255) DEFAULT NULL::character varying NULL,
	edt_vlr_avaliacao numeric(15, 2) DEFAULT 0.00 NULL,
	edt_percentual_minimo numeric(5, 2) DEFAULT NULL::numeric NULL,
	edt_data_avaliacao date NULL,
	edt_parcelamento bool NULL,
	edt_iptu_subroga bool NULL,
	edt_condo_claro bool NULL,
	edt_posse_status varchar(50) DEFAULT NULL::character varying NULL,
	edt_posse_estrategia varchar(50) DEFAULT NULL::character varying NULL,
	fin_lance numeric(15, 2) DEFAULT 0.00 NULL,
	fin_itbi numeric(15, 2) DEFAULT 0.00 NULL,
	fin_dividas numeric(15, 2) DEFAULT 0.00 NULL,
	recomendacao_ia text NULL,
	vlr_avaliacao float8 DEFAULT 0.0 NULL,
	mat_documentos_proprietarios jsonb DEFAULT '[]'::jsonb NULL,
	CONSTRAINT leiloes_analise_detalhada_pkey PRIMARY KEY (site, id_leilao, usuario_id)
);
```


---

## 8. CICLO DE VIDA DE UM LEILÃO

```
[Importado via scraping]
         ↓
     PENDING
         │
    Triagem Rápida
    ┌────┴────┐
    ▼         ▼
ANALISAR   DESCARTAR (fim)
    │
    │  Auditoria Detalhada (auditoria_v2)
    │  ISJ calculado automaticamente
    ┌────┴──────────────┐
    ▼                   ▼
PARTICIPAR            NO_BID (fim)
(ISJ > 60%)          (ISJ ≤ 60% ou nulidade)
```

**Nulidades absolutas** (ISJ = 0, finalização bloqueada):
- `proc_citacao == False` (AC-2)
- `mat_prop_confere == False` (AC-3)

---

## 9. CONVENÇÕES DO PROJETO

| Convenção | Descrição |
|-----------|-----------|
| Prefixo `proc_` | Campos do processo judicial |
| Prefixo `mat_` | Campos da matrícula/registro |
| Prefixo `edt_` | Campos do edital e débitos |
| Prefixo `fin_` | Campos financeiros |
| JSONB no banco | Listas Python (`proc_executados`, `mat_proprietario`, `mat_penhoras`) |
| Cache Streamlit | `@st.cache_resource` para repositório e serviços |
| Upsert nativo | `ON CONFLICT DO UPDATE` para auditoria |
| Merge SQLAlchemy | `session.merge()` para avaliações em lote |
| Session state keys | `carteira_page`, `selected_site`, `selected_id_leilao`, `user_id` |
