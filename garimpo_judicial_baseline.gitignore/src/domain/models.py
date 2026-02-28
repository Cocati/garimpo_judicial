from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

class EvaluationStatus(str, Enum):
    PENDING = "PENDING"       # Ainda na triagem inicial
    ANALISAR = "ANALISAR"     # Triagem positiva (Aba 1)
    PARTICIPAR = "PARTICIPAR" # Aprovado no detalhe (Aba 2)
    DESCARTAR = "DESCARTAR"   # Rejeitado na triagem
    NO_BID = "NO_BID"         # Rejeitado na análise detalhada (Aba 3)

@dataclass
class Auction:
    site: str
    id_leilao: str
    titulo: str
    uf: str
    cidade: str
    tipo_leilao: str
    tipo_bem: str
    valor_1_praca: float
    valor_2_praca: float
    link_detalhe: str
    imagem_capa: str
    # --- NOVOS CAMPOS ---
    data_1_praca: Optional[datetime] = None
    data_2_praca: Optional[datetime] = None
    status_carteira: Optional[str] = None

    @property
    def unique_id(self) -> str:
        """Identificador único composto para uso interno."""
        return f"{self.site}_{self.id_leilao}"

@dataclass
class AuctionFilter:
    """Objeto de valor para transporte de critérios de filtro."""
    # Alterado de str para List[str] para suportar seleção múltipla
    uf: Optional[List[str]] = None
    cidade: Optional[List[str]] = None
    tipo_bem: Optional[List[str]] = None
    site: Optional[List[str]] = None
    tipo_leilao: Optional[List[str]] = None

@dataclass
class Evaluation:
    """Entidade que representa a decisão do analista."""
    usuario_id: str
    site: str
    id_leilao: str
    avaliacao: EvaluationStatus
    data_analise: datetime = field(default_factory=datetime.now)
    
class RiskLevel(str, Enum):
    """Nível de risco jurídico."""
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"

class OccupationStatus(str, Enum):
    """Status de ocupação do imóvel."""
    VAGO = "Vago"
    OCUPADO_PROPRIETARIO = "Ocupado (Proprietário)"
    OCUPADO_INQUILINO = "Ocupado (Inquilino)"
    ESCONHECIDO = "Desconhecido"  # <--- ADICIONE ESTA LINHA

@dataclass
class DetailedAnalysis:
    """
    Entidade para a Fase 2: Análise Jurídica e Financeira Profunda.
    """
    site: str
    id_leilao: str
    usuario_id: str
    
    # --- JURÍDICO ---
    parecer_juridico: Optional[str] = None
    risco_judicial: Optional[RiskLevel] = RiskLevel.BAIXO
    reu_citado: bool = True
    intimacao_credores: bool = True
    
    # --- DÍVIDAS ---
    divida_condominio: float = 0.0
    divida_iptu: float = 0.0
    divida_subroga: bool = True # Se True, quem compra NÃO paga a dívida anterior
    
    # --- IMÓVEL / FINANCEIRO ---
    ocupacao_status: Optional[OccupationStatus] = OccupationStatus.VAGO
    valor_venda_estimado: float = 0.0
    custo_reforma: float = 0.0
    custo_desocupacao: float = 0.0
    
    data_atualizacao: datetime = field(default_factory=datetime.now)
