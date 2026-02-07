
# ======================= IMPORTS =======================
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY
from core.data_utils import (
    load_data_supabase,
    get_manager_data,
    get_starting_lineup,
    calculate_team_gw_points,
    get_teams_avg_points,
    points_per_player_position,
    get_top_performers,
    get_player_progression
)
from core.visuals_utils import (
    display_overview,
    display_performance_trend,
    display_latest_gw,
    display_player_progression,
    display_other_stats,
    display_player_clustering,
    display_player_trends,
    display_consistency_analysis,
    display_player_archetypes_analysis
)


# ======================= CONFIGURATION =======================
st.set_page_config(layout="wide")


# ======================= LOAD DATA & INIT SUPABASE =======================
OWNER = "ldnm99"
REPO = "FPL-ETL"
TOKEN = st.secrets["TOKEN_STREAMLIT"]
BUCKET = "data"  # your Supabase Storage bucket
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_supabase(supabase)  # <-- unpack all 4

# Try to load players data from CSV, fallback to empty dataframe
players = pd.DataFrame()
try:
    players = pd.read_csv("Data/players_data.csv")
except FileNotFoundError:
    st.warning("⚠️ Players data file not found. Using gameweek data only.")
except Exception as e:
    st.warning(f"⚠️ Could not load players file: {str(e)}")


# ======================= PAGE TITLE =======================
st.title("📊 FPL Players Data Analysis")
st.markdown("Comprehensive data science analysis of player performance, trends, and archetypes")

# ======================= TABS =======================
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Data Overview",
    "📋 Player Data", 
    "🎯 Clustering Analysis", 
    "📈 Trend Analysis",
    "🎭 Archetypes",
    "📊 Consistency"
])

# ======================= TAB 0: DATA OVERVIEW =======================
with tab0:
    st.header("📊 Dataset Overview & Analysis")
    
    # ===== SECTION 1: DATASET SUMMARY =====
    st.subheader("1️⃣ Dataset Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{len(df):,}")
    with col2:
        st.metric("Unique Players", f"{df['player_name'].nunique():,}")
    with col3:
        st.metric("Gameweeks", f"{df['gameweek_num'].nunique():,}")
    with col4:
        st.metric("Teams", f"{df['short_name'].nunique():,}")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Owned Players", f"{df['team_name'].notna().sum():,}")
    with col6:
        st.metric("Free Agents", f"{df['team_name'].isna().sum():,}")
    with col7:
        st.metric("Total Columns", f"{len(df.columns):,}")
    with col8:
        st.metric("Data Size (MB)", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f}")
    
    st.markdown("---")
    
    # ===== SECTION 2: MISSING DATA ANALYSIS =====
    st.subheader("2️⃣ Missing Data Analysis")
    
    # Calculate missing data
    missing_data = pd.DataFrame({
        'Column': df.columns,
        'Missing Count': df.isnull().sum(),
        'Missing %': (df.isnull().sum() / len(df) * 100).round(2)
    }).sort_values('Missing Count', ascending=False)
    
    missing_data = missing_data[missing_data['Missing Count'] > 0]
    
    if len(missing_data) > 0:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Missing data bar chart
            fig = px.bar(
                missing_data.head(15),
                x='Missing %',
                y='Column',
                orientation='h',
                title='Top 15 Columns with Missing Data',
                labels={'Missing %': 'Missing Percentage (%)', 'Column': 'Column Name'},
                color='Missing %',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Missing Data Summary**")
            st.dataframe(
                missing_data.head(15).style.format({'Missing %': '{:.2f}%'}),
                use_container_width=True,
                height=500
            )
    else:
        st.success("✅ No missing data detected in the dataset!")
    
    st.markdown("---")
    
    # ===== SECTION 3: DESCRIPTIVE STATISTICS =====
    st.subheader("3️⃣ Descriptive Statistics")
    
    # Select numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_stat_col = st.selectbox(
            "Select column for detailed stats:",
            options=[col for col in numeric_cols if 'gw_' in col or col in ['season_points', 'gameweek_num']]
        )
    
    with col2:
        st.markdown(f"**Statistics for: {selected_stat_col}**")
        stats = df[selected_stat_col].describe()
        stats_df = pd.DataFrame({
            'Statistic': stats.index,
            'Value': stats.values.round(2)
        })
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    
    # Distribution plot
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram
        fig = px.histogram(
            df,
            x=selected_stat_col,
            nbins=50,
            title=f'Distribution of {selected_stat_col}',
            labels={selected_stat_col: selected_stat_col},
            color_discrete_sequence=['#00D9FF']
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Box plot
        fig = px.box(
            df,
            y=selected_stat_col,
            title=f'Box Plot of {selected_stat_col}',
            labels={selected_stat_col: selected_stat_col},
            color_discrete_sequence=['#FF6692']
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ===== SECTION 4: DATA QUALITY METRICS =====
    st.subheader("4️⃣ Data Quality Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Completeness**")
        completeness = ((len(df) * len(df.columns) - df.isnull().sum().sum()) / (len(df) * len(df.columns)) * 100)
        st.metric("Data Completeness", f"{completeness:.2f}%")
        
        # Completeness by position
        if 'player_position' in df.columns:
            pos_completeness = df.groupby('player_position').apply(
                lambda x: ((len(x) * len(x.columns) - x.isnull().sum().sum()) / (len(x) * len(x.columns)) * 100)
            ).round(2)
            st.dataframe(pos_completeness.to_frame('Completeness %'), use_container_width=True)
    
    with col2:
        st.markdown("**Data Consistency**")
        # Check for duplicate records
        duplicates = df.duplicated().sum()
        st.metric("Duplicate Records", f"{duplicates:,}")
        
        # Check for negative values in points columns
        points_cols = [col for col in df.columns if 'points' in col.lower() and df[col].dtype in [np.float64, np.int64]]
        if points_cols:
            negative_points = sum((df[col] < 0).sum() for col in points_cols)
            st.metric("Negative Point Values", f"{negative_points:,}")
    
    with col3:
        st.markdown("**Data Distribution**")
        # Records per gameweek
        records_per_gw = df.groupby('gameweek_num').size()
        st.metric("Avg Records/GW", f"{records_per_gw.mean():.0f}")
        st.metric("Min Records/GW", f"{records_per_gw.min():,}")
        st.metric("Max Records/GW", f"{records_per_gw.max():,}")
    
    st.markdown("---")
    
    # ===== SECTION 5: BASIC INSIGHTS =====
    st.subheader("5️⃣ Basic Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Top 10 Players by Season Points**")
        top_players = df.groupby('player_name').agg({
            'season_points': 'max',
            'short_name': 'first',
            'player_position': 'first'
        }).sort_values('season_points', ascending=False).head(10).reset_index()
        
        top_players.columns = ['Player', 'Season Points', 'Team', 'Position']
        st.dataframe(top_players, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Position Distribution**")
        if 'player_position' in df.columns:
            # Get unique player-position combinations
            unique_players = df.drop_duplicates(subset=['player_name'])[['player_name', 'player_position']]
            pos_dist = unique_players['player_position'].value_counts()
            
            fig = px.pie(
                values=pos_dist.values,
                names=pos_dist.index,
                title='Players by Position',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Points Distribution by Position**")
        if 'player_position' in df.columns and 'gw_points' in df.columns:
            pos_points = df.groupby('player_position')['gw_points'].agg(['mean', 'median', 'sum']).round(2)
            pos_points.columns = ['Avg Points/GW', 'Median Points/GW', 'Total Points']
            st.dataframe(pos_points, use_container_width=True)
    
    with col2:
        st.markdown("**Gameweek Progression**")
        gw_stats = df.groupby('gameweek_num').agg({
            'gw_points': 'sum',
            'player_name': 'count'
        }).reset_index()
        gw_stats.columns = ['Gameweek', 'Total Points', 'Players']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=gw_stats['Gameweek'],
            y=gw_stats['Total Points'],
            name='Total Points',
            line=dict(color='#00D9FF', width=3)
        ))
        fig.update_layout(
            title='Total Points by Gameweek',
            xaxis_title='Gameweek',
            yaxis_title='Total Points',
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # ===== SECTION 6: COLUMN INFORMATION =====
    with st.expander("📋 View All Column Information"):
        col_info = pd.DataFrame({
            'Column': df.columns,
            'Data Type': df.dtypes.astype(str),
            'Non-Null Count': df.count(),
            'Null Count': df.isnull().sum(),
            'Unique Values': [df[col].nunique() for col in df.columns]
        })
        st.dataframe(col_info, use_container_width=True, hide_index=True)


# ======================= TAB 1: PLAYER DATA =======================
with tab1:
    st.header("Player Data Overview")
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.subheader("All Players (Season Summary)")
        
        if not players.empty:
            # Player selection
            selected_player = st.selectbox("Select Player", options=[""] + sorted(players['name'].unique().tolist()))
            
            if selected_player:
                filtered_players = players[players['name'] == selected_player]
            else:
                filtered_players = players.copy()
            
            filtered_players = filtered_players[['name','team','Total points','position','Goals Scored','Assists','CS','xG','starts','yellow_cards','red_cards','news']]
            filtered_players.rename(columns={'name': 'Name', 'team': 'Team', 'Total points': 'Total Points', 'position': 'Position', 'Goals Scored': 'Goals Scored', 'Assists': 'Assists', 'CS': 'Clean Sheets', 'xG': 'xG', 'starts': 'Starts', 'yellow_cards': 'Yellow Cards', 'red_cards': 'Red Cards', 'news': 'News'}, inplace=True)
            
            st.dataframe(filtered_players, use_container_width=True)
        else:
            st.info("📊 Players data not available. See Gameweek Performance Data on the right.")
    
    with col2:
        st.subheader("Gameweek Performance Data")
        
        # Filters
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            owned_only = st.checkbox("Show owned players")
        with col_f2:
            not_owned_only = st.checkbox("Show not owned players")
        
        # Filter logic
        filtered_df = df.copy()
        
        if owned_only:
            filtered_df = filtered_df[filtered_df['team_name'].notnull()]
        
        if not_owned_only:
            filtered_df = filtered_df[filtered_df['team_name'].isnull()]
        
        # Safe column selection - only select columns that exist
        available_cols = filtered_df.columns.tolist()
        
        # Try primary column set, fallback to available columns
        primary_cols = ['team_name', 'player_name', 'short_name', 'gw_points', 'gameweek_num', 'season_points',
                       'gw_goals', 'gw_assists', 'gw_bonus', 'gw_minutes', 'gw_expected_goals', 'gw_expected_assists', 'player_position']
        
        # Filter to only columns that exist in the dataframe
        cols_to_use = [col for col in primary_cols if col in available_cols]
        
        if not cols_to_use:
            # If none of the expected columns exist, show all data
            st.warning(f"⚠️ Expected columns not found. Available columns: {available_cols[:10]}...")
            st.dataframe(filtered_df.head(100), use_container_width=True, height=400)
        else:
            filtered_df = filtered_df[cols_to_use]
            
            # Build rename dictionary only for columns that exist
            rename_map = {
                'team_name': 'Manager', 
                'player_name': 'Name', 
                'short_name': 'Team', 
                'gw_points': 'GW Points', 
                'gameweek_num': 'Gameweek', 
                'season_points': 'Season Points', 
                'gw_goals': 'GW Goals', 
                'gw_assists': 'GW Assists', 
                'gw_bonus': 'GW Bonus', 
                'gw_minutes': 'GW Minutes', 
                'gw_expected_goals': 'GW xG', 
                'gw_expected_assists': 'GW xA', 
                'player_position': 'Position'
            }
            rename_map = {k: v for k, v in rename_map.items() if k in filtered_df.columns}
            filtered_df.rename(columns=rename_map, inplace=True)
            
            st.dataframe(filtered_df, use_container_width=True, height=400)

# ======================= TAB 2: CLUSTERING =======================
with tab2:
    display_player_clustering(df)

# ======================= TAB 3: TRENDS =======================
with tab3:
    display_player_trends(df)

# ======================= TAB 4: ARCHETYPES =======================
with tab4:
    display_player_archetypes_analysis(df)

# ======================= TAB 5: CONSISTENCY =======================
with tab5:
    display_consistency_analysis(df)

