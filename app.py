import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Sheet Configuration
SHEETS_DICT = {
    "Operasi Di Laluan": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Peraturan Memperlahankan Pemanduan dan Memberhentikan Bas Di Setiap Hentian": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "Bas Tamat Operasi - RPG": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils"
}

st.set_page_config(page_title="Depoh Analysis", layout="wide")

@st.cache_data(ttl=600)
def load_single_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(url)
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    date_col = None
    if 'timestamp' in df.columns:
        date_col = 'timestamp'
    elif 'date' in df.columns:
        date_col = 'date'
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
    
    # Pre-process numeric score for calculation
    if 'total score' in df.columns:
        # Extract numeric part (e.g., "5.00 / 5" -> 5.0)
        df['score_numeric'] = df['total score'].astype(str).str.split('/').str[0].astype(float)
    
    return df, date_col

st.title("📊 Staff Analysis by Depoh")

selection = st.sidebar.selectbox("Select Sheet:", list(SHEETS_DICT.keys()))
selected_id = SHEETS_DICT[selection]

try:
    df, date_col_name = load_single_sheet(selected_id)

    if date_col_name:
        min_date = df[date_col_name].min().date()
        max_date = df[date_col_name].max().date()
        st.sidebar.divider()
        st.sidebar.subheader("📅 Filter by Date")
        
        date_range = st.sidebar.date_input(
            "Select Date Range:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            mask = (df[date_col_name].dt.date >= start_date) & (df[date_col_name].dt.date <= end_date)
            df = df[mask]

    # --- BEFORE VS AFTER LOGIC ---
    if 'id pekerja' in df.columns and 'depoh' in df.columns and 'score_numeric' in df.columns:
        
        # Sort by timestamp to identify first vs later attempts
        df_sorted = df.sort_values(by=[date_col_name])
        
        comparison_data = []
        
        for staff_id, group in df_sorted.groupby('id pekerja'):
            # The very first attempt is "Before"
            before_score = group.iloc[0]['score_numeric']
            depoh = group.iloc[0]['depoh']
            
            # If there are more attempts, find the max of the remaining
            after_score = None
            if len(group) > 1:
                after_score = group.iloc[1:]['score_numeric'].max()
            
            comparison_data.append({
                'Staff ID': staff_id,
                'Depoh': depoh,
                'Before Score': before_score,
                'After Score': after_score
            })
        
        comp_df = pd.DataFrame(comparison_data)

        # Calculate Averages for the table
        avg_before = comp_df['Before Score'].mean()
        avg_after = comp_df['After Score'].mean() # This ignores None values automatically

        # --- DISPLAY TABLE ---
        st.subheader("📝 Understanding SOP: Before vs After")
        
        m1, m2 = st.columns(2)
        m1.metric("Avg Score (Before)", f"{avg_before:.2f} / 5")
        m2.metric("Avg Score (After - Best)", f"{avg_after:.2f} / 5" if not pd.isna(avg_after) else "N/A")
        
        st.dataframe(comp_df, hide_index=True, use_container_width=True)
        st.divider()

        # --- ORIGINAL DASHBOARD LOGIC ---
        depoh_stats = df.groupby('depoh')['id pekerja'].nunique().reset_index()
        depoh_stats.columns = ['Depoh Name', 'Unique Staff Count']

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Total Unique Staff", depoh_stats['Unique Staff Count'].sum())
            st.dataframe(depoh_stats, hide_index=True, use_container_width=True)

        with col2:
            fig = px.pie(
                depoh_stats, 
                values='Unique Staff Count', 
                names='Depoh Name',
                hole=0.75,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        st.subheader("Filtered Data Preview")
        st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Required columns (id pekerja, depoh, total score) not found!")
        st.write("Current columns:", list(df.columns))

except Exception as e:
    st.error(f"Error: {e}")
