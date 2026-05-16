# Arquivo: src/presentation/streamlit_app/components/alertas_engine.py
from dataclasses import dataclass
from typing import List, Optional
from src.domain.models import DetailedAnalysis, ConjugeStatus, NaturezaExecucao, EspecieCredito
from datetime import date, timedelta

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

        if analysis.mat_penhora_averbada is False:
            alertas.append(Alerta(
                nivel="critico",
                mensagem="🚨 NULIDADE GRAVE: A penhora do processo não está averbada na matrícula.",
                campo_gatilho="mat_penhora_averbada"
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

        if analysis.proc_coproprietario_intimado is False:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ COPROPRIETÁRIO NÃO INTIMADO: Risco de anulação da venda da quota-parte.",
                campo_gatilho="proc_coproprietario_intimado"
            ))

        if analysis.proc_natureza_execucao == NaturezaExecucao.PROVISORIA:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ EXECUÇÃO PROVISÓRIA: Risco de reversão da decisão que baseia a execução.",
                campo_gatilho="proc_natureza_execucao"
            ))

        if analysis.proc_avaliacao_imovel is False:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ AVALIAÇÃO PARCIAL: A avaliação judicial não abrange 100% do imóvel.",
                campo_gatilho="proc_avaliacao_imovel"
            ))

        if analysis.proc_proporcionalidade < 10:
            alertas.append(Alerta(
                nivel="alto",
                mensagem="⚠️ PROPORCIONALIDADE BAIXA: Risco de anulação por execução desproporcional (dívida/bem < 10%).",
                campo_gatilho="proc_debito_atualizado"
            ))

        # --- Nível MÉDIO (Atenção Necessária) ---
        if analysis.proc_recursos is True:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="⚡ RECURSOS PENDENTES: O leilão pode ser anulado ou suspenso.",
                campo_gatilho="proc_recursos"
            ))

        if analysis.proc_credores is False:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="⚠️ OUTROS CREDORES NÃO INTIMADOS: Risco de contestação da preferência.",
                campo_gatilho="proc_credores"
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

        if analysis.proc_especie_credito == EspecieCredito.COMUM:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="⚠️ CRÉDITO COMUM: Risco de alegação de impenhorabilidade de bem de família.",
                campo_gatilho="proc_especie_credito"
            ))

        if analysis.edt_iptu_subroga is False:
            alertas.append(Alerta(
                nivel="medio",
                mensagem="💰 DÍVIDA DE IPTU NÃO SUB-ROGA: Débitos de IPTU serão de responsabilidade do arrematante.",
                campo_gatilho="edt_iptu_subroga"
            ))

        if analysis.edt_data_avaliacao and analysis.edt_data_avaliacao < (date.today() - timedelta(days=365*2)):
            alertas.append(Alerta(
                nivel="medio",
                mensagem="⚠️ AVALIAÇÃO ANTIGA: Valor do imóvel pode estar defasado (> 2 anos).",
                campo_gatilho="edt_data_avaliacao"
            ))

        # --- Nível INFO ---
        if analysis.edt_parcelamento is True:
            alertas.append(Alerta(
                nivel="info",
                mensagem="ℹ️ PARCELAMENTO DISPONÍVEL: Edital permite pagamento parcelado (Art. 895 CPC).",
                campo_gatilho="edt_parcelamento"
            ))

        if analysis.proc_adv_exec is True:
            alertas.append(Alerta(
                nivel="info",
                mensagem="ℹ️ EXECUTADO COM ADVOGADO: Maior probabilidade de interposição de recursos.",
                campo_gatilho="proc_adv_exec"
            ))

        if analysis.mat_proprietario_pj is True:
            alertas.append(Alerta(
                nivel="info",
                mensagem="ℹ️ PROPRIETÁRIO É PJ: Requer análise da saúde financeira da empresa (certidões, etc.).",
                campo_gatilho="mat_proprietario_pj"
            ))

        if analysis.edt_posse_status == "Ocupado":
            alertas.append(Alerta(
                nivel="info",
                mensagem="ℹ️ IMÓVEL OCUPADO: Custos e prazo de desocupação devem ser considerados no plano.",
                campo_gatilho="edt_posse_status"
            ))

        return alertas