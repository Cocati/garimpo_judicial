import streamlit as st
import pandas as pd

def render_triage_cards(df: pd.DataFrame):
    """
    Renderiza os leilões em formato de Cards verticais com altura de imagem fixa.
    Retorna um dicionário com as decisões tomadas.
    """
    if df.empty:
        # Se o dataframe estiver vazio após a filtragem do main, não mostra nada.
        return {}

    # Sanitização básica: Garante que tem ID, pega os primeiros 15 e reseta o índice
    df_clean = df.dropna(subset=['id_leilao']).head(15).reset_index(drop=True)
    
    if df_clean.empty:
         return {}

    # Dicionário para guardar as decisões temporárias
    decisions = {}

    # Estilo CSS para detalhes do card (exceto a imagem, que faremos inline)
    st.markdown("""
    <style>
        /* Ajuste fino para o container do card */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
            border: 1px solid #444;
            border-radius: 12px;
            padding: 15px;
            background-color: #262730; /* Cor de fundo do card */
        }
        .big-font { font-size: 16px !important; font-weight: 600; line-height: 1.4; margin-bottom: 10px;}
        .price-label { font-size: 12px; color: #aaa; }
        .price-value { font-size: 15px; font-weight: bold; }
        .price-value-2 { font-size: 15px; font-weight: bold; color: #4CAF50; } /* Verde para 2ª praça */
        .link-edital { font-size: 13px; text-decoration: none; color: #4da6ff !important; }
    </style>
    """, unsafe_allow_html=True)
    
    st.write(f"Exibindo {len(df_clean)} oportunidades")

    # --- LOOP DOS CARDS ---
    for index, row in df_clean.iterrows():
        id_leilao = str(row['id_leilao'])
        
        # Cria um container para cada leilão
        with st.container():
            # Layout: Imagem (pequena) | Informações (grande) | Ação (pequena)
            col_img, col_info, col_action = st.columns([1.2, 2.3, 1])
            
            # --- 1. COLUNA DA IMAGEM (FIXA) ---
            with col_img:
                img_url = row.get('imagem_capa')
                
                # Se não tiver URL, usa um placeholder do mesmo tamanho
                if not img_url or pd.isna(img_url):
                    img_url = "https://via.placeholder.com/300x220?text=Sem+Foto"

                # CSS HACK: Usamos HTML direto para forçar a altura e o corte (object-fit)
                # height: 220px -> Define a altura fixa
                # object-fit: cover -> Corta o excesso da imagem sem esticar, centralizando o foco.
                st.markdown(
                    f"""
                    <img src="{img_url}" 
                         style="width: 100%; height: 220px; object-fit: cover; border-radius: 8px;" 
                         alt="Foto do bem">
                    """,
                    unsafe_allow_html=True
                )
                
                st.caption(f"ID: {id_leilao} | {row.get('site', 'N/A')}")

            # --- 2. COLUNA DE INFORMAÇÕES ---
            with col_info:
                # Título com classe CSS para limitar tamanho
                titulo = row.get('titulo', 'Sem Título')
                st.markdown(f"<div class='big-font'>{titulo}</div>", unsafe_allow_html=True)
                
                # Exibição de Valores Formatados
                v1 = float(row.get('valor_1_praca', 0) or 0)
                v2 = float(row.get('valor_2_praca', 0) or 0)
                
                c_v1, c_v2 = st.columns(2)
                with c_v1:
                    st.markdown("<span class='price-label'>1ª Praça:</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='price-value'>R$ {v1:,.2f}</div>", unsafe_allow_html=True)
                with c_v2:
                    st.markdown("<span class='price-label'>2ª Praça:</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='price-value-2'>📉 R$ {v2:,.2f}</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                link = row.get('link_detalhe', '#')
                st.markdown(f"🔗 <a href='{link}' target='_blank' class='link-edital'>Ver Edital no Site</a>", unsafe_allow_html=True)

            # --- 3. COLUNA DE AÇÃO (TRIAGEM) ---
            with col_action:
                st.write("**Decisão**")
                
                # Recupera o estado anterior se existir para manter a seleção ao recarregar
                key = f"decision_{id_leilao}"
                
                # Radio Button para decisão rápida
                decision = st.radio(
                    "Decisão para o ID " + id_leilao, # Label invisível, mas necessário para acessibilidade
                    options=["Pendente", "Analisar", "Descartar"],
                    index=2, # <--- 0=Pendente, 1=Analisar, 2=Descartar
                    key=key,
                    label_visibility="collapsed" # Esconde o label para ficar mais limpo
                )
                
                # Se a decisão mudou de "Pendente", guardamos no dict de retorno
                if decision != "Pendente":
                    decisions[id_leilao] = {
                        "id_leilao": id_leilao,
                        "site": row.get('site'),
                        "decisao": decision
                    }
            
            # Adiciona um espaçamento visual entre os cards
            st.write("") 
            st.write("") 

    return decisions
