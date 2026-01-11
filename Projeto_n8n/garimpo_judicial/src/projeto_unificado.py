
# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/use_cases.py ====
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
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/use_cases.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/interfaces.py ====
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

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/application/interfaces.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/models.py ====
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

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/domain/models.py ====

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
        "get_portfolio_auctions": GetPortfolio(repo), # Resolve o KeyError atual
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
import pandas as pd
from datetime import datetime

def render_carteira(services, user_id):
    st.title("📁 Minha Carteira de Oportunidades")

    # 1. Gestão de Estado da Visualização
    if "editing_auction_id" not in st.session_state:
        st.session_state["editing_auction_id"] = None

    # Se tiver um ID selecionado, mostra a tela de ANÁLISE PROFUNDA
    if st.session_state["editing_auction_id"]:
        _render_detailed_analysis(services, user_id)
    else:
        # Senão, mostra a LISTAGEM com ABAS
        _render_portfolio_list(services, user_id)

def _render_portfolio_list(services, user_id):
    # 1. Busca todos os itens já com o status mapeado
    all_items = services["get_portfolio_auctions"].execute(user_id)
    
    # 2. Filtra as listas baseado no status
    items_analisar = [i for i in all_items if i.status_carteira == 'ANALISAR']
    items_participar = [i for i in all_items if i.status_carteira == 'PARTICIPAR']
    items_descartados = [i for i in all_items if i.status_carteira == 'NO_BID']

    # 3. Cria as abas
    tab1, tab2, tab3 = st.tabs([
        f"📥 A Analisar ({len(items_analisar)})", 
        f"🚀 Participar ({len(items_participar)})", 
        f"🗑️ Descartados ({len(items_descartados)})"
    ])

    with tab1:
        if not items_analisar:
            st.info("Sua esteira de análise está vazia. Volte para a Triagem!")
        for auction in items_analisar:
            _render_card(auction) 

    with tab2:
        if not items_participar:
            st.info("Nenhum imóvel aprovado para leilão ainda.")
        for auction in items_participar:
            _render_card(auction, is_participating=True)

    with tab3:
        if not items_descartados:
            st.info("Lixeira vazia.")
        for auction in items_descartados:
            _render_card(auction, is_readonly=True)

def _render_card(auction, is_participating=False, is_readonly=False):
    """
    Função auxiliar que desenha o card do imóvel na lista.
    """
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 3, 1])
        
        # Coluna 1: Imagem
        with c1:
            if auction.imagem_capa:
                st.image(auction.imagem_capa, width="stretch")
            else:
                st.markdown("📷 *Sem Foto*")
        
        # Coluna 2: Dados e Datas
        with c2:
            st.subheader(f"{auction.titulo}")
            st.caption(f"📍 {auction.cidade} - {auction.uf} | 🏛️ {auction.site}")
            
            # Helper para formatar data
            def fmt_date(dt):
                return dt.strftime("%d/%m/%Y") if dt else "--/--/--"

            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.markdown(f"**1ª Praça** ({fmt_date(auction.data_1_praca)})")
                st.markdown(f"💰 R$ {auction.valor_1_praca:,.2f}")
            
            with col_p2:
                st.markdown(f"**2ª Praça** ({fmt_date(auction.data_2_praca)})")
                val_2 = auction.valor_2_praca
                st.markdown(f":green[**📉 R$ {val_2:,.2f}**]")
        
        # Coluna 3: Ação
        with c3:
            st.write("") # Espaçamento
            
            # Define o texto do botão baseado no contexto
            btn_label = "Avaliar 📝"
            if is_participating:
                btn_label = "Ver Detalhes 🔍"
            elif is_readonly:
                btn_label = "Revisar 📂"

            # Atualizado para evitar warning: use_container_width -> width="stretch" (ainda suportado)
            # ou width='stretch' se seu streamlit for muito novo.
            if st.button(btn_label, key=f"btn_{auction.id_leilao}", width="stretch"):
                # Salva o contexto na sessão
                st.session_state["editing_auction_id"] = auction.id_leilao
                st.session_state["editing_auction_site"] = auction.site
                st.session_state["current_auction_obj"] = auction
                st.rerun()

def _render_detailed_analysis(services, user_id):
    """
    Tela de Imersão: Análise Jurídica e Financeira.
    """
    id_leilao = st.session_state["editing_auction_id"]
    site = st.session_state["editing_auction_site"]
    auction_obj = st.session_state.get("current_auction_obj")

    # Busca dados detalhados do banco
    analysis_data = services["repo"].get_detailed_analysis(user_id, site, id_leilao)
    
    # --- 1. CABEÇALHO DE NAVEGAÇÃO ---
    c_back, c_title = st.columns([1, 10])
    with c_back:
        if st.button("⬅️"):
            st.session_state["editing_auction_id"] = None
            st.session_state["current_auction_obj"] = None
            st.rerun()
    with c_title:
        st.subheader(f"Análise: {id_leilao}")

    # --- 2. CARD DE CONTEXTO ---
    if auction_obj:
        with st.expander("🔎 Dados do Edital (Clique para recolher)", expanded=True):
            c_img, c_info, c_dates = st.columns([1, 2, 2])
            
            with c_img:
                if auction_obj.imagem_capa:
                    st.image(auction_obj.imagem_capa, width="stretch")
                else:
                    st.markdown("📷 *Sem Foto*")
            
            with c_info:
                st.markdown(f"**{auction_obj.titulo}**")
                st.caption(f"📍 {auction_obj.cidade}/{auction_obj.uf}")
                st.markdown(f"🔗 [Abrir Edital no Site]({auction_obj.link_detalhe})")

            with c_dates:
                def fmt(dt): return dt.strftime("%d/%m/%Y") if dt else "--"
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    st.markdown("**1ª Praça**")
                    st.caption(fmt(auction_obj.data_1_praca))
                    st.markdown(f"R$ {auction_obj.valor_1_praca:,.2f}")
                with col_d2:
                    st.markdown("**2ª Praça**")
                    st.caption(fmt(auction_obj.data_2_praca))
                    st.markdown(f":green[**R$ {auction_obj.valor_2_praca:,.2f}**]")

    st.divider()

    # --- 3. ÁREA DE TRABALHO (FORMULÁRIOS) ---
    col_jur, col_fin = st.columns(2)
    
    with col_jur:
        st.markdown("### ⚖️ Análise Jurídica")
        
        parecer = st.text_area("Parecer Jurídico (Resumo)", value=analysis_data.parecer_juridico or "", height=150)
        
        # --- CORREÇÃO DO ERRO DO SELECTBOX (RISCO) ---
        opcoes_risco = ["Baixo", "Médio", "Alto"]
        
        # Verifica se é Enum ou String para evitar erro
        valor_atual_risco = analysis_data.risco_judicial
        if hasattr(valor_atual_risco, 'value'): 
            valor_atual_risco = valor_atual_risco.value
        
        # Garante que o valor existe na lista, senão usa o padrão
        if valor_atual_risco not in opcoes_risco:
            valor_atual_risco = "Baixo"
            
        risco = st.selectbox("Risco Jurídico", opcoes_risco, index=opcoes_risco.index(valor_atual_risco))

        st.markdown("**Checklist de Nulidades**")
        chk_reu = st.checkbox("Réu Citado Corretamente?", value=analysis_data.reu_citado)
        chk_credores = st.checkbox("Credores Intimados?", value=analysis_data.intimacao_credores)
        
        st.markdown("---")
        
        # --- CORREÇÃO DO ERRO DO SELECTBOX (OCUPAÇÃO) ---
        opcoes_ocupacao = ["Vago", "Ocupado (Proprietário)", "Ocupado (Inquilino)", "Desconhecido"]
        
        # Verifica se é Enum ou String
        valor_atual_ocupacao = analysis_data.ocupacao_status
        if hasattr(valor_atual_ocupacao, 'value'):
            valor_atual_ocupacao = valor_atual_ocupacao.value
        
        # Garante que valor existe na lista
        if valor_atual_ocupacao not in opcoes_ocupacao:
            valor_atual_ocupacao = "Vago"

        # Passamos o INDEX (número inteiro) e não uma lista
        idx_ocupacao = opcoes_ocupacao.index(valor_atual_ocupacao)
        ocupacao = st.selectbox("Situação Física", opcoes_ocupacao, index=idx_ocupacao)

    with col_fin:
        st.markdown("### 💰 Estudo de Viabilidade (ROI)")
        
        venda_estimada = st.number_input("Valor de Venda (Mercado)", value=float(analysis_data.valor_venda_estimado or 0.0))
        
        c1, c2 = st.columns(2)
        div_cond = c1.number_input("Dívida Condomínio", value=float(analysis_data.divida_condominio or 0.0))
        div_iptu = c2.number_input("Dívida IPTU", value=float(analysis_data.divida_iptu or 0.0))
        
        custo_ref = st.number_input("Custo Reforma/Desoc.", value=float(analysis_data.custo_reforma or 0.0))
        
        # Cálculo Simples em Tempo Real
        custo_total_dividas = div_cond + div_iptu + custo_ref
        st.info(f"Passivo Total Levantado: **R$ {custo_total_dividas:,.2f}**")

    st.markdown("---")
    
    # --- BARRA DE AÇÃO (DECISÃO) ---
    col_save, col_approve, col_reject = st.columns([2, 2, 2])
    
    # 1. Salvar Rascunho
    with col_save:
        if st.button("💾 Salvar Progresso", width="stretch"):
            _save_analysis(services, analysis_data, parecer, risco, chk_reu, chk_credores, ocupacao, venda_estimada, div_cond, div_iptu, custo_ref)
            st.toast("Dados salvos com sucesso!")

    # 2. Aprovar (Mover para Participar)
    with col_approve:
        if st.button("🟢 APROVAR P/ LEILÃO", type="primary", width="stretch"):
            # Salva
            _save_analysis(services, analysis_data, parecer, risco, chk_reu, chk_credores, ocupacao, venda_estimada, div_cond, div_iptu, custo_ref)
            # Atualiza Status
            services["repo"].update_status(user_id, site, id_leilao, "PARTICIPAR")
            
            st.balloons()
            st.success("Imóvel movido para a aba PARTICIPAR!")
            st.session_state["editing_auction_id"] = None
            st.rerun()

    # 3. Descartar (Mover para Lixeira)
    with col_reject:
        if st.button("🔴 DESCARTAR / NO-BID", width="stretch"):
             _save_analysis(services, analysis_data, parecer, risco, chk_reu, chk_credores, ocupacao, venda_estimada, div_cond, div_iptu, custo_ref)
             
             # Atualiza Status
             services["repo"].update_status(user_id, site, id_leilao, "NO_BID")
             
             st.error("Imóvel descartado.")
             st.session_state["editing_auction_id"] = None
             st.rerun()

def _save_analysis(services, original_obj, parecer, risco, reu, credores, ocupacao, venda, cond, iptu, reforma):
    """Helper para montar o objeto e salvar"""
    original_obj.parecer_juridico = parecer
    original_obj.risco_judicial = risco
    original_obj.reu_citado = reu
    original_obj.intimacao_credores = credores
    original_obj.ocupacao_status = ocupacao
    original_obj.valor_venda_estimado = venda
    original_obj.divida_condominio = cond
    original_obj.divida_iptu = iptu
    original_obj.custo_reforma = reforma
    
    services["repo"].save_detailed_analysis(original_obj)
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
    df_clean = df.dropna(subset=['id_leilao']).head(15).reset_index(drop=True)
    
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
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

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
    Tabela da Análise Profunda (Fase 2).
    Ajustada para bater com o SQL: public.leiloes_analise_detalhada
    """
    __tablename__ = "leiloes_analise_detalhada"
    
    site = Column(String, primary_key=True)
    id_leilao = Column(String, primary_key=True)
    
    usuario_id = Column(String)
    
    # Jurídico
    parecer_juridico = Column(Text, nullable=True)
    risco_judicial = Column(String, default="Baixo")
    reu_citado = Column(Boolean, default=True)
    intimacao_credores = Column(Boolean, default=True)
    
    # Financeiro / Dívidas
    divida_condominio = Column(Float, default=0.0)
    divida_iptu = Column(Float, default=0.0)
    divida_subroga = Column(Boolean, default=True)
    
    # Imóvel / ROI
    ocupacao_status = Column(String, default="Vago")
    valor_venda_estimado = Column(Float, default=0.0)
    custo_reforma = Column(Float, default=0.0)
    custo_desocupacao = Column(Float, default=0.0)
    
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/database/models_sql.py ====

# ==== Início do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/repositories/postgres_repo.py ====
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func, distinct
from datetime import datetime

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
# ==== Fim do arquivo: /home/cocatis/Projeto_n8n/garimpo_judicial/src/infra/repositories/postgres_repo.py ====
