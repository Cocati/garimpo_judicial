# Especificação das Abas - Auditoria V2.0

## Visão Geral

O formulário de Auditoria Jurídica V2.0 possui **6 abas principais** além do **Cabeçalho** e da **Sidebar de Resultados**.

---

## 📍 Cabeçalho (Resumo Visual)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `imagem_capa` | Image | Imagem de capa do leilão |
| `titulo` | String | Título do leilão |
| `data_1_praca` | Date | Data da 1ª Praça |
| `data_2_praca` | Date | Data da 2ª Praça |
| `valor_1_praca` | Float | Valor da 1ª Praça (R$) |
| `valor_2_praca` | Float | Valor da 2ª Praça (R$) |
| `link_detalhe` | URL | Link para o edital |

---

## ⚖️ Aba 1: Processo Judicial

**Descrição:** Análise do Processo Judicial e Riscos Processuais

### Bloco A: Dados Básicos e Executados

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Observações |
|-------|----------|-------------|------------|-----|-------------|
| Nº Processo | `proc_num` | `text_input` | `string` | `k_proc_num` | - |
| Executados | `proc_executados` | `text_area` | `list[string]` | `k_proc_execs` | Conversão: string multilinhas ↔ lista |
| Natureza da Execução | `proc_natureza_execucao` | `selectbox` | `NaturezaExecucao` (enum) | `k_proc_nat` | Enum do domínio |
| Espécie de Crédito | `proc_especie_credito` | `selectbox` | `EspecieCredito` (enum) | `k_proc_esp` | Default: Comum |

### Bloco B: Financeiro do Processo & Proporcionalidade

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Observações |
|-------|----------|-------------|------------|-----|-------------|
| Débito Total | `proc_debito_atualizado` | `number_input` | `float` | `k_proc_deb` | Valor em R$ |
| Avaliação do Imóvel | `vlr_avaliacao` | `number_input` | `float` | `k_proc_aval` | Sincronizado globalmente |
| Proporcionalidade | - | `metric` | `float` | - | **Calculado:** (débito/avaliação)×100 |

### Bloco C: Checklist de Nulidades

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Opções | Observações |
|-------|----------|-------------|------------|-----|--------|-------------|
| Réu Citado? | `proc_citacao` | `radio` | `bool\|None` | `k_citacao` | Sim/Não/N/A | **CRÍTICO** - Bloqueia finalização |
| Cônjuge Intimado? | `proc_conjuge` | `radio` | `bool\|None` | `k_conjuge` | Sim/Não/N/A | - |
| Justiça Gratuita | `proc_justica_gratuita` | `toggle` | `bool` | `k_proc_jg` | - | Aumenta risco de recursos |
| Outros Credores | `proc_credores` | `radio` | `bool\|None` | `k_cred` | Sim/Não/N/A | - |
| Coproprietário Intimado? | `proc_coproprietario_intimado` | `radio` | `bool\|None` | `k_coprop` | Sim/Não/N/A | - |
| Avaliação 100% | `proc_avaliacao_imovel` | `checkbox` | `bool` | `k_aval_full` | - | - |
| Recursos Pendentes | `proc_recursos` | `toggle` | `bool` | `k_rec` | - | - |
| Detalhe Recursos | `proc_recursos_obs` | `text_area` | `string` | - | - | Condicional: exibido se `proc_recursos=True` |

---

## 📜 Aba 2: Matrícula

**Descrição:** Análise Registral e Verificação de Matrícula

### Coluna 1 (2/4 da largura)

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Observações |
|-------|----------|-------------|------------|-----|-------------|
| Nº Matrícula | `mat_num` | `text_input` | `string` | `k_mat_num` | - |
| Proprietários | `mat_proprietario` | `text_area` | `list[string]` | `input_mat_proprietario` | Conversão: string multilinhas ↔ lista |
| Documentos Proprietários | `mat_documentos_proprietarios` | `text_area` | `list[string]` | `input_mat_docs` | CPF/CNPJ, um por linha |
| Penhoras e Averbações | `mat_penhoras` | `text_area` | `list[string]` | `input_mat_penhoras` | R-X ou Av-X |

### Coluna 2 (1/4 da largura)

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Opções | Observações |
|-------|----------|-------------|------------|-----|--------|-------------|
| Proprietário == Executado? | `mat_prop_confere` | `radio` | `bool\|None` | `k_mat_conf_radio` | Sim/Não/N/A | **CRÍTICO** - Bloqueia finalização |
| Penhora Averbada? | `mat_penhora_averbada` | `radio` | `bool\|None` | `k_pen_av_radio` | Sim/Não/N/A | - |
| Possui Usufruto? | `mat_usufruto` | `radio` | `bool\|None` | `k_usu_radio` | Sim/Não/N/A | - |

### Coluna 3 (1/4 da largura)

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Opções | Observações |
|-------|----------|-------------|------------|-----|--------|-------------|
| Proprietário tem Cônjuge? | `mat_conjugue` | `radio` | `bool\|None` | `k_mat_conj_radio` | Sim/Não/N/A | - |
| Proprietário é PJ? | `mat_proprietario_pj` | `radio` | `bool\|None` | `k_mat_pj_radio` | Sim/Não/N/A | - |
| Possui Indisponibilidade? | `mat_indisp` | `radio` | `bool\|None` | `k_ind_radio` | Sim/Não/N/A | - |

---

## 📝 Aba 3: Edital

**Descrição:** Regras e Condições

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Observações |
|-------|----------|-------------|------------|-----|-------------|
| Descrição do Objeto | `edt_objeto` | `text_input` | `string` | `k_edt_obj` | - |
| Avaliação Base | `vlr_avaliacao` | `info` | `float` | - | **Read-only** - Exibição do valor da Tab 1 |
| Data Avaliação | `edt_data_avaliacao` | `date_input` | `date` | `k_edt_dt` | Default: hoje |
| Permite Parcelamento? | `edt_parcelamento` | `toggle` | `bool` | `k_edt_parc` | - |
| IPTU Sub-roga no preço? | `edt_iptu_subroga` | `toggle` | `bool` | `k_edt_iptu` | - |
| Dívida Condomínio Clara? | `edt_condo_claro` | `toggle` | `bool` | `k_edt_condo` | - |
| % Mínimo 2ª Praça | `edt_percentual_minimo` | `number_input` | `float` | `k_edt_perc` | Default: 50.0% |

---

## 🏠 Aba 4: Situação

**Descrição:** Ocupação e Conservação

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Opções/Valores | Observações |
|-------|----------|-------------|------------|-----|----------------|-------------|
| Status Ocupação | `edt_posse_status` | `selectbox` | `string` | `k_posse_st` | Vago/Ocupado/Desconhecido | - |
| Est. Reforma | `custo_reforma` | `number_input` | `float` | `k_ref` | Valor em R$ | - |
| Est. Desocupação | `custo_desocupacao` | `number_input` | `float` | `k_desoc` | Valor em R$ | - |

---

## 💰 Aba 5: Financeiro

**Descrição:** Viabilidade Econômica

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Observações |
|-------|----------|-------------|------------|-----|-------------|
| Lance Máximo Planejado | `fin_lance` | `number_input` | `float` | `k_fin_lance` | Valor em R$ |
| Valor de Venda | `valor_venda_estimado` | `number_input` | `float` | `k_fin_venda` | Valor em R$ |
| Custos ITBI/Cartório | `fin_itbi` | `number_input` | `float` | `k_fin_itbi` | Valor em R$ |
| Dívida Condomínio | `divida_condominio` | `number_input` | `float` | `k_fin_div_c` | Valor em R$ |
| Dívida IPTU | `divida_iptu` | `number_input` | `float` | `k_fin_div_i` | Valor em R$ |

---

## 🤖 Aba 6: Parecer

**Descrição:** Conclusão do Especialista

| Campo | Atributo | Tipo Widget | Tipo Dados | Key | Observações |
|-------|----------|-------------|------------|-----|-------------|
| Nível de Risco Global | `risco_judicial` | `selectbox` | `RiskLevel` (enum) | `k_risco` | Enum do domínio |
| Parecer Final | `analise_ia` | `text_area` | `string` | `k_parecer` | Height: 250px |

---

## 📊 Sidebar de Resultados

### Métricas Calculadas (Read-only)

| Campo | Tipo | Descrição |
|-------|------|-----------|
| ISJ Score | Gauge | Índice de Saúde Jurídica (calculado) |
| Lucro Líquido | Metric | `R$ {lucro_liquido}` |
| ROI Estimado | Metric | `{roi_nominal}%` |
| Investimento Total | Metric | `R$ {investimento_total}` |

### Alertas

| Condição | Tipo | Mensagem |
|----------|------|----------|
| `prop < 10%` | Warning | ⚠️ Risco: Preço Vil (<10%) |
| `proc_citacao is False` | Error | 🚫 **BLOQUEADO** - Nulidade crítica (Citação) |
| `mat_prop_confere is False` | Error | 🚫 **BLOQUEADO** - Nulidade crítica (Propriedade) |

### Botões de Ação

| Botão | Key | Ação | Condição de Desabilitação |
|-------|-----|------|---------------------------|
| 💾 Salvar | `k_btn_save` | `save_rascunho.execute(analysis)` | Nunca |
| 🚀 Finalizar | `k_btn_fin` | `finalizar_auditoria.execute(analysis, user_id)` | `bloqueado = True` |
| 🗑️ OUT | `k_btn_desc` | `descartar_auditoria.execute(analysis, user_id)` | Nunca |

---

## Regras de Bloqueio

A auditoria é **bloqueada** (não pode ser finalizada) quando:

```python
bloqueado = analysis.proc_citacao is False or analysis.mat_prop_confere is False
```

**Condições:**
1. `proc_citacao = False` → Réu não foi devidamente citado
2. `mat_prop_confere = False` → Proprietário não coincide com o executado

---

## Auto-save

O sistema executa auto-save silencioso a cada interação do usuário:

```python
try:
    services['save_rascunho'].execute(analysis)
except Exception:
    pass  # Falhas silenciosas não travam a UI
```

---

## Resumo de Campos por Aba

| Aba | Total de Campos | Campos Obrigatórios | Campos Calculados |
|-----|-----------------|---------------------|-------------------|
| 1. Processo | 14 | - | 1 (Proporcionalidade) |
| 2. Matrícula | 10 | - | - |
| 3. Edital | 7 | - | 1 (Avaliação Base - display) |
| 4. Situação | 3 | - | - |
| 5. Financeiro | 5 | - | - |
| 6. Parecer | 2 | - | - |
| **TOTAL** | **41** | **0** | **2** |

---

## Enums Utilizados

### NaturezaExecucao
- Valores definidos em `src.domain.models`

### EspecieCredito
- Valores definidos em `src.domain.models`

### RiskLevel
- Valores definidos em `src.domain.models`

---

*Documento gerado em: 01/04/2026*
*Arquivo fonte: `presentation/streamlit_app/views/auditoria_v2.py`*