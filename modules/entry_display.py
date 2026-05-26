import streamlit as st


VERIF_LIST = {
    "0": "🔴 Notice non consultée",
    "1": "👤 Nom vérifié",
    "2": "✏️ Notice à revoir",
    "3": "✅ Notice terminée"
}

def render_entry_display(idx, row):
    with st.container(border=True):
        c_title, c_status = st.columns([2,1])
        with c_title:
            st.markdown(f"#### XML:ID : **{row['xml:id']}**")

        with c_status:
            validation = str(row.get("validation", "0"))
            st.markdown(
                VERIF_LIST.get(validation, "🔴 Notice non consultée")
            )

        c_main, c_dates, c_meta, c_btn = st.columns([3, 2, 2, 1])

        with c_main:
            if row['surname']:
                st.markdown(f"Nom complet : **{row['surname']}**")
            else:
                st.error("Sans nom")
            if row['forename']:
                st.markdown(f"Nom complet : **{row['forename']}**")

        with c_dates:
            if row["birth_date"] or row["birth_place"]:
                st.markdown(f"Date de naissance : {row['birth_date']} {row['birth_place']}".strip())

            if row["death_date"] or row["death_place"]:
                st.markdown(f"Date de mort : {row['death_date']} {row['death_place']}".strip())

        with c_meta:
            st.markdown(f"**{row['type'] or '—'}**")
            st.markdown(f"{row['role'] or '—'}")

        with c_btn:
            if st.button("✏️ Éditer", key=f"edit_{idx}"):
                st.session_state.editing = idx
                st.rerun()
        
