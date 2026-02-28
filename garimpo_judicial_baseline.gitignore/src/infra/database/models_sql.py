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
