import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from modules.data_loader import load_data, load_ref_lists
from modules.entry_display import render_entry_display
from modules.entry_editor import render_entry_editor
from modules.pagination import paginate_dataframe, render_pagination
from modules.edit_list import render_ref_editor

st.set_page_config(page_title="Catalogue Arterm", layout="wide")

SPREADSHEET = "https://docs.google.com/spreadsheets/d/10XWqZyB0ADl5Fxu-3H6BGFd2Bgualee9A_0ZAo2nE5c/edit?gid=0#gid=0"
REF_SHEETS = {
    "Rôles": "REF_roles",
    "Types de personnes": "REF_types",
}

conn = st.connection("gsheets", type=GSheetsConnection)

# --- Chargement ---
if "df" not in st.session_state:
    st.session_state.df = load_data(conn, SPREADSHEET)
if "ref_lists" not in st.session_state:
    st.session_state.ref_lists = load_ref_lists(conn, SPREADSHEET)
if "editing" not in st.session_state:
    st.session_state.editing = None
if "last_search" not in st.session_state:
    st.session_state.last_search = ""

# --- Navigation ---
page = st.sidebar.radio("Navigation", ["📋 Catalogue", "📝 Listes de référence"])

st.sidebar.divider()

if st.sidebar.button("🔄 Rafraîchir les données", use_container_width=True):
    st.cache_data.clear()
    st.session_state.df = load_data(conn, SPREADSHEET)
    st.session_state.ref_lists = load_ref_lists(conn, SPREADSHEET)
    st.session_state.editing = None
    st.rerun()

# ================================================================
if page == "📋 Catalogue":
# ================================================================

    df = st.session_state.df

    st.title("📋 Catalogue des personnes")

    col_search, col_refresh = st.columns([4, 1])
    with col_search:
        search = st.text_input("🔍 Rechercher", placeholder="Nom, lieu, rôle...")

    if search != st.session_state.last_search:
        st.session_state.page = 1
        st.session_state.editing = None
        st.session_state.last_search = search

    with col_refresh:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            st.cache_data.clear()
            st.session_state.df = load_data(conn, SPREADSHEET)
            st.session_state.editing = None
            st.rerun()

    if search:
        mask = df.apply(lambda row: row.str.contains(search, case=False, na=False).any(), axis=1)
        filtered_df = df[mask]
    else:
        filtered_df = df

    st.write(f"**{len(filtered_df)}** entrée(s)")
    st.divider()

    page_df, total_entries, total_pages, start, end = paginate_dataframe(filtered_df)
    render_pagination(total_entries, total_pages, start, end, "top")
    st.divider()

    for idx, row in page_df.iterrows():
        if st.session_state.editing == idx:
            render_entry_editor(idx, row, conn, SPREADSHEET)
        else:
            render_entry_display(idx, row)

    render_pagination(total_entries, total_pages, start, end, "bottom")

# ================================================================
elif page == "📝 Listes de référence":
# ================================================================

    st.title("📝 Listes de référence")
    render_ref_editor(conn, SPREADSHEET, REF_SHEETS)
