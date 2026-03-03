from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func, distinct
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from src.application.interfaces import AuctionRepository
from src.domain.models import (
    Auction, AuctionFilter, Evaluation, DetailedAnalysis, 
    RiskLevel, OccupationStatus, ConjugeStatus, NaturezaExecucao, EspecieCredito
)
from src.infra.database.models_sql import (
    LeilaoAnaliticoModel, LeilaoAvaliacaoModel, LeilaoAnaliseDetalhadaModel
)

class PostgresAuctionRepository(AuctionRepository):
    def __init__(self, session: Session):
        self.session = session

    # --- MÉTODOS DA FASE 1 (TRIAGEM) ---
    def get_pending_auctions(self, user_id: str, filters: AuctionFilter) -> List[Auction]:
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
        
        query = query.order_by(LeilaoAnaliticoModel.id_registro_bruto.desc())
        
        results = query.limit(100).all()
        return self._map_to_domain(results)

    def save_evaluations(self, evaluations: List[Evaluation]) -> int:
        count = 0
        try:
            for ev in evaluations:
                raw_id = self.session.query(LeilaoAnaliticoModel.id_registro_bruto)\
                    .filter_by(site=ev.site, id_leilao=ev.id_leilao).scalar()
                
                if raw_id is None:
                    raw_id = self.session.query(LeilaoAnaliticoModel.id_registro_bruto)\
                        .filter_by(id_leilao=ev.id_leilao).first()
                    if raw_id: raw_id = raw_id[0]
                    else: continue

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
        results = self.session.query(
            LeilaoAnaliticoModel,
            LeilaoAvaliacaoModel.avaliacao
        ).join(
            LeilaoAvaliacaoModel,
            and_(
                LeilaoAnaliticoModel.site == LeilaoAvaliacaoModel.site,
                LeilaoAnaliticoModel.id_leilao == LeilaoAvaliacaoModel.id_leilao
            )
        ).filter(
            func.upper(LeilaoAvaliacaoModel.avaliacao).in_([
                "ANALISAR", 
                "PARTICIPAR", 
                "NO_BID"
            ])
        ).all()
        
        portfolio_items = []
        for model, status_text in results:
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
                status_carteira=status_text.upper() if status_text else "ANALISAR"
            )
            portfolio_items.append(auction)
            
        return portfolio_items

    def save_detailed_analysis(self, analysis):
        """
        Salva ou atualiza a análise detalhada (Método Legado - mantido para compatibilidade).
        """
        def get_val(field, default):
            if not field: return default
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
            data_atualizacao=datetime.now()
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['site', 'id_leilao', 'usuario_id'],
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
                data_1_praca=r.data_1_praca,
                data_2_praca=r.data_2_praca
            )
            for r in results
        ]
    
    def update_status(self, user_id: str, site: str, id_leilao: str, new_status: str):
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
        auction = self.session.query(LeilaoAnaliticoModel).filter_by(
            site=site, 
            id_leilao=id_leilao
        ).first()
        
        if not auction:
            raise ValueError("Leilão não encontrado para edição.")

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

    def save_auditoria_rascunho(self, a: DetailedAnalysis) -> None:
        """
        Implementa Upsert (ON CONFLICT DO UPDATE) para todos os novos campos (V2).
        ATENÇÃO: Inclui vlr_avaliacao, proc_executados e conversão de Enums.
        """
        try:
            # Mapeamento do Domínio para o Modelo ORM
            stmt = insert(LeilaoAnaliseDetalhadaModel).values(
                site=a.site,
                id_leilao=a.id_leilao,
                usuario_id=a.usuario_id,
                
                # --- Seção 1 ---
                proc_num=a.proc_num,
                proc_executados=a.proc_executados, # SQLAlchemy mapeia list -> JSONB
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
                vlr_avaliacao=a.vlr_avaliacao, # NOVO: Resolve erro UndefinedColumn

                # --- Seção 2 ---
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
                
                # --- Seção 3 ---
                edt_objeto=a.edt_objeto,
                edt_vlr_avaliacao=a.edt_vlr_avaliacao,
                edt_percentual_minimo=a.edt_percentual_minimo,
                edt_data_avaliacao=a.edt_data_avaliacao,
                edt_parcelamento=a.edt_parcelamento,
                edt_iptu_subroga=a.edt_iptu_subroga,
                edt_condo_claro=a.edt_condo_claro,
                
                # --- Seção 4 & 5 ---
                edt_posse_status=a.edt_posse_status,
                edt_posse_estrategia=a.edt_posse_estrategia,
                fin_lance=a.fin_lance,
                fin_itbi=a.fin_itbi,
                fin_dividas=a.fin_dividas,
                recomendacao_ia=a.parecer_juridico, # Alias
                
                # --- Campos Legado / Financeiros ---
                parecer_juridico=a.analise_ia, # Nota: analise_ia no domain -> parecer_juridico no DB
                valor_venda_estimado=a.valor_venda_estimado,
                custo_reforma=a.custo_reforma,
                custo_desocupacao=a.custo_desocupacao,
                divida_condominio=a.divida_condominio,
                divida_iptu=a.divida_iptu,
                divida_subroga=a.divida_subroga,
                risco_judicial=a.risco_judicial.value if a.risco_judicial else None,
                data_atualizacao=datetime.now()
            )

            # Upsert dinâmico (atualiza tudo que não é chave primária)
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

    def get_detailed_analysis(self, site: str, id_leilao: str, user_id: str) -> Optional[DetailedAnalysis]:
        """
        Recupera e converte o model ORM para a entidade DetailedAnalysis.
        Garante conversão de tipos (Float) e Enums.
        """
        row = self.session.query(LeilaoAnaliseDetalhadaModel).filter_by(
            site=site, id_leilao=id_leilao, usuario_id=user_id
        ).first()

        if not row:
            return DetailedAnalysis(site=site, id_leilao=id_leilao, usuario_id=user_id)

        # Helper interno para Enums
        def safe_enum(enum_class, value):
            try:
                return enum_class(value) if value else None
            except ValueError:
                return None

        # Helper para Listas JSON
        def safe_list(val):
            if val is None: return []
            if isinstance(val, list): return val
            return []

        return DetailedAnalysis(
            site=row.site,
            id_leilao=row.id_leilao,
            usuario_id=row.usuario_id,
            
            # --- Seção 1: Processo Judicial ---
            proc_num=row.proc_num,
            proc_executados=safe_list(row.proc_executados), # Lista segura
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
            vlr_avaliacao=float(row.vlr_avaliacao or 0.0), # NOVO: Campo recuperado do banco
            
            # --- Seção 2: Matrícula e Gravames ---
            mat_num=row.mat_num,
            mat_proprietario=safe_list(row.mat_proprietario),
            mat_penhoras=safe_list(row.mat_penhoras),
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
            analise_ia=row.parecer_juridico,
            risco_judicial=safe_enum(RiskLevel, row.risco_judicial) if row.risco_judicial else RiskLevel.BAIXO,
            valor_venda_estimado=float(row.valor_venda_estimado or 0.0),
            custo_reforma=float(row.custo_reforma or 0.0),
            custo_desocupacao=float(row.custo_desocupacao or 0.0),
            divida_condominio=float(row.divida_condominio or 0.0),
            divida_iptu=float(row.divida_iptu or 0.0),
            divida_subroga=row.divida_subroga or False,
            data_atualizacao=row.data_atualizacao
        )

    def get_auction(self, site: str, id_leilao: str) -> Optional[Auction]:
        """Busca dados básicos do leilão para o cabeçalho."""
        result = self.session.query(LeilaoAnaliticoModel).filter_by(
            site=site, id_leilao=id_leilao
        ).first()
        
        if not result:
            return None
            
        return Auction(
            site=result.site,
            id_leilao=result.id_leilao,
            titulo=result.titulo,
            uf=result.uf,
            cidade=result.cidade,
            tipo_bem=result.tipo_bem,
            tipo_leilao=result.tipo_leilao,
            valor_1_praca=float(result.valor_1_praca or 0.0),
            valor_2_praca=float(result.valor_2_praca or 0.0),
            link_detalhe=result.link_detalhe,
            imagem_capa=result.imagem_capa,
            data_1_praca=result.data_1_praca,
            data_2_praca=result.data_2_praca
        )