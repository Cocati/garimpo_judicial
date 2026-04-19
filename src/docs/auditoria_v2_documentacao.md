# Documentação do Módulo de Análise de Leilão - Auditoria V2.0

## 📋 Visão Geral

O módulo `auditoria_v2.py` é o componente central do sistema de análise jurídica de leilões judiciais. Ele implementa um formulário completo de auditoria que permite ao especialista avaliar todos os aspectos de um leilão antes de tomar a decisão de participação.

### Funcionalidades Principais

- **Formulário estruturado em 6 abas** para organização da análise
- **Cálculo automático do Índice de Segurança Jurídica (ISJ)** de 0 a 100%
- **Motor de alertas** com níveis de criticidade
- **KPIs financeiros** para viabilidade econômica
- **Bloqueios automáticos** para nulidades críticas
- **Auto-save silencioso** para preservação de dados

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    auditoria_v2.py (View)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Tab 1-6    │  │  Sidebar     │  │  Cabeçalho   │      │
│  │  (Formulário)│  │  (Resultados)│  │  (Resumo)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                 │                                 │
│         ▼                 ▼                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              DetailedAnalysis (Model)                │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│         ┌─────────────────┼─────────────────┐               │
│         ▼                 ▼                 ▼               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │IsjCalculator │  │AlertasEngine │  │  Services    │      │
│  │  (Domínio)   │  │  (Component) │  │  (Use Cases) │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Componentes Integrados

| Componente | Arquivo | Função |
|------------|---------|--------|
| `DetailedAnalysis` | `domain/models.py` | Modelo de dados principal |
| `IsjCalculator` | `domain/isj_calculator.py` | Motor de cálculo do ISJ |
| `AlertasEngine` | `components/alertas_engine.py` | Geração de alertas visuais |
| `render_isj_gauge` | `components/isj_gauge.py` | Visualização do score ISJ |

---

## 📑 Abas do Formulário

### ⚖️ Aba 1: Processo Judicial

**Objetivo:** Análise do processo judicial e identificação de riscos processuais.

#### Bloco A: Dados Básicos

| Campo | Tipo | Modelo | Descrição |
|-------|------|--------|-----------|
| Nº Processo | `text_input` | `proc_num` | Número do processo judicial |
| Executados | `text_area` (lista) | `proc_executados` | Nomes dos executados, um por linha |
| Natureza da Execução | `selectbox` | `proc_natureza_execucao` | Definitiva ou Provisória |
| Espécie de Crédito | `selectbox` | `proc_especie_credito` | Condominial, Comum ou Trabalhista |

#### Bloco B: Financeiro do Processo

| Campo | Tipo | Modelo | Descrição |
|-------|------|--------|-----------|
| Débito Total (R$) | `number_input` | `proc_debito_atualizado` | Valor atualizado do débito |
| Avaliação do Imóvel (R$) | `number_input` | `vlr_avaliacao` | Valor de avaliação do bem |
| Proporcionalidade | `metric` (KPI) | Calculado | `(Débito / Avaliação) × 100` |

#### Bloco C: Checklist de Nulidades

| Campo | Tipo | Modelo | Valores | Impacto ISJ |
|-------|------|--------|---------|-------------|
| Réu foi devidamente citado? | `radio` | `proc_citacao` | Sim/Não/N/A | **BLOQUEIO** se False |
| Cônjuge Intimado? | `radio` | `proc_conjuge` | Sim/Não/N/A | -50 se NÃO |
| Executado possui Justiça Gratuita? | `toggle` | `proc_justica_gratuita` | True/False | -10 se True |
| Outros credores intimados? | `radio` | `proc_credores` | Sim/Não/N/A | -20 se False |
| Coproprietário intimado? | `radio` | `proc_coproprietario_intimado` | Sim/Não/N/A | -40 se False |
| Avaliação abrange 100% do imóvel? | `checkbox` | `proc_avaliacao_imovel` | True/False | Informativo |
| Existem recursos pendentes? | `toggle` | `proc_recursos` | True/False | -20 se True |

---

### 📜 Aba 2: Matrícula

**Objetivo:** Análise registral e verificação de gravames na matrícula do imóvel.

#### Coluna 1: Dados da Matrícula

| Campo | Tipo | Modelo | Descrição |
|-------|------|--------|-----------|
| Nº Matrícula | `text_input` | `mat_num` | Número da matrícula no cartório |
| Proprietários | `text_area` (lista) | `mat_proprietario` | Nomes dos proprietários, um por linha |
| Documentos dos Proprietários | `text_area` (lista) | `mat_documentos_proprietarios` | CPF/CNPJ, um por linha |
| Penhoras e Averbações | `text_area` (lista) | `mat_penhoras` | Penhoras (R-X) ou averbações (Av-X) |

#### Coluna 2: Ônus Relevantes

| Campo | Tipo | Modelo | Valores | Impacto ISJ |
|-------|------|--------|---------|-------------|
| Proprietário coincide com o Executado? | `radio` | `mat_prop_confere` | Sim/Não/N/A | **BLOQUEIO** se False |
| Penhora averbada na matrícula? | `radio` | `mat_penhora_averbada` | Sim/Não/N/A | Informativo |
| Possui Usufruto? | `radio` | `mat_usufruto` | Sim/Não/N/A | -60 se True |

#### Coluna 3: Características

| Campo | Tipo | Modelo | Valores | Impacto ISJ |
|-------|------|--------|---------|-------------|
| Proprietário tem cônjuge? | `radio` | `mat_conjugue` | Sim/Não/N/A | Informativo |
| Proprietário é Pessoa Jurídica? | `radio` | `mat_proprietario_pj` | Sim/Não/N/A | Informativo |
| Possui Indisponibilidade? | `radio` | `mat_indisp` | Sim/Não/N/A | -30 se True |

---

### 📝 Aba 3: Edital

**Objetivo:** Análise das regras e condições do edital de leilão.

| Campo | Tipo | Modelo | Descrição | Impacto ISJ |
|-------|------|--------|-----------|-------------|
| Descrição do Objeto | `text_input` | `edt_objeto` | Descrição do bem leiloado | Informativo |
| Data Avaliação | `date_input` | `edt_data_avaliacao` | Data da avaliação do imóvel | -10 se > 1 ano |
| Permite Parcelamento? | `toggle` | `edt_parcelamento` | Edital permite parcelamento | Info (alerta) |
| IPTU Sub-roga no preço? | `toggle` | `edt_iptu_subroga` | IPTU incluso no preço | -20 se False |
| Dívida Condomínio Clara? | `toggle` | `edt_condo_claro` | Dívida condominial transparente | -15 se False |
| % Mínimo 2ª Praça | `number_input` | `edt_percentual_minimo` | Percentual mínimo na 2ª praça | Informativo |

---

### 🏠 Aba 4: Situação

**Objetivo:** Análise da ocupação e estado de conservação do imóvel.

| Campo | Tipo | Modelo | Descrição |
|-------|------|--------|-----------|
| Status Ocupação | `selectbox` | `edt_posse_status` | Vago, Ocupado (Proprietário), Ocupado (Inquilino) ou Desconhecido |
| Est. Reforma (R$) | `number_input` | `custo_reforma` | Custo estimado de reforma |
| Est. Desocupação (R$) | `number_input` | `custo_desocupacao` | Custo estimado de desocupação |

---

### 💰 Aba 5: Financeiro

**Objetivo:** Análise de viabilidade econômica do investimento.

| Campo | Tipo | Modelo | Descrição |
|-------|------|--------|-----------|
| Lance Máximo Planejado (R$) | `number_input` | `fin_lance` | Valor máximo de lance |
| Valor de Venda (R$) | `number_input` | `valor_venda_estimado` | Valor estimado de revenda |
| Custos ITBI/Cartório (R$) | `number_input` | `fin_itbi` | Custos de transferência |
| Dívida Condomínio (R$) | `number_input` | `divida_condominio` | Dívida condominial existente |
| Dívida IPTU (R$) | `number_input` | `divida_iptu` | Dívida de IPTU existente |

---

### 🤖 Aba 6: Parecer

**Objetivo:** Conclusão do especialista sobre a análise.

| Campo | Tipo | Modelo | Descrição |
|-------|------|--------|-----------|
| Nível de Risco Global | `selectbox` | `risco_judicial` | Baixo, Médio ou Alto |
| Parecer Final & Próximos Passos | `text_area` | `analise_ia` | Texto livre com conclusão |

---

## 📊 Índice de Segurança Jurídica (ISJ)

### Visão Geral

O ISJ é um score de **0 a 100%** que indica a segurança jurídica do leilão. Quanto maior o score, menor o risco.

### Regras de Cálculo

#### Bloqueios Críticos (Score = 0)

| Campo | Condição | Motivo |
|-------|----------|--------|
| `proc_citacao` | `False` | Nulidade promissora - Réu não citado |
| `mat_prop_confere` | `False` | Erro de domínio - Proprietário difere do executado |

#### Deduções - Seção 1: Processo Judicial (Peso 40%)

| Campo | Condição | Dedução | Justificativa |
|-------|----------|---------|---------------|
| `proc_conjuge` | `NAO` | **-50** | Risco de meação/nulidade |
| `proc_coproprietario_intimado` | `False` | **-40** | Risco de embargos |
| `proc_natureza_execucao` | `PROVISORIA` | **-20** | Risco de reversão |
| `proc_recursos` | `True` | **-20** | Pode atrasar imissão na posse |
| `proc_credores` | `False` | **-20** | Credores não intimados |
| `proc_especie_credito` | `COMUM` | **-15** | Risco de impenhorabilidade |
| Proporcionalidade | `< 10%` | **-15** | Risco de preço vil |
| `proc_justica_gratuita` | `True` | **-10** | Facilita recursos protelatórios |

#### Deduções - Seção 2: Matrícula e Gravames

| Campo | Condição | Dedução | Justificativa |
|-------|----------|---------|---------------|
| `mat_usufruto` | `True` | **-60** | Impossibilidade de imissão na posse |
| `mat_indisp` | `True` | **-30** | Necessário pedido de baixa em cada juízo |

#### Deduções - Seção 3: Edital e Dívidas

| Campo | Condição | Dedução | Justificativa |
|-------|----------|---------|---------------|
| `edt_iptu_subroga` | `False` | **-20** | IPTU não incluso no preço |
| `edt_condo_claro` | `False` | **-15** | Dívida condominial obscura |
| `edt_data_avaliacao` | `> 365 dias` | **-10** | Avaliação defasada |

### Fórmula Final

```
Score = 100 - Σ(deduções)
Score = max(0, min(100, Score))
```

---

## 🚨 Motor de Alertas

### Níveis de Alerta

| Nível | Ícone | Cor | Condições |
|-------|-------|-----|-----------|
| **CRÍTICO** | 🚨 | Vermelho | Nulidades que impedem participação |
| **ALTO** | ⚠️ | Laranja | Riscos de demora ou custos extras |
| **MÉDIO** | ⚡ | Amarelo | Atenção necessária |
| **INFO** | ℹ️ | Azul | Informações relevantes |

### Alertas por Campo

| Campo | Condição | Nível | Mensagem |
|-------|----------|-------|----------|
| `proc_citacao` | `False` | CRÍTICO | NULIDADE PROMISSORA: Réu não citado |
| `mat_prop_confere` | `False` | CRÍTICO | ERRO DE DOMÍNIO: Proprietário difere do executado |
| `mat_usufruto` | `True` | ALTO | USUFRUTO ATIVO: Risco de impossibilidade de imissão |
| `proc_conjuge` | `NAO` | ALTO | CÔNJUGE NÃO INTIMADO: Risco de embargos |
| `mat_indisp` | `True` | ALTO | INDISPONIBILIDADE: Necessário pedido de baixa |
| `proc_recursos` | `True` | MÉDIO | RECURSOS PENDENTES: Leilão pode ser anulado |
| `edt_condo_claro` | `False` | MÉDIO | DÍVIDA CONDOMINIAL OBSCURA: Risco financeiro |
| `proc_justica_gratuita` | `True` | MÉDIO | JUSTIÇA GRATUITA: Dificuldade na recuperação |
| `edt_parcelamento` | `True` | INFO | PARCELAMENTO DISPONÍVEL |

---

## 💰 KPIs Financeiros

### Fórmulas de Cálculo

#### Investimento Total

```
Investimento = Lance 
             + Comissão Leiloeiro (5%)
             + ITBI/Cartório
             + Dívidas (IPTU + Condomínio + Outras)
             + Reforma
             + Desocupação
```

#### Lucro Líquido

```
Lucro = Venda Estimada 
      - Investimento Total 
      - Corretagem Venda (6%)
```

#### ROI Nominal

```
ROI = (Lucro Líquido / Investimento Total) × 100
```

#### Proporcionalidade do Débito

```
Proporcionalidade = (Débito Atualizado / Avaliação) × 100
```

### Indicadores na Sidebar

| Métrica | Fórmula | Interpretação |
|---------|---------|---------------|
| Lucro Líquido | Venda - Investimento - Corretagem | Verde se > 0 |
| ROI Estimado | (Lucro / Investimento) × 100 | Percentual de retorno |
| Investimento Total | Soma de todos os custos | Valor total necessário |

---

## 🔒 Regras de Bloqueio

### Condições de Bloqueio

O botão **"🚀 Finalizar"** é desabilitado quando:

1. **`proc_citacao = False`** - Réu não foi devidamente citado
2. **`mat_prop_confere = False`** - Proprietário da matrícula difere do executado

### Comportamento

- **Botão "💾 Salvar"**: Sempre habilitado (salva rascunho)
- **Botão "🚀 Finalizar"**: Desabilitado se houver bloqueio
- **Botão "🗑️ OUT"**: Sempre habilitado (descarta análise)

### Mensagem de Bloqueio

Quando bloqueado, exibe:
```
🚫 BLOQUEADO

Nulidade crítica detectada (Citação ou Propriedade).
```

---

## 🔄 Fluxo de Dados

### Ciclo de Vida da Análise

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Criar     │────▶│   Editar    │────▶│   Salvar    │
│  Análise    │     │   Campos    │     │  Rascunho   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Calcular   │
                    │  ISJ/KPIs   │
                    └─────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐          ┌─────────────┐
       │  Finalizar  │          │  Descartar  │
       │  (Participar)│          │   (OUT)     │
       └─────────────┘          └─────────────┘
```

### Persistência

- **Auto-save**: Executado silenciosamente a cada interação
- **Rascunho**: Salvo via `services['save_rascunho'].execute(analysis)`
- **Finalização**: Via `services['finalizar_auditoria'].execute(analysis, user_id)`
- **Descarte**: Via `services['descartar_auditoria'].execute(analysis, user_id)`

---

## 📝 Notas Técnicas

### Tratamento de Listas

Campos de lista (executados, proprietários, penhoras) são convertidos de/para strings multiline:

```python
# Entrada (text_area) → Lista
executados_str = "\n".join(analysis.proc_executados)
new_executados = st.text_area(...)
analysis.proc_executados = [x.strip() for x in new_executados.split('\n') if x.strip()]
```

### Mapeamento de Opções N/A

```python
def map_na_option(choice):
    mapping = {"Sim": True, "Não": False, "N/A": None}
    return mapping.get(choice)

def get_na_index(value):
    if value is True: return 0
    if value is False: return 1
    return 2  # N/A
```

### Estado da Sessão

```python
# Singleton no Session State
if "current_analysis" not in st.session_state or \
   st.session_state.current_analysis.id_leilao != id_leilao:
    analysis = services['repository'].get_detailed_analysis(...)
    st.session_state.current_analysis = analysis
```

---

## 🔗 Referências

- **Modelo de Dados**: `domain/models.py` → `DetailedAnalysis`
- **Cálculo ISJ**: `domain/isj_calculator.py` → `IsjCalculator`
- **Alertas**: `presentation/streamlit_app/components/alertas_engine.py` → `AlertasEngine`
- **Gauge Visual**: `presentation/streamlit_app/components/isj_gauge.py` → `render_isj_gauge`

---

*Documento gerado em 29/03/2026*
*Versão do módulo: 2.0*