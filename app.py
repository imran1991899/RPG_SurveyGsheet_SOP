import streamlit as st
import pandas as pd

# List your 10 Sheet IDs here
SHEET_IDS = [
    "ID_1", "ID_2", "ID_3", "ID_4", "ID_5",
    "ID_6", "ID_7", "ID_8", "ID_9", "ID_10"
]

# This keeps the app fast by remembering data for 10 minutes
@st.cache_data(ttl=600)
def load_and_combine_data(ids):
    all_data = []
    for sid in ids:
        # Direct link to pull live data
        url = f"https://docs.google.com/spreadsheets/d/{sid}/export?format=csv"
        df = pd.read_csv(url)
        all_data.append(df)
    return pd.concat(all_data, ignore_index=True)

st.title("📈 Executive Multi-Sheet Dashboard")

try:
    # Pull the live data
    df = load_and_combine_data(SHEET_IDS)
    
    # 1. Show high-level metrics
    st.subheader("Quick Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Entries", len(df))
    # Change 'Amount' to a column name you actually have in your sheets
    if 'Amount' in df.columns:
        col2.metric("Total Value", f"${df['Amount'].sum():,.2f}")
    
    # 2. Show the data table
    st.subheader("Raw Data (All 10 Sheets Combined)")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("Error connecting to Google Sheets. Check your Sheet IDs and Sharing settings.")
