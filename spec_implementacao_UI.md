# Especificação Técnica: Migração da UI para API Node.js

Este documento descreve as APIs necessárias para substituir a atual interface de usuário baseada em Streamlit por um backend Node.js, que servirá uma nova interface de usuário (frontend).

## 1. Autenticação

### POST /login
- **Descrição:** Autentica um usuário e retorna um token JWT.
- **Request Body:**
  ```json
  {
    "username": "user",
    "password": "password"
  }
  ```
- **Response Body (Sucesso):**
  ```json
  {
    "token": "jwt_token"
  }
  ```
- **Response (Erro):** `401 Unauthorized`

### GET /me
- **Descrição:** Retorna informações sobre o usuário autenticado.
- **Autenticação:** Token JWT no header `Authorization`.
- **Response Body (Sucesso):**
  ```json
  {
    "user_id": "Julio",
    "name": "Julio"
  }
  ```
- **Response (Erro):** `401 Unauthorized`

## 2. Leilões (Triagem)

### GET /auctions
- **Descrição:** Retorna uma lista de leilões para a página de triagem, com opções de filtro.
- **Autenticação:** Token JWT.
- **Query Parameters:**
  - `uf` (string, opcional): Filtra por estado (UF).
  - `cidade` (string, opcional): Filtra por cidade.
  - `tipo_bem` (string, opcional): Filtra por tipo de bem.
  - `site` (string, opcional): Filtra por site de origem.
- **Response Body (Sucesso):**
  ```json
  [
    {
      "id_leilao": "123",
      "site": "megaleiloes",
      "titulo": "Apartamento em Copacabana",
      "cidade": "Rio de Janeiro",
      "uf": "RJ",
      "imagem_capa": "url_da_imagem"
    }
  ]
  ```

### POST /auctions/evaluate
- **Descrição:** Submete as decisões de triagem (analisar/descartar) para um lote de leilões.
- **Autenticação:** Token JWT.
- **Request Body:**
  ```json
  {
    "user_id": "Julio",
    "decisions": [
      { "site": "megaleiloes", "id_leilao": "123", "decision": "ANALISAR" },
      { "site": "megaleiloes", "id_leilao": "456", "decision": "DESCARTAR" }
    ]
  }
  ```
- **Response (Sucesso):** `200 OK`
- **Response (Erro):** `400 Bad Request`, `500 Internal Server Error`

## 3. Carteira

### GET /portfolio
- **Descrição:** Retorna a carteira de leilões do usuário, categorizada por status.
- **Autenticação:** Token JWT.
- **Response Body (Sucesso):**
  ```json
  {
    "ANALISAR": [
      { "site": "megaleiloes", "id_leilao": "123", "titulo": "Apartamento...", "status_carteira": "ANALISAR", ... }
    ],
    "PARTICIPAR": [
      { "site": "sodresantoro", "id_leilao": "789", "titulo": "Casa...", "status_carteira": "PARTICIPAR", ... }
    ],
    "NO_BID": [
      { "site": "freitasleiloeiro", "id_leilao": "101", "titulo": "Terreno...", "status_carteira": "NO_BID", ... }
    ]
  }
  ```

### GET /portfolio/{site}/{id_leilao}
- **Descrição:** Retorna os detalhes de um leilão específico na carteira.
- **Autenticação:** Token JWT.
- **Response Body (Sucesso):**
  ```json
  {
    "site": "megaleiloes",
    "id_leilao": "123",
    "titulo": "Apartamento...",
    ...
  }
  ```

### PUT /portfolio/{site}/{id_leilao}
- **Descrição:** Atualiza os dados principais de um leilão.
- **Autenticação:** Token JWT.
- **Request Body:**
  ```json
  {
    "titulo": "Novo Título",
    "valor_1_praca": 100000,
    "valor_2_praca": 50000,
    "data_1_praca": "2026-01-01T00:00:00Z",
    "data_2_praca": "2026-01-15T00:00:00Z"
  }
  ```
- **Response (Sucesso):** `200 OK`

## 4. Auditoria

### GET /audit/{site}/{id_leilao}
- **Descrição:** Retorna os dados detalhados da análise de auditoria para um leilão.
- **Autenticação:** Token JWT.
- **Response Body (Sucesso):**
  ```json
  {
    "site": "megaleiloes",
    "id_leilao": "123",
    "usuario_id": "Julio",
    "proc_num": "12345-67.2023.8.26.0001",
    ...
  }
  ```

### POST /audit/{site}/{id_leilao}/draft
- **Descrição:** Salva um rascunho da análise de auditoria.
- **Autenticação:** Token JWT.
- **Request Body:** O objeto `DetailedAnalysis` completo.
- **Response (Sucesso):** `200 OK`

### POST /audit/{site}/{id_leilao}/finalize
- **Descrição:** Finaliza a análise de auditoria.
- **Autenticação:** Token JWT.
- **Request Body:** O objeto `DetailedAnalysis` completo.
- **Response (Sucesso):** `200 OK`

### POST /audit/{site}/{id_leilao}/discard
- **Descrição:** Descarta a análise de auditoria e o leilão.
- **Autenticação:** Token JWT.
- **Response (Sucesso):** `200 OK`

## 5. Filtros e Estatísticas

### GET /filters
- **Descrição:** Retorna as opções disponíveis para os filtros de triagem.
- **Autenticação:** Token JWT.
- **Response Body (Sucesso):**
  ```json
  {
    "ufs": ["SP", "RJ", "MG"],
    "cidades": ["São Paulo", "Rio de Janeiro", "Belo Horizonte"],
    "tipos": ["Apartamento", "Casa", "Terreno"],
    "sites": ["megaleiloes", "sodresantoro"]
  }
  ```

### GET /stats
- **Descrição:** Retorna as estatísticas de produtividade do usuário.
- **Autenticação:** Token JWT.
- **Response Body (Sucesso):**
  ```json
  {
    "total_processado": 100,
    "analisar": 20
  }
  ```
