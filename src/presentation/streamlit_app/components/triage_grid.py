import streamlit as st
import pandas as pd

def render_triage_grid(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    # --- SANITIZAÇÃO ---
    cols_visualizacao = ["imagem_capa", "titulo", "valor_1_praca", 
                         "valor_2_praca", "link_detalhe", "site", "id_leilao", "decisao"]
    
    df_clean = df[[c for c in cols_visualizacao if c in df.columns]].copy()
    df_clean = df_clean.head(15).reset_index(drop=True)

    if "titulo" in df_clean.columns:
        df_clean["titulo"] = df_clean["titulo"].astype(str).fillna("")
    if "valor_1_praca" in df_clean.columns:
        df_clean["valor_1_praca"] = pd.to_numeric(df_clean["valor_1_praca"], errors='coerce').fillna(0.0)
    if "valor_2_praca" in df_clean.columns:
        df_clean["valor_2_praca"] = pd.to_numeric(df_clean["valor_2_praca"], errors='coerce').fillna(0.0)

    st.info(f"👇 Exibindo **{len(df_clean)}** itens (Máximo de 15 por página).")

    # --- CONFIG ---
    column_config = {
        
        "imagem_capa": st.column_config.ImageColumn("📸 Foto", width="large"),
        "titulo": st.column_config.TextColumn("Descrição", width="large"),
        "valor_1_praca": st.column_config.NumberColumn("💰 1ª Praça", format="R$ %.2f", width="small"),
        "valor_2_praca": st.column_config.NumberColumn("💰 2ª Praça", format="R$ %.2f", width="small"),
        "link_detalhe": st.column_config.LinkColumn("Edital", display_text="🔗 Link", width="small"),
        "site": st.column_config.Column("Site", width="small", disabled=True), 
        "id_leilao": st.column_config.Column("ID", width="small", disabled=True),
        "decisao": st.column_config.SelectboxColumn("Triagem", options=["Pendente", "Analisar", "Descartar"], width="medium", required=True)
    }

    # --- ALTURA ---
    rows = len(df_clean)
    dynamic_height = (rows * 150) + 42

    edited_df = st.data_editor(
        df_clean,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=f"triage_grid_{rows}",
        height=dynamic_height,
        num_rows="fixed",
        disabled=["imagem_capa", "valor_1_praca", "valor_2_praca", "titulo", "link_detalhe", "site", "id_leilao"]
    )
    
    return edited_df
