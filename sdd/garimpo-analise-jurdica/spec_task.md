{
  "feature": "garimpo-analise-jurdica",
  "feature_id": "feat-001",
  "generated_at": "2026-02-27",
  "local_config": {
    "database": "existing",
    "database_type": "postgresql_local",
    "connection": "localhost:5432/postgres",
    "fury_services": null
  },
  "stats": {
    "total": 15,
    "done": 0,
    "by_layer": {
      "1": 12,
      "2": 0,
      "3": 3
    }
  },
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Script de migração do banco de dados (V2)",
      "description": "Criar e executar `scripts/migration_001_auditoria_v2.sql` com ALTER TABLE ADD COLUMN IF NOT EXISTS para os ~45 novos campos de `leiloes_analise_detalhada`. Todos os campos com DEFAULT NULL para preservar registros existentes. Campos de array (executados, penhoras, proprietários) como JSONB.",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": [],
      "files": [
        "scripts/migration_001_auditoria_v2.sql"
      ],
      "acceptance_criteria": [
        "AC-1: Todos os campos da spec técnica seção 4.4 estão presentes na tabela após execução",
        "AC-2: Registros existentes em `leiloes_analise_detalhada` não foram alterados (novos campos = NULL)",
        "AC-3: Campos JSONB (`proc_executados`, `mat_proprietario`, `mat_penhoras`) aceitam array vazio `[]`",
        "GATE: `SELECT column_name FROM information_schema.columns WHERE table_name = 'leiloes_analise_detalhada'` retorna todos os novos campos"
      ],
      "references": ["DD-001"]
    },
    {
      "id": "TASK-002",
      "title": "Expandir modelo de domínio DetailedAnalysis",
      "description": "Adicionar todos os novos campos ao dataclass `DetailedAnalysis` em `src/domain/models.py` conforme spec técnica seção 4.1. Remover campos duplicados `data_1_praca`/`data_2_praca` (dívida D-002). Adicionar enums necessários (`ConjugeStatus`, `NaturezaExecucao`, `EspecieCredito`, `ObjFracao`, `EstrategiaDesocupacao`).",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": ["TASK-001"],
      "files": [
        "src/domain/models.py"
      ],
      "acceptance_criteria": [
        "AC-1: Todos os 45+ campos novos presentes no dataclass com tipos e defaults corretos",
        "AC-2: Campos duplicados `data_1_praca`/`data_2_praca` (linhas 30-31) removidos",
        "AC-3: Campos de lista (`proc_executados`, `mat_proprietario`, `mat_penhoras`) com type hint `List[str]` e default `field(default_factory=list)`",
        "GATE: `python -c 'from src.domain.models import DetailedAnalysis; a = DetailedAnalysis(site=\"x\", id_leilao=\"1\", usuario_id=\"u\"); print(a.proc_executados)'` retorna `[]`"
      ],
      "references": ["DD-002", "US-001"]
    },
    {
      "id": "TASK-003",
      "title": "IsjCalculator — motor de cálculo do ISJ",
      "description": "Criar `src/domain/isj_calculator.py` com classe `IsjCalculator` e método `calculate(analysis: DetailedAnalysis) -> float`. Implementar todas as 15 regras de dedução da spec técnica seção 4.2. Campos None não deduzem pontos. ISJ mínimo = 0.0.",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": ["TASK-002"],
      "files": [
        "src/domain/isj_calculator.py"
      ],
      "acceptance_criteria": [
        "AC-1: `proc_citacao=False` → ISJ retorna 0.0 imediatamente",
        "AC-2: `mat_prop_confere=False` → ISJ retorna 0.0 imediatamente",
        "AC-3: Campos None são ignorados no cálculo (não deduzem pontos)",
        "AC-4: Múltiplas deduções acumulam corretamente (ex: Provisória -20 + Comum -15 + Recursos -20 = 45 pontos deduzidos → ISJ = 55%)",
        "AC-5: ISJ nunca fica negativo (mínimo 0.0)",
        "GATE: `python -m pytest src/tests/unit/test_isj_calculator.py -v` passa todos os testes"
      ],
      "references": ["US-002", "DD-003"]
    },
    {
      "id": "TASK-004",
      "title": "AlertasEngine — motor de alertas jurídicos visuais",
      "description": "Criar `src/presentation/streamlit_app/components/alertas_engine.py` com classe `AlertasEngine` e método `avaliar(analysis: DetailedAnalysis) -> List[Alerta]`. Implementar as 12 regras de alerta da spec funcional seção 7.2. Dataclass `Alerta(nivel, mensagem, campo_gatilho)` com níveis: `critico`, `alto`, `medio`, `info`.",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": ["TASK-002"],
      "files": [
        "src/presentation/streamlit_app/components/alertas_engine.py"
      ],
      "acceptance_criteria": [
        "AC-1: `proc_citacao=False` gera alerta de nível `critico` com mensagem contendo 'NULIDADE PROMISSORA'",
        "AC-2: `mat_prop_confere=False` gera alerta de nível `critico` com mensagem contendo 'ERRO DE DOMÍNIO'",
        "AC-3: `mat_usufruto=True` gera alerta de nível `alto`",
        "AC-4: Quando condição é corrigida (ex: `proc_citacao=True`), alerta correspondente não aparece na lista",
        "AC-5: Campos None (não preenchidos) não geram alertas",
        "GATE: `python -m pytest src/tests/unit/test_alertas_engine.py -v` passa todos os testes"
      ],
      "references": ["US-003", "DD-003"]
    },
    {
      "id": "TASK-005",
      "title": "Expandir modelo ORM SQLAlchemy (LeilaoAnaliseDetalhadaModel)",
      "description": "Adicionar todas as novas colunas ao `LeilaoAnaliseDetalhadaModel` em `src/infra/database/models_sql.py`. Usar `Column(type, nullable=True)` para todos os novos campos. Campos de array como `Column(JSONB, nullable=True, default=list)`. Importar `JSONB` de `sqlalchemy.dialects.postgresql`.",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": ["TASK-001"],
      "files": [
        "src/infra/database/models_sql.py"
      ],
      "acceptance_criteria": [
        "AC-1: Todas as novas colunas do TASK-001 têm correspondência no ORM model",
        "AC-2: Campos JSONB importados corretamente de `sqlalchemy.dialects.postgresql`",
        "AC-3: Nenhuma coluna existente foi removida ou renomeada no model",
        "GATE: `python -c 'from src.infra.database.models_sql import LeilaoAnaliseDetalhadaModel; print(LeilaoAnaliseDetalhadaModel.__table__.columns.keys())'` lista todas as novas colunas"
      ],
      "references": ["DD-001"]
    },
    {
      "id": "TASK-006",
      "title": "Estender repositório PostgreSQL + corrigir interface",
      "description": "Em `src/infra/repositories/postgres_repo.py`: adicionar método `save_auditoria_rascunho(analysis)` com ON CONFLICT DO UPDATE incluindo todos os novos campos. Atualizar `get_detailed_analysis` para mapear novos campos de volta ao domínio. Em `src/application/interfaces.py`: corrigir assinatura `get_stats(user_id: str)` (dívida D-001) e adicionar métodos abstratos novos.",
      "status": "pending",
      "layer": 1,
      "complexity": "High",
      "depends_on": ["TASK-002", "TASK-005"],
      "files": [
        "src/infra/repositories/postgres_repo.py",
        "src/application/interfaces.py"
      ],
      "acceptance_criteria": [
        "AC-1: `save_auditoria_rascunho()` persiste todos os novos campos via ON CONFLICT DO UPDATE",
        "AC-2: `get_detailed_analysis()` carrega todos os novos campos de volta ao objeto `DetailedAnalysis`",
        "AC-3: Campos JSONB (listas) deserializados corretamente como `List[str]` no domínio",
        "AC-4: Interface `get_stats(user_id: str)` assinatura corrigida (dívida D-001)",
        "AC-5: Rollback em caso de exceção no save",
        "GATE: `python -m pytest src/tests/unit/ -v -k 'test_save_rascunho or test_get_detailed'` passa"
      ],
      "references": ["US-004", "DD-001"]
    },
    {
      "id": "TASK-007",
      "title": "Novos Use Cases: SaveAuditoriaRascunhoUseCase e FinalizarAuditoriaUseCase",
      "description": "Adicionar em `src/application/use_cases.py` os dois novos use cases. `SaveAuditoriaRascunhoUseCase.execute(analysis)` chama `save_auditoria_rascunho` sem alterar status. `FinalizarAuditoriaUseCase.execute(analysis, user_id)` bloqueia se `proc_citacao=False` ou `mat_prop_confere=False`, salva análise e atualiza status (PARTICIPAR se ISJ>60%, NO_BID se ≤60%).",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": ["TASK-003", "TASK-006"],
      "files": [
        "src/application/use_cases.py"
      ],
      "acceptance_criteria": [
        "AC-1: `SaveAuditoriaRascunhoUseCase` NÃO altera `leiloes_avaliacoes` (apenas salva análise)",
        "AC-2: `FinalizarAuditoriaUseCase` lança `ValueError` se `proc_citacao is False`",
        "AC-3: `FinalizarAuditoriaUseCase` lança `ValueError` se `mat_prop_confere is False`",
        "AC-4: ISJ > 60% → status `PARTICIPAR`; ISJ ≤ 60% → status `NO_BID`",
        "AC-5: `FinalizarAuditoriaUseCase` chama `IsjCalculator.calculate()` internamente",
        "GATE: `python -m pytest src/tests/unit/test_auditoria_use_cases.py -v` passa todos os testes"
      ],
      "references": ["US-005", "US-007"]
    },
    {
      "id": "TASK-008",
      "title": "Componente ISJ Gauge (visual)",
      "description": "Criar `src/presentation/streamlit_app/components/isj_gauge.py` com função `render_isj_gauge(isj_score: float, alertas: list)`. Exibir score com barra de progresso colorida (verde >80%, amarelo 60-80%, vermelho <60%). Exibir contagem de alertas ativos por nível abaixo do gauge.",
      "status": "pending",
      "layer": 1,
      "complexity": "Low",
      "depends_on": ["TASK-003", "TASK-004"],
      "files": [
        "src/presentation/streamlit_app/components/isj_gauge.py"
      ],
      "acceptance_criteria": [
        "AC-1: ISJ > 80%: barra verde, texto 'Favorável'",
        "AC-2: ISJ 60-80%: barra amarela, texto 'Favorável com Ressalvas'",
        "AC-3: ISJ < 60%: barra vermelha, texto 'Desfavorável'",
        "AC-4: Contagem de alertas por nível exibida abaixo do gauge",
        "GATE: Componente importado sem erro em script Python standalone"
      ],
      "references": ["US-002"]
    },
    {
      "id": "TASK-009",
      "title": "Nova tela auditoria_v2.py — formulário principal (6 seções)",
      "description": "Criar `src/presentation/streamlit_app/views/auditoria_v2.py` com função `render_auditoria_v2(services, user_id, site, id_leilao)`. Implementar as 6 seções como `st.tabs`. Incluir auto-save (save on re-run quando houver mudança), bloqueio do botão 'Finalizar' em caso de nulidade, painel lateral com KPIs financeiros calculados em tempo real, e banner de alertas no topo.",
      "status": "pending",
      "layer": 1,
      "complexity": "High",
      "depends_on": ["TASK-007", "TASK-008"],
      "files": [
        "src/presentation/streamlit_app/views/auditoria_v2.py"
      ],
      "acceptance_criteria": [
        "AC-1: Formulário exibe os 6 tabs com todos os campos da spec funcional seção 5",
        "AC-2: Campos de lista (executados, penhoras) com botão 'Adicionar / Remover'",
        "AC-3: ISJ e alertas recalculados a cada interação (re-run do Streamlit)",
        "AC-4: Botão 'Finalizar Auditoria' desabilitado quando `proc_citacao=False` OU `mat_prop_confere=False`",
        "AC-5: Painel lateral/fixo exibe: Preço Vil, Investimento Total, ROI Nominal calculados em tempo real",
        "AC-6: Indicador '☁️ Alterações salvas automaticamente' exibido após cada save bem-sucedido",
        "AC-7: Campo condicional `proc_recursos_obs` aparece apenas quando `proc_recursos=True`",
        "GATE: Tela abre sem erro com imóvel existente na carteira e todos os campos em branco carregam corretamente"
      ],
      "references": ["US-001", "US-002", "US-003", "US-004", "US-005", "US-006", "US-007"]
    },
    {
      "id": "TASK-010",
      "title": "Integração na carteira + registro de serviços",
      "description": "Em `src/presentation/streamlit_app/views/carteira.py`: substituir chamada `_render_detailed_analysis()` por `render_auditoria_v2()`. Em `src/presentation/streamlit_app/dependencies.py`: adicionar `save_rascunho: SaveAuditoriaRascunhoUseCase` e `finalizar_auditoria: FinalizarAuditoriaUseCase` ao dict retornado por `get_services()`.",
      "status": "pending",
      "layer": 1,
      "complexity": "Low",
      "depends_on": ["TASK-009"],
      "files": [
        "src/presentation/streamlit_app/views/carteira.py",
        "src/presentation/streamlit_app/dependencies.py"
      ],
      "acceptance_criteria": [
        "AC-1: Clicar em 'Avaliar 📝' na carteira abre `auditoria_v2.py` (não a tela antiga)",
        "AC-2: `get_services()` retorna chaves `save_rascunho` e `finalizar_auditoria`",
        "AC-3: Botão 'Finalizar Auditoria' com parecer Verde/Amarelo move imóvel para aba 'Participar'",
        "AC-4: Botão 'Finalizar Auditoria' com parecer Vermelho move imóvel para aba 'Descartados'",
        "AC-5: Ao retornar da auditoria, carteira recarrega com status atualizado",
        "GATE: Fluxo completo funciona sem erro: Triagem → Analisar → Abrir Análise → Finalizar → Carteira"
      ],
      "references": ["US-007"]
    },
    {
      "id": "TASK-011",
      "title": "Testes unitários (caminho crítico — MVP)",
      "description": "Criar 3 arquivos de teste para os componentes críticos: `test_isj_calculator.py` (5 casos), `test_auditoria_use_cases.py` (4 casos), `test_alertas_engine.py` (2 casos). Usar `unittest.mock.Mock` para repositório (padrão existente do projeto).",
      "status": "pending",
      "layer": 1,
      "complexity": "Medium",
      "depends_on": ["TASK-003", "TASK-004", "TASK-007"],
      "files": [
        "src/tests/unit/test_isj_calculator.py",
        "src/tests/unit/test_auditoria_use_cases.py",
        "src/tests/unit/test_alertas_engine.py"
      ],
      "acceptance_criteria": [
        "AC-1: `test_isj_calculator.py` cobre: citacao=False→0%, dominio=False→0%, deduções múltiplas, campos None ignorados, ISJ não fica negativo",
        "AC-2: `test_auditoria_use_cases.py` cobre: bloqueio por nulidade, ISJ>60%→PARTICIPAR, ISJ≤60%→NO_BID, rascunho não altera status",
        "AC-3: `test_alertas_engine.py` cobre: alerta crítico para citacao=False, nenhum alerta quando campos são None",
        "GATE: `python -m pytest src/tests/unit/ -v` passa com 0 erros (incluindo testes existentes)"
      ],
      "references": ["US-002", "US-003", "US-005"]
    },
    {
      "id": "TASK-012",
      "title": "Corrigir dívida técnica D-002 e D-003",
      "description": "D-002: Remover campos duplicados `data_1_praca`/`data_2_praca` nas linhas 30-31 de `models.py` (já feito como parte do TASK-002, confirmar). D-003: Em `carteira.py`, corrigir `_save_analysis()` para incluir `divida_subroga` e `custo_desocupacao` — porém, como a nova tela `auditoria_v2.py` substitui `_render_detailed_analysis`, verificar se `_save_analysis` ainda é usada. Se não, documentar como obsoleta.",
      "status": "pending",
      "layer": 1,
      "complexity": "Low",
      "depends_on": ["TASK-010"],
      "files": [
        "src/domain/models.py",
        "src/presentation/streamlit_app/views/carteira.py"
      ],
      "acceptance_criteria": [
        "AC-1: Campos duplicados `data_1_praca`/`data_2_praca` não existem mais em `models.py`",
        "AC-2: Função `_save_analysis()` antiga marcada como `# DEPRECATED: substituída por auditoria_v2.py` ou removida se sem outros usos",
        "AC-3: Nenhum teste existente quebrado após as mudanças",
        "GATE: `python -m pytest src/tests/unit/ -v` passa com 0 erros"
      ],
      "references": ["DD-002", "DD-003"]
    },
    {
      "id": "TASK-013",
      "title": "Revisão de código",
      "description": "Executar revisão completa do código implementado nos TASK-001 a TASK-012. Verificar: padrões de Clean Architecture respeitados (sem import de infra em domain), tratamento de exceções, consistência de nomenclatura com código existente, sem código morto ou debug prints.",
      "status": "pending",
      "layer": 3,
      "complexity": "Low",
      "depends_on": ["TASK-011", "TASK-012"],
      "files": [],
      "acceptance_criteria": [
        "AC-1: Nenhum módulo de `infra/` é importado diretamente em `domain/`",
        "AC-2: Todos os métodos novos seguem o padrão de nomenclatura existente (snake_case, verbos em português)",
        "AC-3: Sem `print()` de debug em código de produção",
        "GATE: Revisão via `meli-code-reviewer` skill sem issues críticos"
      ],
      "references": []
    },
    {
      "id": "TASK-014",
      "title": "Revisão de segurança",
      "description": "Verificar aspectos de segurança da nova feature: validação de inputs do formulário antes de persistir, sem SQL injection via campos texto livre (parecer, observações), campos monetários validados como numéricos.",
      "status": "pending",
      "layer": 3,
      "complexity": "Low",
      "depends_on": ["TASK-013"],
      "files": [],
      "acceptance_criteria": [
        "AC-1: Campos de texto livre (parecer, observações) não executam comandos SQL (uso de ORM/prepared statements confirmado)",
        "AC-2: Campos de valor monetário validados como float antes de persistir",
        "AC-3: Sem credenciais expostas em novos arquivos",
        "GATE: Revisão via `meli-security-expert` skill sem issues críticos"
      ],
      "references": []
    },
    {
      "id": "TASK-015",
      "title": "Revisão de performance",
      "description": "Verificar que o auto-save não causa degradação de performance na UI Streamlit. Analisar a query de carregamento de `get_detailed_analysis` com os novos ~45 campos. Verificar que IsjCalculator e AlertasEngine não fazem operações custosas em re-runs frequentes.",
      "status": "pending",
      "layer": 3,
      "complexity": "Low",
      "depends_on": ["TASK-013"],
      "files": [],
      "acceptance_criteria": [
        "AC-1: `get_detailed_analysis()` não executa múltiplas queries por carregamento (N+1 check)",
        "AC-2: `IsjCalculator.calculate()` e `AlertasEngine.avaliar()` são operações puramente in-memory (sem I/O)",
        "AC-3: Auto-save não bloqueia a re-renderização da UI (operação assíncrona ou confirmada como aceitável)",
        "GATE: Revisão via `meli-performance-expert` skill sem issues críticos"
      ],
      "references": []
    }
  ],
  "dependency_graph": {
    "by_layer": {
      "1": {
        "level_0": ["TASK-001"],
        "level_1": ["TASK-002", "TASK-005"],
        "level_2": ["TASK-003", "TASK-004", "TASK-006"],
        "level_3": ["TASK-007", "TASK-008"],
        "level_4": ["TASK-009"],
        "level_5": ["TASK-010"],
        "level_6": ["TASK-011", "TASK-012"]
      },
      "3": {
        "level_0": ["TASK-013"],
        "level_1": ["TASK-014", "TASK-015"]
      }
    }
  }
}
