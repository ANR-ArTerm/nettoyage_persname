import streamlit as st
from modules.list_and_dics import VERIF_LIST
from modules.validation import normalize_validation

def render_entry_display(idx, row):
    with st.container(border=True):

        # En-tête
        c_title, c_status = st.columns([2, 1])
        with c_title:
            st.markdown(f"#### `{row['xml:id']}` — compte : {row['compte']}")
            st.caption(f"Wikidata : {row['wikidata'] or '—'}")
        with c_status:
            validation = normalize_validation(row.get("validation", "0"))
            st.markdown(VERIF_LIST.get(validation, "🔴 Notice non consultée"))

        st.divider()

        # Corps
        c_main, c_dates, c_meta, c_btn = st.columns([3, 2, 2, 1])

        with c_main:
            st.caption("Identité")
            if row.get("name_alias"):
                st.markdown(f"Surnom : **{row['name_alias']}**")
            if row["surname"]:
                st.markdown(f"Nom : **{row['surname']}**")
            else:
                st.error("Sans nom")
            if row["forename"]:
                st.markdown(f"Prénom : **{row['forename']}**")

        with c_dates:
            st.caption("Naissance")
            st.markdown(f"Date : {row['birth_date'] or '—'}")
            st.markdown(f"Lieu : {row['birth_place'] or '—'}")

            st.caption("Décès")
            st.markdown(f"Date : {row['death_date'] or '—'}")
            st.markdown(f"Lieu : {row['death_place'] or '—'}")

        with c_meta:
            st.caption("Type & rôle")
            st.markdown(f"**{row['type'] or '—'}**")
            st.caption(row["role"] or "—")

        with c_btn:
            if st.button("✏️ Éditer", key=f"edit_{idx}"):
                st.session_state.editing = idx
                st.rerun()        
