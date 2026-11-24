import streamlit as st

st.set_page_config(page_title="Financial Modelling Group N", page_icon="📊", layout="wide")
st.title("Financial Modelling Group N")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a page", ["Overview", "Historical Financials", "Financial Forecast", "Valuation", "Scenario Analysis"])
st.header(page)
st.info("This section is under development.")
