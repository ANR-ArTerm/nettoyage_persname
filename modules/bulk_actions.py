# modules/bulk_actions.py
import streamlit as st

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
        "",
        value=idx in st.session_state.selected_entries,
        key=f"select_{idx}",
        on_change=_toggle_entry,
        args=(idx,)
    )

def render_bulk_actions_top(connection, spreadsheet):
    """Panneau affiché EN HAUT — lit session_state déjà mis à jour par le re-run précédent."""
    if not st.session_state.selected_entries:
        return

    with st.container(border=True):
        st.markdown(f"**{len(st.session_state.selected_entries)} notice(s) sélectionnée(s)**")

        types_list = st.session_state.ref_lists["types"]
        bulk_types = st.multiselect(
            "Appliquer ces types aux notices sélectionnées",
            options=types_list,
            key="bulk_types"
        )

        col_apply, col_clear = st.columns(2)

        with col_apply:
            if st.button("✅ Appliquer", use_container_width=True, disabled=not bulk_types):
                with st.spinner("Sauvegarde en cours..."):
                    for idx in st.session_state.selected_entries:
                        st.session_state.df.at[idx, "type"] = ",".join(bulk_types)
                    connection.update(spreadsheet=spreadsheet, data=st.session_state.df)
                    st.cache_data.clear()
                    # Réinitialiser les checkboxes AVANT de vider le set
                    for idx in st.session_state.selected_entries:
                        key = f"select_{idx}"
                        if key in st.session_state:
                            st.session_state[key] = False
                    st.session_state.selected_entries = set()
                    st.success("Types mis à jour")
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