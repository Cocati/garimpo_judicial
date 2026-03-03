# Arquivo: src/presentation/streamlit_app/components/isj_gauge.py
import streamlit as st
from typing import List
from src.presentation.streamlit_app.components.alertas_engine import Alerta

def render_isj_gauge(isj_score: float, alertas: List[Alerta]):
    """
    Renderiza o medidor de score ISJ e o resumo de alertas.
    Ref: Spec Funcional Seção 7.1 e AC-1 a AC-4
    """
    
    # Determinar cor e texto com base no score (AC-1, AC-2, AC-3)
    if isj_score > 80.0:
        color = "green"
        label = "🟢 FAVORÁVEL"
        help_text = "Segurança jurídica robusta. Riscos mínimos identificados."
    elif isj_score > 60.0:
        color = "orange"
        label = "🟡 FAVORÁVEL COM RESSALVAS"
        help_text = "Exige atenção a pontos específicos. Risco moderado."
    else:
        color = "red"
        label = "🔴 DESFAVORÁVEL"
        help_text = "Alto risco de nulidade ou imobilização de capital. Não recomendado."

    # Renderização do Gauge
    st.subheader("Índice de Segurança Jurídica (ISJ)")
    
    # Barra de progresso colorida via CSS customizado (Streamlit nativo é limitado)
    st.markdown(f"""
        <div style="background-color: #f0f2f6; border-radius: 10px; padding: 5px;">
            <div style="
                background-color: {color}; 
                width: {isj_score}%; 
                height: 25px; 
                border-radius: 8px; 
                transition: width 0.5s ease-in-out;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
            ">
                {isj_score:.1f}%
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"**Parecer Preliminar:** {label}")
    st.info(help_text)

    # Resumo de Alertas por Nível (AC-4)
    if alertas:
        st.write("---")
        st.markdown("#### 🚩 Resumo de Alertas")
        
        # Agregação de contagem
        contagem = {
            "critico": len([a for a in alertas if a.nivel == "critico"]),
            "alto": len([a for a in alertas if a.nivel == "alto"]),
            "medio": len([a for a in alertas if a.nivel == "medio"]),
            "info": len([a for a in alertas if a.nivel == "info"])
        }
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Críticos", contagem["critico"], delta_color="inverse")
        col2.metric("Altos", contagem["alto"], delta_color="off")
        col3.metric("Médios", contagem["medio"], delta_color="off")
        col4.metric("Informativos", contagem["info"], delta_color="off")
