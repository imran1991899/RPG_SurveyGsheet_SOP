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
                
                # Ensure timestamp is datetime
                date_col = 'timestamp' if 'timestamp' in temp_df.columns else 'date'
                if date_col in temp_df.columns:
                    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
                    temp_df = temp_df.dropna(subset=[date_col])
                
                all_dfs[name] = temp_df
        except Exception:
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
    return all_dfs

raw_data = load_all_data()

# --- GLOBAL DATE FILTER IN SIDEBAR ---
st.sidebar.title("📅 Global Filters")

# Find min/max dates across all loaded data
all_dates = []
for df in raw_data.values():
    if not df.empty and 'timestamp' in df.columns:
        all_dates.extend(df['timestamp'].dt.date.tolist())

if all_dates:
    min_date, max_date = min(all_dates), max(all_dates)
    date_range = st.sidebar.date_input("Select Date Range:", value=(min_date, max_date), min_value=min_date, max_value=max_date)
else:
    date_range = None

# Apply Date Filter to all data
filtered_data = {}
if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    for name, df in raw_data.items():
        if not df.empty and 'timestamp' in df.columns:
            mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)
            filtered_data[name] = df[mask]
        else:
            filtered_data[name] = df
else:
    filtered_data = raw_data

# --- NAVIGATION ---
st.sidebar.divider()
page_mode = st.sidebar.radio("Go to:", ["Main Summary", "Detailed Sheet View"])

if page_mode == "Main Summary":
    st.title("📋 Master SOP Summary Dashboard")
    
    # Process for Summary (Take 1st attempt only)
    summary_dfs = {}
    for name, df in filtered_data.items():
        if not df.empty:
            summary_dfs[name] = df.sort_values('timestamp').groupby('id pekerja').first().reset_index()
        else:
            summary_dfs[name] = df

    # Build Master Table
    valid_list = [df for df in summary_dfs.values() if not df.empty]
    if valid_list:
        all_staff = pd.concat([df[['id pekerja', 'nama penuh', 'depoh']] for df in valid_list]).drop_duplicates('id pekerja')
        summary_table = all_staff.copy()
        
        for name in SHEETS_DICT.keys():
            df = summary_dfs.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))
            score_sub = df[['id pekerja', 'score_num']].rename(columns={'score_num': name})
            summary_table = pd.merge(summary_table, score_sub, on='id pekerja', how='left')
        
        summary_table = summary_table.fillna(0.0)
        
        # Calculations
        cols = list(SHEETS_DICT.keys())
        summary_table['Total Pre-Score'] = summary_table[cols].sum(axis=1).round(1)
        summary_table['% LULUS PRE'] = ((summary_table['Total Pre-Score'] / (len(cols)*5)) * 100).round(1)
        summary_table['% LULUS POST'] = 0.0

        st.dataframe(
            summary_table.rename(columns={'id pekerja':'ID','nama penuh':'NAMA','depoh':'DEPOH'})
            .style.format({c: "{:.1f}" for c in cols + ['Total Pre-Score', '% LULUS PRE']}),
            use_container_width=True, hide_index=True
        )
    else:
        st.warning("No data found for the selected date range.")

else:
    # --- DETAILED VIEW ---
    selection = st.sidebar.selectbox("Select Detailed Sheet:", list(SHEETS_DICT.keys()))
    st.title(f"📊 {selection}")
    df_view = filtered_data.get(selection, pd.DataFrame())
    
    if df_view.empty:
        st.info("No data for this selection/date range.")
    else:
        st.dataframe(df_view.style.format({"score_num": "{:.1f}"}), use_container_width=True)
