import streamlit as st
from src.infra.database.config import SessionLocal
from src.infra.repositories.postgres_repo import PostgresAuctionRepository

# Importa TODOS os Use Cases (Triagem + Carteira + Auditoria)
from src.application.use_cases import (
    # --- Fase 1: Triagem ---
    GetPendingAuctionsUseCase, 
    SubmitBatchEvaluationUseCase, 
    GetFilterOptionsUseCase,  # <--- O erro estava aqui (faltava injetar este)
    GetUserStatsUseCase,      # <--- Necessário para a sidebar do main.py

    # --- Fase 2: Carteira ---
    GetPortfolioAuctionsUseCase, 
    
    # --- Fase 3: Auditoria V2 ---
    SaveAuditoriaRascunhoUseCase,
    FinalizarAuditoriaUseCase,
    DescartarAuditoriaUseCase,

    # --- Monitoramento ---
    GetScraperRunsUseCase,
    GetScraperSourcesUseCase
)

@st.cache_resource
def get_services():
    """
    Factory de Serviços Unificada:
    Inicializa o Banco e injeta dependências para TODAS as telas do sistema.
    """
    # 1. Cria a sessão do banco
    db_session = SessionLocal()
    
    # 2. Inicializa o repositório com a sessão
    repo = PostgresAuctionRepository(db_session)
    
    # 3. Retorna o dicionário de serviços
    return {
        # --- INFRAESTRUTURA (Acesso Direto) ---
        "repository": repo, 

        # --- FASE 1: TRIAGEM (Usado no main.py) ---
        "get_filters": GetFilterOptionsUseCase(repo),       # Resolve o KeyError: 'get_filters'
        "get_stats": GetUserStatsUseCase(repo),             # Resolve a sidebar
        "get_auctions": GetPendingAuctionsUseCase(repo),    # Busca leilões pendentes
        "submit_eval": SubmitBatchEvaluationUseCase(repo),  # Salva decisões da triagem
        
        # --- FASE 2: CARTEIRA (Usado no carteira.py) ---
        "get_portfolio_auctions": GetPortfolioAuctionsUseCase(repo),
        
        # --- FASE 3: AUDITORIA V2 (Usado no auditoria_v2.py) ---
        "save_rascunho": SaveAuditoriaRascunhoUseCase(repo),
        "finalizar_auditoria": FinalizarAuditoriaUseCase(repo),
        'descartar_auditoria': DescartarAuditoriaUseCase(repo),

        # --- MONITORAMENTO (Usado no monitoramento.py) ---
        "get_scraper_runs": GetScraperRunsUseCase(repo),
        "get_scraper_sources": GetScraperSourcesUseCase(repo)
    }