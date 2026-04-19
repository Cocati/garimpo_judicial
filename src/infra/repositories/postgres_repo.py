from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, func, distinct
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from src.application.interfaces import AuctionRepository
from src.domain.models import (
    Auction, AuctionFilter, Evaluation, DetailedAnalysis,
    RiskLevel, OccupationStatus, ConjugeStatus, NaturezaExecucao, EspecieCredito, EvaluationStatus, NoBidReason
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
        
        results = query.all()
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
        """
        Retorna opções de filtro apenas para leilões pendentes de triagem.
        Filtra leilões que NÃO possuem avaliação na tabela leiloes_avaliacoes.
        """
        # Subquery para identificar leilões já avaliados
        subquery = self.session.query(
            LeilaoAvaliacaoModel.site,
            LeilaoAvaliacaoModel.id_leilao
        ).subquery()
        
        # Query base com outerjoin para filtrar apenas pendentes
        base_query = self.session.query(LeilaoAnaliticoModel).outerjoin(
            subquery,
            and_(
                LeilaoAnaliticoModel.site == subquery.c.site,
                LeilaoAnaliticoModel.id_leilao == subquery.c.id_leilao
            )
        ).filter(subquery.c.id_leilao == None)
        
        return {
            "ufs": [r[0] for r in base_query.with_entities(distinct(LeilaoAnaliticoModel.uf)).order_by(LeilaoAnaliticoModel.uf).all() if r[0]],
            "cidades": [r[0] for r in base_query.with_entities(distinct(LeilaoAnaliticoModel.cidade)).order_by(LeilaoAnaliticoModel.cidade).all() if r[0]],
            "tipos": [r[0] for r in base_query.with_entities(distinct(LeilaoAnaliticoModel.tipo_bem)).order_by(LeilaoAnaliticoModel.tipo_bem).all() if r[0]],
            "sites": [r[0] for r in base_query.with_entities(distinct(LeilaoAnaliticoModel.site)).order_by(LeilaoAnaliticoModel.site).all() if r[0]],
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
            LeilaoAvaliacaoModel.avaliacao,
            LeilaoAnaliseDetalhadaModel.no_bid_reason
        ).join(
            LeilaoAvaliacaoModel,
            and_(
                LeilaoAnaliticoModel.site == LeilaoAvaliacaoModel.site,
                LeilaoAnaliticoModel.id_leilao == LeilaoAvaliacaoModel.id_leilao
            )
        ).outerjoin(
            LeilaoAnaliseDetalhadaModel,
            and_(
                LeilaoAnaliticoModel.site == LeilaoAnaliseDetalhadaModel.site,
                LeilaoAnaliticoModel.id_leilao == LeilaoAnaliseDetalhadaModel.id_leilao,
                # Garante que estamos pegando a análise do usuário correto
                LeilaoAvaliacaoModel.usuario_id == LeilaoAnaliseDetalhadaModel.usuario_id
            )
        ).filter(
            func.upper(LeilaoAvaliacaoModel.avaliacao).in_([
                "ANALISAR", 
                "PARTICIPAR", 
                "NO_BID",
                "OUTBID"
            ])
        ).all()
        
        portfolio_items = []
        for model, status_text, no_bid_reason in results:
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
                status_carteira=status_text.upper() if status_text else "ANALISAR",
                no_bid_reason=no_bid_reason
            )
            portfolio_items.append(auction)
            
        return portfolio_items

    def save_detailed_analysis(self, analysis: DetailedAnalysis):
        """
        Executa o UPSERT (Inserir ou Atualizar) dos dados da auditoria detalhada.
        Mapeia todos os campos do objeto de domínio para as colunas do banco.
        """
        # 1. Construção do dicionário de dados (Mapeamento Domain -> DB)
        data = {
            # --- Chaves Primárias ---
            "site": analysis.site,
            "id_leilao": analysis.id_leilao,
            "usuario_id": analysis.usuario_id,

            # --- Seção 1: Processo Judicial ---
            "proc_num": analysis.proc_num,
            "proc_executados": analysis.proc_executados,  # Lista -> JSONB
            "proc_adv_exec": analysis.proc_adv_exec,
            "proc_citacao": analysis.proc_citacao,
            "proc_conjuge": analysis.proc_conjuge.value if analysis.proc_conjuge else None,
            "proc_credores": analysis.proc_credores,
            "proc_recursos": analysis.proc_recursos,
            "proc_recursos_obs": analysis.proc_recursos_obs,
            "proc_coproprietario_intimado": analysis.proc_coproprietario_intimado,
            "proc_natureza_execucao": analysis.proc_natureza_execucao.value if analysis.proc_natureza_execucao else None,
            "proc_justica_gratuita": analysis.proc_justica_gratuita,
            "proc_especie_credito": analysis.proc_especie_credito.value if analysis.proc_especie_credito else None,
            "proc_debito_atualizado": analysis.proc_debito_atualizado,
            "proc_avaliacao_imovel": analysis.proc_avaliacao_imovel,
            "vlr_avaliacao": analysis.vlr_avaliacao,

            # --- Seção 2: Matrícula e Gravames ---
            "mat_num": analysis.mat_num,
            "mat_proprietario": analysis.mat_proprietario,  # Lista -> JSONB
            "mat_documentos_proprietarios": analysis.mat_documentos_proprietarios, # Lista -> JSONB
            "mat_penhoras": analysis.mat_penhoras,  # Lista -> JSONB
            "mat_conjugue": analysis.mat_conjugue,
            "mat_prop_confere": analysis.mat_prop_confere,
            "mat_proprietario_pj": analysis.mat_proprietario_pj,
            "mat_penhora_averbada": analysis.mat_penhora_averbada,
            "mat_usufruto": analysis.mat_usufruto,
            "mat_indisp": analysis.mat_indisp,
            "mat_vagas_mat": analysis.mat_vagas_mat if "" else None,

            # --- Seção 3: Edital e Dívidas ---
            "edt_objeto": analysis.edt_objeto,
            "edt_vlr_avaliacao": analysis.edt_vlr_avaliacao,
            "edt_percentual_minimo": analysis.edt_percentual_minimo,
            "edt_data_avaliacao": analysis.edt_data_avaliacao,
            "edt_parcelamento": analysis.edt_parcelamento,
            "edt_iptu_subroga": analysis.edt_iptu_subroga,
            "edt_condo_claro": analysis.edt_condo_claro,

            # --- Seção 4: Posse e Situação Física ---
            "edt_posse_status": analysis.edt_posse_status if analysis.edt_posse_status else None,
            #"edt_posse_estrategia": analysis.edt_posse_estrategia,

            # --- Seção 5: Financeiro ---
            "fin_lance": analysis.fin_lance,
            "fin_itbi": analysis.fin_itbi,
            "fin_dividas": analysis.fin_dividas,
            "recomendacao_ia": analysis.recomendacao_ia,

            # --- Legado e Compatibilidade ---
            "parecer_juridico": analysis.analise_ia,  # Mapeado no modelo DDL como parecer_juridico
            "risco_judicial": analysis.risco_judicial.value if analysis.risco_judicial else "Baixo",
            "valor_venda_estimado": analysis.valor_venda_estimado,
            "custo_reforma": analysis.custo_reforma,
            "custo_desocupacao": analysis.custo_desocupacao,
            "divida_condominio": analysis.divida_condominio,
            "divida_iptu": analysis.divida_iptu,
            "divida_subroga": analysis.divida_subroga,
            "data_atualizacao": datetime.now(),
            "no_bid_reason": analysis.no_bid_reason.value if analysis.no_bid_reason else None,
            "no_bid_observation": analysis.no_bid_observation
        }

        stmt = insert(LeilaoAnaliseDetalhadaModel).values(**data)
        
        # Faz o update automático em caso de colisão de chaves
        stmt = stmt.on_conflict_do_update(
            index_elements=["site", "id_leilao", "usuario_id"],
            set_={k: v for k, v in data.items() if k not in ["site", "id_leilao", "usuario_id"]}
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
    
    def update_status(self, user_id: str, site: str, id_leilao: str, new_status: EvaluationStatus) -> None:
        """
        Atualiza o status de avaliação do leilão para um utilizador.
        Implementa UPSERT (ON CONFLICT DO UPDATE) sincronizado com o DDL da tabela leiloes_avaliacoes.
        """
        # 1. Recuperar o id_registro_bruto obrigatório (NOT NULL no DDL)
        analitico = self.session.query(LeilaoAnaliticoModel.id_registro_bruto).filter_by(
            site=site, 
            id_leilao=id_leilao
        ).first()
        
        if not analitico:
            raise RuntimeError(f"Falha de integridade: Leilão {id_leilao} no site {site} não encontrado na base analítica.")
            
        id_registro_bruto = analitico.id_registro_bruto

        # 2. Definir os valores alinhados com as colunas reais (avaliacao, data_analise)
        valores = {
            "id_registro_bruto": id_registro_bruto,
            "site": site,
            "id_leilao": id_leilao,
            "usuario_id": user_id,
            "avaliacao": new_status.value, # Coluna correta conforme DDL
            "data_analise": datetime.now(), 
            "updated_at": datetime.now()
        }

        # 3. Criar a instrução de INSERT do SQLAlchemy (PostgreSQL Dialect)
        stmt = insert(LeilaoAvaliacaoModel).values(**valores)

        # 4. Aplicar a regra de ON CONFLICT (UPSERT)
        # O DDL define a Primary Key como (usuario_id, site, id_leilao)
        stmt = stmt.on_conflict_do_update(
            index_elements=['usuario_id', 'site', 'id_leilao'],
            set_={
                'avaliacao': stmt.excluded.avaliacao,
                'updated_at': stmt.excluded.updated_at
                # data_analise é mantida a da primeira inserção, apenas updated_at muda na atualização
            }
        )

        try:
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise RuntimeError(f"Falha ao atualizar o status do leilão (Upsert): {str(e)}")
        
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
        if "link_detalhe" in data: auction.link_detalhe = data["link_detalhe"]
        
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def save_auditoria_rascunho(self, a: DetailedAnalysis) -> None:
        """
        Salva o rascunho da auditoria.
        Como a estrutura de dados é idêntica à análise final, 
        reutilizamos a lógica centralizada para garantir consistência.
        """
        # Reutiliza o método save_detailed_analysis que já atualizamos e validamos
        self.save_detailed_analysis(a)


    def get_detailed_analysis(self, site: str, id_leilao: str, user_id: str) -> Optional[DetailedAnalysis]:
        """
        Recupera a análise detalhada. Retorna None se não existir.
        Inclui proteção contra transações falhas.
        """
        try:
            row = self.session.query(LeilaoAnaliseDetalhadaModel).filter_by(
                site=site, id_leilao=id_leilao, usuario_id=user_id
            ).first()

            if not row:
                return None

            # Helper interno seguro
            def safe_enum(enum_cls, value):
                try:
                    return enum_cls(value) if value else None
                except ValueError:
                    return None

            return DetailedAnalysis(
                site=row.site,
                id_leilao=row.id_leilao,
                usuario_id=row.usuario_id,
                
                # --- Seção 1 ---
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
                vlr_avaliacao=float(row.vlr_avaliacao or 0.0),

                # --- Seção 2 ---
                mat_num=row.mat_num,
                mat_proprietario=row.mat_proprietario if isinstance(row.mat_proprietario, list) else [],
                mat_documentos_proprietarios=row.mat_documentos_proprietarios if isinstance(row.mat_documentos_proprietarios, list) else [],
                mat_penhoras=row.mat_penhoras if isinstance(row.mat_penhoras, list) else [],
                mat_conjugue=str(row.mat_conjugue) if row.mat_conjugue is not None else "",
                mat_prop_confere=row.mat_prop_confere,
                mat_proprietario_pj=row.mat_proprietario_pj,
                mat_penhora_averbada=row.mat_penhora_averbada,
                mat_usufruto=row.mat_usufruto,
                mat_indisp=row.mat_indisp,
                mat_vagas_mat=str(row.mat_vagas_mat) if row.mat_vagas_mat is not None else "",

                # --- Seção 3 ---
                edt_objeto=row.edt_objeto,
                edt_vlr_avaliacao=float(row.edt_vlr_avaliacao or 0.0),
                edt_percentual_minimo=float(row.edt_percentual_minimo or 0.0),
                edt_data_avaliacao=row.edt_data_avaliacao,
                edt_parcelamento=row.edt_parcelamento,
                edt_iptu_subroga=row.edt_iptu_subroga,
                edt_condo_claro=row.edt_condo_claro,

                # --- Seção 4 ---
                edt_posse_status=safe_enum(OccupationStatus, row.edt_posse_status),
                #edt_posse_estrategia=row.edt_posse_estrategia,

                # --- Seção 5 ---
                fin_lance=float(row.fin_lance or 0.0),
                fin_itbi=float(row.fin_itbi or 0.0),
                fin_dividas=float(row.fin_dividas or 0.0),
                recomendacao_ia=row.recomendacao_ia,

                # --- Legado ---
                analise_ia=row.parecer_juridico,
                risco_judicial=safe_enum(RiskLevel, row.risco_judicial) if row.risco_judicial else RiskLevel.BAIXO,
                valor_venda_estimado=float(row.valor_venda_estimado or 0.0),
                custo_reforma=float(row.custo_reforma or 0.0),
                custo_desocupacao=float(row.custo_desocupacao or 0.0),
                divida_condominio=float(row.divida_condominio or 0.0),
                divida_iptu=float(row.divida_iptu or 0.0),
                divida_subroga=row.divida_subroga if row.divida_subroga is not None else True,

                no_bid_reason=safe_enum(NoBidReason, row.no_bid_reason),
                no_bid_observation=row.no_bid_observation
            )
        except Exception as e:
            # CRÍTICO: Se der erro (ex: coluna não existe), faz rollback para não travar a próxima requisição
            self.session.rollback()
            # Opcional: printar o erro real para debug
            print(f"Erro ao buscar auditoria: {e}")
            raise e
            
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