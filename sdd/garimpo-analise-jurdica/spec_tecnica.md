# Spec Técnica — garimpo-analise-jurdica
## Módulo de Auditoria Jurídica e Score de Viabilidade (V2.0)

**Feature**: feat-001
**Criado**: 2026-02-27
**Status**: draft
**Modo**: Brownfield — extensão do sistema existente
**Stack**: Python · Streamlit · SQLAlchemy · PostgreSQL

---

## 1. Resumo Executivo

Esta feature **estende** o sistema existente de análise de leilões.
A tela atual de análise (`_render_detailed_analysis` em `carteira.py`) é substituída por um módulo estruturado com 6 seções, ISJ em tempo real, alertas automáticos e auto-save.

**Princípio de design**: Mínima ruptura com o existente.
- Tabela `leiloes_analise_detalhada` é estendida (novos campos, dados anteriores preservados)
- Arquitetura Clean Architecture existente é mantida (Domain → Application → Infra → Presentation)
- Nenhum serviço externo adicionado

---

## 2. Arquitetura

### Fluxo de Dados

```
Analista abre imóvel da carteira
        ↓
  [Presentation] auditoria_v2.py
  - Carrega dados existentes
  - Renderiza formulário 6 seções
  - Avalia alertas (AlertasEngine)
  - Calcula ISJ em tempo real (IsjCalculator)
  - Exibe Painel de Viabilidade
        ↓
  [Application] SaveAuditoriaRascunhoUseCase
  - Auto-save em cada interação
        ↓
  [Infrastructure] PostgresAuctionRepository
  - ON CONFLICT DO UPDATE (padrão existente)
        ↓
  [Database] leiloes_analise_detalhada
  - Tabela estendida com novos campos
        ↓
  [Application] FinalizarAuditoriaUseCase
  - Salva análise + atualiza status em leiloes_avaliacoes
```

### Camadas Afetadas

| Camada | Arquivo(s) | Mudança |
|--------|-----------|---------|
| Domain | `src/domain/models.py` | Estender `DetailedAnalysis` + novo `IsjCalculator` |
| Application | `src/application/use_cases.py` | Novos use cases de auditoria |
| Application | `src/application/interfaces.py` | Corrigir assinatura `get_stats()` + novos métodos |
| Infrastructure | `src/infra/database/models_sql.py` | Estender `LeilaoAnaliseDetalhadaModel` |
| Infrastructure | `src/infra/repositories/postgres_repo.py` | Métodos estendidos |
| Presentation | `src/presentation/streamlit_app/views/auditoria_v2.py` | **NOVO** — tela de auditoria |
| Presentation | `src/presentation/streamlit_app/components/isj_gauge.py` | **NOVO** — gauge ISJ |
| Presentation | `src/presentation/streamlit_app/components/alertas_engine.py` | **NOVO** — motor de alertas |
| Presentation | `src/presentation/streamlit_app/views/carteira.py` | Trocar chamada para `auditoria_v2.py` |
| Presentation | `src/presentation/streamlit_app/dependencies.py` | Registrar novos use cases |
| Database | `scripts/migration_001_auditoria_v2.sql` | **NOVO** — script de migração |

---

## 3. Decisões de Design

### DD-001: Extensão aditiva da tabela (não recriação)
**Decisão**: Adicionar ~45 novas colunas à tabela `leiloes_analise_detalhada` com `DEFAULT NULL`.
**Alternativa considerada**: Criar nova tabela `leiloes_auditoria_v2`.
**Rationale**: Manter a chave primária composta `(site, id_leilao)` existente. Zero perda de dados históricos. ON CONFLICT DO UPDATE já funciona com colunas adicionais.

### DD-002: Arrays como JSONB
**Decisão**: Campos de lista (executados, penhoras, proprietários) armazenados como `JSONB` no PostgreSQL.
**Alternativa considerada**: Tabelas separadas (ex: `leilao_executados`).
**Rationale**: Projeto local sem alta carga. JSONB evita 3 novas tabelas e JOINs extras. Consultas sobre esses campos serão raras (apenas leitura/escrita da análise completa).

### DD-003: ISJ calculado em runtime (não persistido como coluna)
**Decisão**: ISJ calculado pela classe `IsjCalculator` em memória durante exibição da tela.
**Alternativa considerada**: Persistir `isj_score` como coluna.
**Rationale**: ISJ é derivado dos campos já persistidos — não há dado novo a salvar. Recalcular em runtime garante que o score sempre reflita o estado atual dos campos, sem risco de ficar desatualizado.
**Exceção**: Se futuras funcionalidades precisarem ordenar/filtrar por ISJ, adicionar a coluna naquele momento.

### DD-004: Auto-save via re-run do Streamlit
**Decisão**: Usar o modelo reativo do Streamlit (re-run em cada interação) como mecanismo de auto-save.
**Rationale**: Streamlit não suporta debounce JavaScript nativo. A cada re-run (toda interação do usuário), o sistema verifica se houve mudança e persiste se necessário. Comportamento percebido pelo usuário é equivalente ao "salvo automaticamente".
**Implementação**: Comparar hash do estado atual com hash do último save. Se diferente, salvar.

### DD-005: Botão "Finalizar Auditoria" separado do auto-save
**Decisão**: Auto-save persiste como rascunho. "Finalizar Auditoria" é ação explícita que gera o parecer e muda o status do imóvel.
**Rationale**: Auto-save nunca deve mudar o status do imóvel (ANALISAR → PARTICIPAR/NO_BID) sem intenção explícita do analista.

### DD-006: View `auditoria_v2.py` substitui `_render_detailed_analysis`
**Decisão**: Criar novo arquivo `auditoria_v2.py` e redirecionar a chamada em `carteira.py`.
**Rationale**: Evitar modificar `carteira.py` além do mínimo necessário. A nova tela é autossuficiente.

---

## 4. Modelo de Dados

### 4.1 Extensão do Domínio: `DetailedAnalysis`

A dataclass `DetailedAnalysis` em `src/domain/models.py` recebe novos campos:

**Campos existentes mantidos** (sem alteração):
- `site`, `id_leilao`, `usuario_id`
- `parecer_juridico` → renomeado internamente para `analise_ia` (campo de texto livre)
- `risco_judicial`, `reu_citado`, `intimacao_credores`
- `divida_condominio`, `divida_iptu`, `divida_subroga`
- `ocupacao_status`, `valor_venda_estimado`, `custo_reforma`, `custo_desocupacao`
- `data_atualizacao`

**Novos campos — Seção 1: Processo Judicial**

| Campo | Tipo Python | Default |
|-------|-------------|---------|
| `proc_num` | `Optional[str]` | `None` |
| `proc_executados` | `List[str]` | `[]` |
| `proc_adv_exec` | `Optional[bool]` | `None` |
| `proc_citacao` | `Optional[bool]` | `None` |
| `proc_conjuge` | `Optional[str]` | `None` (`"S"/"N"/"N/A"`) |
| `proc_credores` | `Optional[bool]` | `None` |
| `proc_recursos` | `Optional[bool]` | `None` |
| `proc_recursos_obs` | `Optional[str]` | `None` |
| `proc_coproprietario_intimado` | `Optional[bool]` | `None` |
| `proc_natureza_execucao` | `Optional[str]` | `None` (`"Definitiva"/"Provisória"`) |
| `proc_justica_gratuita` | `Optional[bool]` | `None` |
| `proc_especie_credito` | `Optional[str]` | `None` (`"Condominial"/"Comum"/"Trabalhista"`) |
| `proc_debito_atualizado` | `float` | `0.0` |
| `proc_avaliacao_imovel` | `Optional[bool]` | `None` |

**Novos campos — Seção 2: Matrícula e Gravames**

| Campo | Tipo Python | Default |
|-------|-------------|---------|
| `mat_num` | `Optional[str]` | `None` |
| `mat_proprietario` | `List[str]` | `[]` |
| `mat_penhoras` | `List[str]` | `[]` |
| `mat_conjugue` | `Optional[bool]` | `None` |
| `mat_prop_confere` | `Optional[bool]` | `None` |
| `mat_proprietario_pj` | `Optional[bool]` | `None` |
| `mat_penhora_averbada` | `Optional[bool]` | `None` |
| `mat_usufruto` | `Optional[bool]` | `None` |
| `mat_indisp` | `Optional[bool]` | `None` |
| `mat_vagas_mat` | `Optional[bool]` | `None` |

**Novos campos — Seção 3: Edital e Dívidas**

| Campo | Tipo Python | Default |
|-------|-------------|---------|
| `edt_objeto` | `Optional[str]` | `None` (`"100%"/"50%"/"Outro"`) |
| `edt_vlr_avaliacao` | `float` | `0.0` |
| `edt_percentual_minimo` | `Optional[float]` | `None` |
| `edt_data_avaliacao` | `Optional[date]` | `None` |
| `edt_parcelamento` | `Optional[bool]` | `None` |
| `edt_iptu_subroga` | `Optional[bool]` | `None` |
| `edt_condo_claro` | `Optional[bool]` | `None` |

**Novos campos — Seção 4: Situação Física**

| Campo | Tipo Python | Default |
|-------|-------------|---------|
| `edt_posse_status` | `Optional[str]` | `None` |
| `edt_posse_estrategia` | `Optional[str]` | `None` |

**Novos campos — Seção 5: Financeiro**

| Campo | Tipo Python | Default |
|-------|-------------|---------|
| `fin_lance` | `float` | `0.0` |
| `fin_itbi` | `float` | `0.0` |
| `fin_dividas` | `float` | `0.0` |
| `recomendacao_ia` | `Optional[str]` | `None` |

> Nota: `fin_reforma` → usa `custo_reforma` existente. `fin_venda_est` → usa `valor_venda_estimado` existente. Nenhuma duplicação.

---

### 4.2 Novo Serviço de Domínio: `IsjCalculator`

**Arquivo**: `src/domain/isj_calculator.py`

Classe pura com método `calculate(analysis: DetailedAnalysis) -> float`.

**Regras de cálculo** (conforme PRD — seção 3.3):

| Condição | Dedução |
|----------|---------|
| `proc_citacao is False` | ISJ → 0% imediatamente |
| `mat_prop_confere is False` | ISJ → 0% imediatamente |
| `proc_conjuge == "N"` | -50% |
| `proc_natureza_execucao == "Provisória"` | -20% |
| `proc_especie_credito == "Comum"` | -15% |
| `proc_recursos is True` | -20% |
| `proc_justica_gratuita is True` | -10% |
| `proc_proporcionalidade < 10%` | -15% |
| `proc_coproprietario_intimado is False` | -40% |
| `proc_credores is False` | -20% |
| `mat_indisp is True` | -30% |
| `mat_usufruto is True` | -60% |
| `edt_condo_claro is False` | -15% |
| `edt_data_avaliacao > 1 ano atrás` | -10% |
| `edt_iptu_subroga is False` | -20% |

> Campos com valor `None` (não preenchidos) são ignorados no cálculo — não deduzem pontos.
> ISJ mínimo: 0%. ISJ máximo: 100%.

**Campos derivados calculados pelo `IsjCalculator`** (não persistidos):
- `proc_proporcionalidade`: `proc_debito_atualizado / edt_vlr_avaliacao * 100` (se `edt_vlr_avaliacao > 0`)
- `edt_fin_lance_minimo_aceitavel`: Preço Vil (conforme fórmula do PRD)
- `fin_comissao`: `fin_lance * 0.05`
- `investimento_total`: `fin_lance + fin_comissao + fin_itbi + fin_dividas + custo_reforma + (edt_vlr_avaliacao * 0.02)`
- `roi_nominal`: `((valor_venda_estimado - investimento_total) / investimento_total) * 100`

---

### 4.3 Motor de Alertas: `AlertasEngine`

**Arquivo**: `src/presentation/streamlit_app/components/alertas_engine.py`

Classe pura com método `avaliar(analysis: DetailedAnalysis) -> List[Alerta]`.

Retorna lista de `Alerta(nivel, mensagem, campo_gatilho)` com base nas 12 regras do PRD.

Níveis: `"critico"` | `"alto"` | `"medio"` | `"info"`.

---

### 4.4 Migração do Banco de Dados

**Arquivo**: `scripts/migration_001_auditoria_v2.sql`

Estratégia: `ALTER TABLE leiloes_analise_detalhada ADD COLUMN IF NOT EXISTS ...`

Todos os novos campos com `DEFAULT NULL` para preservar registros existentes.

Campos JSONB para arrays: `proc_executados JSONB DEFAULT '[]'::jsonb`

Campos booleanos com `DEFAULT NULL` (não `DEFAULT TRUE/FALSE`), para distinguir "não preenchido" de "respondido como Não".

> Rollback: não é necessário script de rollback para campos ADD COLUMN (colunas extras não afetam queries existentes).

---

## 5. Novos Use Cases

### `SaveAuditoriaRascunhoUseCase`

**Arquivo**: `src/application/use_cases.py`

| Aspecto | Detalhe |
|---------|---------|
| Input | `analysis: DetailedAnalysis` (parcialmente preenchido) |
| Operação | Upsert em `leiloes_analise_detalhada` com todos os novos campos |
| Sem efeito colateral | NÃO altera `leiloes_avaliacoes` (status) |
| Pattern | ON CONFLICT DO UPDATE (padrão já existente) |

### `FinalizarAuditoriaUseCase`

| Aspecto | Detalhe |
|---------|---------|
| Input | `analysis: DetailedAnalysis`, `isj_score: float` |
| Operação | (1) Salva análise completa; (2) Atualiza status via `update_status()` |
| Bloqueio | Não executa se `proc_citacao is False` OR `mat_prop_confere is False` |
| Status resultante | ISJ > 60%: `PARTICIPAR`; ISJ ≤ 60%: `NO_BID` |

---

## 6. Correção de Dívida Técnica (Incluída nesta Feature)

Conforme `DISCREPANCIES_REPORT.md`, corrigidos junto com a implementação:

| Issue | Correção |
|-------|---------|
| D-001: `get_stats()` sem `user_id` na interface | Atualizar `interfaces.py:27` |
| D-002: campos `data_1_praca`/`data_2_praca` duplicados | Remover linhas 30-31 de `models.py` |
| D-003: `_save_analysis()` não salva `divida_subroga`/`custo_desocupacao` | Corrigido via novo método |

> D-004 (dead code `GetPortfolio`) e D-005 (`tipo_leilao` não filtrado) ficam para feature separada.

---

## 7. Estrutura de Componentes da Tela

```
auditoria_v2.py
├── Header: ISJ gauge (isj_gauge.py)
├── Alertas ativos (alertas_engine.py → st.warning/st.error)
├── Tabs ou Seções:
│   ├── 1️⃣ Processo Judicial (14 campos)
│   ├── 2️⃣ Matrícula e Gravames (10 campos)
│   ├── 3️⃣ Edital e Dívidas (8 campos)
│   ├── 4️⃣ Situação Física (2 campos)
│   ├── 5️⃣ Business Case (6 campos + KPIs)
│   └── 6️⃣ Parecer do Analista (2 campos texto)
├── Painel Flutuante / Sidebar:
│   ├── ISJ: XX% (gauge colorido)
│   ├── Preço Vil: R$ XX
│   ├── Investimento Total: R$ XX
│   └── ROI Nominal: XX%
└── Footer:
    ├── "☁️ Alterações salvas automaticamente"  (auto-save status)
    ├── [💾 Salvar Rascunho] (botão explícito, redundante)
    └── [✅ Finalizar Auditoria] (habilitado/desabilitado por regra)
```

---

## 8. Interface de Repositório — Novos Métodos

Adicionados ao ABC `AuctionRepository` (`interfaces.py`):

| Método | Assinatura | Responsabilidade |
|--------|-----------|-----------------|
| `save_auditoria_rascunho` | `(analysis: DetailedAnalysis) → None` | Upsert com todos os novos campos |
| `finalizar_auditoria` | `(analysis: DetailedAnalysis, user_id: str, novo_status: str) → None` | Save + update_status |
| `get_stats` | `(user_id: str) → Dict` | Corrige assinatura existente |

---

## 9. Estratégia de Testes (MVP)

Conforme projeto tipo MVP: testes para caminhos críticos apenas.

| Teste | Tipo | Descrição |
|-------|------|-----------|
| `test_isj_calculator_nulidade_citacao` | Unit | proc_citacao=False → ISJ=0% |
| `test_isj_calculator_nulidade_dominio` | Unit | mat_prop_confere=False → ISJ=0% |
| `test_isj_calculator_deducoes_multiplas` | Unit | Vários campos negativos → ISJ correto |
| `test_isj_calculator_campos_nulos_ignorados` | Unit | Campos None não deduzem |
| `test_finalizar_auditoria_bloqueio_nulidade` | Unit | Use case lança exceção se citacao=False |
| `test_finalizar_auditoria_isj_alto_participa` | Unit | ISJ>60% → status PARTICIPAR |
| `test_finalizar_auditoria_isj_baixo_no_bid` | Unit | ISJ≤60% → status NO_BID |
| `test_alertas_engine_banner_vermelho_citacao` | Unit | Alerta crítico gerado para citacao=False |
| `test_save_rascunho_preserva_dados_existentes` | Unit | Upsert não apaga campos não enviados |

**Arquivos de teste**:
- `src/tests/unit/test_isj_calculator.py` (novo)
- `src/tests/unit/test_auditoria_use_cases.py` (novo)
- `src/tests/unit/test_alertas_engine.py` (novo)
- `src/tests/unit/test_use_cases.py` (existente — adicionar casos para `SaveAuditoriaRascunhoUseCase`)

---

## 10. Dependências

| Dependência | Status | Uso |
|-------------|--------|-----|
| PostgreSQL | ✅ Existente | Banco principal — extensão de tabela |
| SQLAlchemy | ✅ Existente | ORM — adição de colunas ao modelo |
| Streamlit | ✅ Existente | UI — novos componentes |
| `sqlalchemy.dialects.postgresql.JSONB` | ✅ Disponível | Arrays (executados, penhoras) |
| Nenhuma dependência nova | — | Zero `pip install` necessário |

---

## 11. Plano de Migração

### Ordem de execução (sem downtime)

```
1. Executar scripts/migration_001_auditoria_v2.sql
   → ALTER TABLE ADD COLUMN IF NOT EXISTS (todos os novos campos)
   → Operação aditiva, não bloqueia leituras/escritas existentes

2. Deploy do código (domain + application + infra + presentation)
   → Código novo lê novos campos (NULL para registros antigos)
   → Código antigo ignora novos campos (sem impacto)

3. Verificar: tela antiga ainda funciona para análises existentes
   → Rota antiga preservada até validação completa

4. Redirecionar carteira.py para auditoria_v2.py
   → Substituição final da tela de análise
```

### Dados existentes após migração

| Dado | Situação |
|------|---------|
| `parecer_juridico` antigo | Migrado como-está para `analise_ia` (campo Seção 6) |
| `reu_citado` antigo | Preservado; mapeado visualmente para `proc_citacao` na nova tela |
| `intimacao_credores` antigo | Preservado; mapeado para `proc_credores` |
| `ocupacao_status` antigo | Preservado; mapeado para `edt_posse_status` |
| Todos os outros campos novos | NULL (exibidos em branco na nova tela) |

---

## 12. Impacto em Funcionalidades Existentes

| Funcionalidade | Impacto |
|----------------|---------|
| UC-001: Triagem Rápida | ✅ Nenhum |
| UC-002: Filtros de Triagem | ✅ Nenhum |
| UC-003: Visualizar Carteira | ✅ Nenhum — cards inalterados |
| UC-004: Análise Detalhada | 🔄 Substituída por `auditoria_v2.py` |
| UC-005: Corrigir Dados Brutos | ✅ Nenhum — funcionalidade separada |
| UC-006: Dashboard de Produtividade | ✅ Nenhum |
| UC-007: Mover entre Estágios | ✅ Integrado ao `FinalizarAuditoriaUseCase` |
