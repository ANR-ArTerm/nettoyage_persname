# modules/bulk_actions.py
import streamlit as st

from modules.list_and_dics import VERIF_LIST
from modules.validation import normalize_validation

def init_bulk_selection():
    """À appeler au début de search_display."""
    if "selected_entries" not in st.session_state:
        st.session_state.selected_entries = set()

def _toggle_entry(idx):
    key = f"select_{idx}"
    if st.session_state[key]:
        st.session_state.selected_entries.add(idx)
    else:
        st.session_state.selected_entries.discard(idx)

def render_entry_checkbox(idx):
    st.checkbox(
        f"Sélectionner la notice {idx}",
        value=idx in st.session_state.selected_entries,
        key=f"select_{idx}",
        label_visibility="collapsed",
        on_change=_toggle_entry,
        args=(idx,)
    )

def render_bulk_actions_top(connection, spreadsheet):
    """Panneau affiché EN HAUT — lit session_state déjà mis à jour par le re-run précédent."""
    if not st.session_state.selected_entries:
        return

    with st.container(border=True):
        st.markdown(f"**{len(st.session_state.selected_entries)} notice(s) sélectionnée(s)**")

        col_types, col_verif = st.columns(2)

        with col_types:
            types_list = st.session_state.ref_lists["types"]
            bulk_types = st.multiselect(
                "Appliquer ces types aux notices sélectionnées",
                options=types_list,
                key="bulk_types"
            )

        with col_verif:
            bulk_verif = st.selectbox(
                "Appliquer un statut de vérification",
                options=[None] + list(VERIF_LIST.keys()),
                format_func=lambda x: "— Aucun changement —" if x is None else VERIF_LIST[x],
                key="bulk_verif"
            )

        col_apply, col_clear = st.columns(2)

        with col_apply:
            apply_disabled = not bulk_types and bulk_verif is None
            if st.button("✅ Appliquer", use_container_width=True, disabled=apply_disabled):
                with st.spinner("Sauvegarde en cours..."):
                    for idx in st.session_state.selected_entries:
                        if bulk_types:
                            st.session_state.df.at[idx, "type"] = ",".join(bulk_types)
                        if bulk_verif is not None:
                            st.session_state.df.at[idx, "verif"] = normalize_validation(bulk_verif)
                    connection.update(spreadsheet=spreadsheet, data=st.session_state.df)
                    st.cache_data.clear()
                    for idx in st.session_state.selected_entries:
                        key = f"select_{idx}"
                        if key in st.session_state:
                            st.session_state[key] = False
                    st.session_state.selected_entries = set()
                    st.success("Modifications appliquées")
                    st.rerun()

        with col_clear:
            if st.button("✖ Désélectionner tout", use_container_width=True):
                for idx in st.session_state.selected_entries:
                    key = f"select_{idx}"
                    if key in st.session_state:
                        st.session_state[key] = False
                st.session_state.selected_entries = set()
                st.rerun()

    st.divider()
