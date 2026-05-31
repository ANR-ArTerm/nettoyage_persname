import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from modules.data_loader import load_data, load_ref_lists
from modules.entry_display import render_entry_display
from modules.entry_editor import render_entry_editor
from modules.import_csv import render_catalogue_importer
from modules.import_xml import render_import_xml_places_page, render_import_xml_persons_page
from modules.pagination import paginate_dataframe, render_pagination
from modules.edit_list import render_ref_editor
from modules.search import search_display
from modules.align_placenames import render_replace_place_qids

st.set_page_config(page_title="Catalogue Arterm", layout="wide")

SPREADSHEET = "https://docs.google.com/spreadsheets/d/10XWqZyB0ADl5Fxu-3H6BGFd2Bgualee9A_0ZAo2nE5c/edit?gid=0#gid=0"
REF_SHEETS = {
    "Rôles": "REF_roles",
    "Types de personnes": "REF_types",
    "PlaceName": "REF_placeName"
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
page = st.sidebar.radio("Navigation", ["📋 Catalogue", 
                                       "📝 Listes de référence", 
                                       "Mise à jour des placename",
                                       "Mise à jour avec l'index des personnes",
                                       "Importer un csv :"
                                       ])

st.sidebar.divider()

if st.sidebar.button("🔄 Rafraîchir les données", width='stretch'):
    st.cache_data.clear()
    st.session_state.df = load_data(conn, SPREADSHEET)
    st.session_state.ref_lists = load_ref_lists(conn, SPREADSHEET)
    st.session_state.editing = None
    st.rerun()

# ================================================================
if page == "📋 Catalogue":
# ================================================================
    search_display(conn, SPREADSHEET)
    
# ================================================================
elif page == "📝 Listes de référence":
# ================================================================

    st.title("📝 Listes de référence")
    render_ref_editor(conn, SPREADSHEET, REF_SHEETS)

elif page == "Mise à jour des placename":
    render_import_xml_places_page()
    render_replace_place_qids(conn, SPREADSHEET)

elif page == "Mise à jour avec l'index des personnes":
    render_import_xml_persons_page()

elif page == "Importer un csv :":
    render_catalogue_importer(conn, SPREADSHEET)