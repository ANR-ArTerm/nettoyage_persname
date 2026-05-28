import math

import streamlit as st

def paginate_dataframe(df, page_size=25):
    total_entries = len(df)
    total_pages = max(1, math.ceil(total_entries / page_size))

    if "page" not in st.session_state:
        st.session_state.page = 1

    st.session_state.page = min(max(st.session_state.page, 1), total_pages)

    start = (st.session_state.page - 1) * page_size
    end = start + page_size

    return df.iloc[start:end], total_entries, total_pages, start, end


def render_pagination(total_entries, total_pages, start, end, key_prefix):
    current_page = st.session_state.page
    shown_start = start + 1 if total_entries else 0
    shown_end = min(end, total_entries)

    col_first, col_prev, col_info, col_next, col_last = st.columns([1, 1, 2, 1, 1])

    with col_first:
        if st.button(
            "⏮ Première",
            disabled=current_page <= 1,
            key=f"{key_prefix}_first",
            use_container_width=True,
        ):
            st.session_state.page = 1
            st.session_state.editing = None
            st.rerun()

    with col_prev:
        if st.button(
            "← Précédent",
            disabled=current_page <= 1,
            key=f"{key_prefix}_prev",
            use_container_width=True,
        ):
            st.session_state.page -= 1
            st.session_state.editing = None
            st.rerun()

    with col_info:
        st.markdown(
            f"<div style='text-align:center'>"
            f"Page {current_page} / {total_pages} · "
            f"{shown_start}-{shown_end} sur {total_entries}"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_next:
        if st.button(
            "Suivant →",
            disabled=current_page >= total_pages,
            key=f"{key_prefix}_next",
            use_container_width=True,
        ):
            st.session_state.page += 1
            st.session_state.editing = None
            st.rerun()

    with col_last:
        if st.button(
            "Dernière ⏭",
            disabled=current_page >= total_pages,
            key=f"{key_prefix}_last",
            use_container_width=True,
        ):
            st.session_state.page = total_pages
            st.session_state.editing = None
            st.rerun()
