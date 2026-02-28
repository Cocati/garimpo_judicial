from abc import ABC, abstractmethod
from typing import List, Dict
from src.domain.models import Auction, AuctionFilter, Evaluation

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
