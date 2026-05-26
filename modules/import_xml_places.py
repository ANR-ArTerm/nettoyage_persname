import re
import xml.etree.ElementTree as ET

import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

SPREADSHEET = "https://docs.google.com/spreadsheets/d/10XWqZyB0ADl5Fxu-3H6BGFd2Bgualee9A_0ZAo2nE5c/edit?gid=0#gid=0"

REF_SHEETS = {
    "Rôles": "REF_roles",
    "Types de personnes": "REF_types",
    "PlaceName": "REF_placeName"
}

ns = {"tei": "http://www.tei-c.org/ns/1.0"}


def extract_places(uploaded_file):
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    rows = []

    for place in root.findall(".//tei:place", ns):
        xml_id = place.get("{http://www.w3.org/XML/1998/namespace}id")
        source = place.get("source", "")

        wikidata_id = None

        match = re.search(r"/(?:wiki|entity)/(Q\d+)", source)

        if match:
            wikidata_id = match.group(1)

        rows.append({
            "xml:id": xml_id,
            "wikidata_id": wikidata_id
        })

    return pd.DataFrame(rows)


def render_import_xml_places_page():
    st.title("Mise à jour des placename")

    st.write("Importer un fichier XML TEI contenant des balises <place>.")

    uploaded_file = st.file_uploader(
        "Choisir un fichier XML",
        type=["xml"]
    )

    if uploaded_file is not None:

        try:
            df = extract_places(uploaded_file)

            st.success(f"{len(df)} lieux extraits")

            st.dataframe(df, use_container_width=True)

            if st.button("Envoyer vers REF_placeName"):

                conn = st.connection("gsheets", type=GSheetsConnection)

                conn.update(
                    spreadsheet=SPREADSHEET,
                    worksheet=REF_SHEETS["PlaceName"],
                    data=df
                )

                st.success("REF_placeName mis à jour avec succès")

        except Exception as e:
            st.error(f"Erreur : {e}")