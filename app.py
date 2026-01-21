import streamlit as st
import pandas as pd
import plotly.express as px  # We use plotly for nice interactive pie charts

# 1. YOUR REAL IDs ONLY
SHEET_IDS = [
    "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils"
]

@st.cache_data(ttl=600)
def load_and_combine_data(ids):
    all_data = []
    for sid in ids:
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
        df = pd.read_csv(url)
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

st.title("📈 HR & Depoh Dashboard")

try:
    df = load_and_combine_data(SHEET_IDS)
    
    # --- METRICS SECTION ---
    st.subheader("General Overview")
    col1, col2 = st.columns(2)
    
    # Count unique ID Pekerja
    total_staff = df['id pekerja'].nunique()
    col1.metric("Total Staff (Unique)", total_staff)
    
    # Count unique Depoh
    total_depoh_count = df['depoh'].nunique()
    col2.metric("Total Active Depoh", total_depoh_count)

    # --- PIE CHART SECTION ---
    st.divider()
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Staff Distribution")
        # Pie chart for ID Pekerja (Total Staff)
        fig_staff = px.pie(df, names='id pekerja', title='Total Staff ID Breakdown')
        st.plotly_chart(fig_staff, use_container_width=True)

    with chart_col2:
        st.subheader("Depoh Distribution")
        # Pie chart for Depoh
        fig_depoh = px.pie(df, names='depoh', title='Staff Count by Depoh')
        st.plotly_chart(fig_depoh, use_container_width=True)

    # Show raw data
    with st.expander("View Combined Data"):
        st.write(df)

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Check if column names 'id pekerja' and 'depoh' exist in all sheets.")
