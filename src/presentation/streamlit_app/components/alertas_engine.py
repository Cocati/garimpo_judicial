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