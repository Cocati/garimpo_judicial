import streamlit as st
from src.infra.database.config import SessionLocal
from src.infra.repositories.postgres_repo import PostgresAuctionRepository

# Importa todos os Use Cases necessários
from src.application.use_cases import (
    GetPendingAuctionsUseCase, 
    SubmitBatchEvaluationUseCase, 
    GetFilterOptionsUseCase,
    GetUserStatsUseCase,
    GetPortfolioUseCase,         # <--- Garanta que esta vírgula existe
    GetDetailedAnalysisUseCase,
    SaveDetailedAnalysisUseCase,
    GetPortfolio
)

@st.cache_resource
def get_services():
    """
    Factory de Serviços: Inicializa o Banco e injeta nos Use Cases.
    """
    # Cria a sessão do banco
    db_session = SessionLocal()
    
    # Inicializa o repositório com a sessão
    repo = PostgresAuctionRepository(db_session)
    
    # Retorna o dicionário de serviços prontos para uso
    return {
        "repo": repo, # Acesso direto ao repo (se necessário para debug)
        
        # --- FASE 1: TRIAGEM ---
        "get_auctions": GetPendingAuctionsUseCase(repo),
        "submit_eval": SubmitBatchEvaluationUseCase(repo),
        "get_filters": GetFilterOptionsUseCase(repo),
        "get_stats": GetUserStatsUseCase(repo),
        
        # --- FASE 2: CARTEIRA E ANÁLISE ---
        "get_portfolio": GetPortfolioUseCase(repo),
        "get_analysis": GetDetailedAnalysisUseCase(repo),
        "save_analysis": SaveDetailedAnalysisUseCase(repo),
        # --- NOVOS REGISTROS ---
        "get_portfolio_auctions": GetPortfolio(repo), # Resolve o KeyError atual
        "repo": repo # Necessário para o acesso direto feito na carteira.py (save_detailed_analysis)
    }
