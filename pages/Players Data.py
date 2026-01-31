
# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY
from core.data_utils import (
    load_data_supabase,
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
    display_player_progression,
    display_other_stats
)


# ======================= CONFIGURATION =======================
st.set_page_config(layout="wide")


# ======================= LOAD DATA & INIT SUPABASE =======================
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets["TOKEN_STREAMLIT"]
BUCKET = "data"  # your Supabase Storage bucket
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_supabase(supabase)  # <-- unpack all 4

players = pd.read_csv("Data/players_data.csv")


# ---------------- DASHBOARD TITLE ------------------
st.title("FPL Draft Players Data")

# ---------------- ALL PLAYERS --------------------------
selected_player = st.selectbox("Select Player", options=[""] + sorted(players['name'].unique().tolist()))

if selected_player:
    players = players[players['name'] == selected_player]


players = players[['name','team','Total points','position','Goals Scored','Assists','CS','xG','starts','yellow_cards','red_cards','news']]
players.rename(columns={'name': 'Name', 'team': 'Team', 'Total points': 'Total Points', 'position': 'Position', 'Goals Scored': 'Goals Scored', 'Assists': 'Assists', 'CS': 'Clean Sheets', 'xG': 'xG', 'starts': 'Starts', 'yellow_cards': 'Yellow Cards', 'red_cards': 'Red Cards', 'news': 'News'}, inplace=True)

# Display filtered dataframe
st.dataframe(players, use_container_width=True)

# ---------------- FILTERS --------------------------

# Checkbox for owned players only
owned_only = st.checkbox("Show owned players")

# Checkbox for not owned players only
not_owned_only = st.checkbox("Show not owned players")

if owned_only:
    df = df[df['team_name'].notnull()]

if not_owned_only:
    df = df[df['team_name'].isnull()]

df = df[['team_name','name','team','Total points','gameweek','total_points','goals_scored','assists','bonus_x','minutes_x','expected_goals','expected_assists_x','defensive_contribution_x','position']]
df.rename(columns={'team_name': 'Manager', 'name': 'Name', 'team': 'Team', 'Total points': 'Season Points', 'gameweek': 'Gameweek', 'total_points': 'GW Points', 'goals_scored': 'GW Goals', 'assists': 'GW Assists', 'bonus_x': 'GW Bonus', 'minutes_x': 'GW Minutes', 'expected_goals': 'GW xG', 'expected_assists_x': 'GW xA', 'defensive_contribution_x': 'GW Def Contribution', 'position': 'Position'}, inplace=True)

# Display filtered dataframe
st.dataframe(df, use_container_width=True)
