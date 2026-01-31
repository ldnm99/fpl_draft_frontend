import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from core.data_utils import (
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points,
    points_per_player_position,
    get_top_performers,
    get_player_progression,
    get_optimal_lineup,
    get_all_optimal_lineups
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
