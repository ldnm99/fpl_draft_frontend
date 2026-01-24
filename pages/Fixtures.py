import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timezone
import base64
from pathlib import Path
import io
from core.error_handler import get_logger, validate_dataframe, safe_operation

logger = get_logger(__name__)

# --- PAGE CONFIG ---
st.set_page_config(page_title="FPL Fixtures", layout="wide")

# --- LOAD DATA ---
try:
    fixtures = pd.read_csv("Data/fixtures.csv")
    validate_dataframe(fixtures, "Fixtures")
except Exception as e:
    logger.error(f"Failed to load fixtures: {str(e)}")
    st.error(f"❌ Failed to load fixtures data: {str(e)}")
    st.stop()

# Try to load gw_data for defensive contributions and bonus analysis
gw_data = None
try:
    from config.supabase_client import get_supabase_client
    from core.data_utils import load_data_supabase
    supabase = get_supabase_client()
    df, _, _, _ = load_data_supabase(supabase)
    gw_data = df
    logger.info(f"Loaded gw_data with {len(gw_data)} rows for performance analysis")
except Exception as e:
    logger.warning(f"Could not load gw_data for performance analysis: {str(e)}")
    gw_data = None

# --- TEAM MAPPINGS ---
teams = {
        1: "Arsenal", 2: "Aston Villa", 3: "Burnley", 4: "Bournemouth",
        5: "Brentford", 6: "Brighton", 7: "Chelsea", 8: "Crystal Palace",
        9: "Everton", 10: "Fulham", 11: "Leeds United", 12: "Liverpool",
        13: "Manchester City", 14: "Manchester United", 15: "Newcastle United",
        16: "Nottingham Forest", 17: "Sunderland", 18: "Tottenham",
        19: "West Ham", 20: "Wolverhampton"
    }

fixtures["team_h_name"] = fixtures["team_h"].map(teams)
fixtures["team_a_name"] = fixtures["team_a"].map(teams)
fixtures["kickoff_time"] = pd.to_datetime(fixtures["kickoff_time"], utc=True)

# --- BASE64 ENCODING FOR BADGES ---
def img_to_base64(path):
    if not Path(path).exists():
        return ""
    with open(path, "rb") as f:
        data = f.read()
    return "data:image/png;base64," + base64.b64encode(data).decode()

team_badges = {team: img_to_base64(f"assets/badges/{team}.png") for team in teams.values()}

# --- DIFFICULTY FUNCTIONS ---
def difficulty_emoji(difficulty):
    if difficulty <= 2: return "🟢"
    elif difficulty == 3: return "🟡"
    elif difficulty == 4: return "🟠"
    else: return "🔴"

def difficulty_bg_color(difficulty):
    if difficulty <= 2: return "#6ebd2e"
    elif difficulty == 3: return "#dadab57a"
    elif difficulty == 4: return "#EE3000"
    else: return "#793131"

# --- HELPER FUNCTIONS FOR PERFORMANCE ANALYSIS ---
def get_top_defensive_players(gw_data, home_team_id, away_team_id, gw):
    """Get top 3 defensive contribution players for each team in a match."""
    if gw_data is None:
        return None, None
    
    try:
        gw_match_data = gw_data[gw_data["gw"] == gw].copy()
        
        # Get home team players (top 3 by defensive contribution)
        home_players = gw_match_data[gw_match_data["manager_team_id"] == home_team_id].copy()
        home_top = home_players.nlargest(3, "gw_defensive_contribution")[
            ["short_name", "position", "gw_defensive_contribution", "real_team"]
        ].reset_index(drop=True)
        
        # Get away team players (top 3 by defensive contribution)
        away_players = gw_match_data[gw_match_data["manager_team_id"] == away_team_id].copy()
        away_top = away_players.nlargest(3, "gw_defensive_contribution")[
            ["short_name", "position", "gw_defensive_contribution", "real_team"]
        ].reset_index(drop=True)
        
        return home_top, away_top
    except Exception as e:
        logger.error(f"Error getting defensive players for GW {gw}: {str(e)}")
        return None, None


def get_top_bonus_players(gw_data, home_team_id, away_team_id, gw):
    """Get top 3 bonus points (BPS) players for each team in a match."""
    if gw_data is None:
        return None, None
    
    try:
        gw_match_data = gw_data[gw_data["gw"] == gw].copy()
        
        # Get home team players (top 3 by bonus points)
        home_players = gw_match_data[gw_match_data["manager_team_id"] == home_team_id].copy()
        home_top = home_players.nlargest(3, "gw_bps")[
            ["short_name", "position", "gw_bps", "gw_bonus", "real_team"]
        ].reset_index(drop=True)
        
        # Get away team players (top 3 by bonus points)
        away_players = gw_match_data[gw_match_data["manager_team_id"] == away_team_id].copy()
        away_top = away_players.nlargest(3, "gw_bps")[
            ["short_name", "position", "gw_bps", "gw_bonus", "real_team"]
        ].reset_index(drop=True)
        
        return home_top, away_top
    except Exception as e:
        logger.error(f"Error getting bonus players for GW {gw}: {str(e)}")
        return None, None

# --- INDIVIDUAL FIXTURES ---
gameweeks = sorted(fixtures["event"].dropna().unique())
selected_gw = st.selectbox("Select Gameweek", gameweeks)
gw_fixtures = fixtures[fixtures["event"] == selected_gw].copy()
gw_fixtures["Kickoff"] = gw_fixtures["kickoff_time"].dt.strftime("%A, %d %B %H:%M")

st.title(f"⚽ Fixtures – Gameweek {selected_gw}")
for idx, (_, row) in enumerate(gw_fixtures.iterrows()):
    col1, col2, col3, col4, col5 = st.columns([1,2,1,2,1])
    with col1: st.image(team_badges[row['team_h_name']], width=50)
    with col2: st.markdown(f"**{row['team_h_name']}** {difficulty_emoji(row['team_h_difficulty'])}")
    with col3: st.markdown("**vs**")
    with col4: st.markdown(f"{difficulty_emoji(row['team_a_difficulty'])} **{row['team_a_name']}**")
    with col5: st.image(team_badges[row['team_a_name']], width=50)
    st.write(f"🕒 Kickoff: {row['Kickoff']}")
    
    # Expandable sections for performance data
    col_perf1, col_perf2 = st.columns(2)
    
    with col_perf1:
        with st.expander(f"🛡️ Top Defenders - {row['team_h_name']} vs {row['team_a_name']}"):
            home_def, away_def = get_top_defensive_players(
                gw_data, 
                int(row['team_h']), 
                int(row['team_a']), 
                int(selected_gw)
            )
            
            if home_def is not None and not home_def.empty:
                st.markdown(f"**{row['team_h_name']} - Top Defenders**")
                home_def_display = home_def.copy()
                home_def_display.columns = ["Player", "Position", "Def. Contributions", "Team"]
                st.dataframe(home_def_display, use_container_width=True, hide_index=True)
            
            if away_def is not None and not away_def.empty:
                st.markdown(f"**{row['team_a_name']} - Top Defenders**")
                away_def_display = away_def.copy()
                away_def_display.columns = ["Player", "Position", "Def. Contributions", "Team"]
                st.dataframe(away_def_display, use_container_width=True, hide_index=True)
            
            if home_def is None:
                st.info("📊 Performance data not available for this gameweek yet")
    
    with col_perf2:
        with st.expander(f"⭐ Bonus Points (BPS) - {row['team_h_name']} vs {row['team_a_name']}"):
            home_bonus, away_bonus = get_top_bonus_players(
                gw_data, 
                int(row['team_h']), 
                int(row['team_a']), 
                int(selected_gw)
            )
            
            if home_bonus is not None and not home_bonus.empty:
                st.markdown(f"**{row['team_h_name']} - Top BPS Scorers**")
                home_bonus_display = home_bonus.copy()
                home_bonus_display.columns = ["Player", "Position", "BPS", "Bonus Points", "Team"]
                st.dataframe(home_bonus_display, use_container_width=True, hide_index=True)
            
            if away_bonus is not None and not away_bonus.empty:
                st.markdown(f"**{row['team_a_name']} - Top BPS Scorers**")
                away_bonus_display = away_bonus.copy()
                away_bonus_display.columns = ["Player", "Position", "BPS", "Bonus Points", "Team"]
                st.dataframe(away_bonus_display, use_container_width=True, hide_index=True)
            
            if home_bonus is None:
                st.info("📊 Performance data not available for this gameweek yet")
    
    st.markdown("---")

# --- TABLE DATA ---
teams_list = sorted(teams.values())
table_data = pd.DataFrame(index=teams_list, columns=gameweeks)
difficulty_data = pd.DataFrame(index=teams_list, columns=gameweeks)
badge_data = pd.DataFrame(index=teams_list, columns=gameweeks)

for _, row in fixtures.iterrows():
    gw = row["event"]
    home, away = row["team_h_name"], row["team_a_name"]
    table_data.loc[home, gw] = f"{away} (h)"
    difficulty_data.loc[home, gw] = row["team_h_difficulty"]
    badge_data.loc[home, gw] = team_badges[away]
    table_data.loc[away, gw] = f"{home} (a)"
    difficulty_data.loc[away, gw] = row["team_a_difficulty"]
    badge_data.loc[away, gw] = team_badges[home]

# --- NEXT UPCOMING GAMEWEEK ---
now = datetime.now(timezone.utc)
upcoming_fixtures = fixtures[fixtures["kickoff_time"] >= now]
next_gw = upcoming_fixtures["event"].min() if not upcoming_fixtures.empty else max(gameweeks)

filtered_gameweeks = [gw for gw in gameweeks if gw >= next_gw]
filtered_table_data = table_data[filtered_gameweeks]
filtered_difficulty_data = difficulty_data[filtered_gameweeks]
filtered_badge_data = badge_data[filtered_gameweeks]

# --- BUILD HTML TABLE WITH TEAM BADGES ONLY IN FIRST COLUMN ---
html = """
<div style='overflow-x:auto; overflow-y:auto; height:1350px; padding:10px;'>
<table style='border-collapse:collapse; width:100%; font-size:16px;'>
<tr>
<th style='border:1px solid #ddd; padding:8px; color:white; background-color:#111;'>Team</th>
"""

# Header GW columns
for gw in filtered_gameweeks:
    html += f"<th style='border:1px solid #ddd; padding:8px; color:white; background-color:#111;'>GW{int(gw)}</th>"
html += "</tr>"

# Data rows
for team in filtered_table_data.index:
    team_badge = team_badges[team]  # Only in first column
    html += f"""
    <tr>
        <td style='border:1px solid #ddd; padding:8px; font-weight:bold; color:white; background-color:#111'>
            <img src='{team_badge}' width='30' style='vertical-align:middle;'> {team}
        </td>
    """
    for gw in filtered_gameweeks:
        cell = filtered_table_data.loc[team, gw]
        if pd.isna(cell):
            html += "<td style='border:1px solid #ddd; padding:8px; text-align:center; color:white; background-color:#000'>-</td>"
        else:
            color = difficulty_bg_color(filtered_difficulty_data.loc[team, gw])
            html += f"<td style='border:1px solid #ddd; padding:8px; text-align:center; background-color:{color}; color:#000; vertical-align:middle'>{cell}</td>"
    html += "</tr>"

html += "</table></div>"
components.html(html, height=1500, scrolling=True)

