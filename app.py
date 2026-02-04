import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuration - Added placeholders to the dictionary
SHEETS_DICT = {
    "Operasi Di Laluan": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Bas Tamat Operasi - RPG": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils",
    "Peraturan Memperlahankan Pemanduan": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "PENGENDALIAN KEROSAKAN": None,
    "PENGOPERASIAN MESIN C360": None
}

st.set_page_config(page_title="Depoh Summary Dashboard", layout="wide")

@st.cache_data(ttl=600)
def load_all_data():
    all_dfs = {}
    for name, sheet_id in SHEETS_DICT.items():
        if sheet_id is None:
            # Create an empty dataframe for the placeholder modules
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
            continue
            
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            temp_df = pd.read_csv(url)
            temp_df.columns = [str(c).lower().strip() for c in temp_df.columns]
            
            if 'id pekerja' in temp_df.columns and 'total score' in temp_df.columns:
                temp_df['score_num'] = temp_df['total score'].astype(str).str.split('/').str[0].astype(float)
                # Keep first attempt for summary
                all_dfs[name] = temp_df.sort_values('timestamp').groupby('id pekerja').first().reset_index()
        except Exception:
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
    return all_dfs

data_map = load_all_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🧭 Navigation")
page_mode = st.sidebar.radio("Go to:", ["Main Summary", "Detailed Sheet View"])

if page_mode == "Main Summary":
    st.title("📋 Master SOP Summary Dashboard")
    
    if data_map:
        # Build Base Staff List
        valid_dfs = [df for name, df in data_map.items() if not df.empty]
        if valid_dfs:
            all_staff = pd.concat([df[['id pekerja', 'nama penuh', 'depoh']] for df in valid_dfs]).drop_duplicates('id pekerja')
        else:
            all_staff = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh'])
            
        summary_table = all_staff.copy()
        
        # Merge scores
        for sheet_name in SHEETS_DICT.keys():
            df = data_map.get(sheet_name, pd.DataFrame(columns=['id pekerja', 'score_num']))
            score_subset = df[['id pekerja', 'score_num']].rename(columns={'score_num': sheet_name})
            summary_table = pd.merge(summary_table, score_subset, on='id pekerja', how='left')
        
        # Fill missing with 0
        summary_table = summary_table.fillna(0)
        
        # Calculations
        score_cols = list(SHEETS_DICT.keys())
        max_possible = len(score_cols) * 5
        summary_table['Total Pre-Score'] = summary_table[score_cols].sum(axis=1)
        summary_table['% LULUS PRE'] = (summary_table['Total Pre-Score'] / max_possible) * 100
        summary_table['% LULUS POST'] = 0 # Placeholder

        st.subheader("SKOR PRA PENILAIAN KENDIRI FC 2025 (PRE)")
        st.dataframe(
            summary_table.rename(columns={'id pekerja': 'ID', 'nama penuh': 'NAMA', 'depoh': 'DEPOH'})
            .style.format({"% LULUS PRE": "{:.0f}%"}), 
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Please connect your data sources.")

else:
    # --- DETAILED SHEET VIEW ---
    selection = st.sidebar.selectbox("Select Detailed Sheet:", list(SHEETS_DICT.keys()))
    st.title(f"📊 Detailed Analysis: {selection}")
    
    selected_df = data_map.get(selection, pd.DataFrame())
    
    if selected_df.empty:
        st.warning(f"No data available for {selection} yet. This module is currently empty.")
        # Show an empty template so the user sees the expected structure
        st.dataframe(pd.DataFrame(columns=['ID', 'NAMA', 'DEPOH', 'SCORE']), use_container_width=True)
    else:
        col1, col2 = st.columns([1, 2])
        with col1:
            depoh_stats = selected_df.groupby('depoh')['id pekerja'].nunique().reset_index()
            st.metric("Unique Staff", depoh_stats['id pekerja'].sum())
            st.dataframe(depoh_stats, hide_index=True)
        with col2:
            fig = px.pie(depoh_stats, values='id pekerja', names='depoh', hole=0.7)
            fig.update_layout(height=300, margin=dict(t=20, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        st.subheader("Raw Data Preview")
        st.dataframe(selected_df, use_container_width=True)
