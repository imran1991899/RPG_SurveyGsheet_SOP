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
    # Clean column names
    df.columns = [str(c).lower().strip() for c in df.columns]
    
    # --- DATE CONVERSION ---
    date_col = None
    if 'timestamp' in df.columns:
        date_col = 'timestamp'
    elif 'date' in df.columns:
        date_col = 'date'
    
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
    
    # Extract numeric score from string (e.g., "4.00 / 5" -> 4.0)
    if 'total score' in df.columns:
        df['score_val'] = df['total score'].astype(str).str.split('/').str[0].astype(float)
    
    return df, date_col

st.title("📊 Staff Analysis by Depoh")

# Sidebar - Sheet Selection
selection = st.sidebar.selectbox("Select Sheet:", list(SHEETS_DICT.keys()))
selected_id = SHEETS_DICT[selection]

try:
    df, date_col_name = load_single_sheet(selected_id)

    # --- DATE FILTER SECTION ---
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

    # --- BEFORE vs AFTER TABLE LOGIC ---
    if 'id pekerja' in df.columns and 'score_val' in df.columns:
        st.subheader("📝 SOP Understanding: Before vs After")
        
        # Sort by timestamp to find 1st attempt
        df_sorted = df.sort_values(by=date_col_name)
        
        comparison_list = []
        for staff_id, group in df_sorted.groupby('id pekerja'):
            # First submission is always 'Before'
            before_score = group.iloc[0]['score_val']
            staff_name = group.iloc[0]['nama penuh'] if 'nama penuh' in group.columns else "N/A"
            depoh_name = group.iloc[0]['depoh'] if 'depoh' in group.columns else "N/A"
            
            # If they have multiple answers, get the highest score from the subsequent ones
            after_score = None
            if len(group) > 1:
                after_score = group.iloc[1:]['score_val'].max()
            
            comparison_list.append({
                "Staff ID": staff_id,
                "Name": staff_name,
                "Depoh": depoh_name,
                "Before (1st Attempt)": before_score,
                "After (Highest of Recent)": after_score
            })
        
        comp_df = pd.DataFrame(comparison_list)
        st.dataframe(comp_df, hide_index=True, use_container_width=True)
        st.divider()

    # --- DASHBOARD LOGIC ---
    if 'id pekerja' in df.columns and 'depoh' in df.columns:
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
        st.error(f"Columns not found! Ensure 'id pekerja' and 'depoh' are in the sheet.")

except Exception as e:
    st.error(f"Error: {e}")
