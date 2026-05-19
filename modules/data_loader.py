import streamlit as st

@st.cache_data(ttl=60)
def load_data(_conn, spreadsheet):
    df = _conn.read(spreadsheet=spreadsheet)
    return df.fillna("").astype(str)

# Chargement des listes de référence (une seule fois au démarrage)
@st.cache_data
def load_ref_lists(_conn, spreadsheet):
    roles = _conn.read(spreadsheet=spreadsheet, worksheet="REF_roles", usecols=[0], ttl=60)
    types = _conn.read(spreadsheet=spreadsheet, worksheet="REF_types", usecols=[0], ttl=60)
    return {
        "roles": roles.iloc[:, 0].dropna().tolist(),
        "types": types.iloc[:, 0].dropna().tolist(),
    }
