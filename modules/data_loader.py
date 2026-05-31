import streamlit as st

from config import REF_SHEETS

@st.cache_data(ttl=60)
def load_data(_conn, spreadsheet):
    df = _conn.read(spreadsheet=spreadsheet)
    return df.fillna("").astype(str)

# Chargement des listes de référence (une seule fois au démarrage)
@st.cache_data
def load_ref_lists(_conn, spreadsheet):
    types = _conn.read(
        spreadsheet=spreadsheet,
        worksheet=REF_SHEETS["Types de personnes"],
        usecols=[0],
        ttl=60,
    )
    return {
        "types": types.iloc[:, 0].dropna().tolist(),
    }
