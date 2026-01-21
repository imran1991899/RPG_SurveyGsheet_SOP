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

# Sidebar Selection
selection = st.sidebar.selectbox("Select Sheet to Analyze:", list(SHEETS_DICT.keys()))
selected_id = SHEETS_DICT[selection]

try:
    df = load_single_sheet(selected_id)
    df.columns = [c.lower().strip() for c in df.columns]

    if 'id pekerja' in df.columns and 'depoh' in df.columns:
        
        # Calculation: Unique ID PEKERJA per DEPOH
        depoh_stats = df.groupby('depoh')['id pekerja'].nunique().reset_index()
        depoh_stats.columns = ['Depoh Name', 'Unique Staff Count']

        col1, col2 = st.columns([1, 2])

        with col1:
            st.write("### Summary")
            st.metric("Total Unique Staff", depoh_stats['Unique Staff Count'].sum())
            st.dataframe(depoh_stats, hide_index=True, use_container_width=True)

        with col2:
            # 2. Make the Chart "Thin" (Donut style)
            fig = px.pie(
                depoh_stats, 
                values='Unique Staff Count', 
                names='Depoh Name',
                hole=0.7, # Higher number (0.7-0.8) makes the ring thinner
                color_discrete_sequence=px.colors.qualitative.Pastel # Professional colors
            )
            
            # 3. Adjusting the layout for a sleek look
            fig.update_traces(textinfo='percent+label', textposition='outside')
            fig.update_layout(
                showlegend=False, 
                height=400, 
                margin=dict(t=20, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        st.subheader("Raw Data Preview")
        st.dataframe(df, use_container_width=True)

    else:
        st.error("Check column names: Ensure 'id pekerja' and 'depoh' exist.")

except Exception as e:
    st.error(f"Error: {e}")
