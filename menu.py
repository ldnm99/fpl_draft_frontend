# menu.py
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY

from core.data_utils import (
    get_next_gameweek,
    get_upcoming_fixtures,
    get_starting_lineup,
    get_team_total_points,
    load_data_supabase
)
from core.error_handler import (
    display_error,
    display_warning,
    display_info,
    get_logger
)

logger = get_logger(__name__)

# --------------------------------------------------------------------
# INIT SUPABASE CLIENT
# --------------------------------------------------------------------
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets.get("TOKEN_STREAMLIT")

BUCKET = "data"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if not TOKEN:
    logger.warning("GitHub token not configured")

# -----
# CONFIG
# -----
st.set_page_config(page_title="FPL Draft Menu", layout="wide")

# -----
# GITHUB ETL TRIGGER
# -----
def trigger_pipeline():
    """Trigger ETL pipeline with error handling."""
    try:
        if not TOKEN:
            raise ValueError("GitHub token not configured")
        
        url = f"https://api.github.com/repos/{OWNER}/{REPO}/dispatches"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
        }
        payload = {
            "event_type": "run_pipeline",
            "client_payload": {"triggered_by": "streamlit"}
        }

        logger.info("Triggering ETL pipeline")
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if r.status_code == 204:
            logger.info("ETL pipeline triggered successfully")
            return r.status_code, "Pipeline triggered"
        else:
            logger.error(f"Pipeline trigger failed: {r.status_code}")
            return r.status_code, r.text
            
    except requests.exceptions.Timeout:
        logger.error("GitHub API request timed out")
        raise Exception("GitHub request timed out. Check your internet connection.")
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub API request failed: {str(e)}")
        raise Exception(f"Failed to reach GitHub API: {str(e)}")
    except Exception as e:
        logger.error(f"Pipeline trigger failed: {str(e)}")
        raise

# -----
# HEADER
# -----
st.title("⚽ Fantasy Premier League Draft Dashboard")
st.markdown("### Select a page to view detailed stats")

# -----
# LOAD DATA
# -----
df = None
standings = None
gameweeks = None
fixtures = None

with st.spinner("📊 Loading data..."):
    try:
        df, standings, gameweeks, fixtures = load_data_supabase(supabase)
        display_info("✅ Data loaded successfully")
    except Exception as e:
        display_error(e, "Failed to load data")
        st.stop()

# Verify data loaded
if df is None or df.empty:
    display_warning("No player data available")
    st.stop()

if standings is None or standings.empty:
    display_warning("No standings data available")

if gameweeks is None or gameweeks.empty:
    display_warning("No gameweeks data available")
    st.stop()

if fixtures is None or fixtures.empty:
    display_warning("No fixtures data available")

# -----
# NEXT GAMEWEEK & FIXTURES
# -----
try:
    now = datetime.now(timezone.utc)
    next_gw = get_next_gameweek(gameweeks, now)
except Exception as e:
    logger.warning(f"Failed to calculate next gameweek: {str(e)}")
    display_warning("Could not calculate gameweek information")
    next_gw = pd.DataFrame()

# -----
# PAGE NAVIGATION
# -----
st.markdown("### 📋 Select a Page")

manager_list = sorted(standings["team_name"].unique().tolist()) if not standings.empty else []
buttons = ["Overall"] + manager_list

# Overall button
if st.button("🌟 Overall", use_container_width=True, type="primary"):
    st.session_state["current_page"] = "Overall"
    st.switch_page("pages/Overall.py")

st.markdown("---")

# Manager buttons (4 per row)
cols_per_row = 4
manager_buttons = [b for b in buttons if b != "Overall"]

if not manager_buttons:
    display_warning("No managers found in standings data")
else:
    for i in range(0, len(manager_buttons), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, name in enumerate(manager_buttons[i:i + cols_per_row]):
            with cols[j]:
                if st.button(name, use_container_width=True):
                    st.session_state["current_page"] = name
                    st.switch_page(f"pages/{name}.py")

st.divider()

# -----
# DEADLINE INFO
# -----
try:
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
        display_info("🏁 No upcoming deadlines found.")
except Exception as e:
    logger.warning(f"Failed to display deadline: {str(e)}")
    display_warning("Could not display deadline information")

# -----
# MAIN CONTENT
# -----
try:
    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("🏆 League Table / Total Team Points")
        try:
            starting = get_starting_lineup(df)
            if not starting.empty:
                totals = get_team_total_points(starting)
                st.dataframe(totals, hide_index=True, use_container_width=True)
            else:
                display_warning("No player data for standings")
        except Exception as e:
            logger.error(f"Error displaying standings: {str(e)}")
            display_error(e, "Error displaying standings")

    with right:
        st.subheader("⚔️ Upcoming Fixtures")
        try:
            upcoming = get_upcoming_fixtures(fixtures, next_gw) if not next_gw.empty else pd.DataFrame()
            if not upcoming.empty:
                st.dataframe(
                    upcoming[["Home", "Away", "Kickoff"]],
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.write("No fixtures available.")
        except Exception as e:
            logger.warning(f"Failed to get upcoming fixtures: {str(e)}")
            st.write("Could not load fixtures")

except Exception as e:
    logger.error(f"Error displaying main content: {str(e)}")
    display_error(e, "Error displaying dashboard content")

st.divider()

# -----
# ETL PIPELINE CONTROL
# -----
st.markdown("### 📊 Data Extraction Pipeline")

if st.button("Run ETL Pipeline"):
    try:
        with st.spinner("⏳ Triggering ETL pipeline…"):
            status, msg = trigger_pipeline()

        if status == 204:
            st.cache_data.clear()
            st.success("✅ Pipeline triggered! Data will be updated shortly.")
            logger.info("Pipeline triggered successfully")
        else:
            display_error(
                Exception(f"Status {status}: {msg}"),
                "Error triggering pipeline"
            )
    except Exception as e:
        display_error(e, "Failed to trigger ETL pipeline")
