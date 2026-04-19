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

    # --- OUTROS CAMPOS E METADADOS ---
    parecer_juridico = Column(String, nullable=True)
    risco_judicial = Column(String, default='Baixo')
    vlr_avaliacao = Column(Float, default=0.0)
    data_atualizacao = Column(DateTime, default=datetime.now, onupdate=datetime.now)

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
    # --- Novos Campos: Seção Matrícula ---
    mat_proprietario = Column(JSONB, default=[])
    mat_documentos_proprietarios = Column(JSONB, default=[])
    mat_penhoras = Column(JSONB, default=[])
    mat_conjugue = Column(Boolean, default=None)

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
    #edt_posse_estrategia = Column(String(50), nullable=True)

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

    # --- Novos Campos: Motivo do Descarte ---
    no_bid_reason = Column(String, nullable=True)
    no_bid_observation = Column(Text, nullable=True)
