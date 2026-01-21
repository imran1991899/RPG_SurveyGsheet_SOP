import streamlit as st
import pandas as pd

# 1. Define your Sheets with Names for the menu
SHEETS_DICT = {
    "Sheet 1": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Sheet 2": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "Sheet 3": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils"
}

st.set_page_config(page_title="Individual Sheet Viewer", layout="wide")

# 2. Function to load just ONE sheet at a time
@st.cache_data(ttl=600)
def load_single_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    return pd.read_csv(url)

st.title("📈 Individual Sheet Dashboard")

# 3. Sidebar Menu to choose which sheet to see
st.sidebar.header("Navigation")
selection = st.sidebar.selectbox("Choose a Sheet to View:", list(SHEETS_DICT.keys()))

# Get the ID based on the user's choice
selected_id = SHEETS_DICT[selection]

try:
    # Load only the chosen sheet
    df = load_single_sheet(selected_id)
    
    st.subheader(f"Showing Data for: {selection}")

    # 4. Show Quick Stats for this specific sheet
    col1, col2 = st.columns(2)
    col1.metric("Total Entries", len(df))
    
    # If your sheet has a 'depoh' column, show how many are in this sheet
    if 'depoh' in df.columns:
        col2.metric("Total Depohs", df['depoh'].nunique())

    # 5. Show the table for this specific sheet
    st.dataframe(df, use_container_width=True)

    # 6. Optional: Add a search box for this specific sheet
    if 'id pekerja' in df.columns:
        search = st.text_input("Search ID Pekerja in this sheet:")
        if search:
            result = df[df['id pekerja'].astype(str).str.contains(search)]
            st.write("Search Results:", result)

except Exception as e:
    st.error(f"Error connecting to {selection}. Please check sharing settings.")
