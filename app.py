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
    
    # Extract numeric score (e.g., "5.00 / 5" -> 5.0)
    if 'total score' in df.columns:
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
    if 'id pekerja' in df.columns and 'score_numeric' in df.columns:
        
        # Sort by timestamp ascending (earliest first)
        df_sorted = df.sort_values(by=[date_col_name], ascending=True)
        
        comparison_results = []
        
        for staff_id, group in df_sorted.groupby('id pekerja'):
            # 1st Timestamp = Before
            before_row = group.iloc[0]
            before_score = before_row['score_numeric']
            staff_name = before_row['nama penuh'] if 'nama penuh' in df.columns else "N/A"
            depoh = before_row['depoh'] if 'depoh' in df.columns else "N/A"
            
            # Submissions AFTER the 1st one
            after_submissions = group.iloc[1:]
            
            if not after_submissions.empty:
                # Take the HIGHEST score from the remaining recent entries
                after_score = after_submissions['score_numeric'].max()
            else:
                after_score = None # No second attempt yet
            
            comparison_results.append({
                "Staff ID": staff_id,
                "Name": staff_name,
                "Depoh": depoh,
                "Before (1st Attempt)": before_score,
                "After (Highest of Recent)": after_score
            })
            
        comp_df = pd.DataFrame(comparison_results)

        # --- DISPLAY SUMMARY TABLE ---
        st.subheader("📋 Staff SOP Understanding: Before vs After")
        st.write("Comparison based on first attempt vs. highest subsequent attempt.")
        
        # Displaying the comparison table
        st.dataframe(comp_df, hide_index=True, use_container_width=True)
        
        st.divider()

    # --- DASHBOARD LOGIC (ORIGINAL) ---
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
        st.error(f"Columns 'id pekerja' and 'depoh' are required.")

except Exception as e:
    st.error(f"Error: {e}")
