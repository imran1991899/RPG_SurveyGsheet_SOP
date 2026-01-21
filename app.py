import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Sheet Configuration
SHEETS_DICT = {
    "Bas Tamat Operasi": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Operasi Di Laluan": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "Peraturan Memperlahankan Pemanduan dan Memberhentikan Bas Di Setiap Hentian": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils"
}

st.set_page_config(page_title="Depoh Analysis", layout="wide")

@st.cache_data(ttl=600)
def load_single_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

st.title("📊 Staff Analysis by Depoh")

# 2. Sidebar Selection
selection = st.sidebar.selectbox("Select Sheet to Analyze:", list(SHEETS_DICT.keys()))
selected_id = SHEETS_DICT[selection]

try:
    df = load_single_sheet(selected_id)
    
    # Standardize column names to lowercase to avoid errors (optional but safer)
    df.columns = [c.lower() for c in df.columns]

    if 'id pekerja' in df.columns and 'depoh' in df.columns:
        
        # 3. Calculation: Unique ID PEKERJA per DEPOH
        # We group by Depoh and count unique staff IDs
        depoh_stats = df.groupby('depoh')['id pekerja'].nunique().reset_index()
        depoh_stats.columns = ['Depoh Name', 'Unique Staff Count']

        # 4. Layout: Metrics and Pie Chart
        col1, col2 = st.columns([1, 2])

        with col1:
            st.metric("Grand Total Unique Staff", depoh_stats['Unique Staff Count'].sum())
            st.write("### Data Breakdown")
            st.dataframe(depoh_stats, hide_index=True)

        with col2:
            # 5. Create the Pie Chart
            fig = px.pie(
                depoh_stats, 
                values='Unique Staff Count', 
                names='Depoh Name',
                title=f"Distribution of Unique Staff by Depoh ({selection})",
                hole=0.3  # Optional: makes it a donut chart for better looks
            )
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        st.subheader(f"Raw Data Preview: {selection}")
        st.dataframe(df, use_container_width=True)

    else:
        st.error("Error: Could not find 'id pekerja' or 'depoh' columns in this sheet.")
        st.write("Found columns:", list(df.columns))

except Exception as e:
    st.error(f"Failed to load {selection}. Please check your Sheet IDs and ensure they are shared 'Anyone with link'.")
