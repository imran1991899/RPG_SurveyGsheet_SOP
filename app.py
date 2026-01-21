import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Sheet Configuration
SHEETS_DICT = {
    "Sheet 1": "1SRlxQQ9OFQJyXDFAP2I2bAKEh2ACc9czqdKvysLWP64",
    "Sheet 2": "1QmdnNFHxIG1o-JeGN_mR9QgdbXc76lFurzh2cgot9gE",
    "Sheet 3": "1P1ThhQJ49Bl9Rh13Aq_rX9eysxDTJFdJL0pX45EGils"
}

st.set_page_config(page_title="SOP Training Analysis", layout="wide")

@st.cache_data(ttl=600)
def load_single_sheet(sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(url)
    # Standardize column names
    df.columns = [str(c).lower().strip() for c in df.columns]
    return df

st.title("👨‍✈️ KAPTEN SOP Training Dashboard")

selection = st.sidebar.selectbox("Select Sheet:", list(SHEETS_DICT.keys()))
selected_id = SHEETS_DICT[selection]

try:
    df = load_single_sheet(selected_id)

    # Required columns for this logic: 'id kapten' and 'score' (or 'total score')
    # If your score column name is different, change 'score' below
    score_col = 'score' if 'score' in df.columns else 'total score'

    if 'id kapten' in df.columns and score_col in df.columns:
        
        # LOGIC: Sort by Timestamp if it exists, otherwise use the order in the sheet
        # We assume the first appearance of an ID is PRE and second is POST
        df['attempt_order'] = df.groupby('id kapten').cumcount() + 1
        
        # Split data into Pre and Post
        pre_test = df[df['attempt_order'] == 1]
        post_test = df[df['attempt_order'] == 2]

        # Calculate metrics
        # Assuming "Right Answer" means score is maximum (e.g., 10/10)
        # You can adjust the "==" to your passing mark
        max_score = df[score_col].max()
        
        wrong_pre = pre_test[pre_test[score_col] < max_score].shape[0]
        right_post = post_test[post_test[score_col] == max_score].shape[0]

        # --- DISPLAY SECTION ---
        st.subheader("SOP Knowledge Improvement")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Kapten Trained", df['id kapten'].nunique())
        m2.error(f"Wrong in Pre-Test: {wrong_pre}")
        m3.success(f"Right in Post-Test: {right_post}")

        # --- COMPARISON TABLE ---
        st.write("### Training Progress Table")
        
        # Merge pre and post to compare side-by-side
        comparison = pd.merge(
            pre_test[['id kapten', score_col]], 
            post_test[['id kapten', score_col]], 
            on='id kapten', 
            how='left', 
            suffixes=('_PRE', '_POST')
        )
        
        st.dataframe(comparison, use_container_width=True, hide_index=True)

        # --- IMPROVEMENT CHART ---
        st.divider()
        st.write("### Score Improvement Chart")
        
        # Prepare data for a bar chart
        chart_data = pd.DataFrame({
            "Stage": ["Pre-Test", "Post-Test"],
            "Correct Answers": [
                pre_test[pre_test[score_col] == max_score].shape[0],
                post_test[post_test[score_col] == max_score].shape[0]
            ]
        })
        
        fig = px.bar(chart_data, x='Stage', y='Correct Answers', 
                     color='Stage', text_auto=True,
                     color_discrete_map={"Pre-Test": "#FF4B4B", "Post-Test": "#00CC96"})
        
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning(f"Columns not found. Sheet must have 'id kapten' and a score column. Found: {list(df.columns)}")

except Exception as e:
    st.error(f"Error: {e}")
