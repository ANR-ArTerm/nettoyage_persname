import streamlit as st
from modules.data_loader import load_data
from modules.entry_display import render_entry_display
from modules.entry_editor import render_entry_editor
from modules.pagination import paginate_dataframe, render_pagination
from modules.bulk_actions import init_bulk_selection, render_bulk_actions_top, render_entry_checkbox

def search_display(connection, spreadsheet):
    init_bulk_selection()          # 1. en tout début de fonctiondef search_display(connection, spreadsheet):
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
            st.session_state.df = load_data(connection, spreadsheet)
            st.session_state.editing = None
            st.rerun()

    VERIF_LIST = {
        "0": "🔴 Notice non consultée",
        "1": "👤 Nom vérifié",
        "2": "✏️ Notice à revoir",
        "3": "✅ Notice terminée"
    }

    SEARCH_COLUMNS = [
        "xml:id",
        "wikidata",
        "surname",
        "forename",
        "birth_date",
        "birth_place",
        "death_date",
        "death_place",
        "type",
        "role",
        "commentaire",
        "validation"
    ]

    # -------------------------
    # FILTRES AVANCÉS
    # -------------------------

    with st.expander("⚙️ Filtres avancés"):

        empty_column = st.selectbox(
            "Afficher seulement les notices où cette colonne est vide",
            SEARCH_COLUMNS,
            placeholder="choix du filtre",
            index=None
        )


        validation_filter = st.selectbox(
            "Filtrer par validation",
            options=["Toutes"] + list(VERIF_LIST.keys()),
            format_func=lambda x: "Toutes" if x == "Toutes" else VERIF_LIST[x]
        )

        selected_columns = st.multiselect(
            "Colonnes de recherche",
            SEARCH_COLUMNS,
            default=SEARCH_COLUMNS
        )

    # Base
    filtered_df = df.copy()

    # Recherche texte
    if search and selected_columns:
        mask = filtered_df[selected_columns].fillna("").apply(
            lambda row: row.astype(str).str.contains(search, case=False, na=False).any(),
            axis=1
        )
        filtered_df = filtered_df[mask]

    # Surname absent
    if empty_column:
        filtered_df = filtered_df[
            filtered_df[empty_column].fillna("").astype(str).str.strip() == ""
        ]

    # Validation
    if validation_filter != "Toutes":
        filtered_df = filtered_df[
            filtered_df["validation"].fillna(0).astype(int).astype(str) == str(validation_filter)
        ]

    st.write(f"**{len(filtered_df)}** entrée(s)")
    st.divider()

    render_bulk_actions_top(connection, spreadsheet)  # ← en haut, instantané

    page_df, total_entries, total_pages, start, end = paginate_dataframe(filtered_df)
    render_pagination(total_entries, total_pages, start, end, "top")
    st.divider()

    for idx, row in page_df.iterrows():
        if st.session_state.editing == idx:
            render_entry_editor(idx, row, connection, spreadsheet)
        else:
            col_check, col_entry = st.columns([0.5, 11.5])
            with col_check:
                render_entry_checkbox(idx)
            with col_entry:
                render_entry_display(idx, row)

    render_pagination(total_entries, total_pages, start, end, "bottom")
