import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime, timezone
from pathlib import Path
import base64

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="FPL Fixtures", layout="wide")

# -------------------------------------------------
# LOAD FIXTURES
# -------------------------------------------------
fixtures = pd.read_csv("Data/fixtures.csv")

# -------------------------------------------------
# TEAM MAPPINGS
# -------------------------------------------------
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

# -------------------------------------------------
# BADGE LOADER
# -------------------------------------------------
def img_to_base64(path: str) -> str:
    path_obj = Path(path)
    if not path_obj.exists():
        return ""
    return (
        "data:image/png;base64,"
        + base64.b64encode(path_obj.read_bytes()).decode()
    )

team_badges = {
    team: img_to_base64(f"badges/{team}.png")
    for team in teams.values()
}

# -------------------------------------------------
# DIFFICULTY VISUALS
# -------------------------------------------------
def difficulty_emoji(difficulty: int) -> str:
    if difficulty <= 2: return "🟢"
    if difficulty == 3: return "🟡"
    if difficulty == 4: return "🟠"
    return "🔴"

def difficulty_bg_color(difficulty: int) -> str:
    if difficulty <= 2: return "#6ebd2e"     # green
    if difficulty == 3: return "#dadab57a"   # yellow
    if difficulty == 4: return "#EE3000"     # orange
    return "#793131"                        # red

# -------------------------------------------------
# SELECT GAMEWEEK (TOP FIXTURE LIST)
# -------------------------------------------------
gameweeks = sorted(fixtures["event"].dropna().unique())
selected_gw = st.selectbox("Select Gameweek", gameweeks)

gw_fixtures = fixtures[fixtures["event"] == selected_gw].copy()
gw_fixtures["Kickoff"] = gw_fixtures["kickoff_time"].dt.strftime("%A, %d %B %H:%M")

# -------------------------------------------------
# DISPLAY INDIVIDUAL FIXTURES
# -------------------------------------------------
st.title(f"⚽ Fixtures — Gameweek {selected_gw}")

for _, row in gw_fixtures.iterrows():
    col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 1])

    with col1:
        st.image(team_badges[row["team_h_name"]], width=50)

    with col2:
        st.markdown(f"**{row['team_h_name']}** {difficulty_emoji(row['team_h_difficulty'])}")

    with col3:
        st.markdown("**vs**")

    with col4:
        st.markdown(f"{difficulty_emoji(row['team_a_difficulty'])} **{row['team_a_name']}**")

    with col5:
        st.image(team_badges[row["team_a_name"]], width=50)

    st.write(f"🕒 Kickoff: {row['Kickoff']}")
    st.markdown("---")

# -------------------------------------------------
# BUILD FIXTURE MATRIX
# -------------------------------------------------
teams_list = sorted(teams.values())

table_data = pd.DataFrame(index=teams_list, columns=gameweeks)
difficulty_data = pd.DataFrame(index=teams_list, columns=gameweeks)

for _, row in fixtures.iterrows():
    gw = row["event"]
    home, away = row["team_h_name"], row["team_a_name"]

    # Home
    table_data.loc[home, gw] = f"{away} (h)"
    difficulty_data.loc[home, gw] = row["team_h_difficulty"]

    # Away
    table_data.loc[away, gw] = f"{home} (a)"
    difficulty_data.loc[away, gw] = row["team_a_difficulty"]

# -------------------------------------------------
# UPCOMING GWs FILTER
# -------------------------------------------------
now = datetime.now(timezone.utc)

future_fixtures = fixtures[fixtures["kickoff_time"] >= now]
next_gw = (
    future_fixtures["event"].min()
    if not future_fixtures.empty
    else max(gameweeks)
)

filtered_gws = [gw for gw in gameweeks if gw >= next_gw]
filtered_table = table_data[filtered_gws]
filtered_difficulty = difficulty_data[filtered_gws]

# -------------------------------------------------
# BUILD HTML MATRIX
# -------------------------------------------------
html = """
<div style='overflow-x:auto; height:1350px; padding:10px;'>
<table style='border-collapse:collapse; width:100%; font-size:16px;'>
<tr>
    <th style='border:1px solid #ddd; padding:8px; color:white; background-color:#111;'>Team</th>
"""

# Header row
for gw in filtered_gws:
    html += (
        f"<th style='border:1px solid #ddd; padding:8px; color:white; background-color:#111;'>"
        f"GW{int(gw)}</th>"
    )
html += "</tr>"

# Data rows
for team in filtered_table.index:
    badge = team_badges[team]

    html += (
        "<tr>"
        f"<td style='border:1px solid #ddd; padding:8px; background-color:#111; color:white; font-weight:bold;'>"
        f"<img src='{badge}' width='30' style='vertical-align:middle;'> {team}"
        "</td>"
    )

    for gw in filtered_gws:
        cell = filtered_table.loc[team, gw]

        if pd.isna(cell):
            html += (
                "<td style='border:1px solid #ddd; padding:8px; background-color:#000; color:white; text-align:center;'>-</td>"
            )
        else:
            diff = filtered_difficulty.loc[team, gw]
            bg = difficulty_bg_color(diff)

            html += (
                f"<td style='border:1px solid #ddd; padding:8px; background-color:{bg}; "
                f"color:black; text-align:center; vertical-align:middle;'>{cell}</td>"
            )

    html += "</tr>"

html += "</table></div>"

components.html(html, height=1500, scrolling=True)
