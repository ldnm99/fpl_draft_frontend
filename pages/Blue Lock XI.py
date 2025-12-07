import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from supabase_client import SUPABASE_URL, SUPABASE_KEY

from data_utils import (
    load_data_supabase,
    get_manager_data,
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points,
    points_per_player_position,
    get_top_performers,
    get_player_progression
)
from supabase_client import SUPABASE_KEY
from visuals_utils import (
    display_overview,
    display_performance_trend,
    display_latest_gw,
    display_top_performers,
    display_player_progression,
    display_other_stats
)

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
GW_DATA_PATH   = "Data/gw_data.parquet"
STANDINGS_PATH = "Data/league_standings.csv"
GAMEWEEKS_PATH = "Data/gameweeks.csv"
FIXTURES_PATH  = "Data/fixtures.csv"

# ---------------- LOAD DATA ----------------
# --------------------------------------------------------------------
# INIT SUPABASE CLIENT
# --------------------------------------------------------------------
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets["TOKEN_STREAMLIT"]

BUCKET = "data"  # your Supabase Storage bucket
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_supabase()  # <-- unpack all 4

# ---------------- MANAGER SELECTION ----------------
manager_name = "Blue Lock XI"
manager_df = get_manager_data(df, manager_name)
if manager_df.empty:
    st.error("⚠️ Manager not found in data")
    st.stop()

st.title(f"📊 {manager_name} Dashboard")

# ---------------- OVERVIEW ----------------
display_overview(manager_name, manager_df)

# ---------------- TEAM PERFORMANCE TREND ----------------
manager_points = display_performance_trend(manager_name, df)

# ---------------- CURRENT GAMEWEEK ----------------
display_latest_gw(manager_df)

# ---------------- TOP PERFORMERS ----------------
top_performances = display_top_performers(manager_df)

# ---------------- PLAYER PROGRESSION ----------------
display_player_progression(manager_df)

# ---------------- OTHER STATS ----------------
display_other_stats(manager_points, top_performances)
