import streamlit as st
import pandas as pd
import plotly.express as px

from visuals_utils import calc_defensive_points

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide")
GW_DATA_PATH   = "Data/gw_data.parquet"
STANDINGS_PATH = "Data/league_standings.csv"
FIXTURES_PATH = "Data/fixtures.csv"
fixtures = pd.read_csv(FIXTURES_PATH)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    df = pd.read_parquet(GW_DATA_PATH)
    standings = pd.read_csv(STANDINGS_PATH)
    return df, standings

df, standings = load_data()

#---------------- OPERATIONS ----------------
latest_gw = df["gw"].max()
latest_df = df[df["gw"] == latest_gw].copy()

# Create fixture name column (e.g. "Liverpool vs Bournemouth")
fixtures["fixture_name"] = fixtures["team_h_name"] + " vs " + fixtures["team_a_name"]


# --- 1️⃣ Merge by home team ---
merged = latest_df.merge(
    fixtures[["event", "team_h_name", "team_a_name", "fixture_name"]],
    left_on=["gw", "real_team"],
    right_on=["event", "team_h_name"],
    how="left"
)

# --- 2️⃣ Identify which rows didn’t match ---
mask_missing = merged["fixture_name"].isna()

# --- 3️⃣ Merge again for away teams, but only on those missing rows ---
away_merged = merged.loc[mask_missing, ["gw", "real_team"]].merge(
    fixtures[["event", "team_h_name", "team_a_name", "fixture_name"]],
    left_on=["gw", "real_team"],
    right_on=["event", "team_a_name"],
    how="left"
)

# --- 4️⃣ Fill fixture_name for those missing ---
merged.loc[mask_missing, "fixture_name"] = away_merged["fixture_name"].values

# --- 5️⃣ Clean up ---
latest_df = merged.drop(columns=["event", "team_h_name", "team_a_name"], errors="ignore")

print(latest_df[["real_team", "fixture_name"]].drop_duplicates().head(10))

latest_df[["def_points", "progress", "total_contributions"]] = latest_df.apply(calc_defensive_points, axis=1)
# ---------------- DASHBOARD TITLE ------------------
st.title(f"FPL Draft Current Gameweek {latest_gw}")

st.subheader("🛡️ Defensive Contributions Points")

st.write("""
Players can earn **up to 2 extra points** for defensive actions:  
- **Defenders:** 2 points if DEFCON ≥ 10  
- **Midfielders:** 2 points if DEFCON ≥ 12  
         
All defensive actions also contribute to **Bonus Points System (BPS)**.
""")

# ---------------- SHOW TOP 5 PER TEAM PER MATCH ----------------
st.header(f"🛡️ Defensive Contributions - Gameweek {latest_gw}")

for fixture in latest_df["fixture_name"].unique():
    fixture_df = latest_df[latest_df["fixture_name"] == fixture]
    teams = fixture_df["real_team"].unique()  

    # Skip invalid or incomplete fixtures
    if len(teams) != 2:
        continue

    st.subheader(f"⚔️ {fixture}")
    col1, col2 = st.columns(2)

    for col, team in zip([col1, col2], teams):
        team_df = fixture_df[fixture_df["real_team"] == team] 
        team_df = team_df[team_df["position"].isin(["DEF", "MID"])]
        top5 = team_df.sort_values("total_contributions", ascending=False).head(5)

        with col:
            st.markdown(f"### {team}")
            for _, row in top5.iterrows():
                st.text(f"{row['short_name']} ({row['position']})")
                st.progress(row["progress"])
                st.caption(f"Total contributions: {row['total_contributions']} | Defensive points: {row['def_points']}")
