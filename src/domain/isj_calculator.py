from typing import List, Dict, Optional
from datetime import date
from src.domain.models import DetailedAnalysis, NaturezaExecucao, EspecieCredito, ConjugeStatus

class IsjCalculator:
    """
    Motor de cálculo do Índice de Segurança Jurídica (ISJ).
    Refatorado para consistência de fluxo e aplicação de pesos da Seção 1 (40%).
    """

    @staticmethod
    def calculate(analysis: DetailedAnalysis) -> float:
        """
        Executa o cálculo do score de 0 a 100%.
        Regra: Nulidades Críticas forçam o score a ZERO imediatamente.
        """
        
        # 1. BLOQUEIOS CRÍTICOS (Nulidades Imediatas - AC-4)
        # Se citação inválida ou propriedade não confere, risco é impeditivo.
        if analysis.proc_citacao is False or analysis.mat_prop_confere is False:
            return 0.0

        # Score base inicial
        score = 100.0

        # 2. DEDUÇÕES SEÇÃO 1: PROCESSO JUDICIAL (Peso focado de 40%)
        # Dedução por falta de intimação de cônjuge (Risco de meação/nulidade)
        if analysis.proc_conjuge == ConjugeStatus.NAO:
            score -= 50.0
            
        # Execução Provisória aumenta risco de reversão da arrematação
        if analysis.proc_natureza_execucao == NaturezaExecucao.PROVISORIA:
            score -= 20.0
            
        # Crédito Comum (ex: nota promissória) vs Bem de Família
        if analysis.proc_especie_credito == EspecieCredito.COMUM:
            score -= 15.0
            
        # Recursos pendentes podem atrasar a imissão na posse
        if analysis.proc_recursos is True:
            score -= 20.0
            
        # Justiça Gratuita do executado facilita recursos sem custos (protelação)
        if analysis.proc_justica_gratuita is True:
            score -= 10.0

        # Intimação de Credores e Coproprietários (Se False, deduz. Se None/NA, ignora)
        if analysis.proc_credores is False:
            score -= 20.0
            
        if analysis.proc_coproprietario_intimado is False:
            score -= 40.0

        # KPI de Proporcionalidade: Dívida muito baixa em relação ao bem (Risco de Preço Vil)
        if analysis.vlr_avaliacao > 0:
            proporcionalidade = (float(analysis.proc_debito_atualizado or 0) / analysis.vlr_avaliacao) * 100
            if proporcionalidade < 10.0:
                score -= 15.0

        # 3. DEDUÇÕES SEÇÃO 2: MATRÍCULA E GRAVAMES
        if getattr(analysis, 'mat_indisp', False) is True:
            score -= 30.0
        if getattr(analysis, 'mat_usufruto', False) is True:
            score -= 60.0

        # 4. DEDUÇÕES SEÇÃO 3: EDITAL E DÍVIDAS
        if analysis.edt_condo_claro is False:
            score -= 15.0
        if analysis.edt_iptu_subroga is False:
            score -= 20.0
        
        # Validação de defasagem da avaliação
        if analysis.edt_data_avaliacao:
            try:
                # Se a avaliação tem mais de 1 ano, risco de preço vil por defasagem
                hoje = date.today()
                diff = (hoje - analysis.edt_data_avaliacao).days
                if diff > 365:
                    score -= 10.0
            except: pass 

        # 5. NORMALIZAÇÃO FINAL
        # O score nunca deve ser menor que 0 ou maior que 100
        return max(0.0, min(100.0, score))

    @staticmethod
    def calculate_financial_kpis(analysis: DetailedAnalysis) -> Dict[str, float]:
        """
        Calcula KPIs financeiros para o Painel de Viabilidade.
        """
        lance = float(analysis.fin_lance or 0.0)
        venda = float(analysis.valor_venda_estimado or 0.0)
        itbi = float(analysis.fin_itbi or 0.0)
        
        # Consolidação de passivos ocultos ou declarados
        iptu = float(analysis.divida_iptu or 0.0)
        condo = float(analysis.divida_condominio or 0.0)
        outras_dividas = float(analysis.fin_dividas or 0.0)
        
        reforma = float(analysis.custo_reforma or 0.0)
        desocupacao = float(analysis.custo_desocupacao or 0.0)
        
        # Comissões padrão de mercado
        comissao_leiloeiro = lance * 0.05
        corretagem_venda = venda * 0.06 
        
        investimento_total = (
            lance + comissao_leiloeiro + itbi + 
            outras_dividas + iptu + condo + 
            reforma + desocupacao
        )

        lucro_liquido = venda - investimento_total - corretagem_venda
        roi_nominal = (lucro_liquido / investimento_total * 100) if investimento_total > 0 else 0.0

        return {
            "investimento_total": investimento_total,
            "lucro_liquido": lucro_liquido,
            "roi_nominal": roi_nominal,
            "proporcionalidade_debito": (float(analysis.proc_debito_atualizado or 0) / analysis.vlr_avaliacao * 100) if analysis.vlr_avaliacao > 0 else 0.0
        }