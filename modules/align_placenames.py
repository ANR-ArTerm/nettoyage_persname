import re

import pandas as pd
import streamlit as st


CATALOGUE_SHEET = "catalogue"
PLACE_REF_SHEET = "REF_placeName"
PLACE_COLUMNS = ["birth_place", "death_place"]


def normalize_cell(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_qid(value):
    value = normalize_cell(value)
    if not value:
        return ""

    if "/" in value:
        value = value.rstrip("/").rsplit("/", 1)[-1]

    return value if re.fullmatch(r"Q\d+", value) else ""


def load_place_reference(conn, spreadsheet, worksheet=PLACE_REF_SHEET):
    ref_df = conn.read(
        spreadsheet=spreadsheet,
        worksheet=worksheet,
        ttl=0,
    ).fillna("")

    ref_df.columns = [str(col).strip() for col in ref_df.columns]

    required = {"xml:id", "wikidata_id"}
    missing = required - set(ref_df.columns)
    if missing:
        raise ValueError(
            f"La feuille {worksheet} doit contenir les colonnes : {', '.join(sorted(required))}."
        )

    qid_to_xml_id = {}

    for _, row in ref_df.iterrows():
        xml_id = normalize_cell(row["xml:id"])
        qid = normalize_qid(row["wikidata_id"])

        if xml_id and qid:
            qid_to_xml_id[qid] = xml_id

    return qid_to_xml_id, ref_df


def find_place_qid_replacements(catalogue_df, qid_to_xml_id):
    catalogue_df = catalogue_df.copy().fillna("")
    catalogue_df.columns = [str(col).strip() for col in catalogue_df.columns]

    missing_columns = [col for col in PLACE_COLUMNS if col not in catalogue_df.columns]
    if missing_columns:
        raise ValueError(
            "Colonnes absentes du catalogue : " + ", ".join(missing_columns)
        )

    replacements = []
    unknown_qids = {}

    for idx, row in catalogue_df.iterrows():
        person_id = normalize_cell(row.get("xml:id", ""))

        for col in PLACE_COLUMNS:
            current_value = normalize_cell(row[col])
            qid = normalize_qid(current_value)

            if not qid:
                continue

            if qid in qid_to_xml_id:
                replacements.append(
                    {
                        "index": idx,
                        "xml:id personne": person_id,
                        "colonne": col,
                        "ancien": qid,
                        "nouveau": qid_to_xml_id[qid],
                    }
                )
            else:
                unknown_qids[qid] = unknown_qids.get(qid, 0) + 1

    return replacements, unknown_qids


def apply_place_qid_replacements(catalogue_df, replacements):
    updated_df = catalogue_df.copy().fillna("")

    for replacement in replacements:
        updated_df.at[replacement["index"], replacement["colonne"]] = replacement["nouveau"]

    return updated_df


def summarize_replacements(replacements):
    summary = {}

    for replacement in replacements:
        key = (replacement["ancien"], replacement["nouveau"])
        summary[key] = summary.get(key, 0) + 1

    rows = [
        {
            "remplacement": f"{old} -> {new}",
            "ancien": old,
            "nouveau": new,
            "occurrences": count,
        }
        for (old, new), count in sorted(summary.items(), key=lambda item: item[0])
    ]

    return pd.DataFrame(rows)


def render_replace_place_qids(conn, spreadsheet):
    st.subheader("Remplacer les QID de lieux par les xml:id")

    st.write(
        "Ce module regarde `REF_placeName`, puis remplace dans `catalogue` "
        "les valeurs `birth_place` et `death_place` qui sont encore sous forme `Q####`."
    )

    if st.button("Chercher les lieux remplaçables", width='stretch'):
        try:
            catalogue_df = conn.read(
                spreadsheet=spreadsheet,
                worksheet=CATALOGUE_SHEET,
                ttl=0,
            ).fillna("")

            qid_to_xml_id, ref_df = load_place_reference(conn, spreadsheet)
            replacements, unknown_qids = find_place_qid_replacements(
                catalogue_df,
                qid_to_xml_id,
            )

            st.session_state.place_qid_catalogue_df = catalogue_df
            st.session_state.place_qid_replacements = replacements
            st.session_state.place_qid_unknown_qids = unknown_qids

        except Exception as e:
            st.error(f"Recherche impossible : {e}")
            return

    replacements = st.session_state.get("place_qid_replacements")
    unknown_qids = st.session_state.get("place_qid_unknown_qids", {})

    if replacements is None:
        return

    if not replacements:
        st.success("Aucun QID remplaçable trouvé dans `birth_place` ou `death_place`.")
    else:
        summary_df = summarize_replacements(replacements)

        st.info(
            f"{len(replacements)} cellule(s) seront remplacée(s), "
            f"pour {len(summary_df)} lieu(x) distinct(s)."
        )

        st.markdown("**Remplacements proposés**")
        st.dataframe(summary_df, width='stretch', hide_index=True)

        with st.expander("Voir les lignes concernées"):
            st.dataframe(
                pd.DataFrame(replacements).drop(columns=["index"]),
                width='stretch',
                hide_index=True,
            )

    if unknown_qids:
        unknown_df = pd.DataFrame(
            [
                {"qid": qid, "occurrences": count}
                for qid, count in unknown_qids.items()
            ]
        ).sort_values(
            by=["occurrences", "qid"],
            ascending=[False, True],
        )


        with st.expander("QID trouvés mais absents de REF_placeName"):
            st.dataframe(unknown_df, width='stretch', hide_index=True)

    if not replacements:
        return

    confirm = st.checkbox(
        "Je confirme vouloir remplacer ces QID dans le catalogue."
    )

    if st.button("Valider les remplacements", type="primary", disabled=not confirm):
        catalogue_df = st.session_state.place_qid_catalogue_df
        updated_df = apply_place_qid_replacements(catalogue_df, replacements)

        with st.spinner("Mise à jour de la feuille catalogue..."):
            conn.update(
                spreadsheet=spreadsheet,
                worksheet=CATALOGUE_SHEET,
                data=updated_df,
            )

        st.cache_data.clear()
        st.session_state.df = updated_df
        st.session_state.editing = None
        st.session_state.place_qid_replacements = None

        st.success(f"{len(replacements)} remplacement(s) appliqué(s).")
        st.rerun()