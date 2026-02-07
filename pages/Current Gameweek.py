import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY
from core.visuals_utils import calc_defensive_points
from core.data_utils import load_data_supabase


# ======================= CONFIGURATION =======================
st.set_page_config(layout="wide")

# ======================= LOAD DATA & INIT SUPABASE =======================
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets["TOKEN_STREAMLIT"]
BUCKET = "data"  # your Supabase Storage bucket
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_supabase(supabase)  # <-- unpack all 4

#---------------- OPERATIONS ----------------
latest_gw = df["gameweek_num"].max()
latest_df = df[df["gameweek_num"] == latest_gw].copy()

# Create fixture name column (e.g. "Liverpool vs Bournemouth")
fixtures["fixture_name"] = fixtures["team_h_name"] + " vs " + fixtures["team_a_name"]


# --- 1️⃣ Merge by home team ---
merged = latest_df.merge(
    fixtures[["event", "team_h_name", "team_a_name", "fixture_name"]],
    left_on=["gameweek_num", "short_name"],
    right_on=["event", "team_h_name"],
    how="left"
)

# --- 2️⃣ Identify which rows didn’t match ---
mask_missing = merged["fixture_name"].isna()

# --- 3️⃣ Merge again for away teams, but only on those missing rows ---
away_merged = merged.loc[mask_missing, ["gameweek_num", "short_name"]].merge(
    fixtures[["event", "team_h_name", "team_a_name", "fixture_name"]],
    left_on=["gameweek_num", "short_name"],
    right_on=["event", "team_a_name"],
    how="left"
)

# --- 4️⃣ Fill fixture_name for those missing ---
merged.loc[mask_missing, "fixture_name"] = away_merged["fixture_name"].values

# --- 5️⃣ Clean up ---
latest_df = merged.drop(columns=["event", "team_h_name", "team_a_name"], errors="ignore")

print(latest_df[["short_name", "fixture_name"]].drop_duplicates().head(10))

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
    teams = fixture_df["short_name"].unique()  

    # Skip invalid or incomplete fixtures
    if len(teams) != 2:
        continue

    st.subheader(f"⚔️ {fixture}")
    col1, col2 = st.columns(2)

    for col, team in zip([col1, col2], teams):
        team_df = fixture_df[fixture_df["short_name"] == team] 
        team_df = team_df[team_df["player_position"].isin(["DEF", "MID"])]
        top5 = team_df.sort_values("total_contributions", ascending=False).head(5)

        with col:
            st.markdown(f"### {team}")
            for _, row in top5.iterrows():
                st.text(f"{row['short_name']} ({row['player_position']})")
                st.progress(row["progress"])
                st.caption(f"Total contributions: {row['total_contributions']} | Defensive points: {row['def_points']}")

