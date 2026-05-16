# Especificação Técnica: Tela de Pesquisa Global

**ID:** 005
**Autor:** Gemini Code Assist
**Data:** 16/05/2026
**Status:** Proposta

---

## 1. Introdução e Objetivos

Esta especificação detalha a criação de uma nova tela no painel "Garimpo Judicial" chamada **"🔎 Pesquisa Global"**. A necessidade surge do problema de que, uma vez que um imóvel é descartado na triagem, ele se torna invisível para o usuário, sem uma forma fácil de consultá-lo ou reverter a decisão.

Os principais objetivos desta nova funcionalidade são:
- **Centralizar a Busca:** Fornecer uma ferramenta única para encontrar *qualquer* leilão na base de dados, independentemente do seu status de avaliação (pendente, em análise, descartado, etc.).
- **Aumentar a Visibilidade:** Permitir que o usuário visualize leilões que foram previamente descartados.
- **Facilitar a Reversão:** Criar um caminho para que o usuário possa reavaliar um leilão descartado, revertendo sua decisão e movendo-o de volta para o fluxo de análise.
- **Busca Flexível:** Permitir a busca por múltiplos critérios, como ID do Leilão, palavras-chave no título, e outros filtros necessários.

## 2. Fonte de Dados

A funcionalidade de busca irá consultar e cruzar informações de duas tabelas principais:

1.  `public.leiloes_analiticos`: A fonte primária contendo todos os leilões coletados pelos scrapers.
2.  `public.leiloes_avaliacoes`: A tabela que armazena as decisões (avaliações) de cada usuário para cada leilão.

A consulta principal realizará um `LEFT JOIN` da `leiloes_analiticos` com a `leiloes_avaliacoes` (filtrando pelo `usuario_id` logado). Isso garante que todos os leilões sejam retornados, junto com o status de avaliação específico do usuário, caso exista. Se não houver uma avaliação correspondente, o status do leilão será considerado "Pendente".

---

## 3. Plano de Implementação (Módulo 1: Backend)

Esta seção descreve as alterações e adições necessárias nas camadas de domínio, aplicação e infraestrutura para suportar a nova funcionalidade de pesquisa.

### 3.1. Domain Layer (`src/domain/models.py`)

Para encapsular os critérios de busca de forma clara e tipada, um novo dataclass será adicionado.

- **Ação:** Criar um novo dataclass `GlobalSearchFilter`.
- **Detalhes:** Este dataclass conterá todos os possíveis filtros que o usuário poderá aplicar na tela, como termo de busca, status, localização, etc.

```python
# Adicionar em src/domain/models.py

@dataclass
class GlobalSearchFilter:
    """Filtros para a pesquisa global de leilões."""
    search_term: Optional[str] = None
    uf: Optional[List[str]] = None
    status: Optional[List[EvaluationStatus]] = None
```

### 3.2. Application Layer (`src/application/`)

A camada de aplicação será estendida para expor a nova capacidade de busca.

- **`interfaces.py`**:
    - **Ação:** Adicionar a assinatura do novo método de busca na interface `AuctionRepository`.
    - **Assinatura:** `search_all_auctions(self, user_id: str, filters: GlobalSearchFilter) -> List[Auction]`

- **`use_cases.py`**:
    - **Ação:** Criar um novo caso de uso, `SearchAllAuctionsUseCase`.
    - **Responsabilidade:** Este caso de uso receberá os parâmetros de filtro da camada de apresentação, irá instanciar o `GlobalSearchFilter` e invocar o método correspondente do repositório.

### 3.3. Infrastructure Layer (`src/infra/repositories/postgres_repo.py`)

Esta é a camada onde a lógica de consulta ao banco de dados será implementada.

- **Ação:** Implementar o método `search_all_auctions` na classe `PostgresAuctionRepository`.
- **Lógica de Implementação:**
    1.  A consulta principal será construída usando SQLAlchemy, partindo do `LeilaoAnaliticoModel`.
    2.  Será utilizado um `outerjoin` (equivalente ao `LEFT JOIN` do SQL) para conectar com `LeilaoAvaliacaoModel`, com a condição de junção incluindo `site`, `id_leilao` e o `user_id` fornecido.
    3.  **Filtros Dinâmicos:**
        - Se `filters.search_term` for fornecido, aplicar uma cláusula `WHERE` com `OR` para buscar o termo no campo `titulo` e `id_leilao` (usando `ilike` para busca case-insensitive).
        - Se `filters.uf` for fornecido, aplicar um filtro `WHERE ... IN (...)`.
        - Se `filters.status` for fornecido, a lógica será mais complexa:
            - Se "Pendente" estiver na lista de status, a consulta deverá incluir registros onde a junção com `leiloes_avaliacoes` é `NULL`.
            - Para outros status, a consulta filtrará pelo valor do campo `avaliacao` na tabela `leiloes_avaliacoes`.
    4.  **Mapeamento de Retorno:** Os resultados da consulta (que incluem colunas de ambas as tabelas) serão mapeados para uma lista de objetos `Auction` do domínio. O campo `status_carteira` do objeto `Auction` será populado com o valor de `avaliacao` ou com "PENDING" se a avaliação não existir.

---
*Próximo Módulo: Implementação do Frontend (View, Roteamento e Dependências).*

## 4. Plano de Implementação (Módulo 2: Frontend)

Esta seção detalha a criação da interface do usuário (UI) para a nova tela de "Pesquisa Global", bem como as integrações necessárias.

### 4.1. Roteamento e Navegação (`src/presentation/streamlit_app/main.py`)

- **Ação:** Adicionar uma nova entrada, **"🔎 Pesquisa Global"**, ao componente de navegação principal (`st.sidebar.radio`).
- **Lógica:** Será adicionada uma nova condição `elif` para detectar a seleção desta página e invocar a função de renderização correspondente da nova view.

### 4.2. Nova View (`src/presentation/streamlit_app/views/pesquisa.py`)

- **Ação:** Criar um novo arquivo `pesquisa.py` no diretório `src/presentation/streamlit_app/views/`.
- **Estrutura Principal:**
  - O arquivo conterá uma função `render_pesquisa(services)`, que encapsulará toda a lógica e os componentes da UI.
  - A função utilizará `st.session_state` para persistir os filtros e os resultados da busca entre as interações do usuário, evitando recarregamentos desnecessários.

### 4.3. Componentes da Interface (UI)

A tela será dividida em duas áreas principais: Filtros e Resultados.

1.  **Container de Filtros (`st.container`):**
    -   **Campo de Busca Principal:** Um `st.text_input` com o label "Buscar por Título ou ID do Leilão".
    -   **Filtros Adicionais (em colunas):**
        -   Um `st.multiselect` para "Status", populado com os valores do enum `EvaluationStatus` (ex: "Pendente", "Descartado", "Analisar").
        -   Um `st.multiselect` para "Estado (UF)". As opções serão carregadas dinamicamente.
    -   **Botão de Ação:** Um `st.button("Buscar Leilões")` para iniciar a consulta.

2.  **Área de Resultados:**
    -   Se a busca retornar resultados, eles serão renderizados em formato de "cards", reutilizando ou adaptando o componente `render_triage_cards` para consistência visual.
    -   **Destaque de Status:** Cada card exibirá uma "badge" ou um texto destacado indicando o status atual do leilão para aquele usuário (ex: `🟢 Analisar`, `🔴 Descartado`, `⚪ Pendente`).
    -   **Ação de Reversão:**
        -   Para cada leilão com o status **"DESCARTAR"**, um botão **"Reverter para Análise"** será exibido no card.
        -   Ao ser clicado, este botão irá:
            1.  Chamar o caso de uso `UpdateStatusUseCase` (já existente) para alterar o status do leilão para `ANALISAR`.
            2.  Exibir uma mensagem de sucesso (`st.toast`).
            3.  Limpar os resultados da busca do `st.session_state` para forçar o usuário a buscar novamente e ver o status atualizado.

### 4.4. Camada de Aplicação e Dependências

Para conectar o frontend ao backend, as seguintes peças serão criadas e registradas.

- **`src/application/use_cases.py`**:
    -   **Ação:** Criar a classe `SearchAllAuctionsUseCase`.
    -   **Lógica:** Esta classe receberá os parâmetros da UI, irá instanciar o dataclass `GlobalSearchFilter` e chamar o método `repository.search_all_auctions(...)`.

- **`src/presentation/streamlit_app/dependencies.py`**:
    -   **Ação:** Registrar o novo `SearchAllAuctionsUseCase` no container de serviços. Isso permitirá que a view `pesquisa.py` o acesse através do objeto `services` injetado.