import streamlit as st
from modules.data_loader import load_ref_lists

def render_entry_editor(idx, row, conn, spreadsheet):
    with st.container():
        st.subheader(f"✏️ Édition — {row['surname'] or row['xml:id']}")

        xml_id = st.text_input("xml:id", value=row["xml:id"], key=f"xml_{idx}")
        wikidata = st.text_input("Wikidata", value=row["wikidata"], key=f"wd_{idx}")
        
        c1, c2 = st.columns(2)

        with c1:
            surname = st.text_input("Nom complet ou nom de famille", value=row["surname"], key=f"surname_{idx}")
            birth_date = st.text_input("Date naissance", value=row["birth_date"], key=f"bd_{idx}")
            death_date = st.text_input("Date décès", value=row["death_date"], key=f"dd_{idx}")
            role_list = [""] + st.session_state.ref_lists["roles"]
            role = st.selectbox(
                "Rôle",
                options=role_list,
                index=role_list.index(row["role"]) if row["role"] in role_list else 0,
                key=f"role_{idx}"
            )

        with c2:
            forename = st.text_input("Prénom", value=row["forename"], key=f"forname_{idx}")
            birth_place = st.text_input("Lieu naissance", value=row["birth_place"], key=f"bp_{idx}")
            death_place = st.text_input("Lieu décès", value=row["death_place"], key=f"dp_{idx}")

            types_list = [""] + st.session_state.ref_lists["types"]
            

            type_personne = st.selectbox(
                "Type",
                options=types_list,
                index=types_list.index(row["type"]) if row["type"] in types_list else 0,
                key=f"type_{idx}"
            )

        commentaire = st.text_area(
            "Commentaire",
            value=row["commentaire"],
            key=f"commentaire_{idx}"
        )

        VERIF_LIST = {
            "0": "🔴 Notice non consultée",
            "1": "👤 Nom vérifié",
            "2": "✏️ Notice à revoir",
            "3": "✅ Notice terminée"
        }
        
        verif = st.selectbox(
            "Vérification",
            options=list(VERIF_LIST.keys()),
            format_func=lambda x: VERIF_LIST[x],
            index=(
                list(VERIF_LIST.keys()).index(str(row["validation"]))
                if str(row["validation"]) in VERIF_LIST
                else 0
            ),
            key=f"verif_{idx}"
            )
        
        btn_save, btn_cancel = st.columns(2)

        with btn_save:
            if st.button("💾 Sauvegarder", key=f"save_{idx}", use_container_width=True):
                with st.spinner("Sauvegarde en cours"):
                    st.session_state.df.loc[idx] = [
                        xml_id, wikidata, surname, forename, birth_date, birth_place,
                        death_date, death_place, type_personne, role, commentaire, verif
                    ]
                    conn.update(spreadsheet=spreadsheet, data=st.session_state.df)
                    st.session_state.editing = None
                    st.cache_data.clear()
                    st.success("Entrée mise à jour")
                    st.rerun()

        with btn_cancel:
            if st.button("✖ Annuler", key=f"cancel_{idx}", use_container_width=True):
                st.session_state.editing = None
                st.rerun()
