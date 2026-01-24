# menu.py
import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
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

# ========================================================================
# PAGE CONFIGURATION
# ========================================================================
st.set_page_config(page_title="FPL Draft Menu", layout="wide")

# ========================================================================
# SUPABASE CLIENT INITIALIZATION
# ========================================================================
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets.get("TOKEN_STREAMLIT")

BUCKET = "data"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if not TOKEN:
    logger.warning("GitHub token not configured")

# ========================================================================
# GITHUB ETL TRIGGER
# ========================================================================
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

# ========================================================================
# LOAD DATA
# ========================================================================
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

# ========================================================================
# CALCULATE GAMEWEEK INFO & STANDINGS
# ========================================================================
try:
    now = datetime.now(timezone.utc)
    next_gw = get_next_gameweek(gameweeks, now)
except Exception as e:
    logger.warning(f"Failed to calculate next gameweek: {str(e)}")
    display_warning("Could not calculate gameweek information")
    next_gw = pd.DataFrame()

try:
    starting = get_starting_lineup(df)
    totals = get_team_total_points(starting) if not starting.empty else pd.DataFrame()
except Exception as e:
    logger.error(f"Error calculating standings: {str(e)}")
    totals = pd.DataFrame()

# ========================================================================
# PAGE HEADER
# ========================================================================
st.markdown("# ⚽ Fantasy Premier League Draft Dashboard")
st.markdown("Comprehensive league analytics and manager performance tracking")

# ========================================================================
# KPI SUMMARY CARDS
# ========================================================================
if not standings.empty and not totals.empty:
    try:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            num_managers = len(standings)
            st.metric("📊 Managers in League", num_managers)
        
        with col2:
            if "gw_points" in totals.columns:
                avg_gw = totals["gw_points"].mean()
                st.metric("📈 Avg Points/GW", f"{avg_gw:.1f}")
            else:
                st.metric("📈 Avg Points/GW", "—")
        
        with col3:
            if "total_points" in totals.columns:
                top_points = totals["total_points"].max()
                st.metric("🥇 Top Team Points", f"{int(top_points)}")
            else:
                st.metric("🥇 Top Team Points", "—")
        
        with col4:
            if "total_points" in totals.columns:
                bottom_points = totals["total_points"].min()
                st.metric("🥈 Bottom Team Points", f"{int(bottom_points)}")
            else:
                st.metric("🥈 Bottom Team Points", "—")
    except Exception as e:
        logger.warning(f"Error displaying KPI cards: {str(e)}")

st.markdown("---")

# ========================================================================
# NAVIGATION SECTION
# ========================================================================
st.markdown("## 🗺️ Navigate to Dashboard")

# Create tabs for different navigation sections
nav_col1, nav_col2 = st.columns([1.5, 1])

with nav_col1:
    st.markdown("### 📋 League Overview & Managers")
    
    # Overall button
    if st.button("🌟 Overall League Dashboard", use_container_width=True, type="primary"):
        st.session_state["current_page"] = "Overall"
        st.switch_page("pages/Overall.py")
    
    st.markdown("**Select a manager to view individual performance:**")
    
    manager_list = sorted(standings["team_name"].unique().tolist()) if not standings.empty else []
    manager_buttons = [b for b in manager_list]
    
    if not manager_buttons:
        display_warning("No managers found in standings data")
    else:
        cols_per_row = 2
        for i in range(0, len(manager_buttons), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, name in enumerate(manager_buttons[i:i + cols_per_row]):
                with cols[j]:
                    if st.button(name, use_container_width=True):
                        st.session_state["current_page"] = name
                        st.switch_page(f"pages/{name}.py")

with nav_col2:
    st.markdown("### ⏰ Quick Info")
    
    try:
        if not next_gw.empty:
            gw_name = next_gw.iloc[0]["name"]
            deadline = next_gw.iloc[0]["deadline_time"]
            remain = deadline - now
            
            st.info(f"📅 **{gw_name}**")
            st.write(f"📍 {deadline.strftime('%a, %d %b %H:%M')}")
            
            days = remain.days
            hours = remain.seconds // 3600
            minutes = (remain.seconds % 3600) // 60
            
            st.write(f"⏳ **{days}d {hours}h {minutes}m**")
        else:
            st.info("🏁 No upcoming deadlines")
    except Exception as e:
        logger.warning(f"Failed to display deadline: {str(e)}")
        st.info("📅 Deadline info unavailable")

st.divider()

# ========================================================================
# MAIN DASHBOARD CONTENT
# ========================================================================
st.markdown("## 📊 League Standing & Upcoming Fixtures")

dashboard_col1, dashboard_col2 = st.columns([1.5, 1], gap="large")

# Left column: League standings
with dashboard_col1:
    st.markdown("### 🏆 League Table - Total Points")
    try:
        if not totals.empty:
            display_data = totals.copy()
            
            st.dataframe(
                display_data,
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            display_warning("No standings data available")
    except Exception as e:
        logger.error(f"Error displaying standings: {str(e)}")
        display_error(e, "Error displaying standings")

# Right column: Upcoming fixtures
with dashboard_col2:
    st.markdown("### 🎯 Upcoming Fixtures")
    try:
        upcoming = get_upcoming_fixtures(fixtures, next_gw) if not next_gw.empty else pd.DataFrame()
        if not upcoming.empty:
            fixture_display = upcoming[["Home", "Away", "Kickoff"]].head(10)
            st.dataframe(
                fixture_display,
                hide_index=True,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No fixtures available.")
    except Exception as e:
        logger.warning(f"Failed to get upcoming fixtures: {str(e)}")
        display_warning("Could not load fixtures")

st.divider()

# ========================================================================
# DATA VISUALIZATION: STANDINGS DISTRIBUTION & TOP PERFORMERS
# ========================================================================
try:
    if not totals.empty and "total_points" in totals.columns:
        viz_col1, viz_col2 = st.columns(2, gap="large")
        
        with viz_col1:
            st.markdown("### 📊 Points Distribution")
            
            fig = go.Figure(data=[
                go.Box(
                    y=totals["total_points"],
                    name="Total Points",
                    marker_color="lightblue",
                    boxmean="sd"
                )
            ])
            
            fig.update_layout(
                showlegend=False,
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                yaxis_title="Points",
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with viz_col2:
            st.markdown("### 🥇 Top Performers")
            
            top_teams = totals.nlargest(5, "total_points")[["team_name", "total_points"]]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=top_teams["total_points"],
                    y=top_teams["team_name"],
                    orientation="h",
                    marker=dict(
                        color=top_teams["total_points"],
                        colorscale="Viridis",
                        showscale=False
                    ),
                    text=top_teams["total_points"],
                    textposition="outside"
                )
            ])
            
            fig.update_layout(
                showlegend=False,
                height=300,
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis_title="Points",
                yaxis_title="",
                hovermode="closest"
            )
            
            st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    logger.warning(f"Error displaying visualizations: {str(e)}")

st.divider()

# ========================================================================
# DATA EXTRACTION PIPELINE CONTROL
# ========================================================================
st.markdown("## 🔄 Data Management")

pipeline_col1, pipeline_col2 = st.columns([2, 1])

with pipeline_col1:
    st.markdown("### 📥 ETL Pipeline")
    st.write("Manually trigger data extraction and synchronization from FPL API:")
    
    if st.button("▶️ Run ETL Pipeline", use_container_width=True):
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

with pipeline_col2:
    st.markdown("### ℹ️ Info")
    with st.expander("About ETL"):
        st.write(
            "The ETL pipeline fetches the latest FPL data from the official API "
            "and updates the Supabase database. This ensures all dashboard metrics "
            "reflect the most current information."
        )

st.divider()

# ========================================================================
# FOOTER: DASHBOARD INFORMATION
# ========================================================================
with st.expander("📖 Dashboard Information & Tips"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🎯 Navigation:**")
        st.write(
            "- **Overall**: View league-wide statistics and comparisons\n"
            "- **Managers**: Click any manager name to see their detailed performance\n"
            "- **Fixtures**: Check upcoming matches and defensive/bonus point stats"
        )
    
    with col2:
        st.markdown("**💡 Tips:**")
        st.write(
            "- Use filters on individual manager pages for detailed analysis\n"
            "- Check upcoming fixtures to plan your transfers\n"
            "- Run ETL Pipeline to refresh data with latest FPL updates"
        )
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("**📊 Data Source:**")
        st.write("Official Fantasy Premier League API + Supabase database")
    
    with col4:
        st.markdown("**⚙️ Last Updated:**")
        st.write(f"{datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}")

