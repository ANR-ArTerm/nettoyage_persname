import re
from datetime import datetime

import pandas as pd
import streamlit as st

import gspread
from google.oauth2.service_account import Credentials

from config import SPREADSHEET


CATALOGUE_SHEET = "catalogue"

def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["connections"]["gsheets"],
        scopes=scopes,
    )
    return gspread.authorize(creds)


def get_spreadsheet_id(spreadsheet_url):
    return spreadsheet_url.split("/d/")[1].split("/")[0]


def create_worksheet_if_missing(spreadsheet_url, worksheet_name, rows=1000, cols=30):
    client = get_gspread_client()
    spreadsheet_id = get_spreadsheet_id(spreadsheet_url)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        return spreadsheet.worksheet(worksheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(
            title=worksheet_name,
            rows=str(max(rows, 1)),
            cols=str(max(cols, 1)),
        )

def normalize_cell(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_df(df):
    df = df.copy()
    df.columns = [str(col).strip() for col in df.columns]
    return df.fillna("").apply(lambda col: col.map(normalize_cell))

def compare_by_xml_id(old_df, new_df):
    old_df = normalize_df(old_df)
    new_df = normalize_df(new_df)

    if "xml:id" not in old_df.columns:
        raise ValueError("La feuille actuelle ne contient pas de colonne xml:id.")
    if "xml:id" not in new_df.columns:
        raise ValueError("Le nouveau tableur ne contient pas de colonne xml:id.")

    old_duplicates = old_df[old_df["xml:id"].duplicated(keep=False)]["xml:id"].unique().tolist()
    new_duplicates = new_df[new_df["xml:id"].duplicated(keep=False)]["xml:id"].unique().tolist()

    if old_duplicates:
        raise ValueError(
            "La feuille actuelle contient des xml:id en double : "
            + ", ".join(old_duplicates[:20])
        )

    if new_duplicates:
        raise ValueError(
            "Le nouveau tableur contient des xml:id en double : "
            + ", ".join(new_duplicates[:20])
        )

    old_indexed = old_df.set_index("xml:id", drop=False)
    new_indexed = new_df.set_index("xml:id", drop=False)

    old_ids = set(old_indexed.index)
    new_ids = set(new_indexed.index)

    added_ids = sorted(new_ids - old_ids)
    removed_ids = sorted(old_ids - new_ids)
    common_ids = sorted(old_ids & new_ids)

    compared_columns = sorted(set(old_df.columns) | set(new_df.columns))
    changed_rows = []
    changed_cells = 0

    for xml_id in common_ids:
        row_changes = []

        for col in compared_columns:
            old_value = old_indexed.at[xml_id, col] if col in old_indexed.columns else ""
            new_value = new_indexed.at[xml_id, col] if col in new_indexed.columns else ""

            old_value = normalize_cell(old_value)
            new_value = normalize_cell(new_value)

            if old_value != new_value:
                row_changes.append(col)
                changed_cells += 1

        if row_changes:
            changed_rows.append(
                {
                    "xml:id": xml_id,
                    "nb_différences": len(row_changes),
                    "colonnes_modifiées": ", ".join(row_changes),
                }
            )

    return {
        "added_ids": added_ids,
        "removed_ids": removed_ids,
        "changed_rows": changed_rows,
        "changed_cells": changed_cells,
        "old_rows": len(old_df),
        "new_rows": len(new_df),
        "old_duplicates": old_duplicates,
        "new_duplicates": new_duplicates,
    }


def make_backup_sheet_name(prefix="BACKUP_catalogue"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def render_catalogue_importer(conn, spreadsheet):
    st.subheader("Importer un nouveau catalogue")

    uploaded_file = st.file_uploader(
        "Importer un tableur CSV",
        type=["csv"],
        help="Le fichier doit contenir une colonne xml:id.",
    )

    if uploaded_file is None:
        return

    try:
        new_df = pd.read_csv(uploaded_file, dtype=str).fillna("")
        old_df = conn.read(
            spreadsheet=spreadsheet,
            worksheet=CATALOGUE_SHEET,
            ttl=0,
        ).fillna("")

        diff = compare_by_xml_id(old_df, new_df)

    except Exception as e:
        st.error(f"Import impossible : {e}")
        return

    st.info(
        f"Ancien catalogue : {diff['old_rows']} lignes. "
        f"Nouveau catalogue : {diff['new_rows']} lignes."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Personnes ajoutées", len(diff["added_ids"]))
    c2.metric("Personnes supprimées", len(diff["removed_ids"]))
    c3.metric("Personnes modifiées", len(diff["changed_rows"]))
    c4.metric("Cellules modifiées", diff["changed_cells"])

    with st.expander("Voir les différences"):
        if diff["added_ids"]:
            st.markdown("**Ajouts**")
            st.dataframe(pd.DataFrame({"xml:id": diff["added_ids"]}), width='stretch')

        if diff["removed_ids"]:
            st.markdown("**Suppressions**")
            st.dataframe(pd.DataFrame({"xml:id": diff["removed_ids"]}), width='stretch')

        if diff["changed_rows"]:
            st.markdown("**Lignes modifiées**")
            st.dataframe(pd.DataFrame(diff["changed_rows"]), width='stretch')

    has_changes = (
        diff["added_ids"]
        or diff["removed_ids"]
        or diff["changed_rows"]
    )

    if not has_changes:
        st.success("Aucune différence détectée.")
        return

    confirm = st.checkbox(
        "Je confirme vouloir sauvegarder l'ancien catalogue puis remplacer la feuille catalogue."
    )

    if st.button("Importer le nouveau catalogue", type="primary", disabled=not confirm):
        backup_sheet = make_backup_sheet_name()

        with st.spinner("Sauvegarde de l'ancien catalogue..."):
            create_worksheet_if_missing(
                spreadsheet,
                backup_sheet,
                rows=len(old_df) + 10,
                cols=len(old_df.columns) + 5,
            )

            conn.update(
                spreadsheet=spreadsheet,
                worksheet=backup_sheet,
                data=old_df,
            )

        with st.spinner("Remplacement du catalogue..."):
            conn.update(
                spreadsheet=spreadsheet,
                worksheet=CATALOGUE_SHEET,
                data=new_df,
            )

        st.cache_data.clear()
        st.session_state.df = new_df
        st.session_state.editing = None

        st.success(
            f"Catalogue importé. Ancienne version sauvegardée dans la feuille {backup_sheet}."
        )
        st.rerun()
