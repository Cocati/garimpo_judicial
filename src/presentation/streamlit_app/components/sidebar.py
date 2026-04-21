import streamlit as st

def render_sidebar(unique_ufs, unique_cities, unique_types, unique_sites, unique_status):
    st.sidebar.header("🔍 Filtros de Busca")
    
    # Filtro UF
    selected_uf = st.sidebar.multiselect(
        "Estado (UF)",
        options=sorted(unique_ufs) if unique_ufs else [],
        default=[]
    )
    
    # Filtro Cidade (lógica de dependência da UF se necessário, ou simples)
    # Aqui assumimos que unique_cities já vem filtrado ou mostra tudo
    selected_city = st.sidebar.multiselect(
        "Cidade",
        options=sorted(unique_cities) if unique_cities else [],
        default=[]
    )
    
    # Filtro Tipo
    selected_type = st.sidebar.multiselect(
        "Tipo do Bem",
        options=sorted(unique_types) if unique_types else [],
        default=[]
    )
    
    # Filtro Site
    selected_site = st.sidebar.multiselect(
        "Leiloeiro / Site",
        options=sorted(unique_sites) if unique_sites else [],
        default=[]
    )
    
    # Filtro Status do Imóvel
    selected_status = st.sidebar.multiselect(
        "Status do Imóvel",
        options=sorted(unique_status) if unique_status else [],
        default=[]
    )
    
    return {
        "uf": selected_uf,
        "cidade": selected_city,
        "tipo_bem": selected_type,
        "site": selected_site,
        "status_imovel": selected_status
    }
