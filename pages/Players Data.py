
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
    display_other_stats,
    display_player_clustering,
    display_player_trends,
    display_consistency_analysis,
    display_player_archetypes_analysis
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


# ======================= PAGE TITLE =======================
st.title("📊 FPL Players Data Analysis")
st.markdown("Comprehensive data science analysis of player performance, trends, and archetypes")

# ======================= TABS =======================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Player Data", 
    "🎯 Clustering Analysis", 
    "📈 Trend Analysis",
    "🎭 Archetypes",
    "📊 Consistency"
])

# ======================= TAB 1: PLAYER DATA =======================
with tab1:
    st.header("Player Data Overview")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.subheader("All Players (Season Summary)")
        
        # Player selection
        selected_player = st.selectbox("Select Player", options=[""] + sorted(players['name'].unique().tolist()))
        
        if selected_player:
            filtered_players = players[players['name'] == selected_player]
        else:
            filtered_players = players.copy()
        
        filtered_players = filtered_players[['name','team','Total points','position','Goals Scored','Assists','CS','xG','starts','yellow_cards','red_cards','news']]
        filtered_players.rename(columns={'name': 'Name', 'team': 'Team', 'Total points': 'Total Points', 'position': 'Position', 'Goals Scored': 'Goals Scored', 'Assists': 'Assists', 'CS': 'Clean Sheets', 'xG': 'xG', 'starts': 'Starts', 'yellow_cards': 'Yellow Cards', 'red_cards': 'Red Cards', 'news': 'News'}, inplace=True)
        
        st.dataframe(filtered_players, use_container_width=True)
    
    with col2:
        st.subheader("Gameweek Performance Data")
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            owned_only = st.checkbox("Show owned players")
        with col_f2:
            not_owned_only = st.checkbox("Show not owned players")
        
        # Filter logic
        filtered_df = df.copy()
        
        if owned_only:
            filtered_df = filtered_df[filtered_df['team_name'].notnull()]
        
        if not_owned_only:
            filtered_df = filtered_df[filtered_df['team_name'].isnull()]
        
        filtered_df = filtered_df[['team_name','full_name','real_team','gw_points','gw','total_points','goals_scored','assists','gw_bonus','minutes','expected_goals','expected_assists','position']]
        filtered_df.rename(columns={'team_name': 'Manager', 'full_name': 'Name', 'real_team': 'Team', 'gw_points': 'GW Points', 'gw': 'Gameweek', 'total_points': 'Season Points', 'goals_scored': 'GW Goals', 'assists': 'GW Assists', 'gw_bonus': 'GW Bonus', 'minutes': 'GW Minutes', 'expected_goals': 'GW xG', 'expected_assists': 'GW xA', 'position': 'Position'}, inplace=True)
        
        st.dataframe(filtered_df, use_container_width=True, height=400)

# ======================= TAB 2: CLUSTERING =======================
with tab2:
    display_player_clustering(df)

# ======================= TAB 3: TRENDS =======================
with tab3:
    display_player_trends(df)

# ======================= TAB 4: ARCHETYPES =======================
with tab4:
    display_player_archetypes_analysis(df)

# ======================= TAB 5: CONSISTENCY =======================
with tab5:
    display_consistency_analysis(df)

