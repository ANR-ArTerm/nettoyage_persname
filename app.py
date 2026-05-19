# streamlit_app.py
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Édition du catalogue")

conn = st.connection("gsheets", type=GSheetsConnection)

spreadsheet_link = "https://docs.google.com/spreadsheets/d/10XWqZyB0ADl5Fxu-3H6BGFd2Bgualee9A_0ZAo2nE5c/edit?gid=0#gid=0"


# Lire les données
df = conn.read(
    spreadsheet=spreadsheet_link
)

# Éditeur interactif
edited_df = st.data_editor(
    df,
    num_rows="dynamic",   # permet d'ajouter des lignes
    width='stretch'
)

# Bouton sauvegarde
if st.button("Sauvegarder les modifications"):
    conn.update(
        spreadsheet=spreadsheet_link,
        data=edited_df
        )
    st.success("Tableur mis à jour ✅")