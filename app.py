import streamlit as st
import pandas as pd

# 1. Configuration
SHEETS_DICT = {
    "Operasi Di Laluan": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Bas Tamat Operasi - RPG": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils",
    "Peraturan Memperlahankan Pemanduan": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "PENGENDALIAN KEROSAKAN": None,
    "PENGOPERASIAN MESIN C360": None
}

# Short headers for the table to prevent horizontal scrolling
SHORT_HEADERS = {
    "Operasi Di Laluan": "M1:Laluan",
    "Bas Tamat Operasi - RPG": "M2:RPG",
    "Peraturan Memperlahankan Pemanduan": "M3:Perat",
    "PENGENDALIAN KEROSAKAN": "M4:Kerosak",
    "PENGOPERASIAN MESIN C360": "M5:Mesin"
}

st.set_page_config(page_title="Depoh Summary Dashboard", layout="wide")

# --- CUSTOM CSS FOR THE YELLOW PROGRESS BAR DESIGN ---
st.markdown("""
    <style>
    .main { background-color: #0b111e; color: white; }
    .depoh-label { font-weight: bold; font-size: 15px; color: #ffffff; margin-top: 10px; }
    .stProgress > div > div > div > div { background-color: #f1c40f; }
    .score-text { font-size: 18px; font-weight: bold; color: #f1c40f; line-height: 1; }
    .sub-text { font-size: 11px; color: #bdc3c7; }
    /* Table Styling */
    .stDataFrame { border: 1px solid #34495e; }
    </style>
    """, unsafe_allow_html=True)

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
        except:
            all_dfs[name] = pd.DataFrame(columns=['id pekerja', 'nama penuh', 'depoh', 'score_num', 'timestamp'])
    return all_dfs

raw_data = load_all_data()

# --- SIDEBAR: DATE SELECTION & RESET ---
st.sidebar.title("📅 Filters")
all_dates = []
for df in raw_data.values():
    if not df.empty: all_dates.extend(df['timestamp'].dt.date.tolist())

if all_dates:
    min_d, max_d = min(all_dates), max(all_dates)
    if st.sidebar.button("🔄 Reset Dates"):
        st.session_state.date_range = (min_d, max_d)
        st.rerun()
    if 'date_range' not in st.session_state: st.session_state.date_range = (min_d, max_d)
    sel_range = st.sidebar.date_input("Select Date Range:", value=st.session_state.date_range, min_value=min_d, max_value=max_d)
    st.session_state.date_range = sel_range
else:
    sel_range = None

# Filter Logic
filtered_data = {}
for name, df in raw_data.items():
    if not df.empty and sel_range and len(sel_range) == 2:
        mask = (df['timestamp'].dt.date >= sel_range[0]) & (df['timestamp'].dt.date <= sel_range[1])
        filtered_data[name] = df[mask]
    else:
        filtered_data[name] = df

# --- PAGE MODE ---
page = st.sidebar.radio("Go to:", ["Main Summary", "Detailed View"])

if page == "Main Summary":
    st.title("📋 Master SOP Summary Dashboard")
    
    # Check for empty filtered data to avoid concatenation errors
    valid_dfs_check = [df for df in filtered_data.values() if not df.empty]
    
    if not valid_dfs_check:
        st.warning("⚠️ No data found for the selected date range.")
    else:
        # 1. Calculate BIL PERCUBAAN
        combined_raw = pd.concat([df[['id pekerja']] for df in filtered_data.values() if not df.empty])
        attempt_counts = combined_raw.value_counts('id pekerja').reset_index()
        attempt_counts.columns = ['id pekerja', 'attempts']
        attempt_counts['BIL'] = attempt_counts['attempts'].astype(str) + "x"

        # 2. Logic for PRE (Earliest) and POST (Latest)
        summary_dfs_pre = {n: df.sort_values('timestamp').groupby('id pekerja').first().reset_index() for n, df in filtered_data.items() if not df.empty}
        summary_dfs_post = {n: df.sort_values('timestamp').groupby('id pekerja').last().reset_index() for n, df in filtered_data.items() if not df.empty}

        # 3. Create Master Summary Table
        all_staff = pd.concat([df[['id pekerja', 'nama penuh', 'depoh']] for df in summary_dfs_pre.values()]).drop_duplicates('id pekerja')
        summary_table = pd.merge(all_staff, attempt_counts[['id pekerja', 'BIL']], on='id pekerja', how='left')
        
        score_cols = list(SHEETS_DICT.keys())
        for name in score_cols:
            # Add Pre-scores
            pre = summary_dfs_pre.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))[['id pekerja', 'score_num']].rename(columns={'score_num': name})
            summary_table = pd.merge(summary_table, pre, on='id pekerja', how='left')
            # Add Post-scores (prefixed with p_)
            post = summary_dfs_post.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))[['id pekerja', 'score_num']].rename(columns={'score_num': f'p_{name}'})
            summary_table = pd.merge(summary_table, post, on='id pekerja', how='left')
        
        summary_table = summary_table.fillna(0.0)
        
        # 4. Totals and Percentages
        summary_table['Total Pre'] = summary_table[score_cols].sum(axis=1).round(1)
        summary_table['% PRE'] = ((summary_table['Total Pre'] / 25.0) * 100).round(1)
        
        p_cols = [f'p_{name}' for name in score_cols]
        summary_table['Total Post'] = summary_table[p_cols].sum(axis=1).round(1)
        summary_table['% POST'] = ((summary_table['Total Post'] / 25.0) * 100).round(1)

        # --- DIAGRAM: THE YELLOW PROGRESS BAR DESIGN ---
        st.markdown("<h2 style='text-align: center; color: #f1c40f; margin-bottom: 30px;'>AVERAGE % SCORE BY DEPOH</h2>", unsafe_allow_html=True)
        
        depoh_avgs = summary_table.groupby('depoh')['% POST'].mean().reset_index().sort_values('% POST', ascending=False)
        
        for _, row in depoh_avgs.iterrows():
            # Creating the row layout: Name | Progress Bar | Score
            d_col, b_col, s_col = st.columns([2, 5, 2])
            with d_col:
                st.markdown(f"<p class='depoh-label'>{row['depoh'].upper()}</p>", unsafe_allow_html=True)
            with b_col:
                st.markdown("<div style='padding-top: 15px;'>", unsafe_allow_html=True)
                st.progress(int(row['% POST']) / 100)
                st.markdown("</div>", unsafe_allow_html=True)
            with s_col:
                st.markdown(f"""
                    <div>
                        <span class='score-text'>{row['% POST']:.1f}%</span><br>
                        <span class='sub-text'>Average Post Score</span>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # --- TABLE: FULL FIT VIEW ---
        st.subheader("SKOR PRA PENILAIAN KENDIRI FC 2025 (PRE vs POST)")
        
        # Prepare for display
        final_df = summary_table.rename(columns={'id pekerja': 'ID', 'nama penuh': 'NAMA', 'depoh': 'DEPOH', **SHORT_HEADERS})
        short_names = list(SHORT_HEADERS.values())
        show_cols = ['ID', 'NAMA', 'DEPOH', 'BIL'] + short_names + ['Total Pre', 'Total Post', '% PRE', '% POST']
        
        st.dataframe(
            final_df[show_cols].style.format({c: "{:.1f}" for c in ['Total Pre', 'Total Post', '% PRE', '% POST']}),
            use_container_width=True, hide_index=True
        )

else:
    selection = st.sidebar.selectbox("Select Detailed Sheet:", list(SHEETS_DICT.keys()))
    df_view = filtered_data.get(selection, pd.DataFrame())
    if not df_view.empty:
        st.dataframe(df_view.style.format({"score_num": "{:.1f}"}), use_container_width=True)
