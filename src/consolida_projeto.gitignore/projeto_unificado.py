
# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/consolida.py ====
#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

def _coletar_py(raiz: Path, ignorar_dirs: set):
    for p in raiz.rglob("*.py"):
        # pula se alguma parte do caminho estiver na lista de ignorados
        if any(part in ignorar_dirs for part in p.parts):
            continue
        yield p

def consolidar(raiz: str, saida: str, ignorar_dirs: set):
    raiz_path = Path(raiz).resolve()
    saida_path = Path(saida).resolve()

    arquivos = [p for p in _coletar_py(raiz_path, ignorar_dirs) if p.resolve() != saida_path]
    print(f"🔎 Encontrados {len(arquivos)} arquivos .py sob '{raiz_path}'")

    if not arquivos:
        print("⚠️ Nenhum arquivo .py encontrado (ou tudo foi ignorado).")
        return 1

    with open(saida_path, "w", encoding="utf-8") as w:
        for i, p in enumerate(arquivos, 1):
            print(f"[{i}/{len(arquivos)}] Processando: {p}")
            try:
                conteudo = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                print(f"⚠️ Erro ao ler {p}: {e}", file=sys.stderr)
                continue
            w.write(f"\n# ==== Início do arquivo: {p} ====\n")
            w.write(conteudo)
            w.write(f"\n# ==== Fim do arquivo: {p} ====\n")

    print(f"✅ Saída escrita em: {saida_path}")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Consolida todos os .py em um único arquivo.")
    parser.add_argument("--root", default=".", help="Pasta raiz do projeto (default: .)")
    parser.add_argument("--out", default="projeto_unificado.py", help="Arquivo de saída")
    parser.add_argument(
        "--ignore", nargs="*", default=[
            "__pycache__", ".git", ".idea", ".venv", "venv", "env",
            "build", "dist", "site-packages"  # adicione "Lib" aqui se quiser pular essa pasta
        ],
        help="Nomes de pastas a ignorar (separadas por espaço)."
    )
    args = parser.parse_args()
    # transforma em set para busca mais rápida
    ignorar = set(args.ignore)
    sys.exit(consolidar(args.root, args.out, ignorar))

if __name__ == "__main__":
    main()


# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/consolida.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/__init__.py ====

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/__init__.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/use_cases.py ====
from typing import List, Dict
from src.domain.models import Auction, AuctionFilter, Evaluation, EvaluationStatus, DetailedAnalysis
from src.application.interfaces import AuctionRepository
from src.domain.isj_calculator import IsjCalculator

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
        # Busca os leilões do repositório
        auctions = self.repository.get_portfolio_auctions(user_id)
        
        # Ordena: os que vencem mais cedo (menor data_ordenacao) no topo
        # Usamos .sort() para performance ou sorted() para imutabilidade
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

class GetPortfolio:
    def __init__(self, repository: AuctionRepository):
        self.repository = repository

    def execute(self, user_id: str) -> List[Auction]:
        return self.repository.get_portfolio_auctions(user_id)

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
        self.repository.update_evaluation_status(
            user_id=user_id,
            site=analysis.site,
            id_leilao=analysis.id_leilao,
            new_status=novo_status
        )
        
        return novo_status.value
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/use_cases.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/interfaces.py ====
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
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/interfaces.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/__init__.py ====

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/__init__.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/models.py ====
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
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/models.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/isj_calculator.py ====
# Arquivo: src/domain/isj_calculator.py
from typing import List
from src.domain.models import DetailedAnalysis, NaturezaExecucao, EspecieCredito, ConjugeStatus

class IsjCalculator:
    """
    Calcula o Índice de Segurança Jurídica (ISJ) com base em regras de dedução.
    Ref: Spec Técnica Seção 4.2
    """

    @staticmethod
    def calculate(analysis: DetailedAnalysis) -> float:
        """
        Executa o cálculo do score de 0 a 100%.
        Campos com valor None são ignorados (não deduzem pontos).
        """
        # Regras de Nulidade Imediata (Hard Stop)
        if analysis.proc_citacao is False:
            return 0.0
        if analysis.mat_prop_confere is False:
            return 0.0

        score = 100.0

        # --- Deduções Seção 1: Processo ---
        if analysis.proc_conjuge == ConjugeStatus.NAO:
            score -= 50.0
        if analysis.proc_natureza_execucao == NaturezaExecucao.PROVISORIA:
            score -= 20.0
        if analysis.proc_especie_credito == EspecieCredito.COMUM:
            score -= 15.0
        if analysis.proc_recursos is True:
            score -= 20.0
        if analysis.proc_justica_gratuita is True:
            score -= 10.0
        if analysis.proc_credores is False:
            score -= 20.0
        if analysis.proc_coproprietario_intimado is False:
            score -= 40.0

        # Cálculo de Proporcionalidade do Débito
        if analysis.edt_vlr_avaliacao > 0:
            proporcionalidade = (analysis.proc_debito_atualizado / analysis.edt_vlr_avaliacao) * 100
            if proporcionalidade < 10.0:
                score -= 15.0

        # --- Deduções Seção 2: Matrícula ---
        if analysis.mat_indisp is True:
            score -= 30.0
        if analysis.mat_usufruto is True:
            score -= 60.0

        # --- Deduções Seção 3: Edital ---
        if analysis.edt_condo_claro is False:
            score -= 15.0
        if analysis.edt_iptu_subroga is False:
            score -= 20.0
        
        # Validação de data da avaliação (mais de 1 ano)
        if analysis.edt_data_avaliacao:
            from datetime import date
            anos_passados = (date.today() - analysis.edt_data_avaliacao).days / 365.25
            if anos_passados > 1.0:
                score -= 10.0

        # Garantir limites [0, 100]
        return max(0.0, min(100.0, score))

    @staticmethod
    def calculate_financial_kpis(analysis: DetailedAnalysis) -> dict:
        """
        Calcula KPIs financeiros derivados para o Painel de Viabilidade.
        """
        comissao = analysis.fin_lance * 0.05
        custos_fixos = analysis.edt_vlr_avaliacao * 0.02  # Estimativa de custos cartorários
        
        investimento_total = (
            analysis.fin_lance + 
            comissao + 
            analysis.fin_itbi + 
            analysis.fin_dividas + 
            analysis.custo_reforma + 
            custos_fixos
        )

        roi_nominal = 0.0
        if investimento_total > 0:
            roi_nominal = ((analysis.valor_venda_estimado - investimento_total) / investimento_total) * 100

        return {
            "investimento_total": investimento_total,
            "roi_nominal": roi_nominal,
            "preco_vil": analysis.edt_vlr_avaliacao * (analysis.edt_percentual_minimo or 0.5)
        }
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/isj_calculator.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/__init__.py ====

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/__init__.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/__init__.py ====

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/__init__.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/unit/test_auditoria_use_cases.py ====
from unittest.mock import Mock
import pytest
from src.application.use_cases import FinalizarAuditoriaUseCase
from src.domain.models import DetailedAnalysis, EvaluationStatus

def test_finalizar_auditoria_bloqueia_nulidade():
    repo = Mock()
    use_case = FinalizarAuditoriaUseCase(repo)
    analysis = DetailedAnalysis(site="x", id_leilao="1", usuario_id="u", proc_citacao=False)
    
    with pytest.raises(ValueError, match="Nulidade de Citação"):
        use_case.execute(analysis, "user123")

def test_finalizar_auditoria_status_participar_isj_alto():
    repo = Mock()
    use_case = FinalizarAuditoriaUseCase(repo)
    # Análise limpa (Score 100)
    analysis = DetailedAnalysis(site="x", id_leilao="1", usuario_id="u", proc_citacao=True, mat_prop_confere=True)
    
    status = use_case.execute(analysis, "user123")
    
    assert status == EvaluationStatus.PARTICIPAR.value
    repo.update_evaluation_status.assert_called_once()
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/unit/test_auditoria_use_cases.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/unit/test_use_cases.py ====
import pytest
from unittest.mock import Mock
from datetime import datetime

# IMPORTANTE: Estas são as classes que estavam faltando (causando o NameError)
from src.domain.models import Auction, Evaluation, EvaluationStatus, AuctionFilter
# Importação dos Casos de Uso
from src.application.use_cases import (
    GetPendingAuctionsUseCase, 
    SubmitBatchEvaluationUseCase, 
    GetPortfolioUseCase
)

class TestAuctionsUseCases:
    
    def setup_method(self):
        # Mock do repositório para isolar a lógica de negócio do Banco de Dados
        self.mock_repo = Mock()
        
    def test_get_pending_auctions_should_call_repository_with_correct_filters(self):
        """
        Garante que o Use Case repassa os filtros corretamente para o Repositório.
        """
        use_case = GetPendingAuctionsUseCase(self.mock_repo)
        user_id = "user_123"
        uf_filter = ["SP"]
        
        # Act
        use_case.execute(user_id=user_id, uf=uf_filter)
        
        # Assert
        args, _ = self.mock_repo.get_pending_auctions.call_args
        called_user_id, called_filter = args
        
        assert called_user_id == user_id
        assert called_filter.uf == uf_filter
        # Aqui não dará mais NameError, pois AuctionFilter foi importado no topo
        assert isinstance(called_filter, AuctionFilter)

    def test_submit_batch_evaluation_should_create_evaluations_correctly(self):
        """
        Verifica se o processamento de lote converte dicts em entidades de Evaluation.
        """
        use_case = SubmitBatchEvaluationUseCase(self.mock_repo)
        user_id = "user_test"
        items = [
            {'site': 'leiloeiro_a', 'id_leilao': '101'},
            {'site': 'leiloeiro_b', 'id_leilao': '102'}
        ]
        decision = EvaluationStatus.ANALISAR # Agora reconhecido via import
        
        # Act
        use_case.execute(user_id, items, decision)
        
        # Assert
        called_evaluations = self.mock_repo.save_evaluations.call_args[0][0]
        
        assert len(called_evaluations) == 2
        assert isinstance(called_evaluations[0], Evaluation)
        assert called_evaluations[0].avaliacao == EvaluationStatus.ANALISAR

    def test_get_portfolio_should_isolate_domain_from_infrastructure(self):
        """
        Verifica se o Use Case retorna os dados do domínio corretamente.
        """
        use_case = GetPortfolioUseCase(self.mock_repo)
        
        # Criamos uma instância real da entidade Auction para o mock retornar
        mock_auction = Auction(
            site="site1", id_leilao="1", titulo="Casa", uf="RJ", cidade="Rio",
            tipo_leilao="Judicial", tipo_bem="Imóvel", valor_1_praca=100.0,
            valor_2_praca=50.0, link_detalhe="...", imagem_capa="..."
        )
        self.mock_repo.get_portfolio_auctions.return_value = [mock_auction]
        
        # Act
        result = use_case.execute("user_1")
        
        # Assert
        assert len(result) == 1
        assert result[0].titulo == "Casa"
        assert isinstance(result[0], Auction)
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/unit/test_use_cases.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/unit/__init__.py ====

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/tests/unit/__init__.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/dependencies.py ====
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
        #"get_portfolio_auctions": GetPortfolio(repo), # Resolve o KeyError atual
        "get_portfolio_auctions": GetPortfolioUseCase(repo), # Use a mesma classe com a lógica
        "repo": repo # Necessário para o acesso direto feito na carteira.py (save_detailed_analysis)
    }

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/dependencies.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/styles.py ====
import streamlit as st

def apply_custom_styles():
    st.markdown("""
    <style>
        /* Força altura da linha */
        div[data-testid="stDataEditor"] table {
            --row-height: 150px !important;
        }
        div[data-testid="stDataEditor"] td {
            vertical-align: middle !important;
            font-size: 16px;
        }
        /* Ajuste de container para remover espaços brancos sobrando */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 2rem;
            max-width: 98% !important;
        }
        div[data-testid="stDataEditor"] th {
            background-color: #f0f2f6;
            min-height: 40px;
            font-size: 15px;
        }
    </style>
    """, unsafe_allow_html=True)

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/styles.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components.py ====
import streamlit as st
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List

# ALTERAÇÃO: Agora aceitamos 4 listas como parâmetros
def render_sidebar(unique_ufs: List[str], unique_cities: List[str], unique_types: List[str], unique_sites: List[str]) -> Dict[str, Any]:
    with st.sidebar:
        st.header("🔍 Filtros de Triagem")
        
        # Filtros vindos do Banco
        uf = st.selectbox("Estado (UF)", options=["Todos"] + unique_ufs)
        
        # Dica: Se quiser filtrar cidade baseado na UF selecionada, precisaria de mais lógica, 
        # mas vamos carregar todas por enquanto para simplificar.
        cidade = st.selectbox("Cidade", options=["Todas"] + unique_cities)
        
        tipo_bem = st.multiselect("Tipo de Bem", options=unique_types)
        site = st.multiselect("Leiloeiro", options=unique_sites)
        
        aplicar = st.button("Aplicar Filtros", type="primary", use_container_width=True)
        
        return {
            "uf": None if uf == "Todos" else uf,
            "cidade": None if cidade == "Todas" else cidade,
            "tipo_bem": tipo_bem if tipo_bem else None,
            "site": site if site else None,
            "clicked": aplicar
        }

# ... (Mantenha o render_dashboard igual) ...
def render_dashboard(df: pd.DataFrame):
    if df.empty:
        return

    with st.expander("📊 Ver Estatísticas da Carteira (Clique para expandir)", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'tipo_bem' in df.columns:
                fig_tipo = px.pie(df, names='tipo_bem', title='Tipo Imóvel', hole=0.5)
                fig_tipo.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_tipo, use_container_width=True)

        with col2:
            if 'tipo_leilao' in df.columns:
                fig_mod = px.pie(df, names='tipo_leilao', title='Modalidade', hole=0.5)
                fig_mod.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_mod, use_container_width=True)

        with col3:
            if 'site' in df.columns:
                fig_site = px.pie(df, names='site', title='Leiloeiro', hole=0.5)
                fig_site.update_layout(showlegend=False, height=250, margin=dict(t=30, b=0, l=0, r=0))
                st.plotly_chart(fig_site, use_container_width=True)

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/main.py ====
import sys
import os
import streamlit as st
import time
import pandas as pd

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Garimpo Judicial",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SETUP PATH ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../.."))
if project_root not in sys.path:
    sys.path.append(project_root)

# --- IMPORTS ---
try:
    from src.domain.models import EvaluationStatus
    from src.presentation.streamlit_app.dependencies import get_services
    # Importa os componentes da Triagem (Antigo)
    from src.presentation.streamlit_app.components import (
        render_sidebar, 
        render_dashboard, 
        render_triage_cards
    )
    # Importa a Nova Página
    from src.presentation.streamlit_app.views.carteira import render_carteira
except ImportError as e:
    st.error(f"Erro de Importação: {e}")
    st.stop()

# --- CSS GLOBAL ---
st.markdown("""
<style>
    .main-header {font-size: 24px; font-weight: bold; color: #333;}
    .stApp {background-color: #0e1117;}
</style>
""", unsafe_allow_html=True)

def main():
    # 1. Inicializa Serviços
    services = get_services()
    
    # Mock User ID (Em prod viria do Auth)
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = "Julio"
    user_id = st.session_state["user_id"]

    # 2. Navegação Lateral (Sidebar Menu)
    with st.sidebar:
        # st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=50) # Placeholder Logo
        st.markdown("### Garimpo Judicial")
        
        # Menu de Opções
        page = st.radio(
            "Navegação", 
            ["🔍 Triagem Rápida", "📁 Minha Carteira"],
            index=0
        )
        
        st.divider()
        # Stats Rápidos na Sidebar
        # Nota: get_stats pode falhar se a tabela não estiver populada ainda, então usamos try/except silencioso ou mock se preferir
        try:
            stats = services["get_stats"].execute(user_id)
            st.caption("📊 Produtividade Hoje")
            st.write(f"Analisados: **{stats.get('total_processado', 0)}**")
            st.write(f"Salvos: **{stats.get('analisar', 0)}**")
        except:
            st.caption("Carregando stats...")

    # 3. Roteamento de Páginas
    
    # --- ROTA: TRIAGEM ---
    if page == "🔍 Triagem Rápida":
        run_triage_page(services, user_id)
        
    # --- ROTA: CARTEIRA ---
    elif page == "📁 Minha Carteira":
        render_carteira(services, user_id)

# =========================================
# LÓGICA DA PÁGINA DE TRIAGEM (Refatorada)
# =========================================
def run_triage_page(services, user_id):
    st.title("🔍 Triagem de Oportunidades")
    
    # 1. Busca as opções disponíveis no banco primeiro
    filter_options = services["get_filters"].execute()
    
    # 2. Passa as listas explícitas para o render_sidebar
    # CORREÇÃO AQUI: Passamos os argumentos nomeados corretos
    filters = render_sidebar(
        unique_ufs=filter_options.get("ufs", []),
        unique_cities=filter_options.get("cidades", []),
        unique_types=filter_options.get("tipos", []),
        unique_sites=filter_options.get("sites", [])
    )
    
    # 3. Busca Leilões com os filtros aplicados
    # Nota: Lembre-se que agora filters['uf'] retorna uma lista, e o repo já espera lista
    auctions_data = services["get_auctions"].execute(
        user_id=user_id,
        uf=filters.get('uf'),
        cidade=filters.get('cidade'),
        tipo_bem=filters.get('tipo_bem'),
        site=filters.get('site')
    )
    
    # Converte para DataFrame para visualização
    df_auctions = pd.DataFrame([vars(a) for a in auctions_data]) if auctions_data else pd.DataFrame()

    # Dashboard Topo
    render_dashboard(df_auctions)
    
    st.divider()

    # Cards de Triagem
    if not df_auctions.empty:
        decisions = render_triage_cards(df_auctions)

        # Botão Flutuante/Fixo de Ação
        if decisions:
            count = len(decisions)
            st.markdown("---")
            col1, col2 = st.columns([4, 1])
            with col2:
                if st.button(f"Processar Lote ({count}) ⚡", type="primary", use_container_width=True):
                    _process_batch(services, decisions)
    else:
        st.info("Nenhum leilão encontrado com estes filtros.")

def _process_batch(services, decisions_dict):
    try:
        to_analyze = []
        to_discard = []

        for item in decisions_dict.values():
            payload = {'site': item['site'], 'id_leilao': item['id_leilao']}
            
            if item['decisao'] == "Analisar":
                to_analyze.append(payload)
            elif item['decisao'] == "Descartar":
                to_discard.append(payload)

        user_id = st.session_state["user_id"]

        if to_discard:
            services["submit_eval"].execute(user_id, to_discard, EvaluationStatus.DESCARTAR)
        
        if to_analyze:
            services["submit_eval"].execute(user_id, to_analyze, EvaluationStatus.ANALISAR)

        st.toast("🚀 Decisões salvas com sucesso!", icon="✅")
        
        # Limpa o session state das decisões antigas
        for key in list(st.session_state.keys()):
            if key.startswith("decision_"):
                del st.session_state[key]

        time.sleep(1)
        st.rerun()
        
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

if __name__ == "__main__":
    main()

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/main.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/views/carteira.py ====
import streamlit as st
from datetime import datetime
from src.presentation.streamlit_app.views.auditoria_v2 import render_auditoria_v2

def render_carteira(services, user_id):
    """
    Ponto de entrada da Carteira. 
    Gerencia o roteamento entre Listagem, Edição de Dados e Auditoria V2.0.
    """
    st.title("📁 Minha Carteira de Oportunidades")

    # Inicialização de estados de navegação
    if "page" not in st.session_state:
        st.session_state.page = "listagem"
    if "selected_auction" not in st.session_state:
        st.session_state.selected_auction = None

    # ROTEAMENTO (Router)
    if st.session_state.page == "auditoria_v2" and st.session_state.selected_auction:
        # Chama a nova implementação da TASK-009
        auction_ref = st.session_state.selected_auction
        
        # Botão flutuante de voltar (UX)
        if st.button("⬅️ Voltar para Carteira"):
            st.session_state.page = "listagem"
            st.session_state.selected_auction = None
            st.rerun()
            
        render_auditoria_v2(
            services, 
            user_id, 
            auction_ref["site"], 
            auction_ref["id_leilao"]
        )
        
    elif st.session_state.page == "editar_dados_brutos":
        _render_edit_source_data(services)
        
    else:
        _render_portfolio_list(services, user_id)

def _render_portfolio_list(services, user_id):
    """Renderiza a listagem segmentada por abas."""
    all_items = services["get_portfolio_auctions"].execute(user_id)
    
    # Categorização baseada no EvaluationStatus
    items_analisar = [i for i in all_items if i.status_carteira == 'ANALISAR']
    items_participar = [i for i in all_items if i.status_carteira == 'PARTICIPAR']
    items_descartados = [i for i in all_items if i.status_carteira == 'NO_BID']

    tabs = st.tabs([
        f"📥 A Analisar ({len(items_analisar)})", 
        f"🚀 Participar ({len(items_participar)})", 
        f"🗑️ Descartados ({len(items_descartados)})"
    ])

    with tabs[0]:
        if not items_analisar:
            st.info("Sua esteira de análise está vazia.")
        for auction in items_analisar:
            _render_card(auction, suffix="analisar") 

    with tabs[1]:
        for auction in items_participar:
            _render_card(auction, suffix="participar", is_participating=True)

    with tabs[2]:
        for auction in items_descartados:
            _render_card(auction, suffix="descartado", is_readonly=True)

def _render_card(auction, suffix, is_participating=False, is_readonly=False):
    """Card de visualização do leilão com botões de ação únicos."""
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 1])
        
        with c1:
            if auction.imagem_capa:
                st.image(auction.imagem_capa, use_container_width=True)
            else:
                st.markdown("📷 *Sem Foto*")
        
        with c2:
            col_t1, col_t2 = st.columns([0.9, 0.1])
            col_t1.subheader(auction.titulo)
            if col_t2.button("✏️", key=f"edit_raw_{auction.id_leilao}_{suffix}"):
                st.session_state.page = "editar_dados_brutos"
                st.session_state.selected_auction = {"site": auction.site, "id_leilao": auction.id_leilao, "obj": auction}
                st.rerun()

            st.caption(f"📍 {auction.cidade}/{auction.uf} | 🏛️ {auction.site}")
            
            c_d1, c_d2 = st.columns(2)
            c_d1.metric("1ª Praça", f"R$ {auction.valor_1_praca:,.2f}", 
                        auction.data_1_praca.strftime("%d/%m/%Y") if auction.data_1_praca else "S/D")
            c_d2.metric("2ª Praça", f"R$ {auction.valor_2_praca:,.2f}", 
                        auction.data_2_praca.strftime("%d/%m/%Y") if auction.data_2_praca else "S/D", delta_color="normal")

        with c3:
            btn_label = "Avaliar 📝"
            if is_participating: btn_label = "Ver Detalhes 🔍"
            elif is_readonly: btn_label = "Revisar 📂"

            if st.button(btn_label, key=f"btn_go_{auction.id_leilao}_{suffix}", use_container_width=True):
                st.session_state.page = "auditoria_v2"
                st.session_state.selected_auction = {"site": auction.site, "id_leilao": auction.id_leilao}
                st.rerun()

def _render_edit_source_data(services):
    """Formulário para correção de dados de scraping."""
    auction_data = st.session_state.selected_auction["obj"]
    
    st.subheader(f"✏️ Corrigir Dados Estruturais: {auction_data.id_leilao}")
    
    with st.form("edit_raw_form"):
        new_title = st.text_input("Título", value=auction_data.titulo)
        c1, c2 = st.columns(2)
        v1 = c1.number_input("Valor 1ª Praça", value=float(auction_data.valor_1_praca))
        v2 = c2.number_input("Valor 2ª Praça", value=float(auction_data.valor_2_praca))
        
        if st.form_submit_button("Salvar Correções"):
            updates = {"titulo": new_title, "valor_1_praca": v1, "valor_2_praca": v2}
            services["repository"].update_auction_core_data(auction_data.site, auction_data.id_leilao, updates)
            st.success("Dados corrigidos!")
            st.session_state.page = "listagem"
            st.rerun()
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/views/carteira.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/views/carteira (Cópia).py ====
import streamlit as st
import pandas as pd
from src.domain.models import DetailedAnalysis, RiskLevel, OccupationStatus

def render_carteira(services, user_id):
    st.title("📁 Minha Carteira de Oportunidades")
    
    # 1. Carrega os itens salvos ("Analisar")
    portfolio = services["get_portfolio"].execute(user_id)
    
    if not portfolio:
        st.info("Sua carteira está vazia. Vá para a 'Triagem' para encontrar oportunidades.")
        return

    # 2. Seletor de Imóvel (Master View)
    # Cria uma lista formatada para o Selectbox
    options = {f"{p.id_leilao} | {p.titulo} ({p.site})": p for p in portfolio}
    selected_label = st.selectbox("Selecione o imóvel para realizar o Deep Dive:", options.keys())
    
    # Recupera o objeto Auction selecionado
    auction = options[selected_label]
    
    st.divider()

    # 3. Busca a Análise Detalhada existente (ou cria nova)
    analysis = services["get_analysis"].execute(user_id, auction.site, auction.id_leilao)

    # Layout: Coluna Esquerda (Resumo Imóvel) | Coluna Direita (Ferramentas de Análise)
    col_left, col_right = st.columns([1, 2])

    # --- COLUNA ESQUERDA: DADOS ESTÁTICOS ---
    with col_left:
        if auction.imagem_capa:
            st.image(auction.imagem_capa, use_container_width=True)
        
        st.subheader("Dados do Edital")
        st.markdown(f"**1ª Praça:** R$ {auction.valor_1_praca:,.2f}")
        st.markdown(f"**2ª Praça:** R$ {auction.valor_2_praca:,.2f}")
        st.markdown(f"**Cidade:** {auction.cidade}/{auction.uf}")
        
        st.markdown("---")
        st.markdown(f"[🔗 Abrir Edital Original]({auction.link_detalhe})")

    # --- COLUNA DIREITA: FORMULÁRIO DE ANÁLISE ---
    with col_right:
        tab_juridico, tab_financeiro = st.tabs(["⚖️ Análise Jurídica", "💰 Calculadora de ROI"])

        # ==========================
        # ABA JURÍDICA
        # ==========================
        with tab_juridico:
            st.caption("Preencha o checklist para validar a segurança jurídica.")
            
            with st.form("form_juridico"):
                c1, c2 = st.columns(2)
                with c1:
                    new_parecer = st.text_area("Parecer Jurídico (Resumo)", value=analysis.parecer_juridico or "")
                    new_risco = st.selectbox(
                        "Risco Jurídico", 
                        options=[e.value for e in RiskLevel], 
                        index=[e.value for e in RiskLevel].index(analysis.risco_judicial.value)
                    )
                with c2:
                    st.write("**Checklist de Nulidades**")
                    new_reu_citado = st.checkbox("Réu Citado Corretamente?", value=analysis.reu_citado)
                    new_intimacao = st.checkbox("Credores Intimados?", value=analysis.intimacao_credores)
                    
                    if not new_reu_citado:
                        st.error("⚠️ ALERTA: Falta de citação é risco de Nulidade Fatal!")

                st.markdown("#### Passivo do Imóvel")
                c3, c4, c5 = st.columns(3)
                with c3:
                    new_div_condo = st.number_input("Dívida Condomínio (R$)", value=analysis.divida_condominio, step=100.0)
                with c4:
                    new_div_iptu = st.number_input("Dívida IPTU (R$)", value=analysis.divida_iptu, step=100.0)
                with c5:
                    new_subroga = st.checkbox("Dívida Sub-roga?", value=analysis.divida_subroga, help="Se marcado, a dívida morre com o leilão. Se desmarcado, você paga.")

                st.markdown("#### Ocupação")
                new_ocupacao = st.selectbox(
                    "Situação Física", 
                    options=[e.value for e in OccupationStatus],
                    index=[e.value for e in OccupationStatus].index(analysis.ocupacao_status.value)
                )

                submit_juridico = st.form_submit_button("💾 Salvar Análise Jurídica")
                
                if submit_juridico:
                    # Atualiza o objeto analysis
                    analysis.parecer_juridico = new_parecer
                    analysis.risco_judicial = RiskLevel(new_risco)
                    analysis.reu_citado = new_reu_citado
                    analysis.intimacao_credores = new_intimacao
                    analysis.divida_condominio = new_div_condo
                    analysis.divida_iptu = new_div_iptu
                    analysis.divida_subroga = new_subroga
                    analysis.ocupacao_status = OccupationStatus(new_ocupacao)
                    
                    services["save_analysis"].execute(analysis)
                    st.success("Dados jurídicos atualizados!")
                    st.rerun()

        # ==========================
        # ABA FINANCEIRA (ROI)
        # ==========================
        with tab_financeiro:
            st.caption("Simule a viabilidade econômica do arremate.")
            
            # INPUTS
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                st.markdown("**Custos Variáveis**")
                val_mercado = st.number_input("Valor de Venda Estimado (Mercado)", value=analysis.valor_venda_estimado or 0.0, step=1000.0)
                custo_obra = st.number_input("Estimativa de Reforma", value=analysis.custo_reforma, step=500.0)
                custo_desoc = st.number_input("Custo Desocupação", value=analysis.custo_desocupacao, step=500.0)
            
            with col_in2:
                st.markdown("**Parâmetros do Leilão**")
                # Se a dívida não sub-roga, ela soma no custo!
                divida_total = 0.0
                if not analysis.divida_subroga:
                    divida_total = analysis.divida_condominio + analysis.divida_iptu
                    st.warning(f"⚠️ Dívidas (R$ {divida_total:,.2f}) somadas ao custo (Não Sub-roga)")
                
                lance_base = st.number_input("Simular Valor de Lance", value=auction.valor_2_praca, step=1000.0)

            # CÁLCULOS
            comissao = lance_base * 0.05
            itbi_registro = lance_base * 0.04 # Estimativa 4%
            custo_aquisicao = lance_base + comissao + itbi_registro + divida_total + custo_obra + custo_desoc
            
            lucro_bruto = val_mercado - custo_aquisicao
            roi_perc = (lucro_bruto / custo_aquisicao * 100) if custo_aquisicao > 0 else 0

            st.divider()
            
            # RESULTADOS (Métricas Grandes)
            m1, m2, m3 = st.columns(3)
            m1.metric("Custo Total Aquisição", f"R$ {custo_aquisicao:,.2f}")
            m2.metric("Lucro Líquido Previsto", f"R$ {lucro_bruto:,.2f}", delta_color="normal")
            m3.metric("ROI Estimado", f"{roi_perc:.1f}%", delta_color="normal" if roi_perc > 0 else "inverse")

            # Botão Salvar Financeiro
            if st.button("💾 Atualizar Financeiro"):
                analysis.valor_venda_estimado = val_mercado
                analysis.custo_reforma = custo_obra
                analysis.custo_desocupacao = custo_desoc
                # Campos calculados não salvamos no banco, apenas os inputs
                services["save_analysis"].execute(analysis)
                st.toast("Premissas financeiras salvas!", icon="💰")

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/views/carteira (Cópia).py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/views/auditoria_v2.py ====
# Arquivo: src/presentation/streamlit_app/views/auditoria_v2.py
import streamlit as st
from datetime import date
from src.domain.models import DetailedAnalysis, ConjugeStatus, NaturezaExecucao, EspecieCredito
from src.domain.isj_calculator import IsjCalculator
from src.presentation.streamlit_app.components.alertas_engine import AlertasEngine
from src.presentation.streamlit_app.components.isj_gauge import render_isj_gauge

def render_auditoria_v2(services, user_id: str, site: str, id_leilao: str):
    """
    Formulário principal de Auditoria Jurídica V2.0.
    Implementa 6 seções, Auto-save, Alertas e KPIs em tempo real.
    """
    
    # 1. Carregamento Inicial ou Recuperação do Estado
    if "current_analysis" not in st.session_state or \
       st.session_state.current_analysis.id_leilao != id_leilao:
        
        analysis = services['repository'].get_detailed_analysis(site, id_leilao, user_id)
        if not analysis:
            analysis = DetailedAnalysis(site=site, id_leilao=id_leilao, usuario_id=user_id)
        st.session_state.current_analysis = analysis

    analysis = st.session_state.current_analysis

    # 2. Motores de Cálculo (Tempo Real)
    alertas = AlertasEngine.avaliar(analysis)
    isj_score = IsjCalculator.calculate(analysis)
    kpis = IsjCalculator.calculate_financial_kpis(analysis)

    # 3. Layout: Banner de Alertas Críticos
    for alerta in [a for a in alertas if a.nivel == "critico"]:
        st.error(alerta.mensagem)

    # 4. Layout: Colunas Principais (Formulário vs Sidebar de Stats)
    col_form, col_stats = st.columns([3, 1])

    with col_form:
        tabs = st.tabs([
            "⚖️ 1. Processo", "📜 2. Matrícula", "📝 3. Edital", 
            "🏠 4. Situação", "💰 5. Financeiro", "🤖 6. Parecer IA"
        ])

        # --- TAB 1: PROCESSO ---
        with tabs[0]:
            analysis.proc_num = st.text_input("Nº Processo", value=analysis.proc_num)
            analysis.proc_citacao = st.checkbox("Réu citado corretamente?", value=analysis.proc_citacao)
            analysis.proc_natureza_execucao = st.selectbox("Natureza da Execução", 
                options=list(NaturezaExecucao), format_func=lambda x: x.value,
                index=list(NaturezaExecucao).index(analysis.proc_natureza_execucao) if analysis.proc_natureza_execucao else 0)
            analysis.proc_debito_atualizado = st.number_input("Débito Atualizado (R$)", value=analysis.proc_debito_atualizado)
            
            # Campo Condicional (AC-7)
            analysis.proc_recursos = st.toggle("Existem recursos pendentes?", value=analysis.proc_recursos)
            if analysis.proc_recursos:
                analysis.proc_recursos_obs = st.text_area("Observações dos Recursos", value=analysis.proc_recursos_obs)

        # --- TAB 2: MATRÍCULA ---
        with tabs[1]:
            analysis.mat_num = st.text_input("Nº Matrícula", value=analysis.mat_num)
            analysis.mat_prop_confere = st.checkbox("Proprietário da Matrícula = Executado?", value=analysis.mat_prop_confere)
            analysis.mat_usufruto = st.checkbox("Existe Usufruto?", value=analysis.mat_usufruto)
            analysis.mat_indisp = st.checkbox("Existe Indisponibilidade?", value=analysis.mat_indisp)

        # --- TAB 5: FINANCEIRO ---
        with tabs[4]:
            analysis.fin_lance = st.number_input("Lance Pretendido (R$)", value=analysis.fin_lance)
            analysis.valor_venda_estimado = st.number_input("Valor de Venda Estimado (R$)", value=analysis.valor_venda_estimado)
            analysis.fin_itbi = st.number_input("ITBI Estimado (R$)", value=analysis.fin_itbi)

        # ... (Outras abas seguem o mesmo padrão de mapeamento)

    # 5. Coluna Lateral: Score e KPIs (AC-5)
    with col_stats:
        render_isj_gauge(isj_score, alertas)
        
        st.metric("Investimento Total", f"R$ {kpis['investimento_total']:,.2f}")
        st.metric("ROI Nominal", f"{kpis['roi_nominal']:.2f}%")
        
        # Botão Finalizar com Bloqueio (AC-4)
        bloqueado = analysis.proc_citacao is False or analysis.mat_prop_confere is False
        if st.button("Finalizar Auditoria", type="primary", disabled=bloqueado):
            novo_status = services['finalizar_auditoria'].execute(analysis, user_id)
            st.success(f"Finalizado! Status: {novo_status}")
            st.rerun()
        
        if bloqueado:
            st.warning("Finalização bloqueada por nulidade absoluta.")

    # 6. Lógica de Auto-save (AC-6)
    # Em uma aplicação real, aqui dispararíamos o use case de rascunho
    services['save_rascunho'].execute(analysis)
    st.toast("Alterações salvas automaticamente ☁️")
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/views/auditoria_v2.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/triage_cards.py ====
import streamlit as st
import pandas as pd

def render_triage_cards(df: pd.DataFrame):
    """
    Renderiza os leilões em formato de Cards verticais com altura de imagem fixa.
    Retorna um dicionário com as decisões tomadas.
    """
    if df.empty:
        # Se o dataframe estiver vazio após a filtragem do main, não mostra nada.
        return {}

    # Sanitização básica: Garante que tem ID, pega os primeiros 15 e reseta o índice
    df_clean = (
    df
    .dropna(subset=['id_leilao'])
    .drop_duplicates(subset=['id_leilao'])  # <- adiciona isso
    .head(15)
    .reset_index(drop=True)
)
    
    if df_clean.empty:
         return {}

    # Dicionário para guardar as decisões temporárias
    decisions = {}

    # Estilo CSS para detalhes do card (exceto a imagem, que faremos inline)
    st.markdown("""
    <style>
        /* Ajuste fino para o container do card */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            border: 1px solid #444;
            border-radius: 12px;
            padding: 15px;
            background-color: #262730; /* Cor de fundo do card */
        }
        .big-font { font-size: 16px !important; font-weight: 600; line-height: 1.4; margin-bottom: 10px;}
        .price-label { font-size: 12px; color: #aaa; }
        .price-value { font-size: 15px; font-weight: bold; }
        .price-value-2 { font-size: 15px; font-weight: bold; color: #4CAF50; } /* Verde para 2ª praça */
        .link-edital { font-size: 13px; text-decoration: none; color: #4da6ff !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.write(f"Exibindo {len(df_clean)} oportunidades")

    # --- LOOP DOS CARDS ---
    for index, row in df_clean.iterrows():
        id_leilao = str(row['id_leilao'])
        
        # Cria um container para cada leilão
        with st.container():
            # Layout: Imagem (pequena) | Informações (grande) | Ação (pequena)
            col_img, col_info, col_action = st.columns([1.2, 2.3, 1])
            
            # --- 1. COLUNA DA IMAGEM (FIXA) ---
            with col_img:
                img_url = row.get('imagem_capa')
                
                # Se não tiver URL, usa um placeholder do mesmo tamanho
                if not img_url or pd.isna(img_url):
                    img_url = "https://via.placeholder.com/300x220?text=Sem+Foto"

                # CSS HACK: Usamos HTML direto para forçar a altura e o corte (object-fit)
                # height: 220px -> Define a altura fixa
                # object-fit: cover -> Corta o excesso da imagem sem esticar, centralizando o foco.
                st.markdown(
                    f"""
                    <img src="{img_url}" 
                         style="width: 100%; height: 220px; object-fit: cover; border-radius: 8px;" 
                         alt="Foto do bem">
                    """,
                    unsafe_allow_html=True
                )
                
                st.caption(f"ID: {id_leilao} | {row.get('site', 'N/A')}")

            # --- 2. COLUNA DE INFORMAÇÕES ---
            with col_info:
                # Título com classe CSS para limitar tamanho
                titulo = row.get('titulo', 'Sem Título')
                st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)
                
                # Exibição de Valores Formatados
                v1 = float(row.get('valor_1_praca', 0) or 0)
                v2 = float(row.get('valor_2_praca', 0) or 0)
                
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    st.markdown("<span class='price-label'>1ª Praça:</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='price-value'>R$ {v1:,.2f}</div>", unsafe_allow_html=True)
                with c_v2:
                    st.markdown("<span class='price-label'>2ª Praça:</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='price-value-2'>📉 R$ {v2:,.2f}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                link = row.get('link_detalhe', '#')
                st.markdown(f"🔗 <a href='{link}' target='_blank' class='link-edital'>Ver Edital no Site</a>", unsafe_allow_html=True)

            # --- 3. COLUNA DE AÇÃO (TRIAGEM) ---
            with col_action:
                st.write("**Decisão**")
                
                # Recupera o estado anterior se existir para manter a seleção ao recarregar
                key = f"decision_{id_leilao}"
                
                # Radio Button para decisão rápida
                decision = st.radio(
                    "Decisão para o ID " + id_leilao, # Label invisível, mas necessário para acessibilidade
                    options=["Pendente", "Analisar", "Descartar"],
                    index=2, # <--- 0=Pendente, 1=Analisar, 2=Descartar
                    key=key,
                    label_visibility="collapsed" # Esconde o label para ficar mais limpo
                )
                
                # Se a decisão mudou de "Pendente", guardamos no dict de retorno
                if decision != "Pendente":
                    decisions[id_leilao] = {
                        "id_leilao": id_leilao,
                        "site": row.get('site'),
                        "decisao": decision
                    }
            
            # Adiciona um espaçamento visual entre os cards
            st.write("") 
            st.write("") 

    return decisions

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/triage_cards.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/alertas_engine.py ====
# Arquivo: src/presentation/streamlit_app/components/alertas_engine.py
from dataclasses import dataclass
from typing import List, Optional
from src.domain.models import DetailedAnalysis, ConjugeStatus

@dataclass
class Alerta:
    nivel: str  # 'critico', 'alto', 'medio', 'info'
    mensagem: str
    campo_gatilho: str

class AlertasEngine:
    """
    Motor de regras para geração de alertas visuais na UI.
    Ref: Spec Funcional Secção 7.2
    """

    @staticmethod
    def avaliar(analysis: DetailedAnalysis) -> List[Alerta]:
        alertas = []

        # --- Nível CRÍTICO (Nulidades ou Erros Graves) ---
        if analysis.proc_citacao is False:
            alertas.append(Alerta(
                nivel="critico",
                mensagem="🚨 NULIDADE PROMISSORA: Réu não citado no processo de origem.",
                campo_gatilho="proc_citacao"
            ))

        if analysis.mat_prop_confere is False:
            alertas.append(Alerta(
                nivel="critico",
                mensagem="🚨 ERRO DE DOMÍNIO: Proprietário da matrícula difere do executado.",
                campo_gatilho="mat_prop_confere"
            ))

        # --- Nível ALTO (Riscos de Demora ou Custos Extras) ---
        if analysis.mat_usufruto is True:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ USUFRUTO ATIVO: Risco de impossibilidade de imissão na posse.",
                campo_gatilho="mat_usufruto"
            ))

        if analysis.proc_conjuge == ConjugeStatus.NAO:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ CÔNJUGE NÃO INTIMADO: Risco de embargos de terceiro.",
                campo_gatilho="proc_conjuge"
            ))

        if analysis.mat_indisp is True:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ INDISPONIBILIDADE: Necessário pedido de baixa em cada juízo.",
                campo_gatilho="mat_indisp"
            ))

        # --- Nível MÉDIO (Atenção Necessária) ---
        if analysis.proc_recursos is True:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="⚡ RECURSOS PENDENTES: O leilão pode ser anulado ou suspenso.",
                campo_gatilho="proc_recursos"
            ))

        if analysis.edt_condo_claro is False:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="💰 DÍVIDA CONDOMINIAL OBSCURA: Risco de surpresa financeira.",
                campo_gatilho="edt_condo_claro"
            ))

        if analysis.proc_justica_gratuita is True:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="⚖️ JUSTIÇA GRATUITA: Dificuldade na recuperação de custas em caso de anulação.",
                campo_gatilho="proc_justica_gratuita"
            ))

        # --- Nível INFO ---
        if analysis.edt_parcelamento is True:
            alertas.append(Alerta(
                nivel="info",
                mensagem="ℹ️ PARCELAMENTO DISPONÍVEL: Edital permite pagamento parcelado (Art. 895 CPC).",
                campo_gatilho="edt_parcelamento"
            ))

        return alertas
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/alertas_engine.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/sidebar.py ====
import streamlit as st

def render_sidebar(unique_ufs, unique_cities, unique_types, unique_sites):
    st.sidebar.header("🔍 Filtros de Busca")
    
    # Filtro UF
    selected_uf = st.sidebar.multiselect(
        "Estado (UF)",
        options=sorted(unique_ufs) if unique_ufs else [],
        default=[]
    )
    
    # Filtro Cidade (lógica de dependência da UF se necessário, ou simples)
    # Aqui assumimos que unique_cities já vem filtrado ou mostra tudo
    selected_city = st.sidebar.multiselect(
        "Cidade",
        options=sorted(unique_cities) if unique_cities else [],
        default=[]
    )
    
    # Filtro Tipo
    selected_type = st.sidebar.multiselect(
        "Tipo do Bem",
        options=sorted(unique_types) if unique_types else [],
        default=[]
    )
    
    # Filtro Site
    selected_site = st.sidebar.multiselect(
        "Leiloeiro / Site",
        options=sorted(unique_sites) if unique_sites else [],
        default=[]
    )
    
    return {
        "uf": selected_uf,
        "cidade": selected_city,
        "tipo_bem": selected_type,
        "site": selected_site
    }

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/sidebar.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/dashboard.py ====
import streamlit as st
import pandas as pd
import plotly.express as px  # Nova importação para gráficos bonitos

def render_dashboard(df: pd.DataFrame, stats_history: dict = None):
    """
    Renderiza o painel de indicadores com gráficos de Pizza/Donut.
    """
    if not stats_history:
        stats_history = {'analisar': 0, 'descartar': 0}

    st.markdown("### 📊 Visão Geral")

    # --- LINHA 1: KPIs GERAIS (Métricas continuam iguais) ---
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        total_pendente = len(df)
        st.metric("📌 Pendentes", total_pendente, help="Fila de espera")
    
    with c2:
        vol_total = df['valor_1_praca'].sum() if not df.empty and 'valor_1_praca' in df.columns else 0
        st.metric("💰 Volume (1ª Praça)", f"R$ {vol_total/1_000_000:.1f}M")

    with c3:
        st.metric("🗑️ Descartados", stats_history.get('descartar', 0))
        
    with c4:
        count_analisar = stats_history.get('analisar', 0)
        total_proc = stats_history.get('total_processado', 1) or 1
        st.metric("⭐ Para Análise", count_analisar, delta=f"{(count_analisar/total_proc)*100:.0f}% Aprov")

    st.markdown("---")

    # --- LINHA 2: GRÁFICOS DE PIZZA (DONUT) ---
    if not df.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        # --- GRÁFICO 1: TIPO DE BEM ---
        with col_chart1:
            if 'tipo_bem' in df.columns:
                # Prepara os dados: Conta quantos de cada tipo
                counts_tipo = df['tipo_bem'].value_counts().reset_index()
                counts_tipo.columns = ['Tipo', 'Qtd']
                
                # Cria o gráfico Donut
                fig_tipo = px.pie(
                    counts_tipo, 
                    names='Tipo', 
                    values='Qtd', 
                    title='🏢 Distribuição por Tipo',
                    hole=0.4, # Faz o buraco no meio (Donut)
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                # Ajustes visuais (fundo transparente para combinar com tema dark)
                fig_tipo.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_tipo, use_container_width=True)

        # --- GRÁFICO 2: TOP LEILOEIROS ---
        with col_chart2:
            if 'site' in df.columns:
                # Prepara os dados: Conta quantos de cada site
                counts_site = df['site'].value_counts().reset_index()
                counts_site.columns = ['Site', 'Qtd']
                
                # Se tiver muitos sites, pega o Top 5 e agrupa o resto em "Outros" (Opcional, mas recomendado)
                if len(counts_site) > 6:
                    top_5 = counts_site.head(5)
                    outros = pd.DataFrame([['Outros', counts_site.iloc[5:]['Qtd'].sum()]], columns=['Site', 'Qtd'])
                    counts_site = pd.concat([top_5, outros])

                # Cria o gráfico Donut
                fig_site = px.pie(
                    counts_site, 
                    names='Site', 
                    values='Qtd', 
                    title='⚖️ Top Leiloeiros',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_site.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig_site, use_container_width=True)
    
    st.markdown("---")

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/dashboard.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/triage_grid.py ====
import streamlit as st
import pandas as pd

def render_triage_grid(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    # --- SANITIZAÇÃO ---
    cols_visualizacao = ["imagem_capa", "titulo", "valor_1_praca", 
                         "valor_2_praca", "link_detalhe", "site", "id_leilao", "decisao"]
    
    df_clean = df[[c for c in cols_visualizacao if c in df.columns]].copy()
    df_clean = df_clean.head(15).reset_index(drop=True)

    if "titulo" in df_clean.columns:
        df_clean["titulo"] = df_clean["titulo"].astype(str).fillna("")
    if "valor_1_praca" in df_clean.columns:
        df_clean["valor_1_praca"] = pd.to_numeric(df_clean["valor_1_praca"], errors='coerce').fillna(0.0)
    if "valor_2_praca" in df_clean.columns:
        df_clean["valor_2_praca"] = pd.to_numeric(df_clean["valor_2_praca"], errors='coerce').fillna(0.0)

    st.info(f"👇 Exibindo **{len(df_clean)}** itens (Máximo de 15 por página).")

    # --- CONFIG ---
    column_config = {
        
        "imagem_capa": st.column_config.ImageColumn("📸 Foto", width="large"),
        "titulo": st.column_config.TextColumn("Descrição", width="large"),
        "valor_1_praca": st.column_config.NumberColumn("💰 1ª Praça", format="R$ %.2f", width="small"),
        "valor_2_praca": st.column_config.NumberColumn("💰 2ª Praça", format="R$ %.2f", width="small"),
        "link_detalhe": st.column_config.LinkColumn("Edital", display_text="🔗 Link", width="small"),
        "site": st.column_config.Column("Site", width="small", disabled=True), 
        "id_leilao": st.column_config.Column("ID", width="small", disabled=True),
        "decisao": st.column_config.SelectboxColumn("Triagem", options=["Pendente", "Analisar", "Descartar"], width="medium", required=True)
    }

    # --- ALTURA ---
    rows = len(df_clean)
    dynamic_height = (rows * 150) + 42

    edited_df = st.data_editor(
        df_clean,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=f"triage_grid_{rows}",
        height=dynamic_height,
        num_rows="fixed",
        disabled=["imagem_capa", "valor_1_praca", "valor_2_praca", "titulo", "link_detalhe", "site", "id_leilao"]
    )
    
    return edited_df

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/triage_grid.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/__init__.py ====
from .sidebar import render_sidebar
from .dashboard import render_dashboard
from .triage_grid import render_triage_grid # Pode manter por segurança
from .triage_cards import render_triage_cards # <--- ADICIONE ESTE

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/__init__.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/isj_gauge.py ====
# Arquivo: src/presentation/streamlit_app/components/isj_gauge.py
import streamlit as st
from typing import List
from src.presentation.streamlit_app.components.alertas_engine import Alerta

def render_isj_gauge(isj_score: float, alertas: List[Alerta]):
    """
    Renderiza o medidor de score ISJ e o resumo de alertas.
    Ref: Spec Funcional Seção 7.1 e AC-1 a AC-4
    """
    
    # Determinar cor e texto com base no score (AC-1, AC-2, AC-3)
    if isj_score > 80.0:
        color = "green"
        label = "🟢 FAVORÁVEL"
        help_text = "Segurança jurídica robusta. Riscos mínimos identificados."
    elif isj_score > 60.0:
        color = "orange"
        label = "🟡 FAVORÁVEL COM RESSALVAS"
        help_text = "Exige atenção a pontos específicos. Risco moderado."
    else:
        color = "red"
        label = "🔴 DESFAVORÁVEL"
        help_text = "Alto risco de nulidade ou imobilização de capital. Não recomendado."

    # Renderização do Gauge
    st.subheader("Índice de Segurança Jurídica (ISJ)")
    
    # Barra de progresso colorida via CSS customizado (Streamlit nativo é limitado)
    st.markdown(f"""
        <div style="background-color: #f0f2f6; border-radius: 10px; padding: 5px;">
            <div style="
                background-color: {color}; 
                width: {isj_score}%; 
                height: 25px; 
                border-radius: 8px; 
                transition: width 0.5s ease-in-out;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            ">
                {isj_score:.1f}%
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"**Parecer Preliminar:** {label}")
    st.info(help_text)

    # Resumo de Alertas por Nível (AC-4)
    if alertas:
        st.write("---")
        st.markdown("#### 🚩 Resumo de Alertas")
        
        # Agregação de contagem
        contagem = {
            "critico": len([a for a in alertas if a.nivel == "critico"]),
            "alto": len([a for a in alertas if a.nivel == "alto"]),
            "medio": len([a for a in alertas if a.nivel == "medio"]),
            "info": len([a for a in alertas if a.nivel == "info"])
        }
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Críticos", contagem["critico"], delta_color="inverse")
        col2.metric("Altos", contagem["alto"], delta_color="off")
        col3.metric("Médios", contagem["medio"], delta_color="off")
        col4.metric("Informativos", contagem["info"], delta_color="off")

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/presentation/streamlit_app/components/isj_gauge.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/database/config.py ====
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Em produção, use variáveis de ambiente. Ex: os.getenv("DB_URL")
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency injection para sessões de banco."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/database/config.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/database/models_sql.py ====
# Arquivo: src/infra/database/models_sql.py
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, Date, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


Base = declarative_base()

class LeilaoAnaliticoModel(Base):
    """
    Tabela com os dados brutos raspados (Scraper).
    """
    __tablename__ = "leiloes_analiticos"  # Verifique se este nome está exato no seu banco
    
    id_registro_bruto = Column(Integer, primary_key=True) 
    site = Column(String)
    id_leilao = Column(String)
    titulo = Column(String)
    uf = Column(String)
    cidade = Column(String)
    tipo_leilao = Column(String)
    tipo_bem = Column(String)
    valor_1_praca = Column(Float)
    valor_2_praca = Column(Float)
    link_detalhe = Column(String)
    imagem_capa = Column(String)
    # data_scrapping = Column(DateTime) # REMOVIDO: Causava o erro pois não existe no banco
    data_1_praca = Column(DateTime, nullable=True) 
    data_2_praca = Column(DateTime, nullable=True)

class LeilaoAvaliacaoModel(Base):
    """
    Tabela da Triagem (Fase 1).
    Ajustada para bater com o SQL: public.leiloes_avaliacoes
    """
    __tablename__ = "leiloes_avaliacoes" # <--- CORRIGIDO (PLURAL)
    
    # PK Composta baseada no seu SQL: PRIMARY KEY (usuario_id, site, id_leilao)
    usuario_id = Column(String, primary_key=True)
    site = Column(String, primary_key=True)
    id_leilao = Column(String, primary_key=True)
    
    id_registro_bruto = Column(Integer) # FK lógica
    avaliacao = Column(String) # 'Analisar' ou 'Descartar'
    data_analise = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class LeilaoAnaliseDetalhadaModel(Base):
    """
    Representação ORM da tabela leiloes_analise_detalhada.
    Mapeia todos os campos da Auditoria Jurídica V2.0.
    """
    __tablename__ = 'leiloes_analise_detalhada'

    # Chaves Primárias / Identificadores (Existentes)
    site = Column(String, primary_key=True)
    id_leilao = Column(String, primary_key=True)
    usuario_id = Column(String, primary_key=True)

    # --- Seção 1: Processo Judicial ---
    proc_num = Column(String, nullable=True)
    proc_executados = Column(JSONB, nullable=True, default=list)
    proc_adv_exec = Column(Boolean, nullable=True)
    proc_citacao = Column(Boolean, nullable=True)
    proc_conjuge = Column(String(10), nullable=True)
    proc_credores = Column(Boolean, nullable=True)
    proc_recursos = Column(Boolean, nullable=True)
    proc_recursos_obs = Column(Text, nullable=True)
    proc_coproprietario_intimado = Column(Boolean, nullable=True)
    proc_natureza_execucao = Column(String(20), nullable=True)
    proc_justica_gratuita = Column(Boolean, nullable=True)
    proc_especie_credito = Column(String(20), nullable=True)
    proc_debito_atualizado = Column(Numeric(15, 2), default=0.00)
    proc_avaliacao_imovel = Column(Boolean, nullable=True)

    # --- Seção 2: Matrícula e Gravames ---
    mat_num = Column(String, nullable=True)
    mat_proprietario = Column(JSONB, nullable=True, default=list)
    mat_penhoras = Column(JSONB, nullable=True, default=list)
    mat_conjugue = Column(Boolean, nullable=True)
    mat_prop_confere = Column(Boolean, nullable=True)
    mat_proprietario_pj = Column(Boolean, nullable=True)
    mat_penhora_averbada = Column(Boolean, nullable=True)
    mat_usufruto = Column(Boolean, nullable=True)
    mat_indisp = Column(Boolean, nullable=True)
    mat_vagas_mat = Column(Boolean, nullable=True)

    # --- Seção 3: Edital e Dívidas ---
    edt_objeto = Column(String(20), nullable=True)
    edt_vlr_avaliacao = Column(Numeric(15, 2), default=0.00)
    edt_percentual_minimo = Column(Numeric(5, 2), nullable=True)
    edt_data_avaliacao = Column(Date, nullable=True)
    edt_parcelamento = Column(Boolean, nullable=True)
    edt_iptu_subroga = Column(Boolean, nullable=True)
    edt_condo_claro = Column(Boolean, nullable=True)

    # --- Seção 4: Situação Física ---
    edt_posse_status = Column(String(50), nullable=True)
    edt_posse_estrategia = Column(String(50), nullable=True)

    # --- Seção 5: Financeiro ---
    fin_lance = Column(Numeric(15, 2), default=0.00)
    fin_itbi = Column(Numeric(15, 2), default=0.00)
    fin_dividas = Column(Numeric(15, 2), default=0.00)
    recomendacao_ia = Column(Text, nullable=True)

    # --- Campos Legados / Seção 6 ---
    # Nota: parecer_juridico mapeado como analise_ia no domínio
    parecer_juridico = Column(Text, nullable=True) 
    risco_judicial = Column(String, nullable=True)
    valor_venda_estimado = Column(Float, default=0.0)
    custo_reforma = Column(Float, default=0.0)
    custo_desocupacao = Column(Float, default=0.0)
    divida_condominio = Column(Float, default=0.0)
    divida_iptu = Column(Float, default=0.0)
    divida_subroga = Column(Boolean, default=False)
    data_atualizacao = Column(Date, nullable=True)

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/database/models_sql.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/repositories/postgres_repo.py ====
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func, distinct
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from src.application.interfaces import AuctionRepository
from src.domain.models import Auction, AuctionFilter, Evaluation, DetailedAnalysis, RiskLevel, OccupationStatus
from src.infra.database.models_sql import LeilaoAnaliticoModel, LeilaoAvaliacaoModel, LeilaoAnaliseDetalhadaModel

class PostgresAuctionRepository(AuctionRepository):
    def __init__(self, session: Session):
        self.session = session

    # --- MÉTODOS DA FASE 1 (TRIAGEM) ---
    def get_pending_auctions(self, user_id: str, filters: AuctionFilter) -> List[Auction]:
        """
        Retorna leilões que NÃO estão na tabela de avaliações.
        Ignora user_id no JOIN para considerar avaliações antigas (histórico global).
        """
        query = self.session.query(LeilaoAnaliticoModel).outerjoin(
            LeilaoAvaliacaoModel,
            and_(
                LeilaoAnaliticoModel.site == LeilaoAvaliacaoModel.site,
                LeilaoAnaliticoModel.id_leilao == LeilaoAvaliacaoModel.id_leilao
            )
        ).filter(LeilaoAvaliacaoModel.id_leilao == None)

        if filters.uf: query = query.filter(LeilaoAnaliticoModel.uf.in_(filters.uf))
        if filters.cidade: query = query.filter(LeilaoAnaliticoModel.cidade.in_(filters.cidade))
        if filters.tipo_bem: query = query.filter(LeilaoAnaliticoModel.tipo_bem.in_(filters.tipo_bem))
        if filters.site: query = query.filter(LeilaoAnaliticoModel.site.in_(filters.site))
        
        # CORREÇÃO: Usamos id_registro_bruto para ordenar (mais recente primeiro)
        # já que data_scrapping não existe no modelo
        query = query.order_by(LeilaoAnaliticoModel.id_registro_bruto.desc())
        
        results = query.limit(100).all()
        return self._map_to_domain(results)

    def save_evaluations(self, evaluations: List[Evaluation]) -> int:
        count = 0
        try:
            for ev in evaluations:
                # Busca ID bruto para integridade
                raw_id = self.session.query(LeilaoAnaliticoModel.id_registro_bruto)\
                    .filter_by(site=ev.site, id_leilao=ev.id_leilao).scalar()
                
                # Fallback se não encontrar direto
                if raw_id is None:
                    raw_id = self.session.query(LeilaoAnaliticoModel.id_registro_bruto)\
                        .filter_by(id_leilao=ev.id_leilao).first()
                    if raw_id: raw_id = raw_id[0]
                    else: continue

                # Upsert (Merge) na tabela leiloes_avaliacoes
                db_model = LeilaoAvaliacaoModel(
                    usuario_id=ev.usuario_id,
                    site=ev.site,
                    id_leilao=ev.id_leilao,
                    id_registro_bruto=raw_id,
                    avaliacao=ev.avaliacao.value,
                    data_analise=ev.data_analise
                )
                self.session.merge(db_model)
                count += 1
            self.session.commit()
            return count
        except Exception as e:
            self.session.rollback()
            raise e

    def get_filter_options(self) -> Dict[str, List[str]]:
        return {
            "ufs": [r[0] for r in self.session.query(distinct(LeilaoAnaliticoModel.uf)).order_by(LeilaoAnaliticoModel.uf).all() if r[0]],
            "cidades": [r[0] for r in self.session.query(distinct(LeilaoAnaliticoModel.cidade)).order_by(LeilaoAnaliticoModel.cidade).all() if r[0]],
            "tipos": [r[0] for r in self.session.query(distinct(LeilaoAnaliticoModel.tipo_bem)).order_by(LeilaoAnaliticoModel.tipo_bem).all() if r[0]],
            "sites": [r[0] for r in self.session.query(distinct(LeilaoAnaliticoModel.site)).order_by(LeilaoAnaliticoModel.site).all() if r[0]],
        }

    def get_stats(self, user_id: str) -> Dict[str, int]:
        try:
            # Stats globais (independente do usuário)
            results = self.session.query(
                LeilaoAvaliacaoModel.avaliacao,
                func.count(LeilaoAvaliacaoModel.id_leilao)
            ).group_by(LeilaoAvaliacaoModel.avaliacao).all()
            
            stats = {'analisar': 0, 'descartar': 0, 'total_processado': 0}
            for status, count in results:
                st_norm = status.capitalize() if status else ""
                if st_norm == 'Analisar': stats['analisar'] = count
                elif st_norm == 'Descartar': stats['descartar'] = count
            stats['total_processado'] = stats['analisar'] + stats['descartar']
            return stats
        except Exception:
            return {'analisar': 0, 'descartar': 0, 'total_processado': 0}

    # --- MÉTODOS DA FASE 2 (CARTEIRA / ANÁLISE) ---

    def get_portfolio_auctions(self, user_id: str) -> List[Auction]:
        """
        Retorna itens da carteira com seus respectivos status.
        Busca: ANALISAR, PARTICIPAR e NO_BID (Descartados).
        """
        # Importe func para tratar maiúsculas/minúsculas se necessário
        from sqlalchemy import and_, func 

        # 1. A Query agora seleciona O Modelo E o Status
        results = self.session.query(
            LeilaoAnaliticoModel,             # O objeto inteiro do leilão
            LeilaoAvaliacaoModel.avaliacao    # A coluna de status
        ).join(
            LeilaoAvaliacaoModel,
            and_(
                LeilaoAnaliticoModel.site == LeilaoAvaliacaoModel.site,
                LeilaoAnaliticoModel.id_leilao == LeilaoAvaliacaoModel.id_leilao
            )
        ).filter(
            # Filtramos pelos 3 estados que queremos ver na carteira
            # Usamos upper() para garantir que pegue 'Analisar' ou 'ANALISAR'
            func.upper(LeilaoAvaliacaoModel.avaliacao).in_([
                "ANALISAR", 
                "PARTICIPAR", 
                "NO_BID"
            ])
            # Se quiser filtrar por usuário descomente abaixo:
            # , LeilaoAvaliacaoModel.usuario_id == user_id
        ).all()
        
        # 2. Mapeamento Manual (pois o _map_to_domain padrão não espera o status)
        portfolio_items = []
        for model, status_text in results:
            # Cria o objeto usando os dados do modelo
            auction = Auction(
                site=model.site,
                id_leilao=model.id_leilao,
                titulo=model.titulo,
                uf=model.uf,
                cidade=model.cidade,
                tipo_leilao=model.tipo_leilao,
                tipo_bem=model.tipo_bem,
                valor_1_praca=float(model.valor_1_praca) if model.valor_1_praca else 0.0,
                valor_2_praca=float(model.valor_2_praca) if model.valor_2_praca else 0.0,
                link_detalhe=model.link_detalhe,
                imagem_capa=model.imagem_capa,
                data_1_praca=model.data_1_praca,
                data_2_praca=model.data_2_praca,
                # AQUI ESTÁ A MÁGICA: Injetamos o status que veio da query
                status_carteira=status_text.upper() if status_text else "ANALISAR"
            )
            portfolio_items.append(auction)
            
        return portfolio_items

    def get_detailed_analysis(self, user_id: str, site: str, id_leilao: str) -> DetailedAnalysis:
        record = self.session.query(LeilaoAnaliseDetalhadaModel).filter_by(
            site=site, id_leilao=id_leilao
        ).first()

        if not record:
            return DetailedAnalysis(site=site, id_leilao=id_leilao, usuario_id=user_id)
        
        return DetailedAnalysis(
            site=record.site,
            id_leilao=record.id_leilao,
            usuario_id=record.usuario_id,
            parecer_juridico=record.parecer_juridico,
            risco_judicial=RiskLevel(record.risco_judicial) if record.risco_judicial else RiskLevel.BAIXO,
            reu_citado=record.reu_citado,
            intimacao_credores=record.intimacao_credores,
            divida_condominio=record.divida_condominio,
            divida_iptu=record.divida_iptu,
            divida_subroga=record.divida_subroga,
            ocupacao_status=OccupationStatus(record.ocupacao_status) if record.ocupacao_status else OccupationStatus.VAGO,
            valor_venda_estimado=record.valor_venda_estimado,
            custo_reforma=record.custo_reforma,
            custo_desocupacao=record.custo_desocupacao,
            data_atualizacao=record.data_atualizacao
        )

    def save_detailed_analysis(self, analysis):
        """
        Salva ou atualiza a análise detalhada.
        """
        from sqlalchemy.dialects.postgresql import insert
        
        # Helper para extrair valor (se for Enum pega .value, se for string usa ela mesma)
        def get_val(field, default):
            if not field:
                return default
            return field.value if hasattr(field, "value") else field

        stmt = insert(LeilaoAnaliseDetalhadaModel).values(
            site=analysis.site,
            id_leilao=analysis.id_leilao,
            usuario_id=analysis.usuario_id,
            parecer_juridico=analysis.parecer_juridico,
            risco_judicial=get_val(analysis.risco_judicial, "Baixo"),
            ocupacao_status=get_val(analysis.ocupacao_status, "Vago"),
            reu_citado=analysis.reu_citado,
            intimacao_credores=analysis.intimacao_credores,
            divida_condominio=analysis.divida_condominio,
            divida_iptu=analysis.divida_iptu,
            divida_subroga=getattr(analysis, 'divida_subroga', True),
            valor_venda_estimado=analysis.valor_venda_estimado,
            custo_reforma=analysis.custo_reforma,
            custo_desocupacao=getattr(analysis, 'custo_desocupacao', 0.0),
            data_atualizacao=datetime.now() # Agora vai funcionar porque importamos lá em cima
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['site', 'id_leilao'],
            set_={
                "parecer_juridico": stmt.excluded.parecer_juridico,
                "risco_judicial": stmt.excluded.risco_judicial,
                "reu_citado": stmt.excluded.reu_citado,
                "intimacao_credores": stmt.excluded.intimacao_credores,
                "divida_condominio": stmt.excluded.divida_condominio,
                "divida_iptu": stmt.excluded.divida_iptu,
                "ocupacao_status": stmt.excluded.ocupacao_status,
                "valor_venda_estimado": stmt.excluded.valor_venda_estimado,
                "custo_reforma": stmt.excluded.custo_reforma,
                "data_atualizacao": datetime.now()
            }
        )
        
        try:
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def _map_to_domain(self, results) -> List[Auction]:
        return [
            Auction(
                site=r.site,
                id_leilao=r.id_leilao,
                titulo=r.titulo,
                uf=r.uf,
                cidade=r.cidade,
                tipo_leilao=r.tipo_leilao,
                tipo_bem=r.tipo_bem,
                valor_1_praca=float(r.valor_1_praca) if r.valor_1_praca else 0.0,
                valor_2_praca=float(r.valor_2_praca) if r.valor_2_praca else 0.0,
                link_detalhe=r.link_detalhe,
                imagem_capa=r.imagem_capa,
                # --- MAPEAMENTO DAS DATAS ---
                data_1_praca=r.data_1_praca,
                data_2_praca=r.data_2_praca
            )
            for r in results
        ]
    
    def update_status(self, user_id: str, site: str, id_leilao: str, new_status: str):
        """
        Atualiza a tabela de controle de fluxo (avaliacoes)
        para mover o card entre as abas.
        """
        from sqlalchemy import text
        
        query = text("""
            UPDATE leiloes_avaliacoes
            SET avaliacao = :status, updated_at = NOW()
            WHERE usuario_id = :uid 
              AND site = :site 
              AND id_leilao = :id_leilao
        """)
        
        self.session.execute(query, {
            "status": new_status,
            "uid": user_id,
            "site": site,
            "id_leilao": id_leilao
        })
        self.session.commit()
        
    def update_auction_core_data(self, site: str, id_leilao: str, data: dict):
        """
        Atualiza dados estruturais do leilão (Correção manual de datas/valores).
        """
        # Busca o leilão
        auction = self.session.query(LeilaoAnaliticoModel).filter_by(
            site=site, 
            id_leilao=id_leilao
        ).first()
        
        if not auction:
            raise ValueError("Leilão não encontrado para edição.")

        # Atualiza os campos se eles estiverem no dicionário 'data'
        if "titulo" in data: auction.titulo = data["titulo"]
        if "valor_1_praca" in data: auction.valor_1_praca = data["valor_1_praca"]
        if "valor_2_praca" in data: auction.valor_2_praca = data["valor_2_praca"]
        if "data_1_praca" in data: auction.data_1_praca = data["data_1_praca"]
        if "data_2_praca" in data: auction.data_2_praca = data["data_2_praca"]
        
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_detailed_analysis(self, site: str, id_leilao: str, user_id: str) -> Optional[DetailedAnalysis]:
        """
        Recupera a análise completa mapeada para o domínio.
        Garante que campos nulos no DB sejam convertidos para os defaults do Dataclass.
        """
        row = self.session.query(LeilaoAnaliseDetalhadaModel).filter_by(
            site=site, id_leilao=id_leilao, usuario_id=user_id
        ).first()

        if not row:
            return None

    def save_auditoria_rascunho(self, a: DetailedAnalysis) -> None:
        """
        Implementa Upsert (ON CONFLICT DO UPDATE) para todos os novos campos.
        Ref: AC-1 e AC-5
        """
        try:
            # Mapeamento do Domínio para o Modelo ORM
            stmt = insert(LeilaoAnaliseDetalhadaModel).values(
                site=a.site,
                id_leilao=a.id_leilao,
                usuario_id=a.usuario_id,
                proc_num=a.proc_num,
                proc_executados=a.proc_executados,
                proc_adv_exec=a.proc_adv_exec,
                proc_citacao=a.proc_citacao,
                proc_conjuge=a.proc_conjuge.value if a.proc_conjuge else None,
                proc_credores=a.proc_credores,
                proc_recursos=a.proc_recursos,
                proc_recursos_obs=a.proc_recursos_obs,
                proc_coproprietario_intimado=a.proc_coproprietario_intimado,
                proc_natureza_execucao=a.proc_natureza_execucao.value if a.proc_natureza_execucao else None,
                proc_justica_gratuita=a.proc_justica_gratuita,
                proc_especie_credito=a.proc_especie_credito.value if a.proc_especie_credito else None,
                proc_debito_atualizado=a.proc_debito_atualizado,
                proc_avaliacao_imovel=a.proc_avaliacao_imovel,
                mat_num=a.mat_num,
                mat_proprietario=a.mat_proprietario,
                mat_penhoras=a.mat_penhoras,
                mat_conjugue=a.mat_conjugue,
                mat_prop_confere=a.mat_prop_confere,
                mat_proprietario_pj=a.mat_proprietario_pj,
                mat_penhora_averbada=a.mat_penhora_averbada,
                mat_usufruto=a.mat_usufruto,
                mat_indisp=a.mat_indisp,
                mat_vagas_mat=a.mat_vagas_mat,
                edt_objeto=a.edt_objeto,
                edt_vlr_avaliacao=a.edt_vlr_avaliacao,
                edt_percentual_minimo=a.edt_percentual_minimo,
                edt_data_avaliacao=a.edt_data_avaliacao,
                edt_parcelamento=a.edt_parcelamento,
                edt_iptu_subroga=a.edt_iptu_subroga,
                edt_condo_claro=a.edt_condo_claro,
                edt_posse_status=a.edt_posse_status,
                edt_posse_estrategia=a.edt_posse_estrategia,
                fin_lance=a.fin_lance,
                fin_itbi=a.fin_itbi,
                fin_dividas=a.fin_dividas,
                parecer_juridico=a.analise_ia, # Mapeamento legado
                valor_venda_estimado=a.valor_venda_estimado,
                custo_reforma=a.custo_reforma,
                custo_desocupacao=a.custo_desocupacao,
                divida_condominio=a.divida_condominio,
                divida_iptu=a.divida_iptu,
                divida_subroga=a.divida_subroga
            )

            # Define o que atualizar em caso de conflito (todas as colunas exceto chaves)
            update_cols = {c.name: c for c in stmt.excluded if not c.primary_key}
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['site', 'id_leilao', 'usuario_id'],
                set_=update_cols
            )

            self.session.execute(upsert_stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e


    # Helper para conversão segura de Enums
    def safe_enum(enum_class, value):
        try:
            return enum_class(value) if value else None
        except ValueError:
            return None

        return DetailedAnalysis(
        site=row.site,
        id_leilao=row.id_leilao,
        usuario_id=row.usuario_id,
        
        # --- Seção 1: Processo Judicial ---
        proc_num=row.proc_num,
        proc_executados=row.proc_executados if isinstance(row.proc_executados, list) else [],
        proc_adv_exec=row.proc_adv_exec,
        proc_citacao=row.proc_citacao,
        proc_conjuge=safe_enum(ConjugeStatus, row.proc_conjuge),
        proc_credores=row.proc_credores,
        proc_recursos=row.proc_recursos,
        proc_recursos_obs=row.proc_recursos_obs,
        proc_coproprietario_intimado=row.proc_coproprietario_intimado,
        proc_natureza_execucao=safe_enum(NaturezaExecucao, row.proc_natureza_execucao),
        proc_justica_gratuita=row.proc_justica_gratuita,
        proc_especie_credito=safe_enum(EspecieCredito, row.proc_especie_credito),
        proc_debito_atualizado=float(row.proc_debito_atualizado or 0.0),
        proc_avaliacao_imovel=row.proc_avaliacao_imovel,

        # --- Seção 2: Matrícula e Gravames ---
        mat_num=row.mat_num,
        mat_proprietario=row.mat_proprietario if isinstance(row.mat_proprietario, list) else [],
        mat_penhoras=row.mat_penhoras if isinstance(row.mat_penhoras, list) else [],
        mat_conjugue=row.mat_conjugue,
        mat_prop_confere=row.mat_prop_confere,
        mat_proprietario_pj=row.mat_proprietario_pj,
        mat_penhora_averbada=row.mat_penhora_averbada,
        mat_usufruto=row.mat_usufruto,
        mat_indisp=row.mat_indisp,
        mat_vagas_mat=row.mat_vagas_mat,

        # --- Seção 3: Edital e Dívidas ---
        edt_objeto=row.edt_objeto,
        edt_vlr_avaliacao=float(row.edt_vlr_avaliacao or 0.0),
        edt_percentual_minimo=float(row.edt_percentual_minimo) if row.edt_percentual_minimo else None,
        edt_data_avaliacao=row.edt_data_avaliacao,
        edt_parcelamento=row.edt_parcelamento,
        edt_iptu_subroga=row.edt_iptu_subroga,
        edt_condo_claro=row.edt_condo_claro,

        # --- Seção 4: Situação Física ---
        edt_posse_status=row.edt_posse_status,
        edt_posse_estrategia=row.edt_posse_estrategia,

        # --- Seção 5: Financeiro ---
        fin_lance=float(row.fin_lance or 0.0),
        fin_itbi=float(row.fin_itbi or 0.0),
        fin_dividas=float(row.fin_dividas or 0.0),
        recomendacao_ia=row.recomendacao_ia,

        # --- Legado e Seção 6 ---
        analise_ia=row.parecer_juridico, # Mapeamento da coluna antiga
        risco_judicial=row.risco_judicial,
        valor_venda_estimado=float(row.valor_venda_estimado or 0.0),
        custo_reforma=float(row.custo_reforma or 0.0),
        custo_desocupacao=float(row.custo_desocupacao or 0.0),
        divida_condominio=float(row.divida_condominio or 0.0),
        divida_iptu=float(row.divida_iptu or 0.0),
        divida_subroga=row.divida_subroga or False,
        data_atualizacao=row.data_atualizacao
    )   
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/repositories/postgres_repo.py ====
