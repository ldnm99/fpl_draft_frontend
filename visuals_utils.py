import streamlit as st
import plotly.express as px
import pandas as pd
from data_utils import (
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points,
    points_per_player_position,
    get_top_performers,
    get_player_progression
)

# ---------------- OVERVIEW ----------------
def display_overview(manager_name: str, manager_df: pd.DataFrame):
    st.header("🏆 Season Overview")
    starting_players = get_starting_lineup(manager_df)

    # Team points per GW
    team_gw_points = calculate_team_gw_points(starting_players)
    team_avg_points = get_teams_avg_points(team_gw_points)

    st.subheader("Team Points by Gameweek")
    st.dataframe(team_gw_points, use_container_width=True)

    if not team_avg_points.empty:
        avg_points = team_avg_points.loc[team_avg_points['team_name'] == manager_name, 'avg_points'].values[0]
        st.metric("Average Points per Gameweek", f"{avg_points:.2f}")

        # Pie chart for points distribution by position
        fig = px.pie(
            points_per_player_position(starting_players),
            names='position',
            values='gw_points',
            title="Points Distribution by Position",
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------- PERFORMANCE TREND ----------------
def display_performance_trend(manager_name: str, df: pd.DataFrame):
    st.header("📈 Points Progression")
    manager_df = df[df['manager_team_name'] == manager_name]
    starting_players = get_starting_lineup(manager_df)
    team_gw_points = calculate_team_gw_points(starting_players)

    manager_row = team_gw_points.loc[manager_name].drop('Total')
    manager_points = pd.DataFrame({'gameweek': manager_row.index.astype(int), 'manager_points': manager_row.values})

    # League average (excluding current manager)
    all_starting = get_starting_lineup(df)
    all_team_gw_points = all_starting.groupby(['manager_team_name', 'gw'])['gw_points'].sum().reset_index()
    other_teams = all_team_gw_points[all_team_gw_points['manager_team_name'] != manager_name]
    league_avg = other_teams.groupby('gw')['gw_points'].mean().reset_index().rename(columns={'gw_points':'avg_points'})

    comparison_df = manager_points.merge(league_avg, left_on='gameweek', right_on='gw', how='left')
    comparison_df.drop(columns='gw', inplace=True)
    plot_df = comparison_df.melt(id_vars='gameweek', var_name='Type', value_name='Points')

    fig = px.line(plot_df, x='gameweek', y='Points', color='Type', markers=True,
                  title=f"{manager_name} Gameweek Points vs League Average")
    fig.update_layout(xaxis=dict(dtick=1))
    fig.update_traces(line=dict(width=3))
    st.plotly_chart(fig, use_container_width=True)

    return manager_points


# ---------------- CURRENT GAMEWEEK ----------------
def display_latest_gw(manager_df: pd.DataFrame):
    st.header("🎯 Latest Gameweek Lineup")
    latest_gw = manager_df['gw'].max()
    latest_gw_df = manager_df[manager_df['gw'] == latest_gw].sort_values('team_position')

    latest_gw_df = latest_gw_df.rename(columns={
        'full_name':'Player', 'real_team':'Team', 'team_position':'Squad Position', 'gw_points':'Points'
    })

    if latest_gw_df.empty:
        st.info("No data for latest gameweek yet.")
    else:
        st.markdown(f"**Gameweek {latest_gw}**")
        st.dataframe(latest_gw_df[['Player','Team','Squad Position','Points']], use_container_width=True)


# ---------------- TOP PERFORMERS ----------------
def display_top_performers(manager_df: pd.DataFrame):
    st.header("⭐ Top Performing Players (Single Gameweek)")
    top_df = get_top_performers(manager_df)
    st.dataframe(top_df, use_container_width=True)
    return top_df


# ---------------- PLAYER PROGRESSION ----------------
def display_player_progression(manager_df: pd.DataFrame):
    st.header("📊 Player Points Over Time")
    pivot = get_player_progression(manager_df)
    fig = px.line(pivot.reset_index(), x='gw', y=pivot.columns, title="Player Points Progression")
    st.plotly_chart(fig, use_container_width=True)


#---------Defensive Contributions ---------
def calc_defensive_points(row):
    # Only Defenders and Midfielders are eligible
    if row["position"] not in ["DEF", "MID"]:
        return pd.Series({
            "def_points": 0,
            "progress": 0.0,
            "total_contributions": 0
        })
    

    contributions = row["gw_defensive_contribution"]
    threshold = 10 if row["position"] == "DEF" else 12

    earned = 2 if contributions >= threshold else 0
    progress = min(contributions / threshold, 1.0)

    return pd.Series({
        "def_points": earned,
        "progress": progress,
        "total_contributions": contributions
    })


# ---------------- OTHER STATS ----------------
def display_other_stats(manager_points: pd.DataFrame, top_performances: pd.DataFrame):
    st.header("📜 Other Stats")
    col1, col2, col3 = st.columns(3)

    best_player = top_performances.iloc[0]
    col1.metric("Top Scorer", best_player['Player'], f"{best_player['Points']} pts")

    best_gw_row = manager_points.loc[manager_points['manager_points'].idxmax()]
    worst_gw_row = manager_points.loc[manager_points['manager_points'].idxmin()]

    col2.metric("Best Gameweek", int(best_gw_row['gameweek']), f"{best_gw_row['manager_points']} pts")
    col3.metric("Toughest Gameweek", int(worst_gw_row['gameweek']), f"{worst_gw_row['manager_points']} pts")
