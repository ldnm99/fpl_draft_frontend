# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY
from core.data_utils import (
    load_data_auto,
    get_manager_data,
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points,
    points_per_player_position,
    get_top_performers,
    get_player_progression
)
from core.visuals_utils import (
    display_overview,
    display_performance_trend,
    display_latest_gw,
    display_optimized_lineup,
    display_other_stats,
    display_injury_alerts,
    display_squad_pitch
)

# ======================= CONFIGURATION =======================
st.set_page_config(layout="wide")

# ======================= LOAD DATA & INIT SUPABASE =======================
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets.get("TOKEN_STREAMLIT")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_auto(supabase)

# ======================= MANAGER SELECTION =======================
manager_name = "dobradinha test"
manager_df = get_manager_data(df, manager_name) if not df.empty else pd.DataFrame()
if manager_df.empty:
    st.info(f"ℹ️ Pre-season status: Squad picks for {manager_name} will be displayed here once Gameweek 1 starts.")
    st.stop()

st.title(f"📊 {manager_name} Dashboard")

# ======================= DASHBOARD SECTIONS =======================
display_overview(manager_name, manager_df)
display_squad_pitch(manager_df)
manager_points = display_performance_trend(manager_name, df)
display_latest_gw(manager_df)
display_optimized_lineup(manager_df)
display_other_stats(manager_points, pd.DataFrame())
