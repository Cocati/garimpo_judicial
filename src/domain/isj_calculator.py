from typing import List, Dict
from datetime import date
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
            try:
                # Proteção caso a data venha como string ou None
                if isinstance(analysis.edt_data_avaliacao, date):
                    anos_passados = (date.today() - analysis.edt_data_avaliacao).days / 365.25
                    if anos_passados > 1.0:
                        score -= 10.0
            except Exception:
                pass # Ignora erro de data para não quebrar o cálculo

        # Garantir limites [0, 100]
        return max(0.0, min(100.0, score))

    @staticmethod
    def calculate_financial_kpis(analysis: DetailedAnalysis) -> Dict[str, float]:
        """
        Calcula KPIs financeiros derivados para o Painel de Viabilidade.
        Adicionado: Lucro Líquido para corrigir o KeyError.
        """
        # Valores base (com tratamento para None)
        lance = analysis.fin_lance or 0.0
        venda = analysis.valor_venda_estimado or 0.0
        itbi = analysis.fin_itbi or 0.0
        dividas = analysis.fin_dividas or 0.0
        reforma = analysis.custo_reforma or 0.0
        desocupacao = getattr(analysis, 'custo_desocupacao', 0.0) or 0.0
        iptu = analysis.divida_iptu or 0.0
        condo = analysis.divida_condominio or 0.0
        
        # Custos Implícitos
        comissao_leiloeiro = lance * 0.05
        # Custos de venda (Corretagem padrão 6%)
        custo_venda = venda * 0.06
        
        # 1. Investimento Total (Saída de Caixa)
        investimento_total = (
            lance + 
            comissao_leiloeiro + 
            itbi + 
            dividas + 
            reforma + 
            desocupacao +
            iptu +
            condo
        )

        # 2. Lucro Líquido (Venda - Investimento - Custo Venda)
        lucro_liquido = venda - investimento_total - custo_venda

        # 3. ROI Nominal
        roi_nominal = 0.0
        if investimento_total > 0:
            roi_nominal = (lucro_liquido / investimento_total) * 100

        return {
            "investimento_total": investimento_total,
            "lucro_liquido": lucro_liquido,  # <--- CHAVE ADICIONADA AQUI
            "roi_nominal": roi_nominal,
            "preco_vil": (analysis.edt_vlr_avaliacao or 0.0) * (analysis.edt_percentual_minimo or 50.0) / 100
        }