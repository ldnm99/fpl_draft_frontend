# supabase.py
from supabase import create_client
import streamlit as st
import os

# Use st.secrets when available (Streamlit Cloud), fallback to env vars (local/CI)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except (FileNotFoundError, KeyError):
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError(
        "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY "
        "in Streamlit secrets or as environment variables."
    )

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
