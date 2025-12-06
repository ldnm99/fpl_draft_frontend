import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
GW_DATA_PATH   = "Data/gw_data.parquet"
STANDINGS_PATH = "Data/league_standings.csv"

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_parquet(GW_DATA_PATH)
    standings = pd.read_csv(STANDINGS_PATH)
    return df, standings

df, standings = load_data()
# ---------------- LOAD PLAYERS DATA ----------------
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