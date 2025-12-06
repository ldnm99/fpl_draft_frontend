# menu.py
import streamlit as st
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime, timezone
from supabase import create_client
from supabase_client import SUPABASE_URL, SUPABASE_KEY

from data_utils import (
    get_next_gameweek,
    get_upcoming_fixtures,
    get_starting_lineup,
    get_team_total_points,
    load_data_supabase
)

# --------------------------------------------------------------------
# INIT SUPABASE CLIENT
# --------------------------------------------------------------------
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets["TOKEN_STREAMLIT"]

BUCKET = "data"  # your Supabase Storage bucket
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------
st.set_page_config(page_title="FPL Draft Menu", layout="wide")

# ---------------------------------------------------------------------
# GITHUB ETL TRIGGER
# ---------------------------------------------------------------------
def trigger_pipeline():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {TOKEN}",
    }
    payload = {
        "event_type": "run_pipeline",
        "client_payload": {"triggered_by": "streamlit"}
    }

    r = requests.post(url, json=payload, headers=headers)
    return r.status_code, r.text


# ---------------------------------------------------------------------
# HEADER
# ---------------------------------------------------------------------
st.title("⚽ Fantasy Premier League Draft Dashboard")
st.markdown("### Select a page to view detailed stats")


# ---------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------
df, standings, gameweeks, fixtures = load_data_supabase(supabase)


# ---------------------------------------------------------------------
# NEXT GAMEWEEK & FIXTURES
# ---------------------------------------------------------------------
now = datetime.now(timezone.utc)
next_gw = get_next_gameweek(gameweeks, now)
upcoming = get_upcoming_fixtures(fixtures, next_gw)


# ---------------------------------------------------------------------
# PAGE NAVIGATION
# ---------------------------------------------------------------------
st.markdown("### 📋 Select a Page")

if standings.empty:
    st.error("❌ Unable to load standings from Supabase.")
    st.stop()

manager_list = sorted(standings["team_name"].unique().tolist())

if st.button("🌟 Overall", use_container_width=True, type="primary"):
    st.session_state["current_page"] = "Overall"
    st.switch_page("pages/Overall.py")

st.markdown("---")

cols_per_row = 4
for i in range(0, len(manager_list), cols_per_row):
    cols = st.columns(cols_per_row)
    for col, name in zip(cols, manager_list[i:i + cols_per_row]):
        with col:
            if st.button(name, use_container_width=True):
                st.session_state["current_page"] = name
                st.switch_page(f"pages/{name}.py")

st.divider()


# ---------------------------------------------------------------------
# DEADLINE INFO
# ---------------------------------------------------------------------
if not next_gw.empty:
    gw_name = next_gw.iloc[0]["name"]
    deadline = next_gw.iloc[0]["deadline_time"]
    remain = deadline - now

    st.markdown(
        f"### ⏰ Next Deadline: **{gw_name}** — "
        f"{deadline.strftime('%A, %d %B %Y %H:%M %Z')}"
    )
    st.write(
        f"Time remaining: **{remain.days} days, "
        f"{remain.seconds // 3600} hours, "
        f"{(remain.seconds % 3600) // 60} minutes**"
    )
else:
    st.info("🏁 No upcoming deadlines found.")


# ---------------------------------------------------------------------
# MAIN CONTENT
# ---------------------------------------------------------------------
left, right = st.columns([1.5, 1])

with left:
    st.subheader("🏆 League Table / Total Team Points")
    starting = get_starting_lineup(df)
    totals = get_team_total_points(starting)
    st.dataframe(totals, hide_index=True, use_container_width=True)

with right:
    st.subheader("⚔️ Upcoming Fixtures")
    if not upcoming.empty:
        st.dataframe(
            upcoming[["Home", "Away", "Kickoff"]],
            hide_index=True,
            use_container_width=True
        )
    else:
        st.write("No fixtures available.")


st.divider()


# ---------------------------------------------------------------------
# ETL PIPELINE CONTROL
# ---------------------------------------------------------------------
st.markdown("### 📊 Data Extraction Pipeline")

if st.button("Run ETL Pipeline"):
    with st.spinner("⏳ Triggering ETL pipeline…"):
        status, msg = trigger_pipeline()

    if status == 204:
        st.cache_data.clear()
        st.success("✅ Pipeline triggered! Data will be updated shortly.")
    else:
        st.error(f"❌ Error triggering pipeline: {status}\n{msg}")
