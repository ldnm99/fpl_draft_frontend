# Centralised app-level constants.
# Import from here rather than defining inline in each page.
import streamlit as st

OWNER = "ldnm99"
REPO = "FPL-ETL"
BUCKET = "data"

# GitHub token — stored in Streamlit secrets
TOKEN = st.secrets.get("TOKEN_STREAMLIT")
