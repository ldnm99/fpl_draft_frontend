import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from core.data_utils import (
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points,
    points_per_player_position,
    get_top_performers,
    get_player_progression,
    get_optimal_lineup,
    get_all_optimal_lineups,
    get_league_optimized_lineups,
    cluster_players,
    analyze_player_trend,
    calculate_player_consistency,
    prepare_player_metrics,
    get_player_archetypes
)
from core.injury_utils import (
    get_squad_status,
    get_at_risk_players,
    get_injury_summary
)

# ============================================================
#                    STYLING & CONFIGURATION
# ============================================================

def apply_metric_styling():
    """Apply consistent styling to metrics"""
    st.markdown("""
    <style>
    [data-testid="metric-container"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 20px;
        border-left: 4px solid #1f77b4;
    }
    </style>
    """, unsafe_allow_html=True)


def create_summary_card(label: str, value: str, subtext: str = "", icon: str = ""):
    """Create a styled summary card"""
    return f"""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="font-size: 12px; opacity: 0.9;">{label}</div>
        <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{icon} {value}</div>
        {f'<div style="font-size: 11px; opacity: 0.8;">{subtext}</div>' if subtext else ''}
    </div>
    """


# ============================================================
#                    OVERVIEW SECTION
# ============================================================

def display_overview(manager_name: str, manager_df: pd.DataFrame):
    """Enhanced overview with better layout and interactivity"""
    st.header("🏆 Season Overview", divider="rainbow")
    
    starting_players = get_starting_lineup(manager_df)
    team_gw_points = calculate_team_gw_points(starting_players)
    team_avg_points = get_teams_avg_points(team_gw_points)
    
    # --- KPI Cards Row ---
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    if not team_avg_points.empty:
        avg_points = team_avg_points.loc[
            team_avg_points['team_name'] == manager_name, 'avg_points'
        ].values[0]
        total_points = team_gw_points.loc[manager_name, 'Total']
        max_gw = team_gw_points.loc[manager_name].drop('Total').max()
        min_gw = team_gw_points.loc[manager_name].drop('Total').min()
    else:
        avg_points = 0
        total_points = 0
        max_gw = 0
        min_gw = 0
    
    col1.metric("📊 Total Season Points", f"{total_points:.0f}", 
                delta=f"Avg: {avg_points:.2f}/GW", delta_color="off")
    col2.metric("📈 Average Points/GW", f"{avg_points:.2f}", 
                delta="Per Gameweek", delta_color="off")
    col3.metric("🔥 Best GW Score", f"{max_gw:.0f}", 
                delta=f"vs Avg", delta_color="inverse")
    col4.metric("❄️ Worst GW Score", f"{min_gw:.0f}", 
                delta=f"vs Avg", delta_color="inverse")
    
    st.markdown("---")
    
    # --- Tabbed interface for detailed data ---
    tab1, tab2, tab3 = st.tabs(["📊 Gameweek Breakdown", "📍 Position Distribution", "📈 Trend"])
    
    with tab1:
        col_data, col_chart = st.columns([1, 1], gap="large")
        with col_data:
            st.subheader("Points by Gameweek")
            # Show only current manager's row as a table
            manager_row = team_gw_points.loc[[manager_name]]
            st.dataframe(
                manager_row, 
                use_container_width=True,
                height=100
            )
        with col_chart:
            st.subheader("Visual Breakdown")
            # Create bar chart for weekly points
            gw_data = team_gw_points.loc[manager_name].drop('Total').reset_index()
            gw_data.columns = ['Gameweek', 'Points']
            gw_data['Gameweek'] = gw_data['Gameweek'].astype(int)
            
            fig = px.bar(
                gw_data, 
                x='Gameweek', 
                y='Points',
                title="Weekly Points Distribution",
                color='Points',
                color_continuous_scale='Viridis',
                text='Points'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                height=400,
                showlegend=False,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, key="overview_bar")
    
    with tab2:
        col_positions, col_positions_chart = st.columns([1, 1], gap="large")
        with col_positions:
            st.subheader("Points by Position")
            pos_df = points_per_player_position(starting_players)
            st.dataframe(pos_df, use_container_width=True, hide_index=True)
        
        with col_positions_chart:
            st.subheader("Position Breakdown")
            fig = px.pie(
                pos_df,
                names='position',
                values='gw_points',
                title="Points Distribution by Position",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.3
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True, key="overview_pie")
    
    with tab3:
        st.subheader("Season Trend Analysis")
        gw_data = team_gw_points.loc[manager_name].drop('Total').reset_index()
        gw_data.columns = ['Gameweek', 'Points']
        gw_data['Gameweek'] = gw_data['Gameweek'].astype(int)
        
        # Add moving average
        gw_data['Moving Avg (3GW)'] = gw_data['Points'].rolling(window=3, center=True).mean()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=gw_data['Gameweek'],
            y=gw_data['Points'],
            mode='lines+markers',
            name='Weekly Points',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8)
        ))
        fig.add_trace(go.Scatter(
            x=gw_data['Gameweek'],
            y=gw_data['Moving Avg (3GW)'],
            mode='lines',
            name='3-GW Moving Average',
            line=dict(color='#ff7f0e', width=3, dash='dash')
        ))
        
        fig.update_layout(
            title="Points Trend with Moving Average",
            xaxis_title="Gameweek",
            yaxis_title="Points",
            height=400,
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True, key="overview_trend")


# ============================================================
#                 PERFORMANCE TREND SECTION
# ============================================================

def display_performance_trend(manager_name: str, df: pd.DataFrame):
    """Enhanced performance trend with comparisons and controls"""
    st.header("📈 Points Progression vs League", divider="rainbow")
    
    manager_df = df[df['manager_team_name'] == manager_name]
    starting_players = get_starting_lineup(manager_df)
    team_gw_points = calculate_team_gw_points(starting_players)
    
    manager_row = team_gw_points.loc[manager_name].drop('Total')
    manager_points = pd.DataFrame({
        'gameweek': manager_row.index.astype(int), 
        'manager_points': manager_row.values
    })
    
    # League average
    all_starting = get_starting_lineup(df)
    all_team_gw_points = all_starting.groupby(['manager_team_name', 'gw'])['gw_points'].sum().reset_index()
    other_teams = all_team_gw_points[all_team_gw_points['manager_team_name'] != manager_name]
    league_avg = other_teams.groupby('gw')['gw_points'].mean().reset_index().rename(columns={'gw_points':'avg_points'})
    
    comparison_df = manager_points.merge(league_avg, left_on='gameweek', right_on='gw', how='left')
    comparison_df.drop(columns='gw', inplace=True)
    
    # Calculate statistics
    manager_avg = manager_points['manager_points'].mean()
    league_avg_val = comparison_df['avg_points'].mean()
    manager_above_avg = (manager_avg - league_avg_val)
    
    # --- Statistics Row ---
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    col_stat1.metric("Your Avg/GW", f"{manager_avg:.2f}", delta="Season Average")
    col_stat2.metric("League Avg/GW", f"{league_avg_val:.2f}", delta="All Teams")
    col_stat3.metric("Difference", f"{manager_above_avg:+.2f}", 
                     delta="You vs League", delta_color="off")
    
    st.markdown("---")
    
    # --- Interactive Chart with Options ---
    col_chart_options, col_chart_display = st.columns([1, 4])
    
    with col_chart_options:
        st.subheader("⚙️ Chart Options")
        show_league_avg = st.checkbox("Show League Average", value=True)
        show_rolling_avg = st.checkbox("Show 3-GW Moving Average", value=True)
        chart_style = st.radio("Chart Style", ["Line", "Area", "Bar"], horizontal=False)
    
    with col_chart_display:
        st.subheader("Your Performance Trend")
        
        if chart_style == "Line":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=manager_points['gameweek'],
                y=manager_points['manager_points'],
                mode='lines+markers',
                name=manager_name,
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=10),
                fill=None
            ))
            
            if show_league_avg:
                fig.add_trace(go.Scatter(
                    x=comparison_df['gameweek'],
                    y=comparison_df['avg_points'],
                    mode='lines+markers',
                    name='League Average',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    marker=dict(size=6)
                ))
            
            if show_rolling_avg:
                manager_points['rolling_avg'] = manager_points['manager_points'].rolling(3, center=True).mean()
                fig.add_trace(go.Scatter(
                    x=manager_points['gameweek'],
                    y=manager_points['rolling_avg'],
                    mode='lines',
                    name='3-GW Trend',
                    line=dict(color='#2ca02c', width=3, dash='dot')
                ))
        
        elif chart_style == "Area":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=manager_points['gameweek'],
                y=manager_points['manager_points'],
                mode='lines',
                name=manager_name,
                line=dict(color='#1f77b4', width=2),
                fill='tozeroy'
            ))
            
            if show_league_avg:
                fig.add_trace(go.Scatter(
                    x=comparison_df['gameweek'],
                    y=comparison_df['avg_points'],
                    mode='lines',
                    name='League Average',
                    line=dict(color='#ff7f0e', width=2, dash='dash'),
                    fill='tozeroy'
                ))
        
        else:  # Bar
            fig = px.bar(
                manager_points,
                x='gameweek',
                y='manager_points',
                title="",
                color='manager_points',
                color_continuous_scale='RdYlGn',
                text='manager_points'
            )
            fig.update_traces(textposition='outside')
        
        fig.update_layout(
            xaxis_title="Gameweek",
            yaxis_title="Points",
            height=450,
            hovermode='x unified',
            template='plotly_white'
        )
        st.plotly_chart(fig, use_container_width=True, key="trend_main")
    
    return manager_points


# ============================================================
#               CURRENT GAMEWEEK SECTION
# ============================================================

def display_latest_gw(manager_df: pd.DataFrame):
    """Enhanced current gameweek display with better layout"""
    st.header("🎯 Latest Gameweek Lineup", divider="rainbow")
    
    latest_gw = manager_df['gw'].max()
    latest_gw_df = manager_df[manager_df['gw'] == latest_gw].sort_values('team_position').copy()
    
    if latest_gw_df.empty:
        st.info("📊 No data for latest gameweek yet.")
        return
    
    latest_gw_df = latest_gw_df.rename(columns={
        'full_name': 'Player',
        'real_team': 'Team',
        'team_position': 'Position',
        'position': 'Role',
        'gw_points': 'Points',
        'gw_bonus': 'Bonus'
    })
    
    # --- Statistics Row ---
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    total_points = latest_gw_df['Points'].sum()
    avg_points = latest_gw_df['Points'].mean()
    max_player = latest_gw_df.loc[latest_gw_df['Points'].idxmax()]
    
    col_stat1.metric("🎯 Gameweek", latest_gw)
    col_stat2.metric("📊 Total Points", f"{total_points:.0f}")
    col_stat3.metric("📈 Avg/Player", f"{avg_points:.2f}")
    col_stat4.metric("⭐ Top Scorer", f"{max_player['Player'][:15]} ({max_player['Points']:.0f})")
    
    st.markdown("---")
    
    # --- Tabs for different views ---
    tab1, tab2, tab3 = st.tabs(["📋 Full Squad", "🔝 Top Performers", "👥 By Position"])
    
    with tab1:
        col_list, col_visual = st.columns([1, 1], gap="large")
        
        with col_list:
            st.subheader("Squad Lineup")
            display_df = latest_gw_df[['Position', 'Player', 'Team', 'Role', 'Points', 'Bonus']].copy()
            display_df['Status'] = display_df['Position'].apply(lambda x: '✅ Starting' if x <= 11 else '🔄 Bench')
            display_df = display_df.sort_values('Points', ascending=False)
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=400,
                hide_index=True
            )
        
        with col_visual:
            st.subheader("Points Breakdown")
            role_points = latest_gw_df.groupby('Role')['Points'].sum().reset_index()
            
            # Create pie chart with percentage labels
            fig = px.pie(
                role_points,
                names='Role',
                values='Points',
                title="Points Distribution by Position",
                color_discrete_sequence=px.colors.qualitative.Set3,
                hole=0.3
            )
            fig.update_traces(
                textposition='inside',
                textinfo='label+percent+value',
                hovertemplate='<b>%{label}</b><br>Points: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True, key="gw_position_pie")
    
    with tab2:
        col_top_list, col_top_visual = st.columns([1, 1], gap="large")
        
        top_5 = latest_gw_df.nlargest(5, 'Points')[['Player', 'Team', 'Role', 'Points', 'Bonus']]
        
        with col_top_list:
            st.subheader("Top 5 Performers")
            st.dataframe(top_5, use_container_width=True, hide_index=True, height=300)
        
        with col_top_visual:
            st.subheader("Top Scorers")
            fig = px.bar(
                top_5,
                y='Player',
                x='Points',
                color='Points',
                color_continuous_scale='RdYlGn',
                orientation='h',
                text='Points'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True, key="gw_top_scorers")
    
    with tab3:
        st.subheader("Squad Composition by Role")
        
        col_dist, col_points = st.columns([1, 1], gap="large")
        
        with col_dist:
            role_counts = latest_gw_df['Role'].value_counts().reset_index()
            role_counts.columns = ['Role', 'Count']
            fig = px.pie(
                role_counts,
                names='Role',
                values='Count',
                title="Player Count by Position",
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.3
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True, key="gw_role_dist")
        
        with col_points:
            role_avg = latest_gw_df.groupby('Role')['Points'].agg(['sum', 'mean', 'count']).reset_index()
            role_avg.columns = ['Role', 'Total Points', 'Avg Points', 'Players']
            st.dataframe(role_avg, use_container_width=True, hide_index=True)


# ============================================================
#              TOP PERFORMERS SECTION
# ============================================================

def display_top_performers(manager_df: pd.DataFrame):
    """Enhanced top performers with filtering and sorting"""
    st.header("⭐ Top Performing Players (Single Gameweek)", divider="rainbow")
    
    top_df = get_top_performers(manager_df).copy()
    
    if top_df.empty:
        st.info("No performer data available.")
        return top_df
    
    # --- Filter Options ---
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        selected_position = st.multiselect(
            "Filter by Position",
            options=top_df['Position'].unique(),
            default=top_df['Position'].unique()
        )
    
    with col_filter2:
        min_points = st.slider("Minimum Points", 
                               min_value=int(top_df['Points'].min()),
                               max_value=int(top_df['Points'].max()),
                               value=int(top_df['Points'].min()))
    
    with col_filter3:
        sort_by = st.selectbox("Sort by", ["Points (Desc)", "Points (Asc)", "Alphabetical"])
    
    # Apply filters
    filtered_df = top_df[
        (top_df['Position'].isin(selected_position)) &
        (top_df['Points'] >= min_points)
    ].copy()
    
    # Apply sorting
    if sort_by == "Points (Desc)":
        filtered_df = filtered_df.sort_values('Points', ascending=False)
    elif sort_by == "Points (Asc)":
        filtered_df = filtered_df.sort_values('Points', ascending=True)
    else:
        filtered_df = filtered_df.sort_values('Player')
    
    st.markdown("---")
    
    # --- Display Options ---
    col_data, col_viz = st.columns([1, 1], gap="large")
    
    with col_data:
        st.subheader("Performance Table")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
    
    with col_viz:
        st.subheader("Top Performers Chart")
        display_df = filtered_df.head(10)
        fig = px.bar(
            display_df,
            y='Player',
            x='Points',
            color='Points',
            color_continuous_scale='Viridis',
            orientation='h',
            text='Points',
            title="Top 10 Performers"
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True, key="top_performers")
    
    return filtered_df


# ============================================================
#           PLAYER PROGRESSION SECTION
# ============================================================

def display_player_progression(manager_df: pd.DataFrame):
    """Enhanced player progression with interactive controls"""
    st.header("📊 Player Points Over Time", divider="rainbow")
    
    pivot = get_player_progression(manager_df)
    
    if pivot.empty:
        st.info("No progression data available.")
        return
    
    # --- Player Selection ---
    col_select, col_options = st.columns([2, 1])
    
    with col_select:
        selected_players = st.multiselect(
            "Select Players to Display",
            options=pivot.columns.tolist(),
            default=pivot.columns.tolist()[:5] if len(pivot.columns) > 5 else pivot.columns.tolist()
        )
    
    with col_options:
        show_total = st.checkbox("Show Season Total", value=True)
    
    if not selected_players:
        st.warning("Please select at least one player.")
        return
    
    # Prepare data
    plot_data = pivot[selected_players].reset_index()
    
    # --- Chart Display ---
    fig = go.Figure()
    
    for player in selected_players:
        fig.add_trace(go.Scatter(
            x=plot_data['gw'],
            y=plot_data[player],
            mode='lines+markers',
            name=player,
            line=dict(width=2),
            marker=dict(size=6)
        ))
    
    if show_total:
        totals = plot_data[selected_players].sum(axis=1)
        fig.add_trace(go.Scatter(
            x=plot_data['gw'],
            y=totals,
            mode='lines',
            name='Total Selected',
            line=dict(width=3, dash='dash', color='black'),
            fill=None
        ))
    
    fig.update_layout(
        title="Player Points Progression",
        xaxis_title="Gameweek",
        yaxis_title="Points",
        height=500,
        hovermode='x unified',
        template='plotly_white',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99
        )
    )
    
    st.plotly_chart(fig, use_container_width=True, key="player_progression")


# ============================================================
#                  OTHER STATS SECTION
# ============================================================

def display_other_stats(manager_points: pd.DataFrame, top_performances: pd.DataFrame):
    """Enhanced stats display with summary cards"""
    st.header("📜 Key Statistics & Highlights", divider="rainbow")
    
    if top_performances.empty or manager_points.empty:
        st.info("Insufficient data for statistics.")
        return
    
    # --- Key Metrics Row ---
    best_player = top_performances.iloc[0]
    best_gw_row = manager_points.loc[manager_points['manager_points'].idxmax()]
    worst_gw_row = manager_points.loc[manager_points['manager_points'].idxmin()]
    
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("🌟 Top Scorer", best_player['Player'][:20], f"{best_player['Points']} pts")
    col2.metric("🔥 Best Gameweek", int(best_gw_row['gameweek']), f"{best_gw_row['manager_points']} pts")
    col3.metric("❄️ Toughest GW", int(worst_gw_row['gameweek']), f"{worst_gw_row['manager_points']} pts")
    col4.metric("📊 Consistency", 
                f"{manager_points['manager_points'].std():.2f}", 
                "Std Dev (Lower=Better)")
    
    st.markdown("---")
    
    # --- Expandable sections for more details ---
    with st.expander("📈 Performance Analysis", expanded=False):
        col_analysis1, col_analysis2 = st.columns(2)
        
        with col_analysis1:
            st.subheader("Distribution Stats")
            stats = {
                'Mean': manager_points['manager_points'].mean(),
                'Median': manager_points['manager_points'].median(),
                'Std Dev': manager_points['manager_points'].std(),
                'Min': manager_points['manager_points'].min(),
                'Max': manager_points['manager_points'].max(),
                'Range': manager_points['manager_points'].max() - manager_points['manager_points'].min()
            }
            stats_df = pd.DataFrame(stats.items(), columns=['Metric', 'Value'])
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
        
        with col_analysis2:
            st.subheader("Performance Distribution")
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=manager_points['manager_points'],
                nbinsx=15,
                name='Frequency',
                marker_color='rgba(31, 119, 180, 0.7)'
            ))
            fig.update_layout(
                title="Distribution of Gameweek Points",
                xaxis_title="Points",
                yaxis_title="Frequency",
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, key="dist_hist")
    
    with st.expander("🎯 Top 10 Performers", expanded=False):
        top_10 = top_performances.head(10)
        col_top_table, col_top_chart = st.columns([1, 1])
        
        with col_top_table:
            st.dataframe(top_10, use_container_width=True, hide_index=True)
        
        with col_top_chart:
            fig = px.bar(
                top_10,
                x='Points',
                y='Player',
                color='Points',
                color_continuous_scale='RdYlGn',
                orientation='h',
                text='Points'
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(
                showlegend=False,
                height=400,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig, use_container_width=True, key="top_10_chart")


# ============================================================
#          OPTIMIZED LINEUP SECTION (NEW)
# ============================================================

def display_optimized_lineup(manager_df: pd.DataFrame):
    """
    Display optimized team for each gameweek showing highest possible points
    based on squad and constraints.
    """
    st.header("🎯 Optimized Team Strategy", divider="rainbow")
    
    if manager_df.empty:
        st.info("No data available for optimization.")
        return
    
    # Get all optimal lineups
    optimal_df = get_all_optimal_lineups(manager_df)
    
    if optimal_df.empty:
        st.info("Unable to calculate optimal lineups.")
        return
    
    # --- Statistics Row ---
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    
    total_actual = optimal_df['actual_points'].sum()
    total_optimal = optimal_df['optimal_points'].sum()
    total_potential = total_optimal - total_actual
    avg_gain_pct = optimal_df['potential_gain_pct'].mean()
    
    col_stat1.metric("📊 Total Actual Points", f"{total_actual:.0f}")
    col_stat2.metric("🚀 Total Optimal Points", f"{total_optimal:.0f}")
    col_stat3.metric("💡 Total Potential Gain", f"{total_potential:.0f}")
    col_stat4.metric("📈 Avg Gain %", f"{avg_gain_pct:.1f}%")
    
    st.markdown("---")
    
    # --- Gameweek Selection ---
    selected_gw = st.slider(
        "Select Gameweek to View Optimal Lineup",
        min_value=int(optimal_df['gameweek'].min()),
        max_value=int(optimal_df['gameweek'].max()),
        value=int(optimal_df['gameweek'].max())
    )
    
    st.markdown("---")
    
    # --- Tab for comparison and details ---
    tab1, tab2, tab3 = st.tabs(["📊 Comparison", "⭐ Optimal Lineup", "📋 All Gameweeks"])
    
    with tab1:
        # Comparison chart
        col_chart1, col_chart2 = st.columns([1, 1], gap="large")
        
        with col_chart1:
            st.subheader("Actual vs Optimal Points")
            comparison_df = optimal_df.copy()
            comparison_df['gameweek'] = comparison_df['gameweek'].astype(int)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=comparison_df['gameweek'],
                y=comparison_df['actual_points'],
                name='Actual Points',
                marker_color='#3498db'
            ))
            fig.add_trace(go.Bar(
                x=comparison_df['gameweek'],
                y=comparison_df['optimal_points'],
                name='Optimal Points',
                marker_color='#2ecc71'
            ))
            fig.update_layout(
                barmode='group',
                title="Actual vs Optimal Points by Gameweek",
                xaxis_title="Gameweek",
                yaxis_title="Points",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, key="actual_vs_optimal")
        
        with col_chart2:
            st.subheader("Potential Gain Analysis")
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=comparison_df['gameweek'],
                y=comparison_df['difference'],
                mode='lines+markers',
                name='Potential Gain',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=8),
                fill='tozeroy'
            ))
            fig.update_layout(
                title="Potential Gain Points per Gameweek",
                xaxis_title="Gameweek",
                yaxis_title="Potential Gain",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, key="potential_gain")
    
    with tab2:
        st.subheader(f"Optimal Lineup - Gameweek {selected_gw}")
        
        # Get optimal lineup for selected GW
        optimal_result = get_optimal_lineup(manager_df, gameweek=selected_gw)
        
        if not optimal_result['valid']:
            st.warning(f"⚠️ Could not create valid lineup: {', '.join(optimal_result['errors'])}")
            return
        
        lineup_df = optimal_result['lineup'].copy()
        bench_df = optimal_result['bench'].copy()
        
        if not lineup_df.empty:
            # Format lineup display
            lineup_display = lineup_df[[
                'full_name', 'real_team', 'position', 'gw_points', 'team_position'
            ]].copy()
            lineup_display.columns = ['Player', 'Team', 'Position', 'Points', 'Squad Pos']
            lineup_display = lineup_display.sort_values('Points', ascending=False)
            lineup_display['Squad Pos'] = lineup_display['Squad Pos'].apply(
                lambda x: f"#{x} Starting" if x <= 11 else f"#{x} Bench"
            )
            
            col_lineup, col_breakdown = st.columns([2, 1], gap="large")
            
            with col_lineup:
                st.dataframe(
                    lineup_display,
                    use_container_width=True,
                    hide_index=True
                )
            
            with col_breakdown:
                # Position breakdown
                pos_breakdown = lineup_df['position'].value_counts().reset_index()
                pos_breakdown.columns = ['Position', 'Count']
                
                fig = px.pie(
                    pos_breakdown,
                    names='Position',
                    values='Count',
                    title="Optimal Squad Composition",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.3
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True, key="optimal_composition")
            
            # Summary
            st.markdown("---")
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            
            actual_gw = optimal_df[optimal_df['gameweek'] == selected_gw]
            if not actual_gw.empty:
                actual_pts = actual_gw['actual_points'].values[0]
                optimal_pts = actual_gw['optimal_points'].values[0]
                gain = actual_gw['difference'].values[0]
                
                col_sum1.metric("Your Actual Points", f"{actual_pts:.0f}")
                col_sum2.metric("Optimal Points", f"{optimal_pts:.0f}")
                col_sum3.metric("Potential Gain", f"{gain:.0f}")
    
    with tab3:
        st.subheader("All Gameweeks Summary")
        display_table = optimal_df.copy()
        display_table['gameweek'] = display_table['gameweek'].astype(int)
        display_table['actual_points'] = display_table['actual_points'].round(0).astype(int)
        display_table['optimal_points'] = display_table['optimal_points'].round(0).astype(int)
        display_table['difference'] = display_table['difference'].round(0).astype(int)
        display_table['potential_gain_pct'] = display_table['potential_gain_pct'].round(1)
        
        display_table = display_table.rename(columns={
            'gameweek': 'GW',
            'actual_points': 'Actual',
            'optimal_points': 'Optimal',
            'difference': 'Gain',
            'potential_gain_pct': 'Gain %'
        })
        
        st.dataframe(
            display_table[['GW', 'Actual', 'Optimal', 'Gain', 'Gain %']],
            use_container_width=True,
            hide_index=True
        )
        
        # Download as CSV
        csv = display_table.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"optimized_lineup_{selected_gw}.csv",
            mime="text/csv"
        )


# ============================================================
#          DATA SCIENCE ANALYSIS - PLAYERS SECTION
# ============================================================

def display_player_clustering(df: pd.DataFrame):
    """
    Display player clustering analysis with archetypes and characteristics.
    """
    st.header("🎯 Player Performance Clustering", divider="rainbow")
    
    if df.empty:
        st.info("No data available for clustering analysis.")
        return
    
    # Filter out rows with missing critical data
    df_clean = df.dropna(subset=['full_name', 'position', 'gw_points']).copy()
    
    if df_clean.empty or len(df_clean) < 10:
        st.warning("⚠️ Insufficient player data for clustering analysis. Need at least 10 players with complete data.")
        return
    
    # Get unique positions
    positions = sorted(df_clean['position'].unique())
    
    col_select, col_info = st.columns([2, 1])
    
    with col_select:
        selected_position = st.selectbox(
            "Select Position to Analyze",
            options=["All Positions"] + positions
        )
    
    with col_info:
        st.markdown("<br>", unsafe_allow_html=True)
        n_clusters = st.slider("Number of Clusters", min_value=2, max_value=5, value=3)
    
    st.markdown("---")
    
    # Prepare data
    analysis_df = df_clean if selected_position == "All Positions" else df_clean[df_clean['position'] == selected_position]
    
    if len(analysis_df) < n_clusters:
        st.warning(f"⚠️ Not enough players ({len(analysis_df)}) for {n_clusters} clusters. Please reduce cluster count or select 'All Positions'.")
        return
    
    # Run clustering
    clustering_result = cluster_players(analysis_df, n_clusters=n_clusters, 
                                       position=None if selected_position == "All Positions" else selected_position)
    
    if 'error' in clustering_result:
        st.warning(f"⚠️ {clustering_result['error']}")
        return
    
    cluster_df = clustering_result['cluster_df']
    sil_score = clustering_result['silhouette_score']
    
    if cluster_df.empty:
        st.info("No clustering data available.")
        return
    
    # --- Quality Metrics ---
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    
    col_metric1.metric(
        "📊 Silhouette Score",
        f"{sil_score:.3f}",
        help="Higher = better separated clusters (0-1 scale)"
    )
    col_metric2.metric(
        "👥 Players Analyzed",
        len(cluster_df)
    )
    col_metric3.metric(
        "🎯 Clusters",
        n_clusters
    )
    
    st.markdown("---")
    
    # --- Three Tabs ---
    tab1, tab2, tab3 = st.tabs(["📈 Cluster Visualization", "📋 Player Groups", "🔍 Cluster Characteristics"])
    
    with tab1:
        st.subheader("Player Clusters (Performance Space)")
        
        # Create scatter plot
        fig = px.scatter(
            cluster_df,
            x='avg_points_norm',
            y='consistency_norm',
            color='cluster',
            size='games_played',
            hover_data=['player_name', 'position', 'avg_points', 'consistency'],
            labels={
                'avg_points_norm': 'Average Points (Normalized)',
                'consistency_norm': 'Consistency (Normalized)',
                'cluster': 'Cluster'
            },
            title="Player Clustering: Average Points vs Consistency",
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        fig.update_layout(height=500, hovermode='closest')
        st.plotly_chart(fig, use_container_width=True, key="cluster_scatter")
    
    with tab2:
        st.subheader("Players by Cluster Group")
        
        for cluster_id in sorted(cluster_df['cluster'].unique()):
            cluster_players_df = cluster_df[cluster_df['cluster'] == cluster_id].copy()
            cluster_players_df = cluster_players_df.sort_values('avg_points', ascending=False)
            
            with st.expander(f"🔹 Cluster {cluster_id} ({len(cluster_players_df)} players)", expanded=(cluster_id == 0)):
                display_cols = ['player_name', 'position', 'team', 'avg_points', 
                               'std_points', 'games_played', 'consistency']
                
                col_table, col_stats = st.columns([2, 1])
                
                with col_table:
                    st.dataframe(
                        cluster_players_df[display_cols],
                        use_container_width=True,
                        hide_index=True
                    )
                
                with col_stats:
                    st.write("**Cluster Stats:**")
                    st.metric("Avg Points", f"{cluster_players_df['avg_points'].mean():.2f}")
                    st.metric("Avg Consistency", f"{cluster_players_df['consistency'].mean():.2f}")
                    st.metric("Total Games", int(cluster_players_df['games_played'].sum()))
    
    with tab3:
        st.subheader("Cluster Characteristics")
        
        cluster_centers = clustering_result['cluster_centers']
        
        # Heatmap of cluster characteristics
        fig = px.imshow(
            cluster_centers.set_index('cluster')[['avg_points_norm', 'consistency_norm', 'bonus_norm']],
            labels=dict(x="Metric", y="Cluster", color="Score"),
            x=['Avg Points', 'Consistency', 'Bonus'],
            y=[f'Cluster {i}' for i in range(n_clusters)],
            color_continuous_scale='RdYlGn',
            aspect='auto',
            title="Cluster Characteristics Heatmap"
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True, key="cluster_heatmap")
        
        # Cluster descriptions
        cluster_descriptions = {
            0: "Primary cluster - baseline performance",
            1: "Secondary cluster - alternative performance profile",
            2: "Tertiary cluster - another performance group",
            3: "Quaternary cluster",
            4: "Quinary cluster"
        }
        
        for cluster_id in sorted(cluster_df['cluster'].unique()):
            cluster_data = cluster_df[cluster_df['cluster'] == cluster_id]
            
            st.write(f"**Cluster {cluster_id}** - {cluster_descriptions.get(cluster_id, 'Cluster group')}")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Avg Points", f"{cluster_data['avg_points'].mean():.2f}")
            col2.metric("Consistency", f"{cluster_data['consistency'].mean():.2f}")
            col3.metric("Players", len(cluster_data))
            col4.metric("Total Games", int(cluster_data['games_played'].sum()))


def display_player_trends(df: pd.DataFrame):
    """
    Display player trend analysis (improving/declining over season).
    """
    st.header("📈 Player Performance Trends", divider="rainbow")
    
    if df.empty:
        st.info("No data available for trend analysis.")
        return
    
    # Filter out rows with missing critical data
    df_clean = df.dropna(subset=['full_name', 'gw_points', 'gw']).copy()
    
    if df_clean.empty:
        st.warning("⚠️ No valid player data available for trend analysis.")
        return
    
    # Player selection
    players = sorted(df_clean['full_name'].unique())
    
    if not players:
        st.warning("⚠️ No players available for trend analysis.")
        return
    
    col_select, col_filter = st.columns([2, 1])
    
    with col_select:
        selected_player = st.selectbox(
            "Select Player to Analyze",
            options=players,
            help="Choose a player to see their season trend"
        )
    
    with col_filter:
        show_trend_line = st.checkbox("Show Trend Line", value=True)
    
    st.markdown("---")
    
    # Analyze trend
    trend_result = analyze_player_trend(df_clean, selected_player)
    
    if 'error' in trend_result:
        st.warning(f"⚠️ {trend_result['error']}")
        return
    
    trend_df = trend_result['trend_df']
    slope = trend_result['slope']
    r_squared = trend_result['r_squared']
    classification = trend_result['classification']
    predicted_next = trend_result['predicted_next_gw']
    
    # --- Metrics Row ---
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    col_m1.metric("📊 Classification", classification)
    col_m2.metric("📈 Trend Slope", f"{slope:.3f}", help="Points per gameweek change")
    col_m3.metric("🎯 Fit Quality (R²)", f"{r_squared:.3f}", help="0-1: higher = better fit")
    col_m4.metric("🔮 Next GW Prediction", f"{predicted_next:.1f}")
    
    st.markdown("---")
    
    # --- Trend Visualization ---
    col_chart, col_table = st.columns([2, 1], gap="large")
    
    with col_chart:
        st.subheader("Performance Over Season")
        
        fig = go.Figure()
        
        # Actual points
        fig.add_trace(go.Scatter(
            x=trend_df['gw'],
            y=trend_df['gw_points'],
            mode='lines+markers',
            name='Actual Points',
            line=dict(color='#3498db', width=2),
            marker=dict(size=8)
        ))
        
        # Trend line if selected
        if show_trend_line:
            fig.add_trace(go.Scatter(
                x=trend_df['gw'],
                y=trend_df['trend_line'],
                mode='lines',
                name='Trend Line',
                line=dict(color='#e74c3c', width=3, dash='dash')
            ))
        
        # Future prediction
        future_gw = max(trend_df['gw']) + 1
        fig.add_trace(go.Scatter(
            x=[max(trend_df['gw']), future_gw],
            y=[trend_df['trend_line'].iloc[-1], predicted_next],
            mode='lines+markers',
            name='Prediction',
            line=dict(color='#2ecc71', width=2, dash='dot'),
            marker=dict(size=8, symbol='diamond')
        ))
        
        fig.update_layout(
            title=f"{selected_player} - Season Performance Trend",
            xaxis_title="Gameweek",
            yaxis_title="Points",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True, key="trend_analysis")
    
    with col_table:
        st.subheader("Season Summary")
        
        player_info = trend_df.iloc[0] if not trend_df.empty else {}
        
        st.write(f"**Position:** {player_info.get('position', 'N/A')}")
        st.write(f"**Team:** {player_info.get('real_team', 'N/A')}")
        
        st.divider()
        
        st.metric("Total Points", f"{trend_df['gw_points'].sum():.0f}")
        st.metric("Average", f"{trend_df['gw_points'].mean():.1f}")
        st.metric("Max", f"{trend_df['gw_points'].max():.0f}")
        st.metric("Min", f"{trend_df['gw_points'].min():.0f}")
        st.metric("Std Dev", f"{trend_df['gw_points'].std():.2f}")


def display_consistency_analysis(df: pd.DataFrame):
    """
    Display player consistency rankings and performance stability.
    """
    st.header("📊 Player Consistency Analysis", divider="rainbow")
    
    if df.empty:
        st.info("No data available for consistency analysis.")
        return
    
    # Calculate consistency
    consistency_df = calculate_player_consistency(df)
    
    if consistency_df.empty:
        st.info("No consistency data available.")
        return
    
    # Position filter
    selected_position = st.selectbox(
        "Filter by Position",
        options=["All Positions"] + sorted(consistency_df['position'].unique())
    )
    
    if selected_position != "All Positions":
        display_df = consistency_df[consistency_df['position'] == selected_position].copy()
    else:
        display_df = consistency_df.copy()
    
    if display_df.empty:
        st.warning("⚠️ No data available for the selected position.")
        return
    
    st.markdown("---")
    
    # --- Tabs ---
    tab1, tab2, tab3 = st.tabs(["🏆 Rankings", "📈 Distribution", "📋 Detailed Metrics"])
    
    with tab1:
        st.subheader("Consistency Rankings")
        
        col_most, col_least = st.columns(2, gap="large")
        
        with col_most:
            st.write("**Most Consistent Players**")
            top_consistent = display_df.nlargest(10, 'consistency_score')[
                ['player_name', 'position', 'team', 'consistency_score', 'avg_points']
            ].copy()
            
            fig = px.bar(
                top_consistent,
                y='player_name',
                x='consistency_score',
                color='consistency_score',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                text='consistency_score',
                orientation='h'
            )
            fig.update_traces(texttemplate='%{value:.1f}', textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="consistency_top")
        
        with col_least:
            st.write("**Most Volatile Players**")
            least_consistent = display_df.nsmallest(10, 'consistency_score')[
                ['player_name', 'position', 'team', 'consistency_score', 'avg_points']
            ].copy()
            
            fig = px.bar(
                least_consistent,
                y='player_name',
                x='consistency_score',
                color='consistency_score',
                color_continuous_scale='RdYlGn',
                range_color=[0, 100],
                text='consistency_score',
                orientation='h'
            )
            fig.update_traces(texttemplate='%{value:.1f}', textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True, key="consistency_bottom")
    
    with tab2:
        st.subheader("Consistency Score Distribution")
        
        fig = px.histogram(
            display_df,
            x='consistency_score',
            nbins=20,
            color='position',
            marginal='box',
            title="Distribution of Player Consistency Scores",
            labels={'consistency_score': 'Consistency Score (0-100)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True, key="consistency_dist")
    
    with tab3:
        st.subheader("Detailed Consistency Metrics")
        
        display_cols = ['player_name', 'position', 'team', 'avg_points', 'std_points',
                       'consistency_score', 'cv', 'performance_range', 'games']
        
        display_data = display_df[display_cols].copy()
        display_data = display_data.sort_values('consistency_score', ascending=False)
        
        st.dataframe(
            display_data,
            use_container_width=True,
            hide_index=True
        )


def display_player_archetypes_analysis(df: pd.DataFrame):
    """
    Display identified player archetypes and performance profiles.
    """
    st.header("🎭 Player Archetypes & Profiles", divider="rainbow")
    
    if df.empty:
        st.info("No data available for archetype analysis.")
        return
    
    archetypes = get_player_archetypes(df)
    
    col1, col2, col3 = st.columns(3, gap="large")
    
    if 'High Performers' in archetypes and not archetypes['High Performers'].empty:
        with col1:
            st.subheader("🌟 High Performers")
            high_perf = archetypes['High Performers'].copy()
            st.dataframe(high_perf, use_container_width=True, hide_index=True)
    
    if 'Most Consistent' in archetypes and not archetypes['Most Consistent'].empty:
        with col2:
            st.subheader("🎯 Most Consistent")
            consistent = archetypes['Most Consistent'].copy()
            st.dataframe(consistent, use_container_width=True, hide_index=True)
    
    if 'Bonus Hunters' in archetypes and not archetypes['Bonus Hunters'].empty:
        with col3:
            st.subheader("💎 Bonus Hunters")
            bonus = archetypes['Bonus Hunters'].copy()
            st.dataframe(bonus, use_container_width=True, hide_index=True)


# ============================================================
#       LEAGUE-WIDE OPTIMIZED LINEUPS DISPLAY
# ============================================================

def display_league_optimized_lineups(df: pd.DataFrame):
    """
    Display league-wide optimized lineup comparison.
    Shows all teams with their actual vs potential optimal points.
    """
    st.header("🏆 Optimized League Classification", divider="rainbow")
    
    if df.empty:
        st.info("No data available for league analysis.")
        return
    
    # Get actual points (same method as Team Performance tab which works correctly)
    starting_players = get_starting_lineup(df)
    team_gw_points = calculate_team_gw_points(starting_players)
    
    if team_gw_points.empty:
        st.info("No data available.")
        return
    
    # Extract actual total points for each team
    actual_points_dict = team_gw_points['Total'].to_dict()
    
    # Calculate optimal points for each team
    results = []
    for team_name in actual_points_dict.keys():
        team_df = df[df['manager_team_name'] == team_name].copy()
        
        if team_df.empty:
            continue
        
        actual_total = actual_points_dict[team_name]
        
        # Get optimal
        gw_results = get_all_optimal_lineups(team_df)
        if gw_results.empty:
            optimal_total = actual_total
        else:
            optimal_total = gw_results['optimal_points'].sum()
        
        difference = optimal_total - actual_total
        gain_pct = (difference / actual_total * 100) if actual_total > 0 else 0
        
        results.append({
            'Team': team_name,
            'Actual Points': int(actual_total),
            'Optimal Points': int(optimal_total),
            'Potential Gain': int(difference),
            'Gain %': round(gain_pct, 1)
        })
    
    # Create results dataframe sorted by actual points
    result_df = pd.DataFrame(results).sort_values('Actual Points', ascending=False).reset_index(drop=True)
    result_df.index = result_df.index + 1
    result_df.index.name = 'Rank'
    
    # Display table
    st.subheader("League Classification Table")
    st.dataframe(result_df, use_container_width=True, height=500)
    
    # Show summary stats
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 Total League Points (Actual)", int(result_df['Actual Points'].sum()))
    col2.metric("🚀 Total League Points (Optimal)", int(result_df['Optimal Points'].sum()))
    col3.metric("💡 League Potential Gain", int(result_df['Potential Gain'].sum()))


# ============================================================
#       INJURY & STATUS ALERTS
# ============================================================

def display_injury_alerts(manager_df: pd.DataFrame):
    """
    Display injury and status alerts for manager's squad.
    Highlights at-risk and injured players.
    """
    st.header("⚕️ Squad Health Status", divider="rainbow")
    
    if manager_df.empty:
        st.info("No data available.")
        return
    
    # Get injury summary
    summary = get_injury_summary(manager_df)
    
    # Show summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    col1.metric("📋 Total Squad", summary['total_players'])
    col2.metric("✅ Healthy", summary['healthy'], delta="players", delta_color="normal")
    col3.metric("🟡 At Risk", summary['at_risk'], delta="players", delta_color="inverse")
    col4.metric("🚨 Out", summary['out'], delta="players", delta_color="inverse")
    col5.metric("⚠️ Starting At Risk", summary['starting_at_risk'], delta="critical", delta_color="inverse")
    
    st.markdown("---")
    
    # Get full squad status
    squad_status = get_squad_status(manager_df, latest_gw_only=True)
    
    if squad_status.empty:
        st.info("No injury data available.")
        return
    
    # Display by status category
    tab1, tab2, tab3 = st.tabs(["⚠️ At Risk Players", "📋 Full Squad Status", "📊 Risk Analysis"])
    
    with tab1:
        at_risk = squad_status[squad_status['chance_of_playing'] < 100].copy()
        
        if at_risk.empty:
            st.success("✅ No players at risk - full squad healthy!")
        else:
            st.warning(f"⚠️ {len(at_risk)} players with injury concerns")
            
            # Highlight starting XI at risk
            starting_at_risk = at_risk[at_risk['is_starting'] == True]
            if not starting_at_risk.empty:
                st.error(f"🚨 **{len(starting_at_risk)} Starting XI players at risk!**")
                display_cols = ['full_name', 'position', 'real_team', 'status', 'chance_of_playing', 'news']
                at_risk_display = starting_at_risk[display_cols].copy()
                at_risk_display.rename(columns={
                    'full_name': 'Player',
                    'position': 'Position',
                    'real_team': 'Team',
                    'status': 'Status',
                    'chance_of_playing': 'Chance %',
                    'news': 'Update'
                }, inplace=True)
                st.dataframe(at_risk_display, use_container_width=True, hide_index=True)
            
            # Show bench at risk
            bench_at_risk = at_risk[at_risk['is_starting'] == False]
            if not bench_at_risk.empty:
                with st.expander(f"📌 {len(bench_at_risk)} Bench players at risk"):
                    display_cols = ['full_name', 'position', 'real_team', 'status', 'chance_of_playing', 'news']
                    bench_display = bench_at_risk[display_cols].copy()
                    bench_display.rename(columns={
                        'full_name': 'Player',
                        'position': 'Position',
                        'real_team': 'Team',
                        'status': 'Status',
                        'chance_of_playing': 'Chance %',
                        'news': 'Update'
                    }, inplace=True)
                    st.dataframe(bench_display, use_container_width=True, hide_index=True)
    
    with tab2:
        # Full squad status with color coding
        display_cols = ['full_name', 'position', 'real_team', 'status', 'chance_of_playing', 'gw_points']
        display_df = squad_status[display_cols].copy()
        display_df['Type'] = display_df.apply(
            lambda x: '🔴 Starting' if x['real_team'] and squad_status.loc[display_df.index.get_loc(x.name), 'is_starting'] else '⚪ Bench',
            axis=1
        )
        
        display_df.rename(columns={
            'full_name': 'Player',
            'position': 'Position',
            'real_team': 'Team',
            'status': 'Status',
            'chance_of_playing': 'Chance %',
            'gw_points': 'This GW'
        }, inplace=True)
        
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
    
    with tab3:
        st.subheader("Risk Distribution")
        
        risk_counts = squad_status['status'].value_counts().reset_index()
        risk_counts.columns = ['Status', 'Count']
        
        fig = px.bar(
            risk_counts,
            x='Status',
            y='Count',
            color='Status',
            color_discrete_map={
                '✅ Healthy': '#2ecc71',
                '🟡 At Risk': '#f39c12',
                '⚠️ Doubtful': '#e74c3c',
                '🚨 Out': '#c0392b'
            },
            title="Squad Health Distribution",
            labels={'Count': 'Number of Players', 'Status': 'Player Status'}
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        # Chance of playing distribution
        st.subheader("Chance of Playing Distribution")
        
        fig2 = px.histogram(
            squad_status,
            x='chance_of_playing',
            nbins=5,
            title="Distribution of Injury Risk",
            labels={'chance_of_playing': 'Chance of Playing (%)', 'count': 'Players'},
            color_discrete_sequence=['#3498db']
        )
        fig2.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
