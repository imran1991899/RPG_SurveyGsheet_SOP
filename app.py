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

SHORT_HEADERS = {
    "Operasi Di Laluan": "M1:Laluan",
    "Bas Tamat Operasi - RPG": "M2:RPG",
    "Peraturan Memperlahankan Pemanduan": "M3:Perat",
    "PENGENDALIAN KEROSAKAN": "M4:Kerosak",
    "PENGOPERASIAN MESIN C360": "M5:Mesin"
}

st.set_page_config(page_title="Depoh Summary Dashboard", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #0b111e; color: white; }
    .depoh-label { 
        font-weight: bold; font-size: 14px; color: #ffffff; 
        margin-top: 10px; text-align: right; margin-right: -15px; 
    }
    .stProgress > div > div > div > div { background-color: #f1c40f; }
    .score-text { font-size: 18px; font-weight: bold; color: #f1c40f; line-height: 1; }
    .sub-text { font-size: 11px; color: #bdc3c7; }
    .stDataFrame { border: 1px solid #34495e; }
    
    /* Merit Table Styling */
    .merit-box {
        padding: 10px; border-radius: 5px; border: 1px solid #34495e;
        background-color: #161b22; width: 100%;
    }
    .merit-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .merit-table th, .merit-table td { padding: 5px; text-align: center; border: 1px solid #30363d; }
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

# --- CORRECTED HIGHLIGHTING LOGIC (Using Score, 50% Opacity) ---
def highlight_merit(row):
    score = row['Total Post']
    color = '' 
    
    # Based on raw score 0-25 as per your Merit Reference Table
    if 0 <= score <= 5:
        color = 'background-color: rgba(255, 0, 0, 0.5); color: white;'     # RED
    elif 6 <= score <= 10:
        color = 'background-color: rgba(255, 255, 0, 0.5); color: black;'   # YELLOW
    elif 11 <= score <= 15:
        color = 'background-color: rgba(255, 165, 0, 0.5); color: white;'   # ORANGE
    elif 16 <= score <= 20:
        color = 'background-color: rgba(0, 191, 255, 0.5); color: white;'   # BLUE
    elif 21 <= score <= 25:
        color = 'background-color: rgba(0, 128, 0, 0.5); color: white;'     # GREEN
    
    return [color] * len(row)

raw_data = load_all_data()

# --- FILTERS ---
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

filtered_data = {n: (df[(df['timestamp'].dt.date >= sel_range[0]) & (df['timestamp'].dt.date <= sel_range[1])] if not df.empty and sel_range and len(sel_range)==2 else df) for n, df in raw_data.items()}

# --- MAIN PAGE ---
page = st.sidebar.radio("Go to:", ["Main Summary", "Detailed View"])

if page == "Main Summary":
    st.title("📋 Master SOP Summary Dashboard")
    
    valid_dfs_check = [df for df in filtered_data.values() if not df.empty]
    
    if not valid_dfs_check:
        st.warning("⚠️ No data found for selected dates.")
    else:
        combined_raw = pd.concat([df[['id pekerja']] for df in filtered_data.values() if not df.empty])
        attempt_counts = combined_raw.value_counts('id pekerja').reset_index()
        attempt_counts.columns = ['id pekerja', 'attempts']
        attempt_counts['BIL'] = attempt_counts['attempts'].astype(str) + "x"

        pre_dfs = {n: df.sort_values('timestamp').groupby('id pekerja').first().reset_index() for n, df in filtered_data.items() if not df.empty}
        post_dfs = {n: df.sort_values('timestamp').groupby('id pekerja').last().reset_index() for n, df in filtered_data.items() if not df.empty}

        all_staff = pd.concat([df[['id pekerja', 'nama penuh', 'depoh']] for df in pre_dfs.values()]).drop_duplicates('id pekerja')
        summary_table = pd.merge(all_staff, attempt_counts[['id pekerja', 'BIL']], on='id pekerja', how='left')
        
        score_cols = list(SHEETS_DICT.keys())
        for name in score_cols:
            pre = pre_dfs.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))[['id pekerja', 'score_num']].rename(columns={'score_num': name})
            summary_table = pd.merge(summary_table, pre, on='id pekerja', how='left')
            post = post_dfs.get(name, pd.DataFrame(columns=['id pekerja', 'score_num']))[['id pekerja', 'score_num']].rename(columns={'score_num': f'p_{name}'})
            summary_table = pd.merge(summary_table, post, on='id pekerja', how='left')
        
        summary_table = summary_table.fillna(0.0)
        summary_table['Total Pre'] = summary_table[score_cols].sum(axis=1).round(1)
        summary_table['% PRE'] = ((summary_table['Total Pre'] / 25.0) * 100).round(1)
        p_cols = [f'p_{name}' for name in score_cols]
        summary_table['Total Post'] = summary_table[p_cols].sum(axis=1).round(1)
        summary_table['% POST'] = ((summary_table['Total Post'] / 25.0) * 100).round(1)

        # --- PROGRESS BARS ---
        depoh_list = sorted(summary_table['depoh'].unique())
        header_col, reset_col = st.columns([8, 2])
        with header_col: st.markdown("<h2 style='color: #f1c40f;'>AVERAGE % SCORE BY DEPOH</h2>", unsafe_allow_html=True)
        with reset_col:
            if st.button("🔄 Reset Graph"):
                st.session_state.selected_depoh = "All Depohs"
                st.rerun()

        if 'selected_depoh' not in st.session_state: st.session_state.selected_depoh = "All Depohs"
        selected_depoh = st.selectbox("Select Depoh:", ["All Depohs"] + depoh_list, key="selected_depoh")

        depoh_avgs = summary_table.groupby('depoh')['% POST'].mean().reset_index().sort_values('% POST', ascending=False)
        for _, row in depoh_avgs.iterrows():
            d_col, b_col, s_col = st.columns([1.1, 5, 2])
            highlight = "border-right: 3px solid #f1c40f; color: #f1c40f;" if row['depoh'] == selected_depoh else "color: #ffffff;"
            with d_col: st.markdown(f"<p class='depoh-label' style='{highlight}'>{row['depoh'].upper()}</p>", unsafe_allow_html=True)
            with b_col: 
                st.markdown("<div style='padding-top: 15px;'>", unsafe_allow_html=True)
                st.progress(int(row['% POST']) / 100)
                st.markdown("</div>", unsafe_allow_html=True)
            with s_col: st.markdown(f"<div><span class='score-text'>{row['% POST']:.1f}%</span><br><span class='sub-text'>Avg Post Score</span></div>", unsafe_allow_html=True)

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        # --- DATA TABLE ---
        display_table = summary_table.copy()
        if selected_depoh != "All Depohs": display_table = display_table[display_table['depoh'] == selected_depoh]

        st.subheader(f"SKOR PRA PENILAIAN KENDIRI FC 2025 ({selected_depoh})")
        
        final_df = display_table.rename(columns={'id pekerja': 'ID', 'nama penuh': 'NAMA', 'depoh': 'DEPOH', **SHORT_HEADERS})
        short_names = list(SHORT_HEADERS.values())
        show_cols = ['ID', 'NAMA', 'DEPOH', 'BIL'] + short_names + ['Total Pre', 'Total Post', '% PRE', '% POST']
        
        format_dict = {c: "{:.0f}" for c in short_names} 
        format_dict.update({c: "{:.1f}" for c in ['Total Pre', 'Total Post', '% PRE', '% POST']})
        
        # Applying styling
        styled_df = final_df[show_cols].style.apply(highlight_merit, axis=1).format(format_dict)
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        # --- MERIT REFERENCE TABLE ---
        st.markdown("<br>", unsafe_allow_html=True)
        col_merit_1, col_merit_2 = st.columns([1, 2])
        with col_merit_1:
            st.markdown("""
            <div class="merit-box">
                <table class="merit-table">
                    <tr style="background-color: #30363d;">
                        <th>Merit</th>
                        <th>Score</th>
                        <th>Percentage</th>
                    </tr>
                    <tr>
                        <td style="background-color: #ff0000; color: white; font-weight: bold;">LEMAH</td>
                        <td>0 - 5</td>
                        <td>0 - 20%</td>
                    </tr>
                    <tr>
                        <td style="background-color: #ffff00; color: black; font-weight: bold;">TIDAK MAHIR</td>
                        <td>6 - 10</td>
                        <td>24 - 40%</td>
                    </tr>
                    <tr>
                        <td style="background-color: #ffa500; color: black; font-weight: bold;">SEDERHANA MAHIR</td>
                        <td>11 - 15</td>
                        <td>44 - 60%</td>
                    </tr>
                    <tr>
                        <td style="background-color: #00bfff; color: white; font-weight: bold;">MAHIR</td>
                        <td>16 - 20</td>
                        <td>64 - 80%</td>
                    </tr>
                    <tr>
                        <td style="background-color: #008000; color: white; font-weight: bold;">SANGAT MAHIR</td>
                        <td>21 - 25</td>
                        <td>84 - 100%</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

else:
    selection = st.sidebar.selectbox("Select Detailed Sheet:", list(SHEETS_DICT.keys()))
    df_view = filtered_data.get(selection, pd.DataFrame())
    if not df_view.empty:
        st.dataframe(df_view.style.format({"score_num": "{:.0f}"}), use_container_width=True)
