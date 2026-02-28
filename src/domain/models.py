from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

# --- ENUMS DE APOIO ---

class EvaluationStatus(str, Enum):
    PENDING = "PENDING"       # Ainda na triagem inicial
    ANALISAR = "ANALISAR"     # Triagem positiva (Aba 1)
    PARTICIPAR = "PARTICIPAR" # Aprovado no detalhe (Aba 2)
    DESCARTAR = "DESCARTAR"   # Rejeitado na triagem
    NO_BID = "NO_BID"         # Rejeitado na análise detalhada (Aba 3)

class RiskLevel(str, Enum):
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"

class OccupationStatus(str, Enum):
    VAGO = "Vago"
    OCUPADO_PROPRIETARIO = "Ocupado (Proprietário)"
    OCUPADO_INQUILINO = "Ocupado (Inquilino)"
    DESCONHECIDO = "Desconhecido"

class ConjugeStatus(str, Enum):
    SIM = "S"
    NAO = "N"
    NA = "N/A"

class NaturezaExecucao(str, Enum):
    DEFINITIVA = "Definitiva"
    PROVISORIA = "Provisória"

class EspecieCredito(str, Enum):
    CONDOMINIAL = "Condominial"
    COMUM = "Comum"
    TRABALHISTA = "Trabalhista"

# --- ENTIDADES CORE ---

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
    data_1_praca: Optional[datetime] = None
    data_2_praca: Optional[datetime] = None
    status_carteira: Optional[str] = None

    @property
    def unique_id(self) -> str:
        return f"{self.site}_{self.id_leilao}"
        
    @property
    def data_ordenacao(self) -> datetime:
        datas = [d for d in [self.data_1_praca, self.data_2_praca] if d is not None]
        return max(datas) if datas else datetime.max

@dataclass
class AuctionFilter:
    uf: Optional[List[str]] = None
    cidade: Optional[List[str]] = None
    tipo_bem: Optional[List[str]] = None
    site: Optional[List[str]] = None
    tipo_leilao: Optional[List[str]] = None

@dataclass
class Evaluation:
    usuario_id: str
    site: str
    id_leilao: str
    avaliacao: EvaluationStatus
    data_analise: datetime = field(default_factory=datetime.now)

# --- ENTIDADE DE AUDITORIA DETALHADA (V2.0) ---

@dataclass
class DetailedAnalysis:
    """
    Representa a análise detalhada unificada.
    Integra a estrutura da V2.0 preservando campos para compatibilidade com dados V1.0.
    """
    site: str
    id_leilao: str
    usuario_id: str
    
    # --- Seção 1: Processo Judicial ---
    proc_num: Optional[str] = None
    proc_executados: List[str] = field(default_factory=list)
    proc_adv_exec: Optional[bool] = None
    proc_citacao: Optional[bool] = None
    proc_conjuge: Optional[ConjugeStatus] = None
    proc_credores: Optional[bool] = None
    proc_recursos: Optional[bool] = None
    proc_recursos_obs: Optional[str] = None
    proc_coproprietario_intimado: Optional[bool] = None
    proc_natureza_execucao: Optional[NaturezaExecucao] = None
    proc_justica_gratuita: Optional[bool] = None
    proc_especie_credito: Optional[EspecieCredito] = None
    proc_debito_atualizado: float = 0.0
    proc_avaliacao_imovel: Optional[bool] = None

    # --- Seção 2: Matrícula e Gravames ---
    mat_num: Optional[str] = None
    mat_proprietario: List[str] = field(default_factory=list)
    mat_penhoras: List[str] = field(default_factory=list)
    mat_conjugue: Optional[bool] = None
    mat_prop_confere: Optional[bool] = None
    mat_proprietario_pj: Optional[bool] = None
    mat_penhora_averbada: Optional[bool] = None
    mat_usufruto: Optional[bool] = None
    mat_indisp: Optional[bool] = None
    mat_vagas_mat: Optional[bool] = None

    # --- Seção 3: Edital e Dívidas ---
    edt_objeto: Optional[str] = None
    edt_vlr_avaliacao: float = 0.0
    edt_percentual_minimo: Optional[float] = None
    edt_data_avaliacao: Optional[date] = None
    edt_parcelamento: Optional[bool] = None
    edt_iptu_subroga: Optional[bool] = None
    edt_condo_claro: Optional[bool] = None

    # --- Seção 4: Situação Física ---
    edt_posse_status: Optional[str] = None # Mapeado do ocupacao_status legado
    edt_posse_estrategia: Optional[str] = None

    # --- Seção 5: Financeiro ---
    fin_lance: float = 0.0
    fin_itbi: float = 0.0
    fin_dividas: float = 0.0
    recomendacao_ia: Optional[str] = None

    # --- Seção 6: Legado e Compatibilidade ---
    analise_ia: Optional[str] = None  # Antigo parecer_juridico
    risco_judicial: Optional[RiskLevel] = RiskLevel.BAIXO
    valor_venda_estimado: float = 0.0
    custo_reforma: float = 0.0
    custo_desocupacao: float = 0.0
    divida_condominio: float = 0.0
    divida_iptu: float = 0.0
    divida_subroga: bool = False
    data_atualizacao: Optional[datetime] = field(default_factory=datetime.now)

    # --- Propriedades de Compatibilidade (Getters) ---
    @property
    def reu_citado(self) -> bool:
        """Alias para manter compatibilidade com lógica antiga."""
        return self.proc_citacao if self.proc_citacao is not None else True

    @property
    def intimacao_credores(self) -> bool:
        """Alias para manter compatibilidade com lógica antiga."""
        return self.proc_credores if self.proc_credores is not None else True