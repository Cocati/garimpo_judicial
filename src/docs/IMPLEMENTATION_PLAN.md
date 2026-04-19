# IMPLEMENTATION_PLAN.md — Garimpo Judicial

> **Propósito deste documento:** Template de planejamento para desenvolvimento assistido por IA.
> Ao iniciar qualquer análise ou ajuste, copie o checklist correspondente, cole no chat com a IA
> e preencha os campos entre `< >` antes de pedir implementação.
> Mantenha a seção de Débitos Técnicos atualizada.

---

## COMO USAR COM IA

**Prompt recomendado para iniciar qualquer tarefa:**

```
Contexto do projeto: [cole o conteúdo de COMPONENTS.md]

Tarefa: [cole o checklist preenchido abaixo]

Arquivos relevantes para esta tarefa:
- <listar apenas os arquivos que serão tocados>
```

**Regras para o chat com IA:**
1. Sempre forneça `COMPONENTS.md` como contexto antes de pedir código
2. Indique a camada que será alterada (Domain / Application / Infra / Presentation)
3. Especifique se é adição, modificação ou remoção
4. Peça código seguindo os padrões já estabelecidos (prefixos de campo, enums, padrão de upsert)
5. Após a IA gerar o código, verifique os itens de validação antes de aceitar

---

## ÍNDICE DE CHECKLISTS

| # | Tipo de Trabalho | Quando Usar |
|---|-----------------|-------------|
| A | [Bug Fix](#a-bug-fix) | Comportamento incorreto, dado errado, crash |
| B | [Nova Feature](#b-nova-feature) | Adicionando funcionalidade inexistente |
| C | [Novo Campo na Auditoria](#c-novo-campo-na-auditoria) | Adicionar campo ao `DetailedAnalysis` |
| D | [Novo Caso de Uso](#d-novo-caso-de-uso) | Nova lógica de negócio |
| E | [Novo Componente de UI](#e-novo-componente-de-ui) | Nova tela ou componente Streamlit |
| F | [Migração de Schema](#f-migração-de-schema) | Alteração nas tabelas do banco |
| G | [Ajuste no ISJ / Alertas](#g-ajuste-no-isj--alertas) | Mudar pesos, regras ou nulidades |
| H | [Refatoração](#h-refatoração) | Melhorar estrutura sem mudar comportamento |
| I | [Adição de Testes](#i-adição-de-testes) | Aumentar cobertura |
| J | [Revisão Geral](#j-revisão-geral-de-qualidade) | Periódica ou antes de release |

---

## A. Bug Fix

> Comportamento incorreto, crash, dado inconsistente.

```
TAREFA: Bug Fix
Data: <data>
Prioridade: [ ] Crítico  [ ] Alto  [ ] Médio  [ ] Baixo

DESCRIÇÃO DO BUG:
- Comportamento observado: <descrever>
- Comportamento esperado: <descrever>
- Passos para reproduzir: <descrever>

DIAGNÓSTICO:
- [ ] Bug reproduzido localmente
- [ ] Camada afetada identificada:
      [ ] domain/models.py
      [ ] domain/isj_calculator.py
      [ ] application/use_cases.py
      [ ] application/interfaces.py
      [ ] infra/database/models_sql.py
      [ ] infra/repositories/postgres_repo.py
      [ ] presentation/.../main.py
      [ ] presentation/.../views/carteira.py
      [ ] presentation/.../views/auditoria_v2.py
      [ ] presentation/.../components/<componente>
- [ ] Arquivo e linha exatos: <arquivo:linha>
- [ ] Causa raiz: <descrever>
- [ ] Outros locais com o mesmo padrão: <listar ou "nenhum">

IMPLEMENTAÇÃO:
- [ ] Teste que reproduz o bug escrito (se possível)
- [ ] Correção mínima implementada
- [ ] Fluxos verificados após correção:
      [ ] Triagem Rápida
      [ ] Auditoria Detalhada (auditoria_v2)
      [ ] Gestão de Portfólio (carteira)
      [ ] Cálculo ISJ
      [ ] Alertas

VALIDAÇÃO:
- [ ] Teste passando
- [ ] Testado manualmente
- [ ] Banco de dados verificado
- [ ] Nenhum outro fluxo quebrado

ENTREGA:
- [ ] Sem prints de debug
- [ ] COMPONENTS.md atualizado (se comportamento mudou)
```

---

## B. Nova Feature

> Adicionar funcionalidade nova ao sistema.

```
TAREFA: Nova Feature
Data: <data>
Feature: <nome>
Objetivo: <o que o usuário ganha com isso>

REQUISITOS:
- Caso principal (happy path): <descrever>
- Casos alternativos: <descrever>
- Casos de erro: <descrever>
- Impacto em fluxos existentes: <descrever ou "nenhum">

DESIGN — responda antes de pedir código à IA:

  DOMAIN (domain/models.py):
  - [ ] Nova entidade? Nome: <nome>
  - [ ] Novo enum? Nome: <nome>, Valores: <listar>
  - [ ] Campo novo em entidade existente? Entidade: <nome>, Campo: <nome: tipo>

  APPLICATION (application/use_cases.py):
  - [ ] Novo caso de uso? Nome: <NomeCasoDeUsoUseCase>
        execute() recebe: <params>
        execute() retorna: <tipo>
  - [ ] Novo método na interface (interfaces.py)?
        Assinatura: <método(params) -> tipo>

  INFRA (infra/):
  - [ ] Nova tabela? Nome: <nome>
  - [ ] Nova coluna? Tabela: <nome>, Coluna: <nome: tipo>
  - [ ] Novo método no repositório? Nome: <nome>
  - [ ] Migração necessária? [ ] Sim  [ ] Não

  PRESENTATION (presentation/streamlit_app/):
  - [ ] Nova página/view? Arquivo: <views/nome.py>
  - [ ] Novo componente? Arquivo: <components/nome.py>
  - [ ] Componente existente modificado? Arquivo: <nome>
  - [ ] Novo estado no session_state? Chave: <chave>
  - [ ] Novo serviço em dependencies.py? Nome: <nome>

IMPLEMENTAÇÃO (ordem obrigatória):
- [ ] 1. Domain — entidades/enums
- [ ] 2. Application — interface + caso de uso
- [ ] 3. Infra/DB — modelo SQL
- [ ] 4. Infra/Repo — implementação
- [ ] 5. Dependencies — registrar serviço
- [ ] 6. Presentation — componente → view → main
- [ ] 7. Tests — caso de uso com Mock

VALIDAÇÃO:
- [ ] Testes passando
- [ ] Fluxo completo testado manualmente
- [ ] Triagem Rápida intacta
- [ ] Auditoria intacta
- [ ] Portfólio intacto
- [ ] Cálculo ISJ intacto

ENTREGA:
- [ ] COMPONENTS.md atualizado com novo componente/feature
- [ ] Débitos técnicos registrados (se aplicável)
```

---

## C. Novo Campo na Auditoria

> Adicionar campo ao formulário `auditoria_v2` e à entidade `DetailedAnalysis`.
> Use este checklist específico — é mais rápido que o checklist genérico de feature.

```
TAREFA: Novo Campo na Auditoria
Data: <data>
Campo: <nome_do_campo>
Tipo Python: <str | float | bool | Enum | Optional[...] | List[str]>
Tipo SQL: <String | Numeric | Boolean | Text | JSONB>
Default: <valor default>
Seção no formulário: [ ] Processo  [ ] Matrícula  [ ] Edital  [ ] Situação  [ ] Financeiro  [ ] Parecer
Prefixo correto: [ ] proc_  [ ] mat_  [ ] edt_  [ ] fin_  [ ] sem prefixo

ARQUIVOS A MODIFICAR (nesta ordem):
- [ ] domain/models.py          → adicionar campo em DetailedAnalysis
- [ ] infra/database/models_sql.py → adicionar coluna em LeilaoAnaliseDetalhadaModel
- [ ] infra/repositories/postgres_repo.py
      → get_detailed_analysis(): mapear coluna → campo
      → save_auditoria_rascunho(): incluir no INSERT/UPDATE
- [ ] presentation/.../views/auditoria_v2.py → adicionar widget na aba correta
- [ ] domain/isj_calculator.py  → impacta score ISJ? [ ] Sim  [ ] Não
      Se sim: Condição: <descrever>, Penalidade: <−X%>
- [ ] presentation/.../components/alertas_engine.py → gera alerta? [ ] Sim  [ ] Não
      Se sim: Nível: <critico|alto|medio|info>, Condição: <descrever>

SE CAMPO FOR Lista (List[str]):
- [ ] Usar JSONB no banco (como proc_executados, mat_proprietario, mat_penhoras)
- [ ] Garantir parse seguro em get_detailed_analysis(): json.loads() com fallback []

VALIDAÇÃO:
- [ ] Campo persiste corretamente (salvar e recarregar)
- [ ] Campo aparece na aba correta
- [ ] Auto-save funciona para o campo
- [ ] ISJ recalculado corretamente (se aplicável)
- [ ] Alerta gerado corretamente (se aplicável)

ENTREGA:
- [ ] COMPONENTS.md atualizado (tabela de campos da seção correspondente)
```

---

## D. Novo Caso de Uso

> Adicionar lógica de negócio em `application/use_cases.py`.

```
TAREFA: Novo Caso de Uso
Data: <data>
Nome: <NomeCasoDeUsoUseCase>
Propósito: <uma frase>

ESPECIFICAÇÃO:
- execute() recebe: <params com tipos>
- execute() retorna: <tipo>
- Lógica principal:
  1. <passo 1>
  2. <passo 2>
  3. <passo 3>
- Usa repositório? [ ] Sim  [ ] Não
  Se sim, método(s) necessário(s): <listar>

ARQUIVOS A MODIFICAR:
- [ ] application/interfaces.py  → novo método abstrato (se necessário)
- [ ] application/use_cases.py   → implementar a classe
- [ ] infra/repositories/postgres_repo.py → implementar método (se necessário)
- [ ] presentation/.../dependencies.py    → registrar no dict de serviços
- [ ] presentation/.../main.py ou view    → consumir o serviço

VALIDAÇÃO:
- [ ] Teste unitário escrito com Mock do repositório
- [ ] execute() chamado com parâmetros corretos
- [ ] Retorno conforme especificado
- [ ] Integrado na UI
```

---

## E. Novo Componente de UI

> Adicionar tela, aba ou componente Streamlit.

```
TAREFA: Novo Componente de UI
Data: <data>
Tipo: [ ] View (nova página)  [ ] Componente reutilizável  [ ] Nova aba em view existente
Arquivo: presentation/streamlit_app/<views|components>/<nome.py>
Propósito: <descrever>

ESPECIFICAÇÃO:
- Função principal: <nome_da_funcao(params) -> retorno>
- Dados necessários (de qual use case?): <listar>
- Inputs do usuário: <listar widgets>
- Outputs/efeitos: <listar ações que executa>
- Session state keys usados: <listar>

PADRÕES A SEGUIR (verificar ao gerar código com IA):
- [ ] Recebe `services` dict e `user_id` como parâmetros (não importa use case diretamente)
- [ ] Usa `st.session_state` para navegação, não re-renders
- [ ] Chama use cases via `services["chave"].execute()`
- [ ] Não acessa `repo` diretamente (apenas use cases)
- [ ] CSS via `st.markdown(unsafe_allow_html=True)` quando necessário

INTEGRAÇÃO:
- [ ] Adicionado em main.py (se nova página) ou importado na view correta
- [ ] Serviço registrado em dependencies.py (se novo use case)
- [ ] Navegação via session_state documentada

VALIDAÇÃO:
- [ ] Renderiza sem erro com dados reais
- [ ] Renderiza sem erro com dados vazios
- [ ] Navegação de volta funciona
- [ ] Nenhum estado anterior vaza entre sessões
```

---

## F. Migração de Schema

> Alterar tabelas: adicionar/remover coluna, criar tabela, mudar tipo.

```
TAREFA: Migração de Schema
Data: <data>
Mudança: <descrever>
Tabela(s): <leiloes_analiticos | leiloes_avaliacoes | leiloes_analise_detalhada>

PLANEJAMENTO:
- Tipo de mudança: [ ] Nova coluna  [ ] Nova tabela  [ ] Remover coluna  [ ] Mudar tipo
- Dados existentes impactados? [ ] Sim  [ ] Não
  Se sim, estratégia: [ ] Backfill com default  [ ] Coluna nullable  [ ] Script de migração

SQL DE MIGRAÇÃO:
<escrever aqui o SQL antes de executar>

SQL DE ROLLBACK:
<escrever aqui o SQL de reversão>

ARQUIVOS A ATUALIZAR (todos obrigatórios para nova coluna):
- [ ] infra/database/models_sql.py        → coluna no modelo SQLAlchemy
- [ ] domain/models.py                    → campo na entidade de domínio
- [ ] infra/repositories/postgres_repo.py → _map_to_domain(), get_detailed_analysis(), save_auditoria_rascunho()
- [ ] application/use_cases.py            → se afeta lógica de caso de uso
- [ ] presentation/.../views/auditoria_v2.py → widget no formulário
- [ ] tests/unit/                          → atualizar fixtures/mocks

EXECUÇÃO:
- [ ] SQL testado em banco de desenvolvimento
- [ ] Backup realizado (se produção)
- [ ] Migração executada
- [ ] Dados verificados pós-migração
- [ ] Aplicação funcionando normalmente

ENTREGA:
- [ ] COMPONENTS.md atualizado
```

---

## G. Ajuste no ISJ / Alertas

> Alterar pesos, adicionar/remover critério, mudar nulidades ou alertas.

```
TAREFA: Ajuste no ISJ / Alertas
Data: <data>
Tipo: [ ] ISJ — novo critério  [ ] ISJ — alterar peso  [ ] ISJ — remover critério
      [ ] Alerta — novo  [ ] Alerta — alterar  [ ] Nulidade — nova

ESPECIFICAÇÃO:
- Campo gatilho: <nome do campo em DetailedAnalysis>
- Condição: <condição Python exata, ex: analysis.proc_conjuge == ConjugeStatus.NAO>
- Efeito atual: <descrever ou "nenhum">
- Efeito desejado:
  Se ISJ: penalidade de <−X%> quando <condição>
  Se Alerta: nível <critico|alto|medio|info>, mensagem "<texto>", campo_gatilho "<campo>"
  Se Nulidade: retorna score = 0 quando <condição>

ARQUIVOS A MODIFICAR:
- [ ] domain/isj_calculator.py          → IsjCalculator.calculate()
- [ ] presentation/.../components/alertas_engine.py → AlertasEngine.avaliar()

VALIDAÇÃO:
- [ ] Score calculado corretamente para o novo critério
- [ ] Score não alterado quando condição NÃO satisfeita
- [ ] Alerta aparece na interface (isj_gauge.py)
- [ ] Nulidade bloqueia botão "Finalizar Auditoria" (auditoria_v2.py)
- [ ] KPIs financeiros não afetados

ENTREGA:
- [ ] COMPONENTS.md atualizado (tabela de deduções em isj_calculator.py)
```

---

## H. Refatoração

> Melhorar estrutura interna sem alterar comportamento observável.

```
TAREFA: Refatoração
Data: <data>
Alvo: <arquivo(s) ou função(ões)>
Motivação: <duplicação | acoplamento | complexidade | clareza>

ANÁLISE ANTES DE COMEÇAR:
- [ ] Código lido e compreendido completamente
- [ ] Comportamento atual documentado (o que faz, o que retorna)
- [ ] Testes existentes listados: <listar>
- [ ] Todos os testes passando ANTES de começar

ESTRATÉGIA:
- [ ] Extrair função/método
- [ ] Mover para camada correta (ex.: lógica de negócio que está na view)
- [ ] Eliminar duplicação (ex.: dois render_sidebar())
- [ ] Simplificar condicional
- [ ] Outro: <descrever>

REGRA: cada passo deve manter todos os testes passando.

VALIDAÇÃO:
- [ ] Todos os testes passando após refatoração
- [ ] Comportamento externo idêntico (testado manualmente)
- [ ] Código mais simples, legível ou eficiente
```

---

## I. Adição de Testes

> Aumentar cobertura ou cobrir novo comportamento.

```
TAREFA: Adição de Testes
Data: <data>
Alvo: <caso de uso ou componente>
Arquivo: tests/unit/<nome.py>

CASOS A COBRIR:
- [ ] Happy path (entrada válida, retorno correto)
- [ ] Filtros vazios / sem filtro
- [ ] Lista vazia (repositório retorna [])
- [ ] Nulidade ISJ (proc_citacao=False, mat_prop_confere=False)
- [ ] ISJ limítrofe (exatamente 60%)
- [ ] Status de transição: ANALISAR → PARTICIPAR → NO_BID
- [ ] Campo JSONB com lista vazia e lista preenchida
- [ ] <casos específicos para esta feature>

PADRÃO DE TESTE (seguir exatamente):
```python
def test_<descricao_do_comportamento>():
    # Arrange
    mock_repo = Mock(spec=AuctionRepository)
    mock_repo.<metodo>.return_value = <valor>
    use_case = <NomeCasoDeUsoUseCase>(mock_repo)

    # Act
    result = use_case.execute(<params>)

    # Assert
    mock_repo.<metodo>.assert_called_once_with(<params_esperados>)
    assert result == <valor_esperado>
```

VALIDAÇÃO:
- [ ] Teste roda sem banco de dados real
- [ ] Teste é independente (não depende de outro teste)
- [ ] Assert em resultado E em chamadas ao repositório
```

---

## J. Revisão Geral de Qualidade

> Executar periodicamente ou antes de releases.

```
TAREFA: Revisão de Qualidade
Data: <data>

ARQUITETURA:
- [ ] Domain não importa application, infra ou presentation
- [ ] Application não importa infra ou presentation
- [ ] Views não acessam repositório diretamente (só via use cases)
- [ ] Use cases não contêm SQL ou lógica de UI

SEGURANÇA E CONFIGURAÇÃO:
- [ ] DATABASE_URL via variável de ambiente (não hardcoded em config.py)
- [ ] usuario_id vem de autenticação real (não "Julio" hardcoded em main.py)
- [ ] Nenhuma credencial no repositório de código

CÓDIGO:
- [ ] Sem prints de debug
- [ ] Sem arquivos de backup (`carteira (Cópia).py`)
- [ ] Sem código morto comentado sem justificativa
- [ ] Duplicações eliminadas (dois render_sidebar(), GetPortfolio vs GetPortfolioAuctionsUseCase)

BANCO DE DADOS:
- [ ] JSONB com parse seguro (json.loads + try/except com fallback [])
- [ ] Sessões sempre fechadas (try/finally em get_db())
- [ ] Índices em campos de filtro frequente:
      [ ] leiloes_analiticos: (uf, cidade, tipo_bem, site)
      [ ] leiloes_avaliacoes: (usuario_id, avaliacao)

STREAMLIT:
- [ ] @st.cache_resource para repositório e serviços pesados
- [ ] Session state não cresce indefinidamente (limpar ao sair de views)
- [ ] Limite de 15 cards por lote na triagem

TESTES:
- [ ] pytest tests/ rodando sem erros
- [ ] Testes cobrem pelo menos os 8 use cases principais
- [ ] Testes não dependem de banco real

DOCUMENTAÇÃO:
- [ ] COMPONENTS.md reflete o estado atual do código
- [ ] IMPLEMENTATION_PLAN.md com débitos técnicos atualizados
```

---

## DÉBITOS TÉCNICOS

> Mantenha esta tabela atualizada. Priorize ao planejar sprints.

| ID | Descrição | Impacto | Prioridade | Checklist |
|----|-----------|---------|------------|-----------|
| DT-001 | `DATABASE_URL` hardcoded em `infra/database/config.py` | Segurança | Alta | [J] |
| DT-002 | `user_id = "Julio"` hardcoded em `main.py` — sem autenticação real | Funcional | Alta | [B] |
| DT-003 | Arquivo `views/carteira (Cópia).py` no repositório — backup não utilizado | Limpeza | Baixa | [H] |
| DT-004 | `render_sidebar()` duplicado em `components.py` e `components/sidebar.py` | Manutenção | Baixa | [H] |
| DT-005 | `GetPortfolioAuctionsUseCase` e referência legada `get_portfolio` em `dependencies.py` — possível redundância | Clareza | Média | [H] |
| DT-006 | Sem índices declarados explicitamente no ORM para campos filtrados | Performance | Média | [F] |
| DT-007 | Cobertura de testes limitada — `test_auditoria_use_cases.py` pode estar incompleto | Qualidade | Média | [I] |
| DT-008 | Auto-save em cada campo do `auditoria_v2` pode causar excesso de writes | Performance | Baixa | [D] |

---

## HISTÓRICO DE DECISÕES

> Registre aqui decisões arquiteturais e seu contexto para referência futura.

| Data | Decisão | Motivação |
|------|---------|-----------|
| — | Usar ISJ > 60% como threshold para PARTICIPAR | Balanceia rigor jurídico com oportunidade |
| — | Nulidades absolutas: proc_citacao e mat_prop_confere | Irregularidades que invalidam o leilão independente do score |
| — | JSONB para listas (proc_executados, mat_proprietario, mat_penhoras) | Flexibilidade sem migração ao adicionar itens |
| — | Auto-save por campo em auditoria_v2 | Evitar perda de dados em formulário longo |
| — | Clean Architecture com 4 camadas | Facilita testes unitários e troca de banco/UI |
| <data> | <decisão> | <motivação> |
