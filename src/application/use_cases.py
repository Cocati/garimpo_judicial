from typing import List, Dict
from src.domain.models import Auction, AuctionFilter, Evaluation, EvaluationStatus, DetailedAnalysis
from src.application.interfaces import AuctionRepository

class GetPendingAuctionsUseCase:
    """Caso de uso: Recuperar fila de triagem para o usuário."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, user_id: str, uf: List[str] = None, cidade: List[str] = None, 
                tipo_bem: List[str] = None, site: List[str] = None) -> List[Auction]:
        filters = AuctionFilter(uf=uf, cidade=cidade, tipo_bem=tipo_bem, site=site)
        return self.repository.get_pending_auctions(user_id, filters)

class GetPortfolioUseCase:
    """Caso de uso: Recuperar itens aprovados ('Analisar') para a Carteira."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository
    
    def execute(self, user_id: str) -> List[Auction]:
        return self.repository.get_portfolio_auctions(user_id)

class GetDetailedAnalysisUseCase:
    """Caso de uso: Recuperar os dados da análise profunda (Jurídico/Financeiro)."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository
        
    def execute(self, user_id: str, site: str, id_leilao: str) -> DetailedAnalysis:
        return self.repository.get_detailed_analysis(user_id, site, id_leilao)

class SaveDetailedAnalysisUseCase:
    """Caso de uso: Salvar os dados do formulário de análise."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository
        
    def execute(self, analysis: DetailedAnalysis):
        return self.repository.save_detailed_analysis(analysis)

class SubmitBatchEvaluationUseCase:
    """Caso de uso: Processar a decisão do usuário (Descartar/Analisar)."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, user_id: str, items: List[dict], decision: EvaluationStatus) -> int:
        evaluations_to_save = []
        for item in items:
            evaluation = Evaluation(
                usuario_id=user_id,
                site=item['site'],
                id_leilao=item['id_leilao'],
                avaliacao=decision
            )
            evaluations_to_save.append(evaluation)
        return self.repository.save_evaluations(evaluations_to_save)
    
class GetFilterOptionsUseCase:
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self):
        return self.repository.get_filter_options()

class GetUserStatsUseCase:
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, user_id: str) -> Dict[str, int]:
        return self.repository.get_stats(user_id)

class GetPortfolio:
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, user_id: str) -> List[Auction]:
        return self.repository.get_portfolio_auctions(user_id)