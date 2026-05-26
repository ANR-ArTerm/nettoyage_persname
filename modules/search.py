import streamlit as st
from modules.data_loader import load_data
from modules.entry_display import render_entry_display
from modules.entry_editor import render_entry_editor
from modules.pagination import paginate_dataframe, render_pagination


def search_display(connection, spreadsheet):
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
            render_entry_editor(idx, row, connection, spreadsheet)
        else:
            render_entry_display(idx, row)

    render_pagination(total_entries, total_pages, start, end, "bottom")
