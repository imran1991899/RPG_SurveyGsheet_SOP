import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuration
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
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
            continue
            
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        try:
            temp_df = pd.read_csv(url)
            temp_df.columns = [str(c).lower().strip() for c in temp_df.columns]
            
            if 'id pekerja' in temp_df.columns and 'total score' in temp_df.columns:
                temp_df['score_num'] = temp_df['total score'].astype(str).str.split('/').str[0].astype(float).round(1)
                
                date_col = 'timestamp' if 'timestamp' in temp_df.columns else 'date'
                if date_col in temp_df.columns:
                    temp_df['timestamp'] = pd.to_datetime(temp_df[date_col], errors='coerce')
                    temp_df = temp_df.dropna(subset=['timestamp'])
                
                all_dfs[name] = temp_df
        except Exception:
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
    return all_dfs

raw_data = load_all_data()

# --- SIDEBAR: DATE SELECTION & RESET ---
st.sidebar.title("📅 Filters")

all_dates = []
for df in raw_data.values():
    if not df.empty and 'timestamp' in df.columns:
        all_dates.extend(df['timestamp'].dt.date.tolist())

if all_dates:
    min_date, max_date = min(all_dates), max(all_dates)
    
    if st.sidebar.button("🔄 Reset Dates"):
        st.session_state.date_range = (min_date, max_date)
        st.rerun()

    if 'date_range' not in st.session_state:
        st.session_state.date_range = (min_date, max_date)

    selected_date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=st.session_state.date_range,
        min_value=min_date,
        max_value=max_date
    )
    st.session_state.date_range = selected_date_range
else:
    selected_date_range = None

filtered_data = {}
for name, df in raw_data.items():
    if not df.empty and 'timestamp' in df.columns and selected_date_range and len(selected_date_range) == 2:
        start, end = selected_date_range
        mask = (df['timestamp'].dt.date >= start) & (df['timestamp'].dt.date <= end)
        filtered_data[name] = df[mask]
    else:
        filtered_data[name] = df

# --- SIDEBAR: NAVIGATION ---
st.sidebar.divider()
st.sidebar.title("🧭 Navigation")
page_mode = st.sidebar.radio("Go to:", ["Main Summary", "Detailed Sheet View"])

if page_mode == "Main Summary":
    st.title("📋 Master SOP Summary Dashboard")
    
    summary_dfs_pre = {}
    summary_dfs_post = {}
    
    for name, df in filtered_data.items():
        if not df.empty:
            # PRE: Earliest entry
            summary_dfs_pre[name] = df.sort_values('timestamp').groupby('id pekerja').first().reset_index()
            # POST: Most recent entry
            summary_dfs_post[name] = df.sort_values('timestamp').groupby('id pekerja').last().reset_index()
        else:
            summary_dfs_pre[name] = df
            summary_dfs_post[name] = df

    valid_dfs = [df for df in summary_dfs_pre.values() if not df.empty]
    if valid_dfs:
        all_staff = pd.concat([df[['id pekerja', 'nama penuh', 'depoh']] for df in valid_dfs]).drop_duplicates('id pekerja')
        summary_table = all_staff.copy()
        
        score_cols = list(SHEETS_DICT.keys())
        for name in score_cols:
            pre_score = summary_dfs_pre.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))[['id pekerja', 'score_num']].rename(columns={'score_num': name})
            summary_table = pd.merge(summary_table, pre_score, on='id pekerja', how='left')
            
            post_score = summary_dfs_post.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))[['id pekerja', 'score_num']].rename(columns={'score_num': f'p_{name}'})
            summary_table = pd.merge(summary_table, post_score, on='id pekerja', how='left')
        
        summary_table = summary_table.fillna(0.0)
        
        # Calculations
        summary_table['Total Pre-Sc'] = summary_table[score_cols].sum(axis=1).round(1)
        summary_table['% LULUS PRE'] = ((summary_table['Total Pre-Sc'] / 25.0) * 100).round(1)
        
        p_cols = [f'p_{name}' for name in score_cols]
        # ADDED: Total Post-Sc column calculation
        summary_table['Total Post-Sc'] = summary_table[p_cols].sum(axis=1).round(1)
        summary_table['% LULUS POST'] = ((summary_table['Total Post-Sc'] / 25.0) * 100).round(1)

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Staff", len(summary_table))
        m2.metric("Avg Pre Score %", f"{summary_table['% LULUS PRE'].mean():.1f}%")
        m3.metric("Avg Post Score %", f"{summary_table['% LULUS POST'].mean():.1f}%")

        # Table Display
        st.subheader("SKOR PRA PENILAIAN KENDIRI FC 2025 (PRE vs POST)")
        formatted_df = summary_table.rename(columns={'id pekerja': 'ID', 'nama penuh': 'NAMA', 'depoh': 'DEPOH'})
        
        # Updated columns to include Total Post-Sc
        show_columns = ['ID', 'NAMA', 'DEPOH'] + score_cols + ['Total Pre-Sc', 'Total Post-Sc', '% LULUS PRE', '% LULUS POST']
        
        st.dataframe(
            formatted_df[show_columns].style.format({col: "{:.1f}" for col in score_cols + ['Total Pre-Sc', 'Total Post-Sc', '% LULUS PRE', '% LULUS POST']}), 
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No data available.")

else:
    selection = st.sidebar.selectbox("Select Detailed Sheet:", list(SHEETS_DICT.keys()))
    st.title(f"📊 {selection}")
    df_view = filtered_data.get(selection, pd.DataFrame())
    if not df_view.empty:
        st.dataframe(df_view.style.format({"score_num": "{:.1f}"}), use_container_width=True)
