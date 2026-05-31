import streamlit as st
from modules.data_loader import load_ref_lists
from modules.list_and_dics import VERIF_LIST
from modules.validation import normalize_validation

def render_entry_editor(idx, row, conn, spreadsheet):
    with st.container():
        st.subheader(f"✏️ Édition — {row['xml:id']}")
        st.markdown("##### Informations principales")
        xml_id = st.text_input("xml:id", value=row["xml:id"], key=f"xml_{idx}")
        wikidata = st.text_input("Wikidata", value=row["wikidata"], key=f"wd_{idx}")

        # TYPES
        types_list = st.session_state.ref_lists["types"]
        # Le CSV stocke plusieurs valeurs séparées par une virgule, ex: "prêtre,évêque"
        current_types = [t.strip() for t in str(row["type"]).split(",") if t.strip() in types_list]

        type_personne = st.multiselect(
            "Type",
            options=types_list,
            default=current_types,
            key=f"type_{idx}"
        )

        st.markdown("##### Nom")
        name_alias = st.text_input("Surnom ou nom d'usage", value=row["name_alias"], key=f"name_alias_{idx}")


        c_name_1, c_name_2 = st.columns(2)


        with c_name_1:
            surname = st.text_input("Nom complet ou nom de famille", value=row["surname"], key=f"surname_{idx}")
        with c_name_2:
            forename = st.text_input("Prénom", value=row["forename"], key=f"forname_{idx}")

        c_date_1, c_date_2 = st.columns(2)
        
        with c_date_1:
            birth_date = st.text_input("Date naissance", value=row["birth_date"], key=f"bd_{idx}")
            death_date = st.text_input("Date décès", value=row["death_date"], key=f"dd_{idx}")

        with c_date_2:
            birth_place = st.text_input("Lieu naissance", value=row["birth_place"], key=f"bp_{idx}")
            death_place = st.text_input("Lieu décès", value=row["death_place"], key=f"dp_{idx}")

        role = st.text_area("Role (texte libre)", value=row["role"], key=f"role_{idx}")

        commentaire = st.text_area(
            "Commentaire (caché sur le site, seulement pour nous)",
            value=row["commentaire"],
            key=f"commentaire_{idx}"
        )

        validation = normalize_validation(row["validation"])
        
        verif = st.selectbox(
            "Vérification",
            options=list(VERIF_LIST.keys()),
            format_func=lambda x: VERIF_LIST[x],
            index=list(VERIF_LIST.keys()).index(validation),
            key=f"verif_{idx}"
            )
        
        btn_save, btn_cancel = st.columns(2)

        with btn_save:
            if st.button("💾 Sauvegarder", key=f"save_{idx}", width='stretch'):
                with st.spinner("Sauvegarde en cours"):
                    st.session_state.df.loc[idx, "xml:id"]      = xml_id
                    st.session_state.df.loc[idx, "wikidata"]    = wikidata
                    st.session_state.df.loc[idx, "name_alias"]  = name_alias
                    st.session_state.df.loc[idx, "surname"]     = surname
                    st.session_state.df.loc[idx, "forename"]    = forename
                    st.session_state.df.loc[idx, "birth_date"]  = birth_date
                    st.session_state.df.loc[idx, "birth_place"] = birth_place
                    st.session_state.df.loc[idx, "death_date"]  = death_date
                    st.session_state.df.loc[idx, "death_place"] = death_place
                    st.session_state.df.loc[idx, "type"]        = ",".join(type_personne)
                    st.session_state.df.loc[idx, "role"]        = role
                    st.session_state.df.loc[idx, "commentaire"] = commentaire
                    st.session_state.df.loc[idx, "validation"]  = verif
                    st.session_state.df.loc[idx, "compte"] = row["compte"]
                    
                    conn.update(spreadsheet=spreadsheet, data=st.session_state.df)
                    st.session_state.editing = None
                    st.cache_data.clear()
                    st.success("Entrée mise à jour")
                    st.rerun()


        with btn_cancel:
            if st.button("✖ Annuler", key=f"cancel_{idx}", width='stretch'):
                st.session_state.editing = None
                st.rerun()
