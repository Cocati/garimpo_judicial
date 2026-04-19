# Gemini Contexto do Projeto

Este arquivo (GEMINI.md) fornece contexto e diretrizes para a IA do Gemini sobre este projeto.

## Sobre o Projeto

(Descreva brevemente o objetivo e a finalidade deste projeto. Com base na estrutura de arquivos e nas dependências, parece ser um aplicativo da web de ciência de dados ou um painel, possivelmente relacionado a dados judiciais ou de leilão.)

## Tecnologias e Frameworks

- **Linguagem Principal:** Python
- **Framework Principal:** Streamlit
- **Banco de Dados:** PostgreSQL (baseado no uso de `sqlalchemy.dialects.postgresql`)
- **Outras Bibliotecas:**
    - `pandas` para manipulação de dados
    - `plotly.express` para visualização de dados
    - `sqlalchemy` como ORM para interação com o banco de dados
    - `python-dotenv` para gerenciamento de configuração
    - `argparse` para análise de argumentos de linha de comando
    - `pathlib` para manipulação de caminhos do sistema de arquivos

## Convenções do Projeto

- **Estilo de Código:** O código parece seguir o PEP 8, mas não há um linter configurado. Recomenda-se o uso de um formatador como o `black` e um linter como o `ruff` ou `flake8`.
- **Convenções de Nomenclatura:** `snake_case` para variáveis e funções, `PascalCase` para classes.
- **Estrutura de Diretórios:** O projeto segue uma estrutura de aplicativo em camadas, com separação de interesses:
    - `application`: Contém a lógica de negócios e os casos de uso.
    - `domain`: Define os modelos de dados e a lógica de domínio.
    - `infra`: Gerencia o acesso a recursos externos, como o banco de dados.
    - `presentation`: Lida com a interface do usuário (aplicativo Streamlit).

## Módulo de Auditoria (`auditoria_v2.py`)

Este módulo é o coração da aplicação, renderizando a interface de auditoria de leilões.

### Fluxo de Funcionamento

1.  **Inicialização e Carregamento de Dados**:
    *   Verifica se uma análise (`current_analysis`) já existe na sessão do Streamlit (`st.session_state`).
    *   Se não houver, ou se for um leilão diferente, carrega os dados da análise do repositório (`services['repository'].get_detailed_analysis`).
    *   Se nenhuma análise existir para o leilão, uma nova instância de `DetailedAnalysis` é criada.
    *   Os dados do leilão (`auction_data`) também são carregados para exibição.

2.  **Exibição do Cabeçalho**:
    *   Apresenta um resumo visual do leilão, incluindo imagem, título, datas e valores da 1ª e 2ª praça.

3.  **Layout Principal**:
    *   A tela é dividida em duas colunas: o formulário de auditoria (`col_form`) e uma barra lateral com estatísticas e ações (`col_stats`).

4.  **Formulário de Auditoria (Abas)**:
    *   O formulário é organizado em seis abas, cada uma focada em um aspecto da auditoria:
        *   **1. Processo**: Coleta de dados sobre o processo judicial (nº, executados, natureza, etc.) e um checklist de nulidades (citação, recursos pendentes).
        *   **2. Matrícula**: Análise dos dados da matrícula do imóvel (nº, proprietários, penhoras, etc.).
        *   **3. Edital**: Detalhes do edital do leilão (descrição do objeto, condições de pagamento, etc.).
        *   **4. Situação**: Informações sobre a ocupação do imóvel e custos de reforma/desocupação.
        *   **5. Financeiro**: Entradas para o planejamento financeiro do arremate (lance, valor de venda, custos).
        *   **6. Parecer**: Campo para o parecer final do auditor, incluindo nível de risco e observações.

5.  **Cálculos em Tempo Real**:
    *   Com base nos dados inseridos, o sistema calcula:
        *   **Alertas**: O `AlertasEngine` gera alertas sobre riscos potenciais.
        *   **KPIs Financeiros**: O `IsjCalculator` calcula indicadores como lucro líquido e ROI.
        *   **Score ISJ**: O `IsjCalculator` também calcula o "Índice de Segurança Jurídica" (ISJ), uma nota que resume o risco legal da operação.

6.  **Barra Lateral de Estatísticas e Ações**:
    *   Exibe os resultados dos cálculos:
        *   Um "medidor" (gauge) para o score ISJ e os alertas.
        *   KPIs financeiros.
        *   Um aviso de **bloqueio** se forem detectadas nulidades críticas.
    *   Contém os botões de ação:
        *   **💾 Salvar**: Salva a auditoria como rascunho.
        *   **🚀 Finalizar**: Finaliza a auditoria (desabilitado em caso de bloqueio).
        *   **🗑️ OUT**: Descarta a auditoria e rejeita o leilão.

7.  **Auto-save**:
    *   Um mecanismo de salvamento automático silencioso é executado para evitar a perda de dados durante o preenchimento.


## Como Executar o Projeto

(As instruções a seguir são baseadas em suposições e precisam ser validadas.)

### Pré-requisitos

- Python 3.8+
- Poetry (recomendado para gerenciamento de dependências)

### Instalação

Como não há um arquivo `requirements.txt`, você pode gerar um com o `pipreqs` ou criar manualmente um com base nas importações:

```bash
# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install streamlit pandas plotly sqlalchemy psycopg2-binary python-dotenv
```

### Executando a Aplicação

O ponto de entrada principal parece ser `presentation/streamlit_app/main.py`.

```bash
streamlit run presentation/streamlit_app/main.py
```

### Executando os Testes

(Nenhum framework de teste foi identificado. Recomenda-se o uso do `pytest`.)

## Instruções Adicionais para a IA

- Sempre crie testes para novas funcionalidades.
- Use o `black` para formatar o código antes de confirmar.
- Mantenha a separação de interesses entre as camadas da aplicação.
- Não modifique o arquivo `infra/database/config.py` diretamente. Use variáveis de ambiente para configuração.
