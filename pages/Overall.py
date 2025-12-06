import streamlit as st
import pandas as pd
import plotly.express as px
from data_utils import load_data, get_starting_lineup, calculate_team_gw_points, get_teams_avg_points

# ---------------- CONFIG ----------------
st.set_page_config(page_title="FPL Draft Overall Dashboard", layout="wide")

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_all_data():
    df, standings, gameweeks, fixtures = load_data()
    return df, standings, gameweeks, fixtures

df, standings, gameweeks, fixtures = load_all_data()

# ---------------- DASHBOARD TITLE ----------------
st.title("FPL Draft Overall Dashboard")
st.write("Explore managers and gameweek stats.")

# ---------------- FILTERS ----------------
min_gw, max_gw = int(df['gw'].min()), int(df['gw'].max())
selected_gw_range = st.slider(
    "Select Gameweek Range",
    min_value=min_gw,
    max_value=max_gw,
    value=(min_gw, max_gw)
)
selected_team = st.selectbox(
    "Select Manager",
    options=[None] + sorted(df['manager_team_name'].dropna().unique())
)

# ---------------- FILTER DATA ----------------
filtered_df = df[
    (df['gw'] >= selected_gw_range[0]) &
    (df['gw'] <= selected_gw_range[1])
]
if selected_team:
    filtered_df = filtered_df[filtered_df['manager_team_name'] == selected_team]

# ---------------- TEAM POINTS ----------------
starting_players = get_starting_lineup(filtered_df)
team_gw_points   = calculate_team_gw_points(starting_players)
team_avg_points  = get_teams_avg_points(team_gw_points)

st.subheader("🏆 Team Points by Gameweek (Starting XI)")
st.dataframe(team_gw_points, use_container_width=True)

st.subheader("Average Points per Gameweek (Starting XI)")
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

# ---------------- TEAM POINTS MELTED ----------------
team_gw_points_melted = team_gw_points.reset_index().melt(
    id_vars ='manager_team_name',
    var_name='gw',
    value_name='points'
) if not team_gw_points.empty else pd.DataFrame(columns=['manager_team_name', 'gw', 'points'])

# Remove 'Total' column
team_gw_points_melted = team_gw_points_melted[team_gw_points_melted['gw'] != 'Total']
if not team_gw_points_melted.empty:
    team_gw_points_melted['gw'] = team_gw_points_melted['gw'].astype(int)
    team_gw_points_melted = team_gw_points_melted[
        (team_gw_points_melted['gw'] >= selected_gw_range[0]) &
        (team_gw_points_melted['gw'] <= selected_gw_range[1])
    ]

# ---------------- LINE & CUMULATIVE CHARTS ----------------
st.subheader("Team Points Overview")
col1, col2 = st.columns(2)

with col1:
    if not team_gw_points_melted.empty:
        fig_line = px.line(
            team_gw_points_melted,
            x='gw',
            y='points',
            color='manager_team_name',
            markers=True,
            title="Team Points per Gameweek"
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No data for the selected gameweek/manager.")

with col2:
    if not team_gw_points_melted.empty:
        team_cumsum = team_gw_points_melted.copy()
        team_cumsum['season_points'] = team_cumsum.groupby('manager_team_name')['points'].cumsum()
        fig_cumsum = px.line(
            team_cumsum,
            x='gw',
            y='season_points',
            color='manager_team_name',
            markers=True,
            title="Cumulative Team Points"
        )
        st.plotly_chart(fig_cumsum, use_container_width=True)
    else:
        st.info("No data for the selected gameweek/manager.")

# ---------------- HEATMAP & SCATTER ----------------
st.subheader("Heatmap & Scatter")
col3, col4 = st.columns(2)

heatmap_data = team_gw_points.loc[:, [c for c in team_gw_points.columns if c != 'Total']]
if not heatmap_data.empty:
    heatmap_data = heatmap_data.loc[:, heatmap_data.columns[
        (heatmap_data.columns >= selected_gw_range[0]) & 
        (heatmap_data.columns <= selected_gw_range[1])
    ]]

with col3:
    if not heatmap_data.empty:
        fig_heatmap = px.imshow(
            heatmap_data,
            labels=dict(x="Gameweek", y="Team", color="Points"),
            x=heatmap_data.columns,
            y=heatmap_data.index,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    else:
        st.info("No data for the selected gameweek/manager.")

with col4:
    if not team_gw_points_melted.empty:
        fig_scatter = px.scatter(
            team_gw_points_melted,
            labels=dict(x="Gameweek", y="Team", color="Points"),
            x='gw',
            y='manager_team_name',
            size='points',
            color='points',
            color_continuous_scale='Viridis',
            hover_data=['points'],
            
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("No data for the selected gameweek/manager.")
# ---------------- END OF DASHBOARD ----------------