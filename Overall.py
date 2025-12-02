import streamlit as st
import pandas as pd
import plotly.express as px

from data_utils import (
    load_data_supabase,
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points
)

# ---------------- CONFIG ----------------
st.set_page_config(page_title="FPL Draft Overall Dashboard", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_all_data():
    return load_data_supabase()   # SUPABASE instead of local

df, standings, gameweeks, fixtures = load_all_data()

# ---------------- TITLE ----------------
st.title("🏆 FPL Draft Overall Dashboard")
st.write("Explore managers, gameweeks, and team statistics.")

# ---------------- FILTERS ----------------
min_gw = int(df["gw"].min())
max_gw = int(df["gw"].max())

selected_gw_range = st.slider(
    "Select Gameweek Range",
    min_value=min_gw,
    max_value=max_gw,
    value=(min_gw, max_gw)
)

selected_team = st.selectbox(
    "Select Manager",
    options=[None] + sorted(df["manager_team_name"].dropna().unique())
)

# ---------------- FILTER DATA ----------------
filtered_df = df[
    (df["gw"] >= selected_gw_range[0]) &
    (df["gw"] <= selected_gw_range[1])
]

if selected_team:
    filtered_df = filtered_df[filtered_df["manager_team_name"] == selected_team]

# ---------------- STARTING XI → POINTS ----------------
starting_players = get_starting_lineup(filtered_df)
team_gw_points = calculate_team_gw_points(starting_players)
team_avg_points = get_teams_avg_points(team_gw_points)

# ---------------- TABLE: TEAM GW POINTS ----------------
st.subheader("📊 Team Points per Gameweek (Starting XI)")
st.dataframe(team_gw_points, use_container_width=True)

# ---------------- AVG CARDS ----------------
st.subheader("🏅 Average Points per Gameweek")

cols = st.columns(3)
for i, row in team_avg_points.iterrows():
    with cols[i % 3]:
        st.markdown(
            f"""
            <div style="
                background-color: #1E1E1E;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                text-align: center;
                color: white;
            ">
                <div style="font-size: 2rem; font-weight: 600;">{row['avg_points']:.1f}</div>
                <div style="font-size: 1.1rem; font-weight: 500; opacity: 0.8;">{row['team_name']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------- MELT DATA ----------------
if not team_gw_points.empty:
    melted = (
        team_gw_points
        .reset_index()
        .melt(id_vars="manager_team_name", var_name="gw", value_name="points")
    )
    melted = melted[melted["gw"] != "Total"]
    melted["gw"] = melted["gw"].astype(int)

    melted = melted[
        (melted["gw"] >= selected_gw_range[0]) &
        (melted["gw"] <= selected_gw_range[1])
    ]
else:
    melted = pd.DataFrame(columns=["manager_team_name", "gw", "points"])

# ---------------- LINE CHARTS ----------------
st.subheader("📈 Team Points Overview")

col1, col2 = st.columns(2)

with col1:
    if not melted.empty:
        fig = px.line(
            melted,
            x="gw",
            y="points",
            color="manager_team_name",
            markers=True,
            title="Team Points per Gameweek"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available.")

with col2:
    if not melted.empty:
        melted["season_points"] = melted.groupby("manager_team_name")["points"].cumsum()
        fig = px.line(
            melted,
            x="gw",
            y="season_points",
            color="manager_team_name",
            markers=True,
            title="Cumulative Team Points"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available.")

# ---------------- HEATMAP & SCATTER ----------------
st.subheader("🔍 Heatmap & Scatter")
col3, col4 = st.columns(2)

heatmap_data = team_gw_points.drop(columns=["Total"], errors="ignore")

if not heatmap_data.empty:
    heatmap_data = heatmap_data[
        (heatmap_data.columns.astype(int) >= selected_gw_range[0]) &
        (heatmap_data.columns.astype(int) <= selected_gw_range[1])
    ]

with col3:
    if not heatmap_data.empty:
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Gameweek", y="Team", color="Points"),
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No heatmap data.")

with col4:
    if not melted.empty:
        fig = px.scatter(
            melted,
            x="gw",
            y="manager_team_name",
            size="points",
            color="points",
            hover_data=["points"],
            color_continuous_scale="Viridis",
            title="Points Scatter Plot"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No scatter data.")
