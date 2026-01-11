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