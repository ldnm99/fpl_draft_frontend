import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.data_utils import (
    load_data_supabase, 
    get_starting_lineup, 
    calculate_team_gw_points, 
    get_teams_avg_points
)
from core.visuals_utils import display_league_optimized_lineups
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY

# ============================================================
#                    PAGE CONFIGURATION
# ============================================================

st.set_page_config(layout="wide", page_title="FPL Overall Dashboard")

# ============================================================
#                    DATA LOADING
# ============================================================

OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets["TOKEN_STREAMLIT"]
BUCKET = "data"

try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    df, standings, gameweeks, fixtures = load_data_supabase(supabase)
except Exception as e:
    st.error(f"Failed to load data: {str(e)}")
    st.stop()

# ============================================================
#                    PAGE HEADER
# ============================================================

st.title("📊 FPL Overall Dashboard", anchor=False)
st.markdown("Comprehensive league overview with team performance analytics and comparisons")

# ============================================================
#                    FILTER SECTION
# ============================================================

st.markdown("---")
col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1], gap="medium")

with col_filter1:
    min_gw, max_gw = int(df['gw'].min()), int(df['gw'].max())
    selected_gw_range = st.slider(
        "Select Gameweek Range",
        min_value=min_gw,
        max_value=max_gw,
        value=(min_gw, max_gw),
        step=1
    )

with col_filter2:
    selected_team = st.selectbox(
        "Filter by Manager (Optional)",
        options=["All Managers"] + sorted(df['manager_team_name'].dropna().unique()),
        index=0
    )

with col_filter3:
    st.markdown("<br>", unsafe_allow_html=True)
    apply_filter = st.button("🔄 Refresh", use_container_width=True)

# ============================================================
#                    FILTER DATA
# ============================================================

filtered_df = df[
    (df['gw'] >= selected_gw_range[0]) &
    (df['gw'] <= selected_gw_range[1])
]

if selected_team != "All Managers":
    filtered_df = filtered_df[filtered_df['manager_team_name'] == selected_team]

# Calculate metrics
starting_players = get_starting_lineup(filtered_df)
team_gw_points = calculate_team_gw_points(starting_players)
team_avg_points = get_teams_avg_points(team_gw_points)

st.markdown("---")

# ============================================================
#                    KPI SUMMARY CARDS
# ============================================================

st.subheader("📈 League Overview", divider="rainbow")

# Calculate summary statistics
total_teams = len(team_avg_points)
avg_league_points = team_avg_points['avg_points'].mean()
top_team = team_avg_points.loc[team_avg_points['avg_points'].idxmax()]
bottom_team = team_avg_points.loc[team_avg_points['avg_points'].idxmin()]

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4, gap="medium")

col_kpi1.metric(
    "🏆 Teams in League",
    f"{total_teams}",
    delta="Active managers" if selected_team == "All Managers" else "Filtered view"
)

col_kpi2.metric(
    "📊 League Average",
    f"{avg_league_points:.1f}",
    delta="Avg Points/GW",
    delta_color="off"
)

col_kpi3.metric(
    "🥇 Top Team",
    f"{top_team['team_name']}",
    f"{top_team['avg_points']:.1f} pts/GW"
)

col_kpi4.metric(
    "🥈 Bottom Team",
    f"{bottom_team['team_name']}",
    f"{bottom_team['avg_points']:.1f} pts/GW"
)

st.markdown("---")

# ============================================================
#                    TABBED INTERFACE
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Team Performance", "🔥 Rankings & Averages", "📈 Trends", "🎯 Advanced Analysis", "🏆 Optimized League"])

# ============================================================
#                    TAB 1: TEAM PERFORMANCE
# ============================================================

with tab1:
    st.subheader("Team Performance Metrics")
    
    col_perf1, col_perf2 = st.columns([1, 1], gap="large")
    
    with col_perf1:
        st.markdown("**Gameweek Points Table**")
        # Show only non-Total columns
        if not team_gw_points.empty:
            display_table = team_gw_points.copy()
            st.dataframe(
                display_table,
                use_container_width=True,
                height=400
            )
        else:
            st.info("No data available for the selected filters.")
    
    with col_perf2:
        st.markdown("**Weekly Points Distribution**")
        if not team_gw_points.empty:
            # Prepare data for visualization
            gw_cols = [c for c in team_gw_points.columns if c != 'Total']
            manager_names = team_gw_points.index.tolist()
            
            # Create box plot for points distribution
            box_data = []
            for manager in manager_names:
                points = team_gw_points.loc[manager, gw_cols].values
                for pt in points:
                    box_data.append({'Manager': manager, 'Points': pt})
            
            box_df = pd.DataFrame(box_data)
            fig = px.box(
                box_df,
                y='Manager',
                x='Points',
                color='Manager',
                title="Points Distribution by Manager",
                labels={'Points': 'Points per Gameweek'},
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
#                    TAB 2: RANKINGS & AVERAGES
# ============================================================

with tab2:
    st.subheader("Team Rankings & Statistics")
    
    col_rank1, col_rank2 = st.columns([1, 1], gap="large")
    
    with col_rank1:
        st.markdown("**Average Points per Gameweek**")
        
        # Sort by average points
        sorted_avg = team_avg_points.sort_values('avg_points', ascending=False).reset_index(drop=True)
        sorted_avg['Rank'] = range(1, len(sorted_avg) + 1)
        
        # Display table
        display_cols = ['Rank', 'team_name', 'avg_points']
        display_df = sorted_avg[display_cols].copy()
        display_df.columns = ['Rank', 'Team', 'Avg Points/GW']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=400,
            hide_index=True
        )
    
    with col_rank2:
        st.markdown("**Team Rankings Bar Chart**")
        
        sorted_avg_viz = team_avg_points.sort_values('avg_points', ascending=True)
        
        fig = px.bar(
            sorted_avg_viz,
            y='team_name',
            x='avg_points',
            color='avg_points',
            color_continuous_scale='RdYlGn',
            orientation='h',
            text='avg_points',
            title="Average Points per Gameweek",
            labels={'avg_points': 'Points', 'team_name': 'Team'}
        )
        fig.update_traces(textposition='outside', texttemplate='%{text:.1f}')
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
#                    TAB 3: TRENDS
# ============================================================

with tab3:
    st.subheader("Performance Trends Over Gameweeks")
    
    # Prepare data for trend analysis
    team_gw_points_melted = team_gw_points.reset_index().melt(
        id_vars='manager_team_name',
        var_name='gw',
        value_name='points'
    ) if not team_gw_points.empty else pd.DataFrame(columns=['manager_team_name', 'gw', 'points'])
    
    # Remove 'Total' and filter by range
    team_gw_points_melted = team_gw_points_melted[team_gw_points_melted['gw'] != 'Total']
    if not team_gw_points_melted.empty:
        team_gw_points_melted['gw'] = team_gw_points_melted['gw'].astype(int)
        team_gw_points_melted = team_gw_points_melted[
            (team_gw_points_melted['gw'] >= selected_gw_range[0]) &
            (team_gw_points_melted['gw'] <= selected_gw_range[1])
        ]
    
    col_trend1, col_trend2 = st.columns([1, 1], gap="large")
    
    with col_trend1:
        st.markdown("**Weekly Points Trend**")
        
        if not team_gw_points_melted.empty:
            # Interactive line chart
            fig_line = go.Figure()
            
            for team in team_gw_points_melted['manager_team_name'].unique():
                team_data = team_gw_points_melted[team_gw_points_melted['manager_team_name'] == team]
                fig_line.add_trace(go.Scatter(
                    x=team_data['gw'],
                    y=team_data['points'],
                    mode='lines+markers',
                    name=team,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            fig_line.update_layout(
                title="Weekly Points by Manager",
                xaxis_title="Gameweek",
                yaxis_title="Points",
                height=400,
                hovermode='x unified',
                template='plotly_white'
            )
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No data available for trend analysis.")
    
    with col_trend2:
        st.markdown("**Cumulative Season Points**")
        
        if not team_gw_points_melted.empty:
            # Calculate cumulative points
            team_cumsum = team_gw_points_melted.copy()
            team_cumsum['season_points'] = team_cumsum.groupby('manager_team_name')['points'].cumsum()
            
            fig_cumsum = go.Figure()
            
            for team in team_cumsum['manager_team_name'].unique():
                team_data = team_cumsum[team_cumsum['manager_team_name'] == team]
                fig_cumsum.add_trace(go.Scatter(
                    x=team_data['gw'],
                    y=team_data['season_points'],
                    mode='lines+markers',
                    name=team,
                    line=dict(width=2),
                    marker=dict(size=6),
                    fill='tozeroy'
                ))
            
            fig_cumsum.update_layout(
                title="Cumulative Season Points",
                xaxis_title="Gameweek",
                yaxis_title="Total Points",
                height=400,
                hovermode='x unified',
                template='plotly_white'
            )
            st.plotly_chart(fig_cumsum, use_container_width=True)
        else:
            st.info("No data available for trend analysis.")

# ============================================================
#                    TAB 4: ADVANCED ANALYSIS
# ============================================================

with tab4:
    st.subheader("Advanced Analytics")
    
    # Heatmap section
    st.markdown("**Performance Heatmap (Points by Manager × Gameweek)**")
    
    heatmap_data = team_gw_points.loc[:, [c for c in team_gw_points.columns if c != 'Total']]
    if not heatmap_data.empty:
        heatmap_data = heatmap_data.loc[:, heatmap_data.columns[
            (heatmap_data.columns >= selected_gw_range[0]) & 
            (heatmap_data.columns <= selected_gw_range[1])
        ]]
        
        if not heatmap_data.empty:
            col_heat1, col_heat2 = st.columns([1, 1], gap="large")
            
            with col_heat1:
                fig_heatmap = px.imshow(
                    heatmap_data,
                    labels=dict(x="Gameweek", y="Manager", color="Points"),
                    x=heatmap_data.columns,
                    y=heatmap_data.index,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Viridis",
                    title="Points Heatmap"
                )
                fig_heatmap.update_layout(height=450)
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            with col_heat2:
                st.markdown("**Heatmap Insights**")
                
                # Calculate insights
                with st.expander("📊 Detailed Analysis", expanded=True):
                    st.markdown("**Highest Point Games:**")
                    
                    # Find max points per manager
                    max_per_manager = heatmap_data.max(axis=1).sort_values(ascending=False)
                    for manager, max_pts in max_per_manager.items():
                        st.markdown(f"• {manager}: **{max_pts:.0f} pts**")
                    
                    st.markdown("---")
                    st.markdown("**Consistency Scores (Std Dev):**")
                    
                    # Calculate standard deviation per manager
                    consistency = heatmap_data.std(axis=1).sort_values()
                    for manager, std in consistency.items():
                        consistency_score = (1 - (std / heatmap_data.std().max())) * 100
                        st.markdown(f"• {manager}: **{consistency_score:.1f}%** (Lower variance = more consistent)")
        else:
            st.info("No data available for heatmap.")
    else:
        st.info("No data available for analysis.")

# ============================================================
#                    TAB 5: OPTIMIZED LEAGUE
# ============================================================

with tab5:
    display_league_optimized_lineups(filtered_df)

st.markdown("---")

# ============================================================
#                    FOOTER
# ============================================================

with st.expander("📋 About This Dashboard", expanded=False):
    st.markdown("""
    ### Dashboard Information
    
    This comprehensive FPL league dashboard provides:
    
    **Features:**
    - 📊 **Team Performance**: Compare all teams' weekly and cumulative scores
    - 🏆 **Rankings**: View teams ranked by average points per gameweek
    - 📈 **Trends**: Track performance trends across the season
    - 🎯 **Advanced Analytics**: Heatmaps and consistency analysis
    - 🏆 **Optimized League**: See league-wide optimal vs actual lineup performance
    
    **Filtering Options:**
    - Gameweek Range: Select specific gameweeks to analyze
    - Manager Filter: Focus on a single manager or view all
    
    **Data Source:**
    - Gameweek data from Supabase
    - Starting XI statistics
    - Live league standings
    
    **Tips:**
    - Use the gameweek slider to focus on specific periods
    - Click on tabs to explore different perspectives
    - Hover over charts for detailed information
    - Use the manager filter to isolate individual performance
    """)