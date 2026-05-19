import streamlit as st


def render_entry_display(idx, row):
    with st.container(border=True):
        st.markdown(f"#### XML:ID : **{row['xml:id']}**")

        c_main, c_dates, c_meta, c_btn = st.columns([3, 2, 2, 1])

        with c_main:
            if row['name']:
                st.markdown(f"Nom complet : **{row['name']}**")
            else:
                st.error("Sans nom")

        with c_dates:
            if row["birth_date"] or row["birth_place"]:
                st.markdown(f"° {row['birth_date']} {row['birth_place']}".strip())
            if row["death_date"] or row["death_place"]:
                st.markdown(f"† {row['death_date']} {row['death_place']}".strip())

        with c_meta:
            st.markdown(f"**{row['type'] or '—'}**")
            st.markdown(f"{row['role'] or '—'}")

        with c_btn:
            if st.button("✏️ Éditer", key=f"edit_{idx}"):
                st.session_state.editing = idx
                st.rerun()
