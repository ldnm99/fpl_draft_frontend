# Centralised app-level constants.
# Import from here rather than defining inline in each page.
import streamlit as st

import os

OWNER = "ldnm99"
REPO = "FPL-ETL"
BUCKET = st.secrets.get("STORAGE_BUCKET") or os.getenv("STORAGE_BUCKET", "data")
SEASON_PREFIX = st.secrets.get("SEASON_PREFIX") or os.getenv("SEASON_PREFIX", "2025_2026/")

# GitHub token — stored in Streamlit secrets
TOKEN = st.secrets.get("TOKEN_STREAMLIT")
