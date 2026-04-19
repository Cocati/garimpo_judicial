from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

# --- ENUMS DE APOIO ---

class EvaluationStatus(str, Enum):
    """
    Possíveis status de avaliação.

    :param PENDING: Ainda na triagem inicial.
    :param ANALISAR: Triagem positiva (Aba 1).
    :param PARTICIPAR: Aprovado no detalhe (Aba 2).
    :param DESCARTAR: Rejeitado na triagem.
    :param NO_BID: Rejeitado na análise detalhada (Aba 3).
    """
    PENDING = "PENDING"       # Ainda na triagem inicial
    ANALISAR = "ANALISAR"     # Triagem positiva (Aba 1)
    PARTICIPAR = "PARTICIPAR" # Aprovado no detalhe (Aba 2)
    DESCARTAR = "DESCARTAR"   # Rejeitado na triagem
    NO_BID = "NO_BID"         # Rejeitado na análise detalhada (Aba 3)

class NoBidReason(str, Enum):
    """Motivos para descarte na análise detalhada (NO_BID)."""
    RISCO_JURIDICO = "Risco Jurídico/Processual"
    PROBLEMA_MATRICULA = "Ônus/Problema na Matrícula"
    CONDICAO_FINANCEIRA = "Condição Financeira/Pagamento"
    ESTRATEGIA_CAPITAL = "Estratégia/Capital Indisponível"
    SITUACAO_IMOVEL = "Situação Física/Ocupação do Imóvel"
    NULIDADE_CRITICA = "Nulidade Crítica Impeditiva"
    OUTRO = "Outro"

class RiskLevel(str, Enum):
    """
    Níveis de risco.

    :param BAIXO: Risco baixo.
    :param MEDIO: Risco médio.
    :param ALTO: Risco alto.
    """
    BAIXO = "Baixo"
    MEDIO = "Médio"
    ALTO = "Alto"

class OccupationStatus(str, Enum):
    """
    Status de ocupação.

    :param VAGO: Casa vaga.
    :param OCUPADO_PROPRIETARIO: Casa ocupada pelo proprietário.
    :param OCUPADO_INQUILINO: Casa ocupada por inquilino.
    :param DESCONHECIDO: Status desconhecido.
    """
    VAGO = "Vago"
    OCUPADO_PROPRIETARIO = "Ocupado (Proprietário)"
    OCUPADO_INQUILINO = "Ocupado (Inquilino)"
    DESCONHECIDO = "Desconhecido"

class ConjugeStatus(str, Enum):
    """
    Status do cônjuge.

    :param SIM: Cônjuge presente.
    :param NAO: Cônjuge não presente.
    :param NA: Não aplicável.
    """
    SIM = "S"
    NAO = "N"
    NA = "N/A"

class NaturezaExecucao(str, Enum):
    """
    Tipos de natureza de execução.

    :param DEFINITIVA: Execução definitiva.
    :param PROVISORIA: Execução provisória.
    """
    DEFINITIVA = "Definitiva"
    PROVISORIA = "Provisória"

class EspecieCredito(str, Enum):
    """
    Tipos de espécie de crédito.

    :param CONDOMINIAL: Crédito condominial.
    :param COMUM: Crédito comum.
    :param TRABALHISTA: Crédito trabalhista.
    """
    CONDOMINIAL = "Condominial"
    COMUM = "Comum"
    TRABALHISTA = "Trabalhista"

# --- ENTIDADES CORE ---

@dataclass
class Auction:
    """
    Representa um leilão.

    :param site: Nome do site onde o leilão ocorre.
    :param id_leilao: Identificador único do leilão.
    :param titulo: Título do leilão.
    :param uf: Unidade Federativa onde o leilão ocorre.
    :param cidade: Cidade onde o leilão ocorre.
    :param tipo_leilao: Tipo de leilão (e.g., licitação).
    :param tipo_bem: Tipo do bem a ser vendido (e.g., imóvel).
    :param valor_1_praca: Valor da primeira praca do leilão.
    :param valor_2_praca: Valor da segunda praca do leilão (se houver).
    :param link_detalhe: Link para detalhes do leilão.
    :param imagem_capa: URL da imagem de capa do leilão.
    :param data_1_praca: Data da primeira praca do leilão (opcional).
    :param data_2_praca: Data da segunda praca do leilão (opcional).
    :param status_carteira: Status da carteira do leilão (opcional).
    """
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
    no_bid_reason: Optional[str] = None

    @property
    def unique_id(self) -> str:
        """
        Retorna uma string única identificando o leilão.

        :return: Identificador único do leilão.
        :rtype: str
        """
        return f"{self.site}_{self.id_leilao}"
        
    @property
    def data_ordenacao(self) -> datetime:
        """
        Retorna a maior data entre as pracas disponíveis.

        :return: Maior data das pracas.
        :rtype: datetime
        """
        datas = [d for d in [self.data_1_praca, self.data_2_praca] if d is not None]
        return max(datas) if datas else datetime.max

@dataclass
class AuctionFilter:
    """
    Filtros para busca de leilões.

    :param uf: Lista de estados para filtro.
    :param cidade: Lista de cidades para filtro (opcional).
    :param tipo_bem: Lista de tipos de bem para filtro (opcional).
    :param site: Lista de sites para filtro (opcional).
    :param tipo_leilao: Lista de tipos de leilão para filtro (opcional).
    """
    uf: Optional[List[str]] = None
    cidade: Optional[List[str]] = None
    tipo_bem: Optional[List[str]] = None
    site: Optional[List[str]] = None
    tipo_leilao: Optional[List[str]] = None

@dataclass
class Evaluation:
    """
    Representa a avaliação de um leilão.

    :param usuario_id: ID do usuário que fez a avaliação.
    :param site: Nome do site onde o leilão ocorre.
    :param id_leilao: Identificador único do leilão.
    :param avaliacao: Status da avaliação (PENDING, ANALISAR, PARTICIPAR, DESCARTAR, NO_BID).
    :param data_analise: Data em que a avaliação foi realizada (padrão é a data atual).
    """
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

    :param site: Nome do site onde o leilão ocorre.
    :param id_leilao: Identificador único do leilão.
    :param usuario_id: ID do usuário que fez a avaliação.
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

    # --- OUTROS CAMPOS (V2.0) ---
    vlr_avaliacao: float = 0.0
    risco_judicial: str = "Baixo"
    parecer_juridico: Optional[str] = None
    data_atualizacao: datetime = field(default_factory=datetime.now)

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
    # --- Novos Campos: Seção Matrícula (03/03/2026) ---
    mat_documentos_proprietarios: List[str] = field(default_factory=list)


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
    #edt_posse_estrategia: Optional[str] = None

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

    # --- Novos Campos: Motivo do Descarte (NO_BID) ---
    no_bid_reason: Optional[NoBidReason] = None
    no_bid_observation: Optional[str] = None

    # --- Propriedades de Compatibilidade (Getters) ---
    @property
    def reu_citado(self) -> bool:

        """
        Alias para manter compatibilidade com lógica antiga.

        :return: Status de citação do réu.
        :rtype: bool
        """
        return self.proc_citacao if self.proc_citacao is not None else True

    @property
    def intimacao_credores(self) -> bool:

        """
        Alias para manter compatibilidade com lógica antiga.

        :return: Status de intimação dos credores.
        :rtype: bool
        """
        return self.proc_credores if self.proc_credores is not None else True
    
    @property
    def proc_proporcionalidade(self) -> float:
        """
        Calcula o Índice de Proporcionalidade: (Dívida / Avaliação) * 100.
        Regra de Negócio: Se a avaliação for zero, retorna 0.0 para evitar ZeroDivisionError.
        """
        if not self.vlr_avaliacao or self.vlr_avaliacao == 0:
            return 0.0
        return (self.proc_debito_atualizado / self.vlr_avaliacao) * 100