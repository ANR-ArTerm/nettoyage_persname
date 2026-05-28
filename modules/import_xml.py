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

        rows.append({
            "xml:id": xml_id,
            "wikidata": source,
            "role": role
        })

    return pd.DataFrame(rows)



# ======================================
# Merge sans écraser
# ======================================

def merge_new_and_fill_empty_roles(existing_df, new_df):

    existing_df = existing_df.copy()
    new_df = new_df.copy()

    if "role" not in existing_df.columns:
        existing_df["role"] = ""

    existing_ids = set(existing_df["xml:id"].astype(str))

    df_to_add = new_df[
        ~new_df["xml:id"].astype(str).isin(existing_ids)
    ]

    merged_df = pd.concat(
        [existing_df, df_to_add],
        ignore_index=True
    )

    roles_by_id = (
        new_df.dropna(subset=["xml:id"])
        .set_index("xml:id")["role"]
        .astype(str)
        .to_dict()
    )

    filled_count = 0

    for index, row in merged_df.iterrows():
        current_role = str(row.get("role", "") or "").strip()
        xml_id = str(row.get("xml:id", "") or "").strip()
        xml_role = roles_by_id.get(xml_id, "").strip()

        if not current_role and xml_role:
            merged_df.at[index, "role"] = xml_role
            filled_count += 1

    return merged_df, len(df_to_add), df_to_add, filled_count


def merge_only_new(existing_df, new_df):

    existing_ids = set(
        existing_df["xml:id"].astype(str)
    )

    df_to_add = new_df[
        ~new_df["xml:id"].astype(str).isin(existing_ids)
    ]

    merged_df = pd.concat(
        [existing_df, df_to_add],
        ignore_index=True
    )

    return merged_df, len(df_to_add)


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

            merged_df, added_count, df_to_add, filled_count = merge_new_and_fill_empty_roles(
                existing_df,
                new_df
            )

            existing_ids = set(
                existing_df["xml:id"].astype(str)
            )

            df_to_add = new_df[
                ~new_df["xml:id"].astype(str).isin(existing_ids)
            ]

            st.success(
                f"{added_count} nouvelles personnes détectées"
            )

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
                    f"{added_count} nouvelles personnes détectées, "
                    f"{filled_count} rôles complétés"
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