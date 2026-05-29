import pandas as pd
import xml.etree.ElementTree as ET
import streamlit as st
from streamlit_gsheets import GSheetsConnection


SPREADSHEET = "https://docs.google.com/spreadsheets/d/10XWqZyB0ADl5Fxu-3H6BGFd2Bgualee9A_0ZAo2nE5c/edit?gid=0#gid=0"

REF_SHEETS = {
    "Rôles": "REF_roles",
    "Types de personnes": "REF_types",
    "PlaceName": "REF_placeName"
}

ns = {"tei": "http://www.tei-c.org/ns/1.0"}

# Colonnes officielles du tableur — ordre conservé
CATALOGUE_COLUMNS = [
    "xml:id", "wikidata", "name_alias", "surname", "forename",
    "birth_date", "birth_place", "death_date", "death_place",
    "type", "role", "commentaire", "validation", "compte"
]


# ======================================
# Utilitaires
# ======================================

def is_empty(value):
    return pd.isna(value) or str(value).strip() == ""


# ======================================
# Extraction générique TEI
# ======================================

def extract_tei_entities(uploaded_file, tag_name):

    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    rows = []
    xpath = f".//tei:{tag_name}"

    for element in root.findall(xpath, ns):

        xml_id = element.get(
            "{http://www.w3.org/XML/1998/namespace}id"
        )

        source = element.get("source", "").strip()
        role = element.get("role", "").strip()

        # Extraction forename et surname depuis persName
        # (uniquement forename et surname, pas addName)
        forename = ""
        surname = ""

        pers_name = element.find("tei:persName", ns)
        if pers_name is not None:
            forename_el = pers_name.find("tei:forename", ns)
            surname_el  = pers_name.find("tei:surname", ns)
            if forename_el is not None and forename_el.text:
                forename = forename_el.text.strip()
            if surname_el is not None and surname_el.text:
                surname = surname_el.text.strip()

        # Si forename == surname : on garde seulement surname, forename vide
        if forename and surname and forename == surname:
            forename = ""

        rows.append({
            "xml:id": xml_id,
            "wikidata": source,
            "role": role,
            "forename": forename,
            "surname": surname,
        })

    return pd.DataFrame(rows)


# ======================================
# Merge sans écraser les champs existants
# ======================================

def merge_new_and_fill_empty_roles(existing_df, new_df):

    existing_df = existing_df.copy()
    new_df = new_df.copy()

    # Garantir que toutes les colonnes du tableur existent dans les deux df
    for col in CATALOGUE_COLUMNS:
        if col not in existing_df.columns:
            existing_df[col] = ""
        if col not in new_df.columns:
            new_df[col] = ""

    # Réduire new_df aux seules colonnes du tableur (ignorer colonnes XML inconnues)
    new_df = new_df[[c for c in CATALOGUE_COLUMNS if c in new_df.columns]]

    existing_ids = set(
        existing_df["xml:id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df_to_add = new_df[
        ~new_df["xml:id"]
        .fillna("")
        .astype(str)
        .str.strip()
        .isin(existing_ids)
    ].copy()

    merged_df = pd.concat(
        [existing_df, df_to_add],
        ignore_index=True
    )

    # S'assurer que l'ordre des colonnes est respecté après concat
    for col in CATALOGUE_COLUMNS:
        if col not in merged_df.columns:
            merged_df[col] = ""
    merged_df = merged_df[CATALOGUE_COLUMNS]

    # Construire un index xml:id → valeur depuis le XML
    def build_field_index(field):
        return (
            new_df[
                new_df["xml:id"].notna()
                & new_df[field].notna()
                & (new_df[field].astype(str).str.strip() != "")
            ]
            .assign(
                **{
                    "xml:id": lambda df: df["xml:id"].astype(str).str.strip(),
                    field: lambda df: df[field].astype(str).str.strip(),
                }
            )
            .drop_duplicates(subset=["xml:id"], keep="first")
            .set_index("xml:id")[field]
            .to_dict()
        )

    roles_by_id     = build_field_index("role")
    forenames_by_id = build_field_index("forename")
    surnames_by_id  = build_field_index("surname")

    filled_roles = 0
    filled_names = 0

    for index, row in merged_df.iterrows():

        # Ligne verrouillée si validation == 3
        try:
            if float(row.get("validation", 0) or 0) == 3.0:
                continue
        except (ValueError, TypeError):
            pass

        xml_id = str(row.get("xml:id", "") or "").strip()

        # Rôle : remplir seulement si vide
        if is_empty(row.get("role")) and roles_by_id.get(xml_id):
            merged_df.at[index, "role"] = roles_by_id[xml_id]
            filled_roles += 1

        # Noms : on ne touche que si surname ET forename sont tous les deux vides
        if is_empty(row.get("surname")) and is_empty(row.get("forename")):
            new_surname  = surnames_by_id.get(xml_id, "")
            new_forename = forenames_by_id.get(xml_id, "")
            if new_surname or new_forename:
                merged_df.at[index, "surname"]  = new_surname
                merged_df.at[index, "forename"] = new_forename
                filled_names += 1

    return merged_df, len(df_to_add), df_to_add, filled_roles, filled_names


# ======================================
# IMPORT PERSONNES
# ======================================

def render_import_xml_persons_page():

    st.title("Mise à jour des personnes")

    st.write(
        "Importer un fichier XML TEI contenant des balises <person>."
    )

    uploaded_file = st.file_uploader(
        "Choisir un fichier XML",
        type=["xml"],
        key="person_xml"
    )

    if uploaded_file is not None:

        try:

            new_df = extract_tei_entities(
                uploaded_file,
                "person"
            )

            conn = st.connection(
                "gsheets",
                type=GSheetsConnection
            )

            existing_df = conn.read(
                spreadsheet=SPREADSHEET,
                worksheet="catalogue",
                ttl=0
            )

            merged_df, added_count, df_to_add, filled_roles, filled_names = (
                merge_new_and_fill_empty_roles(
                    existing_df,
                    new_df
                )
            )

            st.success(
                f"{added_count} nouvelles personnes détectées — "
                f"{filled_roles} rôles et "
                f"{filled_names} paires nom/prénom à compléter"
            )

            if added_count > 0:
                st.subheader("Nouvelles personnes")
                st.dataframe(
                    df_to_add,
                    use_container_width=True
                )

            if st.button("Mettre à jour catalogue"):

                conn.update(
                    spreadsheet=SPREADSHEET,
                    worksheet="catalogue",
                    data=merged_df
                )

                st.success(
                    f"{added_count} nouvelles personnes ajoutées — "
                    f"{filled_roles} rôles et "
                    f"{filled_names} paires nom/prénom complétées"
                )

        except Exception as e:
            st.error(f"Erreur : {e}")


# ======================================
# IMPORT LIEUX
# ======================================

def render_import_xml_places_page():

    st.title("Mise à jour des placename")

    st.write(
        "Importer un fichier XML TEI contenant des balises <place>."
    )

    uploaded_file = st.file_uploader(
        "Choisir un fichier XML",
        type=["xml"],
        key="place_xml"
    )

    if uploaded_file is not None:

        try:

            df = extract_tei_entities(
                uploaded_file,
                "place"
            )

            st.success(
                f"{len(df)} lieux extraits"
            )

            st.dataframe(
                df,
                use_container_width=True
            )

            if st.button("Envoyer vers REF_placeName"):

                conn = st.connection(
                    "gsheets",
                    type=GSheetsConnection
                )

                conn.update(
                    spreadsheet=SPREADSHEET,
                    worksheet=REF_SHEETS["PlaceName"],
                    data=df
                )

                st.success(
                    "REF_placeName mis à jour avec succès"
                )

        except Exception as e:
            st.error(f"Erreur : {e}")