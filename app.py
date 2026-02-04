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
            
            # Identify ID and Score columns
            if 'id pekerja' in temp_df.columns and 'total score' in temp_df.columns:
                temp_df['score_num'] = temp_df['total score'].astype(str).str.split('/').str[0].astype(float).round(1)
                
                # Ensure timestamp is datetime for filtering
                date_col = 'timestamp' if 'timestamp' in temp_df.columns else 'date'
                if date_col in temp_df.columns:
                    temp_df['timestamp'] = pd.to_datetime(temp_df[date_col], errors='coerce')
                    temp_df = temp_df.dropna(subset=['timestamp'])
                
                all_dfs[name] = temp_df
        except Exception:
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
    return all_dfs

raw_data = load_all_data()

# --- SIDEBAR: DATE SELECTION ---
st.sidebar.title("📅 Filters")

# Collect all dates to find the absolute min and max
all_dates = []
for df in raw_data.values():
    if not df.empty and 'timestamp' in df.columns:
        all_dates.extend(df['timestamp'].dt.date.tolist())

if all_dates:
    min_date, max_date = min(all_dates), max(all_dates)
    selected_date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
else:
    selected_date_range = None

# Apply Filter Logic
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
    
    # Process "Before" logic (1st attempt) for the Summary Table
    summary_dfs = {}
    for name, df in filtered_data.items():
        if not df.empty:
            summary_dfs[name] = df.sort_values('timestamp').groupby('id pekerja').first().reset_index()
        else:
            summary_dfs[name] = df

    # Build Master Table
    valid_dfs = [df for df in summary_dfs.values() if not df.empty]
    if valid_dfs:
        all_staff = pd.concat([df[['id pekerja', 'nama penuh', 'depoh']] for df in valid_dfs]).drop_duplicates('id pekerja')
        summary_table = all_staff.copy()
        
        for name in SHEETS_DICT.keys():
            df = summary_dfs.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))
            score_sub = df[['id pekerja', 'score_num']].rename(columns={'score_num': name})
            summary_table = pd.merge(summary_table, score_sub, on='id pekerja', how='left')
        
        summary_table = summary_table.fillna(0.0)
        
        # Calculations
        score_cols = list(SHEETS_DICT.keys())
        max_possible = len(score_cols) * 5
        summary_table['Total Pre-Score'] = summary_table[score_cols].sum(axis=1).round(1)
        summary_table['% LULUS PRE'] = ((summary_table['Total Pre-Score'] / max_possible) * 100).round(1)
        summary_table['% LULUS POST'] = 0.0

        # --- TOP METRICS ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Staff", len(summary_table))
        m2.metric("Avg Score %", f"{summary_table['% LULUS PRE'].mean():.1f}%")
        m3.metric("Depohs Active", summary_table['depoh'].nunique())
        
        # --- BAR CHART (DEPOH PERFORMANCE) ---
        st.subheader("📊 Average Performance by Depoh")
        depoh_perf = summary_table.groupby('depoh')['% LULUS PRE'].mean().reset_index()
        fig_bar = px.bar(depoh_perf, x='depoh', y='% LULUS PRE', 
                         color='depoh', text_auto='.1f',
                         labels={'% LULUS PRE': 'Average Lulus %', 'depoh': 'Depoh Name'})
        fig_bar.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        # --- DATA TABLE ---
        st.subheader("SKOR PRA PENILAIAN KENDIRI FC 2025 (PRE)")
        formatted_df = summary_table.rename(columns={'id pekerja': 'ID', 'nama penuh': 'NAMA', 'depoh': 'DEPOH'})
        float_cols = score_cols + ['Total Pre-Score', '% LULUS PRE', '% LULUS POST']
        
        st.dataframe(
            formatted_df.style.format({col: "{:.1f}" for col in float_cols}), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("No data available for the selected date range.")

else:
    # --- DETAILED SHEET VIEW ---
    selection = st.sidebar.selectbox("Select Detailed Sheet:", list(SHEETS_DICT.keys()))
    st.title(f"📊 Detailed Analysis: {selection}")
    
    selected_df = filtered_data.get(selection, pd.DataFrame())
    
    if selected_df.empty:
        st.warning(f"No data available for {selection} within the selected dates.")
    else:
        st.dataframe(
            selected_df.style.format({"score_num": "{:.1f}"}), 
            use_container_width=True
        )
