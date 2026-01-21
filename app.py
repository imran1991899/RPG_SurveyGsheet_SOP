import streamlit as st
import pandas as pd

# List your 10 Sheet IDs here
SHEET_IDS = [
    "1A2b3C4d5E6f7G8h9I0jKLmNoPqRsTuVw",  # ID from Sheet 1
    "9Z8y7X6w5V4u3T2s1R0qPlMnOkJihGfE",  # ID from Sheet 2
    "AnotherLongIDStringHere_3",         # ID from Sheet 3
    "AnotherLongIDStringHere_4",         # ID from Sheet 4
    "AnotherLongIDStringHere_5",         # ID from Sheet 5
    "AnotherLongIDStringHere_6",         # ID from Sheet 6
    "AnotherLongIDStringHere_7",         # ID from Sheet 7
    "AnotherLongIDStringHere_8",         # ID from Sheet 8
    "AnotherLongIDStringHere_9",         # ID from Sheet 9
    "AnotherLongIDStringHere_10"         # ID from Sheet 10
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
