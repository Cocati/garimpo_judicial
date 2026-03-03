# Spec Funcional — garimpo-analise-jurdica
## Módulo de Auditoria Jurídica e Score de Viabilidade (V2.0)

**Feature**: feat-001
**Criado**: 2026-02-27
**Status**: draft
**Modo**: Brownfield (delta sobre sistema existente)
**Fonte**: PRD "Garimpo Leilao Judicial - Checklist.pdf" + análise do código existente

---

## 1. Declaração do Problema

### Problema
A tela atual de análise de leilões (UC-004) é superficial e não padronizada. O analista preenche campos livres sem orientação estruturada, sem alertas de risco jurídico automáticos e sem cálculo do índice de segurança. Resultado: análises inconsistentes entre leilões, risco de aprovar imóveis com nulidades absolutas, e ausência de um parecer final rastreável.

### Solução
Substituir a tela de análise atual por um formulário estruturado em 6 seções com:
- **Cálculo em tempo real** do ISJ (Índice de Segurança Jurídica, 0–100%)
- **Alertas visuais automáticos** baseados em regras jurídicas
- **Auto-save** para nunca perder dados
- **Bloqueio inteligente** que impede aprovar imóveis com nulidades absolutas
- **Painel de Viabilidade** com ROI calculado automaticamente
- **Parecer Final** estruturado (Verde / Amarelo / Vermelho)

### Valor de Negócio
- Padroniza a análise entre diferentes leilões e sessões
- Reduz o risco de aprovar imóveis com problemas jurídicos graves
- Documenta o raciocínio de investimento de forma auditável

---

## 2. Atores

| Ator | Tipo | Interação |
|------|------|-----------|
| Analista | Humano — usuário final | Preenche o formulário, visualiza alertas e ISJ, finaliza auditoria |
| Sistema | Automatizado | Calcula ISJ, ROI, gera alertas e salva rascunhos automaticamente |

---

## 3. User Stories

### US-001 — Formulário Estruturado de Auditoria

**Como** analista,
**Quero** preencher um formulário com 6 seções (Processo, Matrícula, Edital, Situação Física, Financeiro, Parecer),
**Para** documentar minha análise de forma padronizada e rastreável.

**Critérios de Aceite:**
- [ ] Formulário acessível a partir do card de um imóvel na carteira (substitui a tela atual de análise)
- [ ] Seções exibidas em sequência ou em abas: (1) Processo Judicial, (2) Matrícula e Gravames, (3) Edital e Dívidas, (4) Situação Física, (5) Business Case, (6) Parecer do Analista
- [ ] Todos os campos definidos no PRD estão presentes nas seções corretas (ver Seção 5 — Modelo de Dados)
- [ ] Dados pré-existentes da análise anterior são carregados ao abrir o formulário
- [ ] Campos de array (Executados, Penhoras Ativas, Proprietários) permitem adicionar/remover múltiplos itens
- [ ] Campo condicional: se `proc_recursos = "Sim"`, exibe campo `proc_recursos_obs` (campo de observação)
- [ ] Campo condicional: se `edt_parcelamento = "Sim"`, exibe simulador de parcelas (Art. 895 CPC)

---

### US-002 — ISJ em Tempo Real

**Como** analista,
**Quero** ver o ISJ (Índice de Segurança Jurídica) atualizado enquanto preencho os campos,
**Para** entender instantaneamente o nível de risco jurídico do imóvel.

**Critérios de Aceite:**
- [ ] ISJ exibido como gauge/barra de progresso visível em todos os momentos (painel lateral ou topo fixo)
- [ ] ISJ parte de 100% e sofre deduções conforme regras da Seção 7 (Regras de Negócio)
- [ ] Cor do ISJ muda dinamicamente: Verde (>80%), Amarelo (60-80%), Vermelho (<60%)
- [ ] Qualquer alteração em campo relevante atualiza o ISJ imediatamente (sem clique)
- [ ] Se `proc_citacao = "Não"` OU `mat_prop_confere = "Não"`, ISJ vai para 0% imediatamente

---

### US-003 — Alertas Visuais Automáticos

**Como** analista,
**Quero** ver alertas e banners de risco gerados automaticamente pelo sistema conforme preencho os campos,
**Para** receber orientação jurídica inline e não perder problemas críticos.

**Critérios de Aceite:**
- [ ] Alerta gerado para cada condição listada na Seção 7 (Gatilhos de Alerta)
- [ ] Alertas de nulidade (proc_citacao=Não, mat_prop_confere=Não) exibidos como banners vermelhos no topo
- [ ] Alertas de risco médio exibidos como banners amarelos ou laranja
- [ ] Alertas informativos exibidos inline ao lado do campo
- [ ] Alertas desaparecem automaticamente se a condição for resolvida (ex: usuário muda a resposta)

---

### US-004 — Auto-Save (Rascunho Automático)

**Como** analista,
**Quero** que minha análise seja salva automaticamente conforme preencho os campos,
**Para** nunca perder dados por fechar a janela ou navegação acidental.

**Critérios de Aceite:**
- [ ] Qualquer alteração de campo dispara salvamento automático com 3 segundos de debounce (ou onBlur)
- [ ] Indicador visual "☁️ Alterações salvas automaticamente" exibido no topo após cada save
- [ ] Salvamento não bloqueia a interface (assíncrono)
- [ ] Ao reabrir o formulário do mesmo imóvel, todos os campos preenchidos anteriormente são restaurados

---

### US-005 — Bloqueio de Nulidades Absolutas

**Como** analista,
**Quero** que o sistema impeça finalizar a auditoria quando houver nulidade absoluta detectada,
**Para** evitar avançar com imóveis juridicamente inviáveis por erro processual.

**Critérios de Aceite:**
- [ ] Botão "Finalizar Auditoria" desabilitado se `proc_citacao = "Não"` OU `mat_prop_confere = "Não"`
- [ ] Quando bloqueado, mensagem explicativa é exibida: "Auditoria bloqueada: [motivo específico]"
- [ ] Auto-save continua funcionando normalmente mesmo com botão bloqueado (salva como rascunho)
- [ ] Bloqueio é removido automaticamente se o campo responsável for corrigido

---

### US-006 — Painel de Viabilidade Financeira

**Como** analista,
**Quero** ver um painel com os KPIs financeiros calculados automaticamente (Preço Vil, Investimento Total, ROI),
**Para** tomar a decisão de investimento com os números consolidados.

**Critérios de Aceite:**
- [ ] Painel sempre visível durante o preenchimento do formulário (coluna lateral ou seção fixada)
- [ ] **Preço Vil** calculado automaticamente: `(percentual_minimo / 100) * vlr_avaliacao`. Se `percentual_minimo` for nulo, assumir 50%
- [ ] **Investimento Total (IT)** calculado: `fin_lance + (fin_lance * 0.05) + fin_itbi + fin_dividas + fin_reforma + (0.02 * edt_vlr_avaliacao)`
- [ ] **ROI Nominal** calculado: `((fin_venda_est - IT) / IT) * 100`
- [ ] Todos os valores se atualizam em tempo real conforme os campos de entrada mudam
- [ ] Valores exibidos formatados como moeda (R$) e percentual (%)

---

### US-007 — Finalizar Auditoria e Gerar Parecer

**Como** analista,
**Quero** clicar em "Finalizar Auditoria" para gerar um Parecer Final estruturado e mover o imóvel para a próxima etapa,
**Para** registrar a decisão de investimento de forma rastreável.

**Critérios de Aceite:**
- [ ] Botão "Finalizar Auditoria" disponível quando não há nulidades absolutas
- [ ] Ao finalizar, sistema gera Parecer com base no ISJ:
  - ISJ > 80%: **Parecer Favorável** (Sinal Verde) — imóvel aprovado para participar do leilão
  - ISJ 60-80%: **Parecer Favorável com Ressalvas** (Sinal Amarelo) — analista confirma ciência dos riscos
  - ISJ < 60%: **Parecer Desfavorável** (Sinal Vermelho) — imóvel movido para NO_BID
- [ ] Parecer exibe resumo dos riscos detectados (lista dos alertas ativos no momento da finalização)
- [ ] Ao finalizar com sinal Verde ou Amarelo: status do imóvel muda para `PARTICIPAR`
- [ ] Ao finalizar com sinal Vermelho: status do imóvel muda para `NO_BID`
- [ ] Campo `Parecer do Analista` (Seção 6) é texto livre para observações adicionais do analista
- [ ] Dados salvos e tela retorna à carteira

---

## 4. Escopo

### Dentro do Escopo
- Substituição da tela atual de análise detalhada (UC-004) por este novo módulo
- Formulário completo com 6 seções conforme PRD
- Cálculo do ISJ em tempo real
- Sistema de alertas visuais baseado nas 12 condições do PRD
- Auto-save com debounce de 3 segundos
- Bloqueio de finalização por nulidades absolutas
- Painel de viabilidade financeira (Preço Vil, IT, ROI)
- Geração de parecer automático ao finalizar (Verde/Amarelo/Vermelho)
- Seção 6: campos manuais do analista (Parecer Livre e Recomendação)
- Migração dos dados existentes de `leiloes_analise_detalhada` para o novo modelo

### Fora do Escopo
- Integração com API de IA externa (Seção 6 é manual nesta versão)
- Simulador de parcelas Art. 895 CPC (campo `edt_parcelamento` presente, mas simulador como feature separada)
- Sistema de autenticação multi-usuário (user_id ainda será "Julio" por enquanto)
- Exportação do parecer como PDF
- Integração com scraper para pré-preencher `proc_num` automaticamente

---

## 5. Modelo de Dados (Campos por Seção)

### Seção 1: Processo Judicial

| ID Campo | Rótulo | Tipo | Regra |
|----------|--------|------|-------|
| proc_num | Nº do Processo | String | — |
| proc_executados | Executados | Array[String] | Múltiplos proprietários |
| proc_adv_exec | Executado com Advogado? | Boolean | Se Não → conferência de citação por edital |
| proc_citacao | Citação Válida? | Boolean | **FLAG CRÍTICA**: ISJ = 0% se Não |
| proc_conjuge | Intimação Cônjuge | Enum (S/N/N/A) | Se N → alerta nulidade 50% |
| proc_credores | Intimação Credores | Boolean | — |
| proc_recursos | Recursos Pendentes? | Boolean | Se Sim → exibe `proc_recursos_obs` |
| proc_recursos_obs | Observações dos Recursos | String | Condicional (proc_recursos=Sim) |
| proc_coproprietario_intimado | Intimação Coproprietários | Boolean | — |
| proc_natureza_execucao | Trânsito em Julgado | Enum (Definitiva/Provisória) | Provisória = maior risco |
| proc_justica_gratuita | Beneficiário de Justiça Gratuita | Boolean | — |
| proc_especie_credito | Tipo de Crédito | Enum (Condominial/Comum/Trabalhista) | Comum = risco impenhorabilidade |
| proc_debito_atualizado | Valor da Dívida | Decimal (R$) | — |
| proc_proporcionalidade | Índice de Proporcionalidade | % (Calculado) | `proc_debito_atualizado / edt_vlr_avaliacao * 100` |
| proc_avaliacao_imovel | Avaliação é de toda a propriedade? | Boolean | — |

### Seção 2: Matrícula e Gravames

| ID Campo | Rótulo | Tipo | Regra |
|----------|--------|------|-------|
| mat_num | Matrícula nº | String | — |
| mat_proprietario | Documentos Proprietários | Array[String] | Múltiplos proprietários |
| mat_penhoras | Penhoras Ativas | Array[String] | Múltiplas penhoras |
| mat_conjugue | Proprietário tem cônjuge? | Boolean | — |
| mat_prop_confere | Proprietário = Executado? | Boolean | **FLAG CRÍTICA**: ISJ = 0% se Não |
| mat_proprietario_pj | Proprietário é PJ? | Boolean | Alerta CND se Sim |
| mat_penhora_averbada | Penhora foi registrada? | Boolean | — |
| mat_usufruto | Existe Usufruto? | Boolean | Alerta: deduz 60 pts ISJ |
| mat_indisp | Indisponibilidades? | Boolean | Verificar CNIB |
| mat_vagas_mat | Vaga com Matrícula Própria? | Boolean | Se Sim → conferir penhora na vaga |

### Seção 3: Edital e Dívidas

| ID Campo | Rótulo | Tipo | Regra |
|----------|--------|------|-------|
| edt_objeto | Fração ou Integral? | Enum (100%/50%/Outro) | < 100% → risco condomínio forçado |
| edt_vlr_avaliacao | Valor da Avaliação | Decimal (R$) | Base para ISJ e cálculos |
| edt_percentual_minimo | Percentual Mínimo | % | Default 50% se vazio |
| edt_data_avaliacao | Data da Avaliação | Date | Alerta se > 1 ano |
| edt_parcelamento | Admite Art. 895 CPC? | Boolean | — |
| edt_iptu_subroga | IPTU Sub-roga no preço? | Boolean | Se Sim → IPTU não soma passivo |
| edt_condo_claro | Condomínio citado? | Boolean | Se Não → +15% margem risco |
| edt_fin_lance_minimo_aceitavel | Preço Vil | Decimal (Calculado) | `edt_vlr_avaliacao * edt_percentual_minimo / 100` |

### Seção 4: Situação Física

| ID Campo | Rótulo | Tipo | Regra |
|----------|--------|------|-------|
| edt_posse_status | Status Ocupação | Enum (Vago/Ocupado Proprietário/Inquilino/Desconhecido) | — |
| edt_posse_estrategia | Estratégia de Desocupação | Enum (Imissão nos Autos/Ação Autônoma/Negociação) | — |

### Seção 5: Business Case (Financeiro)

| ID Campo | Rótulo | Tipo | Regra |
|----------|--------|------|-------|
| fin_lance | Valor do Lance (R$) | Decimal | Input base para todos os cálculos |
| fin_comissao | Comissão Leiloeiro | Decimal (Calculado) | `fin_lance * 0.05` |
| fin_itbi | ITBI Estimado | Decimal | Input manual (varia por cidade) |
| fin_dividas | Dívidas NÃO Sub-rogadas | Decimal | Soma IPTU/Condomínio não absorvidos pelo edital |
| fin_reforma | Estimativa de Reforma | Decimal | Input manual |
| fin_venda_est | Valor de Venda (Mercado) | Decimal | Input para cálculo de saída |

### Seção 6: Parecer do Analista

| ID Campo | Rótulo | Tipo | Regra |
|----------|--------|------|-------|
| analise_ia | Parecer Livre | String (texto longo) | Campo manual do analista |
| recomendacao_ia | Recomendação | String | Campo manual do analista |

---

## 6. Métricas de Sucesso

| Métrica | Meta |
|---------|------|
| Tempo para completar análise | Reduzir de ~20min para ~10min (formulário guiado) |
| Imóveis aprovados com nulidade absoluta | 0% (bloqueio ativo) |
| Consistência entre análises | 100% dos registros com ISJ calculado |
| Dados perdidos por abandono de formulário | 0% (auto-save) |

---

## 7. Regras de Negócio

### 7.1 ISJ — Deduções

O ISJ começa em **100%**. Cada condição abaixo deduz pontos:

| Condição | Dedução | Justificativa |
|----------|---------|---------------|
| `proc_citacao = Não` | **-100%** (ISJ → 0%) | Nulidade absoluta do processo |
| `proc_conjuge = Não` | -50% | Risco de violação à meação |
| `proc_natureza_execucao = Provisória` | -20% | Decisão sem trânsito em julgado |
| `proc_especie_credito = Comum` | -15% | Menor privilégio na ordem de pagamento |
| `proc_recursos = Sim` | -20% | Instabilidade da decisão |
| `proc_justica_gratuita = Sim` | -10% | Dificulta condenação por má-fé |
| `proc_proporcionalidade < 10%` | -15% | Possível excesso de execução (Art. 805 CPC) |
| `proc_coproprietario_intimado = Não` | -40% | Risco de nulidade ou direito de preferência tardio |
| `proc_credores = Não` | -20% | Hipoteca pode não ser extinta (Art. 1.501 CC) |
| `mat_prop_confere = Não` | **-100%** (ISJ → 0%) | Erro de domínio inviabiliza aquisição |
| `mat_indisp = Sim` | -30% | Necessidade de cancelamento via CNIB |
| `mat_usufruto = Sim` | -60% | ROI despenca com usufruto |
| `edt_condo_claro = Não` | -15% | Risco financeiro oculto |
| `edt_data_avaliacao > 1 ano` | -10% | Defasagem de valor de mercado |
| `edt_iptu_subroga = Não` | -20% | Passivo oculto de IPTU |

> ISJ nunca fica negativo (limite inferior: 0%).

### 7.2 Gatilhos de Alerta Visual

| Condição | Nível | Mensagem |
|----------|-------|---------|
| `proc_citacao = Não` | 🔴 Banner Vermelho | NULIDADE PROMISSORA: O executado não foi citado. Risco alto de desfazimento da arrematação. |
| `mat_usufruto = Sim` | ⚠️ Alerta | ATENÇÃO: Você está comprando a nua-propriedade. A posse depende da extinção do usufruto. |
| `proc_natureza_execucao = Provisória` | 🟡 Banner Amarelo | EXECUÇÃO PROVISÓRIA: O título ainda pode ser alterado. Risco de retorno ao status quo ante (Art. 520, II, CPC). |
| `proc_especie_credito = Comum` AND `edt_posse_status = Ocupado Proprietário` | 🟠 Banner Laranja | RISCO DE BEM DE FAMÍLIA: Créditos comuns são vulneráveis à tese de impenhorabilidade. |
| `proc_justica_gratuita = Sim` | ℹ️ Alerta Informativo | BENEFICIÁRIO DE JUSTIÇA GRATUITA: Alta probabilidade de recursos protelatórios. |
| `edt_data_avaliacao > 12 meses` | ⚠️ Alerta | AVALIAÇÃO DESATUALIZADA: Risco de nova avaliação ou discussão sobre preço vil (Art. 873, IV, CPC). |
| `proc_coproprietario_intimado = Não` AND `edt_objeto < 100%` | 🔴 Banner Vermelho | RISCO DE NULIDADE: Coproprietários podem anular o leilão ou exercer preferência (Art. 843, §1º, CPC). |
| `proc_proporcionalidade < 15%` | 🟡 Banner Amarelo | ALTO RISCO DE REMISSÃO: Dívida ínfima frente ao bem. Executado pode quitar e cancelar o leilão. |
| `mat_proprietario_pj = Sim` | 🏢 Alerta | PROPRIETÁRIO PESSOA JURÍDICA: Verifique exigência de CND do INSS/Receita para registro. |
| `mat_prop_confere = Não` | 🔴 Banner Vermelho | ERRO DE DOMÍNIO: Proprietário ≠ Executado. Inviabiliza aquisição. |
| `proc_coproprietario_intimado = Não` | ⚠️ Alerta | Coproprietários não intimados — verificar direito de preferência. |
| `proc_avaliacao_imovel = Não` | ⚠️ Alerta | Avaliação pode não refletir o imóvel completo. |

### 7.3 Bloqueio de Finalização

O botão "Finalizar Auditoria" fica **desabilitado** quando:
- `proc_citacao = "Não"` → Mensagem: "Auditoria bloqueada: citação inválida (nulidade absoluta)"
- `mat_prop_confere = "Não"` → Mensagem: "Auditoria bloqueada: proprietário ≠ executado (erro de domínio)"

Auto-save continua funcionando (rascunho) independente do bloqueio.

### 7.4 Cálculos Automáticos

| Campo | Fórmula |
|-------|---------|
| `proc_proporcionalidade` | `proc_debito_atualizado / edt_vlr_avaliacao * 100` |
| `edt_fin_lance_minimo_aceitavel` | Se `edt_percentual_minimo` preenchido: `edt_vlr_avaliacao * edt_percentual_minimo / 100`. Senão: `edt_vlr_avaliacao / 2` |
| `fin_comissao` | `fin_lance * 0.05` |
| **Investimento Total (IT)** | `fin_lance + fin_comissao + fin_itbi + fin_dividas + fin_reforma + (edt_vlr_avaliacao * 0.02)` |
| **ROI Nominal** | `((fin_venda_est - IT) / IT) * 100` |

### 7.5 Parecer Final (ao clicar "Finalizar Auditoria")

| ISJ | Resultado | Status do Imóvel |
|-----|-----------|-----------------|
| > 80% | Parecer Favorável 🟢 | → `PARTICIPAR` |
| 60–80% | Parecer Favorável com Ressalvas 🟡 | → `PARTICIPAR` |
| < 60% | Parecer Desfavorável 🔴 | → `NO_BID` |

### 7.6 Compatibilidade com Dados Existentes

- Campos da análise atual que têm equivalente novo: mapeados para os novos campos
- Campos que existem na DB atual mas não têm campo correspondente no novo modelo (ex: `parecer_juridico` → `analise_ia`): dados preservados
- ISJ calculado retroativamente para análises existentes com base nos campos disponíveis (campos ausentes = não deduzem)

---

## 8. Riscos e Dependências

### Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Migração da tabela `leiloes_analise_detalhada` sem perda de dados | Média | Alto | Migração aditiva (novos campos com default, campos antigos preservados) |
| Auto-save com debounce pode criar condições de corrida no Streamlit | Média | Médio | Usar `st.session_state` como buffer, salvar apenas no onBlur |
| ISJ com muitos campos ainda não preenchidos (parcial = 100% falso) | Alta | Médio | Mostrar ISJ como "parcial" até todos os campos críticos serem preenchidos |

### Dependências
- Tabela `leiloes_analise_detalhada`: precisa ser migrada com novos campos
- Nova tabela ou JSONB para campos de array (Executados, Penhoras, Proprietários)
- Status `PARTICIPAR` já existe no enum `EvaluationStatus` ✅

---

## 9. Fora de Escopo (Explícito)

- Integração com IA externa para gerar parecer automaticamente
- Simulador de parcelas Art. 895 CPC (campo presente, funcionalidade futura)
- Exportação em PDF
- Autenticação real multi-usuário
- Pré-preenchimento automático via scraper
