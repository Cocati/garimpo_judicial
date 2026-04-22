from typing import List, Dict, Optional
from src.domain.models import Auction, AuctionFilter, Evaluation, EvaluationStatus, DetailedAnalysis, ScraperRunFilter
from src.application.interfaces import AuctionRepository
from src.domain.isj_calculator import IsjCalculator

class GetPendingAuctionsUseCase:
    """Caso de uso: Recuperar fila de triagem para o usuário."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, user_id: str, uf: List[str] = None, cidade: List[str] = None, 
                tipo_bem: List[str] = None, site: List[str] = None, status_imovel: List[str] = None) -> List[Auction]:
        filters = AuctionFilter(uf=uf, cidade=cidade, tipo_bem=tipo_bem, site=site, status_imovel=status_imovel)
        return self.repository.get_pending_auctions(user_id, filters)

class GetPortfolioAuctionsUseCase:
    """
    Caso de uso: Recuperar itens aprovados ('Analisar', 'Participar', 'No Bid') para a Carteira.
    NOTA: Renomeado de GetPortfolioUseCase para evitar erros de importação.
    """
    def __init__(self, repository: AuctionRepository):
        self.repository = repository
    
    def execute(self, user_id: str) -> List[Auction]:
        # Busca os leilões do repositório
        auctions = self.repository.get_portfolio_auctions(user_id)
        
        # Ordena: os que vencem mais cedo (menor data_ordenacao) no topo
        return sorted(auctions, key=lambda x: x.data_ordenacao)

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

class SaveAuditoriaRascunhoUseCase:
    """
    Caso de Uso: Salvar Rascunho.
    Apenas persiste os dados preenchidos pelo analista sem alterar o status do leilão.
    """
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, analysis: DetailedAnalysis) -> None:
        # Persiste no banco de dados via Upsert (conforme TASK-006)
        self.repository.save_auditoria_rascunho(analysis)


class FinalizarAuditoriaUseCase:
    """
    Caso de Uso: Finalizar Auditoria.
    Valida nulidades, calcula o ISJ final e move o leilão para a carteira apropriada.
    Ref: Spec Técnica Seção 4.2 e AC-2, AC-3, AC-4
    """
    def __init__(self, repository: AuctionRepository):
        self.repository = repository
        self.calculator = IsjCalculator()

    def execute(self, analysis: DetailedAnalysis, user_id: str) -> str:
        # AC-2 & AC-3: Bloqueio por Nulidade Absoluta
        if analysis.proc_citacao is False:
            raise ValueError("Não é possível finalizar: Nulidade de Citação detectada.")
        
        if analysis.mat_prop_confere is False:
            raise ValueError("Não é possível finalizar: Divergência de Proprietário na Matrícula.")

        # Calcula o Score Final
        isj_score = self.calculator.calculate(analysis)
        
        # Determina o novo status baseado no ISJ (AC-4)
        # ISJ > 60% -> PARTICIPAR | ISJ <= 60% -> NO_BID (Descartado)
        novo_status = EvaluationStatus.PARTICIPAR if isj_score > 60.0 else EvaluationStatus.NO_BID
        
        # 1. Salva os dados finais da análise
        self.repository.save_auditoria_rascunho(analysis)
        
        # 2. Atualiza o status do leilão na tabela de avaliações (tabela core)
        self.repository.update_status(
            user_id=user_id,
            site=analysis.site,
            id_leilao=analysis.id_leilao,
            new_status=novo_status
        )
        
        return novo_status.value
    
class DescartarAuditoriaUseCase:
    """
    Caso de Uso: Descartar Auditoria Detalhada.
    Interrompe o fluxo de análise e move o leilão para status de rejeição (NO_BID).
    Ref: Ciclo de Vida do Leilão (COMPONENTS.md)
    """
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, analysis: DetailedAnalysis, user_id: str) -> None:
        """
        Executa o descarte da análise atual.
        
        :param analysis: A entidade DetailedAnalysis atual da sessão.
        :param user_id: ID do usuário executando a ação.
        """
        # 1. Salva o rascunho atual para manter histórico de dados parciais preenchidos 
        # (auditoria passiva de motivos de descarte)
        self.repository.save_auditoria_rascunho(analysis)
        
        # 2. Atualiza o status do leilão para NO_BID (fim da linha na Aba 3)
        # O Enum DESCARTAR é exclusivo da Triagem (Aba 1). Na auditoria_v2 usamos NO_BID.
        self.repository.update_status(
            user_id=user_id,
            site=analysis.site,
            id_leilao=analysis.id_leilao,
            new_status=EvaluationStatus.NO_BID
        )

class GetScraperRunsUseCase:
    """Caso de uso: Recuperar dados de execução dos scrapers para monitoramento."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, start_date: Optional[str] = None, end_date: Optional[str] = None,
                sources: Optional[List[str]] = None, statuses: Optional[List[str]] = None) -> List[Dict]:
        filters = ScraperRunFilter(start_date=start_date, end_date=end_date, sources=sources, statuses=statuses)
        return self.repository.get_scraper_runs(filters)

class GetScraperSourcesUseCase:
    """Caso de uso: Obter a lista de nomes de fontes de scraper."""
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self) -> List[str]:
        return self.repository.get_scraper_sources()