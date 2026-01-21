import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Sheet Configuration
SHEETS_DICT = {
    "Sheet 1": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Sheet 2": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "Sheet 3": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils"
}

st.set_page_config(page_title="Depoh Analysis", layout="wide")

@st.cache_data(ttl=600)
def load_single_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

st.title("📊 Staff Analysis by Depoh")

# Sidebar
selection = st.sidebar.selectbox("Select Sheet:", list(SHEETS_DICT.keys()))
selected_id = SHEETS_DICT[selection]

try:
    df = load_single_sheet(selected_id)
    # Clean column names: lowercase and remove hidden spaces
    df.columns = [str(c).lower().strip() for c in df.columns]

    if 'id pekerja' in df.columns and 'depoh' in df.columns:
        # Grouping and counting unique IDs
        depoh_stats = df.groupby('depoh')['id pekerja'].nunique().reset_index()
        depoh_stats.columns = ['Depoh Name', 'Unique Staff Count']

        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Total Unique Staff", depoh_stats['Unique Staff Count'].sum())
            st.dataframe(depoh_stats, hide_index=True)

        with col2:
            # The "Thin" Donut Chart
            fig = px.pie(
                depoh_stats, 
                values='Unique Staff Count', 
                names='Depoh Name',
                hole=0.75
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.error(f"Columns not found! Sheet has: {list(df.columns)}")

except Exception as e:
    st.error(f"Error: {e}")
