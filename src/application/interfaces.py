from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from src.domain.models import Auction, AuctionFilter, Evaluation, DetailedAnalysis


class AuctionRepository(ABC):
    """
    Contrato (Interface) para acesso a dados de leilões.
    Qualquer banco de dados (Postgres, Mongo, Memory) deve implementar isso.
    """

    @abstractmethod
    def get_pending_auctions(self, user_id: str, filters: AuctionFilter) -> List[Auction]:
        """
        Retorna leilões que correspondem aos filtros E que ainda não foram
        avaliados pelo usuário específico.
        """
        pass

    @abstractmethod
    def save_evaluations(self, evaluations: List[Evaluation]) -> int:
        """
        Persiste uma lista de avaliações (Batch update).
        Retorna o número de registros salvos.
        """
        pass
        
    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """Retorna dados agregados para o dashboard."""
        pass
    
    @abstractmethod
    def get_stats(self, user_id: str) -> dict:
        """Corrigido: agora aceita user_id para estatísticas segmentadas."""
        pass

    @abstractmethod
    def save_auditoria_rascunho(self, analysis: DetailedAnalysis) -> None:
        """Persiste os dados da análise sem alterar o status do leilão."""
        pass

    @abstractmethod
    def get_detailed_analysis(self, site: str, id_leilao: str, user_id: str) -> Optional[DetailedAnalysis]:
        """Recupera a análise completa mapeada para o domínio."""
        pass