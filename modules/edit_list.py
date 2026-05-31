# pages/listes_reference.py
import streamlit as st
import pandas as pd
from modules.data_loader import load_data  # optionnel si besoin

def render_ref_editor(conn, spreadsheet, ref_sheets):
    """
    conn        : st.connection GSheets
    spreadsheet : URL du spreadsheet
    ref_sheets  : dict {"label affiché": "nom_onglet"}, ex: {"Rôles": "REF_roles"}
    """
    selected_label = st.selectbox("Liste à éditer", list(ref_sheets.keys()))
    selected_sheet = ref_sheets[selected_label]

    @st.cache_data
    def load_ref(_conn, spreadsheet, worksheet):
        df = _conn.read(spreadsheet=spreadsheet, worksheet=worksheet, usecols=[0], ttl=5)
        return df.dropna(how="all").reset_index(drop=True)

    df_ref = load_ref(conn, spreadsheet, selected_sheet)
    col_name = df_ref.columns[0]

    st.divider()
    st.subheader(f"Valeurs — {selected_label}")

    state_key = f"ref_edit_{selected_sheet}"
    if state_key not in st.session_state or st.session_state.get("ref_sheet_loaded") != selected_sheet:
        st.session_state[state_key] = df_ref[col_name].tolist()
        st.session_state["ref_sheet_loaded"] = selected_sheet

    items = st.session_state[state_key]

    to_delete = None
    for i, val in enumerate(items):
        c1, c2 = st.columns([5, 1])
        with c1:
            items[i] = st.text_input(f"Valeur {i+1}", value=val, key=f"ref_item_{selected_sheet}_{i}", label_visibility="collapsed")
        with c2:
            if st.button("🗑️", key=f"del_{selected_sheet}_{i}"):
                to_delete = i

    if to_delete is not None:
        items.pop(to_delete)
        st.rerun()

    st.divider()
    new_item = st.text_input("➕ Nouvelle valeur", key=f"new_item_{selected_sheet}")
    if st.button("Ajouter", width='stretch') and new_item.strip():
        items.append(new_item.strip())
        st.rerun()

    st.divider()
    if st.button("💾 Sauvegarder", type="primary", width='stretch'):
        updated_df = pd.DataFrame({col_name: items})
        conn.update(spreadsheet=spreadsheet, worksheet=selected_sheet, data=updated_df)
        st.cache_data.clear()
        if "ref_lists" in st.session_state:
            key = selected_sheet.replace("REF_", "").lower() + "s"
            st.session_state.ref_lists[key] = items
        st.success(f"✅ {selected_label} mis à jour ({len(items)} valeurs)")
        st.rerun()