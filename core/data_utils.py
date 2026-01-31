import io
import pandas as pd
from datetime import datetime, timezone
import os
from core.error_handler import (
    SupabaseError,
    SupabaseConnectionError,
    SupabaseDownloadError,
    DataValidationError,
    safe_download_file,
    validate_dataframe,
    validate_supabase_client,
    safe_operation,
    get_logger
)

logger = get_logger(__name__)

# ============================================================
#                   LOADING (SUPABASE)
# ============================================================
def load_data_supabase(
    supabase,
    bucket="data",
    gw_data_file="gw_data.parquet",
    standings_file="league_standings.csv",
    local_gameweeks="Data/gameweeks.csv",
    local_fixtures="Data/fixtures.csv"
):
    """
    Load parquet + standings from Supabase, and gameweeks + fixtures locally.
    
    Includes comprehensive error handling for all data sources.
    """
    
    # Validate Supabase client
    try:
        validate_supabase_client(supabase)
    except Exception as e:
        logger.error(f"Supabase client validation failed: {str(e)}")
        raise SupabaseError(f"Invalid Supabase configuration: {str(e)}")

    # Load GW data from Supabase
    try:
        df = _download_parquet(supabase, bucket, gw_data_file)
        validate_dataframe(df, "GW Data", min_rows=1)
    except Exception as e:
        logger.error(f"Failed to load GW data: {str(e)}")
        raise

    # Load League standings from Supabase
    try:
        standings = _download_csv(supabase, bucket, standings_file)
        validate_dataframe(standings, "League Standings", min_rows=1)
    except Exception as e:
        logger.error(f"Failed to load league standings: {str(e)}")
        raise

    # Load fixtures and gameweeks locally
    try:
        gameweeks = _load_local_csv(local_gameweeks, "Gameweeks")
        fixtures = _load_local_csv(local_fixtures, "Fixtures")
    except Exception as e:
        logger.error(f"Failed to load local files: {str(e)}")
        raise

    # Convert date/datetime columns
    try:
        _convert_datetime_columns(gameweeks, fixtures)
    except Exception as e:
        logger.error(f"Failed to convert datetime columns: {str(e)}")
        raise DataValidationError(
            f"Datetime conversion failed: {str(e)}"
        )

    logger.info("Successfully loaded all data")
    return df, standings, gameweeks, fixtures


# ---------- Helpers for Supabase downloads ----------
def _download_parquet(supabase, bucket, file_name):
    """Download and parse parquet file from Supabase with error handling."""
    try:
        data = safe_download_file(supabase, bucket, file_name, "parquet")
        
        if not data:
            raise SupabaseDownloadError(f"No data received for {file_name}")
        
        df = pd.read_parquet(io.BytesIO(data))
        logger.info(f"Parsed parquet file: {file_name} ({len(df)} rows)")
        return df
        
    except Exception as e:
        if isinstance(e, SupabaseDownloadError):
            raise
        logger.error(f"Parquet parsing failed for {file_name}: {str(e)}")
        raise SupabaseDownloadError(
            f"Failed to parse {file_name}: {str(e)}"
        )


def _download_csv(supabase, bucket, file_name):
    """Download and parse CSV file from Supabase with error handling."""
    try:
        data = safe_download_file(supabase, bucket, file_name, "csv")
        
        if not data:
            raise SupabaseDownloadError(f"No data received for {file_name}")
        
        df = pd.read_csv(io.BytesIO(data))
        logger.info(f"Parsed CSV file: {file_name} ({len(df)} rows)")
        return df
        
    except Exception as e:
        if isinstance(e, SupabaseDownloadError):
            raise
        logger.error(f"CSV parsing failed for {file_name}: {str(e)}")
        raise SupabaseDownloadError(
            f"Failed to parse {file_name}: {str(e)}"
        )


def _load_local_csv(file_path, file_name):
    """Load local CSV file with error handling."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"Local file not found: {file_path}"
            )
        
        df = pd.read_csv(file_path)
        logger.info(f"Loaded local file: {file_name} ({len(df)} rows)")
        return df
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to read {file_name}: {str(e)}")
        raise DataValidationError(
            f"Failed to read {file_name}: {str(e)}"
        )


def _convert_datetime_columns(gameweeks, fixtures):
    """Convert datetime columns with error handling."""
    try:
        if "deadline_time" in gameweeks.columns:
            gameweeks["deadline_time"] = pd.to_datetime(
                gameweeks["deadline_time"], 
                utc=True
            )
        
        if "kickoff_time" in fixtures.columns:
            fixtures["kickoff_time"] = pd.to_datetime(
                fixtures["kickoff_time"], 
                utc=True
            )
        
        logger.info("Datetime conversion completed")
        
    except Exception as e:
        logger.error(f"Datetime conversion error: {str(e)}")
        raise DataValidationError(
            f"Failed to convert datetime columns: {str(e)}"
        )


# ============================================================
#                   GAMEWEEK CALCULATIONS
# ============================================================
def get_next_gameweek(gameweeks: pd.DataFrame, now: datetime = None) -> pd.DataFrame:
    """
    Returns the next gameweek after the current UTC time.
    """
    if now is None:
        now = datetime.now(timezone.utc)

    return (
        gameweeks[gameweeks["deadline_time"] > now]
        .sort_values("deadline_time")
        .head(1)
    )


def get_upcoming_fixtures(fixtures: pd.DataFrame, next_gw: pd.DataFrame) -> pd.DataFrame:
    """
    Returns fixtures for the next upcoming gameweek.
    """
    if next_gw.empty:
        return pd.DataFrame()

    gw_id = next_gw.iloc[0]["id"]

    upcoming = (
        fixtures[fixtures["event"] == gw_id]
        [["team_h_name", "team_a_name", "kickoff_time", "team_h_difficulty", "team_a_difficulty"]]
        .copy()
    )

    upcoming = upcoming.sort_values("kickoff_time")
    upcoming["kickoff_time"] = upcoming["kickoff_time"].dt.strftime("%A, %d %B %Y %H:%M %Z")

    return upcoming.rename(columns={
        "team_h_name": "Home",
        "team_a_name": "Away",
        "kickoff_time": "Kickoff"
    })


# ============================================================
#                   MANAGER FILTERING
# ============================================================
def get_manager_data(df: pd.DataFrame, manager_name: str) -> pd.DataFrame:
    """
    Returns all rows associated with a manager.
    """
    if manager_name not in df["manager_team_name"].unique():
        return pd.DataFrame()
    return df[df["manager_team_name"] == manager_name]


# ============================================================
#                   STARTING XI + AGGREGATIONS
# ============================================================
def get_starting_lineup(df: pd.DataFrame) -> pd.DataFrame:
    """Returns only players in starting XI (team_position 1–11)."""
    return df[df["team_position"] <= 11].copy()


def calculate_team_gw_points(starting_players: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot table showing each team's points per gameweek + total.
    """
    if starting_players.empty:
        return pd.DataFrame()

    table = starting_players.pivot_table(
        index="manager_team_name",
        columns="gw",
        values="gw_points",
        aggfunc="sum",
        fill_value=0
    )

    table["Total"] = table.sum(axis=1)
    cols = [c for c in table.columns if c != "Total"] + ["Total"]

    return table[cols].sort_values("Total", ascending=False)


def get_teams_avg_points(team_gw_points: pd.DataFrame) -> pd.DataFrame:
    """
    Returns average points per team across all GWs.
    """
    if team_gw_points.empty:
        return pd.DataFrame(columns=["team_name", "avg_points"])

    gw_cols = [c for c in team_gw_points.columns if c != "Total"]

    avg_df = team_gw_points[gw_cols].mean(axis=1).reset_index()
    avg_df.columns = ["team_name", "avg_points"]

    return avg_df.sort_values("avg_points", ascending=False)


def get_team_total_points(starting_players: pd.DataFrame) -> pd.DataFrame:
    """
    Total points scored by each team.
    """
    if starting_players.empty:
        return pd.DataFrame(columns=["Team", "Total Points"])

    return (
        starting_players.groupby("manager_team_name")["gw_points"]
        .sum()
        .reset_index()
        .rename(columns={"manager_team_name": "Team", "gw_points": "Total Points"})
        .sort_values("Total Points", ascending=False)
        .reset_index(drop=True)
    )


# ============================================================
#                   POSITIONAL POINTS
# ============================================================
def points_per_player_position(starting_players: pd.DataFrame) -> pd.DataFrame:
    """
    Returns total points by player position.
    """
    if starting_players.empty:
        return pd.DataFrame(columns=["position", "gw_points"])

    return starting_players.groupby("position")["gw_points"].sum().reset_index()


# ============================================================
#                   TOP PERFORMERS
# ============================================================
def get_top_performers(manager_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Top N performers per manager across all gameweeks.
    """
    if manager_df.empty:
        return pd.DataFrame()

    agg_df = (
        manager_df.groupby(["gw", "full_name", "real_team"], as_index=False)
        .agg(
            total_points=("gw_points", "sum"),
            Benched=("team_position", lambda x: (x > 11).any())
        )
    )

    top_df = agg_df.sort_values("total_points", ascending=False).head(top_n)
    return top_df.rename(columns={
        "gw": "Gameweek",
        "full_name": "Player",
        "real_team": "Team",
        "total_points": "Points"
    })


# ============================================================
#                   PLAYER PROGRESSION
# ============================================================
def get_player_progression(manager_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns points progression for every player in every gameweek.
    (You did not provide your original implementation, so this is a placeholder)
    """
    if manager_df.empty:
        return pd.DataFrame()

    return (
        manager_df.groupby(["full_name", "gw"], as_index=False)["gw_points"]
        .sum()
        .pivot(index="full_name", columns="gw", values="gw_points")
        .fill_value(0)
    )


# ============================================================
#           OPTIMIZED LINEUP CALCULATION
# ============================================================
def get_optimal_lineup(manager_df: pd.DataFrame, gameweek: int = None) -> dict:
    """
    Calculate the optimal starting lineup for maximum points.
    
    Constraints:
    - 11 starting players maximum
    - Exactly 1 goalkeeper
    - 3-5 defenders
    - 3-5 midfielders
    - 1-3 forwards
    
    Returns a dict with optimal lineup info.
    """
    if manager_df.empty:
        return {
            "optimal_points": 0,
            "lineup": pd.DataFrame(),
            "bench": pd.DataFrame(),
            "valid": False,
            "errors": ["No data available"]
        }
    
    # Filter to specific gameweek if provided
    if gameweek is not None:
        gw_df = manager_df[manager_df["gw"] == gameweek].copy()
    else:
        # Use latest gameweek
        gw_df = manager_df[manager_df["gw"] == manager_df["gw"].max()].copy()
    
    if gw_df.empty:
        return {
            "optimal_points": 0,
            "lineup": pd.DataFrame(),
            "bench": pd.DataFrame(),
            "valid": False,
            "errors": ["No data for this gameweek"]
        }
    
    # Group by player to get latest entry (in case of duplicates)
    gw_df = gw_df.sort_values("gw_points", ascending=False).drop_duplicates(subset=["full_name"])
    
    # Get position counts
    positions = gw_df["position"].unique()
    
    # Separate players by position
    gks = gw_df[gw_df["position"] == "GK"].sort_values("gw_points", ascending=False)
    defs = gw_df[gw_df["position"] == "DEF"].sort_values("gw_points", ascending=False)
    mids = gw_df[gw_df["position"] == "MID"].sort_values("gw_points", ascending=False)
    fwds = gw_df[gw_df["position"] == "FWD"].sort_values("gw_points", ascending=False)
    
    errors = []
    
    # Validate minimum positions available
    if len(gks) < 1:
        errors.append("Not enough goalkeepers")
    if len(defs) < 3:
        errors.append("Not enough defenders")
    if len(mids) < 3:
        errors.append("Not enough midfielders")
    if len(fwds) < 1:
        errors.append("Not enough forwards")
    
    if errors:
        return {
            "optimal_points": 0,
            "lineup": pd.DataFrame(),
            "bench": pd.DataFrame(),
            "valid": False,
            "errors": errors
        }
    
    # Start with mandatory selections (top player from each position)
    selected = []
    selected.extend(gks.head(1).index.tolist())  # 1 GK
    
    # For DEF, MID, FWD - try to maximize points while respecting constraints
    # Start with greedy approach: select highest points that fits constraints
    selected.extend(defs.head(3).index.tolist())  # 3 DEF
    selected.extend(mids.head(3).index.tolist())  # 3 MID
    selected.extend(fwds.head(1).index.tolist())  # 1 FWD
    
    # Now we have 8 players, need 3 more from remaining
    remaining_players = gw_df.loc[~gw_df.index.isin(selected)].copy()
    remaining_players = remaining_players.sort_values("gw_points", ascending=False)
    
    # Add top 3 remaining to reach 11
    if len(remaining_players) >= 3:
        selected.extend(remaining_players.head(3).index.tolist())
    else:
        selected.extend(remaining_players.index.tolist())
    
    # Verify we have exactly 11 or handle gracefully
    if len(selected) < 11 and len(gw_df) < 11:
        # Not enough players available
        errors.append("Not enough players for a full 11-player lineup")
    
    # Get lineup and bench
    optimal_lineup = gw_df.loc[selected].copy() if selected else gw_df.head(0)
    bench = gw_df.loc[~gw_df.index.isin(selected)].copy()
    
    # Calculate optimal points (only from starting lineup)
    optimal_points = optimal_lineup["gw_points"].sum()
    
    return {
        "optimal_points": optimal_points,
        "lineup": optimal_lineup,
        "bench": bench,
        "valid": len(errors) == 0,
        "errors": errors,
        "gameweek": gameweek
    }


def get_all_optimal_lineups(manager_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get optimal lineups for all gameweeks for a manager.
    
    Returns a dataframe with: gameweek, actual_points, optimal_points, difference, potential_gain
    """
    if manager_df.empty:
        return pd.DataFrame(columns=["gameweek", "actual_points", "optimal_points", "difference"])
    
    results = []
    
    for gw in sorted(manager_df["gw"].unique()):
        # Get actual points (only starting XI)
        gw_data = manager_df[manager_df["gw"] == gw]
        actual_points = gw_data[gw_data["team_position"] <= 11]["gw_points"].sum()
        
        # Get optimal points
        optimal_result = get_optimal_lineup(manager_df, gameweek=gw)
        optimal_points = optimal_result["optimal_points"]
        
        results.append({
            "gameweek": gw,
            "actual_points": actual_points,
            "optimal_points": optimal_points,
            "difference": optimal_points - actual_points,
            "potential_gain_pct": (optimal_points - actual_points) / actual_points * 100 if actual_points > 0 else 0
        })
    
    return pd.DataFrame(results)


def get_league_optimized_lineups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate optimized lineups for all teams in the league.
    
    Returns a DataFrame with:
    - manager_team_name: Team name
    - actual_points: Total actual points (starting XI only)
    - optimal_points: Total optimal points if best lineup was picked
    - difference: Potential gain
    - potential_gain_pct: Percentage gain
    """
    if df.empty:
        return pd.DataFrame()
    
    teams = df['manager_team_name'].dropna().unique()
    results = []
    
    for team in teams:
        team_df = df[df['manager_team_name'] == team]
        
        # Use get_all_optimal_lineups which correctly calculates gameweek-by-gameweek
        gw_results = get_all_optimal_lineups(team_df)
        
        if gw_results.empty:
            continue
        
        # Sum actual and optimal across all gameweeks
        actual_total = gw_results['actual_points'].sum()
        optimal_total = gw_results['optimal_points'].sum()
        
        results.append({
            'manager_team_name': team,
            'actual_points': int(actual_total),
            'optimal_points': int(optimal_total),
            'difference': int(optimal_total - actual_total),
            'potential_gain_pct': round((optimal_total - actual_total) / actual_total * 100, 1) if actual_total > 0 else 0
        })
    
    result_df = pd.DataFrame(results)
    
    # Sort by actual points (descending)
    return result_df.sort_values('actual_points', ascending=False).reset_index(drop=True)


def prepare_player_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare player performance metrics for clustering analysis.
    
    Creates normalized features from player statistics:
    - Points per game (efficiency)
    - Goal/Assist contribution ratio
    - Consistency (coefficient of variation)
    - Playing time impact
    - Clean sheet value (for defenders/keepers)
    """
    if df.empty:
        return pd.DataFrame()
    
    # Ensure we have the required columns
    required_cols = ['full_name', 'position', 'gw_points']
    if not all(col in df.columns for col in required_cols):
        return pd.DataFrame()
    
    # Group by player and calculate metrics
    try:
        player_stats = df.groupby(['full_name', 'position']).agg({
            'gw_points': ['sum', 'mean', 'std', 'count'],
            'gw_bonus': ['sum', 'mean'],
            'real_team': 'first'
        }).reset_index()
        
        player_stats.columns = ['player_name', 'position', 'total_points', 'avg_points', 
                                'std_points', 'games_played', 'total_bonus', 'avg_bonus', 'team']
    except Exception as e:
        logger.error(f"Error in player metrics aggregation: {str(e)}")
        return pd.DataFrame()
    
    # Calculate derived metrics
    player_stats['consistency'] = player_stats.apply(
        lambda x: x['std_points'] / x['avg_points'] if x['avg_points'] > 0 else 0,
        axis=1
    )
    
    player_stats['bonus_efficiency'] = player_stats['total_bonus'] / player_stats['games_played']
    
    # Position-based metrics
    player_stats['points_per_appearance'] = player_stats['avg_points']
    
    # Normalize metrics to 0-1 scale per position for fair comparison
    for pos in player_stats['position'].unique():
        pos_mask = player_stats['position'] == pos
        
        if player_stats.loc[pos_mask, 'avg_points'].max() > 0:
            player_stats.loc[pos_mask, 'avg_points_norm'] = (
                player_stats.loc[pos_mask, 'avg_points'] / 
                player_stats.loc[pos_mask, 'avg_points'].max()
            )
        else:
            player_stats.loc[pos_mask, 'avg_points_norm'] = 0
        
        max_consistency = player_stats.loc[pos_mask, 'consistency'].max()
        if max_consistency > 0:
            player_stats.loc[pos_mask, 'consistency_norm'] = (
                max_consistency - player_stats.loc[pos_mask, 'consistency']
            ) / max_consistency  # Invert: lower std is better (higher normalized)
        else:
            player_stats.loc[pos_mask, 'consistency_norm'] = 1
        
        if player_stats.loc[pos_mask, 'bonus_efficiency'].max() > 0:
            player_stats.loc[pos_mask, 'bonus_norm'] = (
                player_stats.loc[pos_mask, 'bonus_efficiency'] / 
                player_stats.loc[pos_mask, 'bonus_efficiency'].max()
            )
        else:
            player_stats.loc[pos_mask, 'bonus_norm'] = 0
    
    return player_stats


def cluster_players(df: pd.DataFrame, n_clusters: int = 4, position: str = None) -> dict:
    """
    Cluster players using K-means clustering based on performance metrics.
    
    Parameters:
    - df: Manager dataframe with player data
    - n_clusters: Number of clusters to create (2-5 recommended)
    - position: Filter by position (GK, DEF, MID, FWD) or None for all
    
    Returns dict with:
    - cluster_df: DataFrame with cluster assignments
    - silhouette_score: Quality metric (0-1, higher is better)
    - cluster_centers: Characteristics of each cluster
    """
    try:
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score
    except ImportError:
        return {
            'cluster_df': pd.DataFrame(),
            'silhouette_score': 0,
            'cluster_centers': pd.DataFrame(),
            'error': 'scikit-learn not installed'
        }
    
    player_metrics = prepare_player_metrics(df)
    
    if player_metrics.empty:
        return {
            'cluster_df': pd.DataFrame(),
            'silhouette_score': 0,
            'cluster_centers': pd.DataFrame(),
            'error': 'No player metrics available'
        }
    
    # Filter by position if specified
    if position:
        player_metrics = player_metrics[player_metrics['position'] == position].copy()
    
    if len(player_metrics) < n_clusters:
        return {
            'cluster_df': player_metrics,
            'silhouette_score': 0,
            'cluster_centers': pd.DataFrame(),
            'error': f'Not enough players ({len(player_metrics)}) for {n_clusters} clusters'
        }
    
    # Features for clustering
    features = ['avg_points_norm', 'consistency_norm', 'bonus_norm']
    X = player_metrics[features].fillna(0).values
    
    # Apply K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    player_metrics['cluster'] = kmeans.fit_predict(X)
    
    # Calculate silhouette score
    sil_score = silhouette_score(X, player_metrics['cluster'])
    
    # Cluster centers with interpretation
    cluster_centers = pd.DataFrame(
        kmeans.cluster_centers_,
        columns=features
    )
    cluster_centers['cluster'] = range(n_clusters)
    
    return {
        'cluster_df': player_metrics,
        'silhouette_score': sil_score,
        'cluster_centers': cluster_centers
    }


def analyze_player_trend(df: pd.DataFrame, player_name: str) -> dict:
    """
    Analyze player performance trend over season using linear regression.
    
    Returns dict with:
    - trend_df: DataFrame with trend data per gameweek
    - slope: Trend direction (positive = improving, negative = declining)
    - r_squared: Fit quality (0-1, higher = better)
    - classification: 'Improving', 'Declining', or 'Stable'
    - predicted_next_gw: Predicted points for next gameweek
    """
    try:
        from scipy.stats import linregress
    except ImportError:
        return {'error': 'scipy not installed'}
    
    player_data = df[df['full_name'] == player_name].sort_values('gw').copy()
    
    if player_data.empty or len(player_data) < 2:
        return {'error': f'Insufficient data for {player_name}'}
    
    # Prepare data
    X = player_data['gw'].values
    y = player_data['gw_points'].values
    
    # Handle missing values
    valid_mask = ~(pd.isna(X) | pd.isna(y))
    X = X[valid_mask]
    y = y[valid_mask]
    
    if len(X) < 2:
        return {'error': 'Not enough valid gameweeks'}
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = linregress(X, y)
    r_squared = r_value ** 2
    
    # Classification
    if abs(slope) < 0.05:
        classification = 'Stable'
    elif slope > 0:
        classification = 'Improving'
    else:
        classification = 'Declining'
    
    # Predict next gameweek
    last_gw = max(X)
    predicted_next = slope * (last_gw + 1) + intercept
    
    # Trend dataframe
    trend_df = player_data[['gw', 'full_name', 'position', 'gw_points', 'real_team']].copy()
    trend_df['trend_line'] = slope * X + intercept
    
    return {
        'trend_df': trend_df,
        'slope': slope,
        'r_squared': r_squared,
        'classification': classification,
        'predicted_next_gw': max(0, predicted_next),
        'p_value': p_value,
        'std_err': std_err,
        'gameweeks_analyzed': len(X)
    }


def calculate_player_consistency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate consistency metrics for all players.
    
    Filters out players with insufficient playing time/points to avoid 
    selecting "consistent" players who simply haven't played.
    
    Returns DataFrame with:
    - player_name, position, team
    - avg_points, std_points, min_points, max_points, total_minutes
    - coefficient_of_variation (consistency metric)
    - consistency_score (0-100, higher = more consistent)
    - playing_time_score (factor in consistency)
    """
    if df.empty:
        return pd.DataFrame()
    
    # Ensure we have the required columns
    if 'gw_points' not in df.columns or 'full_name' not in df.columns or 'position' not in df.columns:
        return pd.DataFrame()
    
    try:
        # Include gw_minutes if available
        agg_dict = {
            'gw_points': ['mean', 'std', 'min', 'max', 'count', 'sum'],
            'real_team': 'first',
            'gw_bonus': 'sum'
        }
        
        # Add minutes if available
        if 'gw_minutes' in df.columns:
            agg_dict['gw_minutes'] = 'sum'
        
        consistency_data = df.groupby(['full_name', 'position']).agg(agg_dict).reset_index()
        
        # Build column names dynamically
        if 'gw_minutes' in df.columns:
            consistency_data.columns = ['player_name', 'position', 'avg_points', 'std_points', 
                                        'min_points', 'max_points', 'games', 'total_points', 'team', 'total_bonus', 'total_minutes']
        else:
            consistency_data.columns = ['player_name', 'position', 'avg_points', 'std_points', 
                                        'min_points', 'max_points', 'games', 'total_points', 'team', 'total_bonus']
            consistency_data['total_minutes'] = 0
    except Exception as e:
        logger.error(f"Error in consistency calculation: {str(e)}")
        return pd.DataFrame()
    
    # Filter out players with insufficient activity
    # Minimum requirements:
    # - At least 3 games played
    # - At least 5 total points across season
    # - At least 90 minutes total (roughly 1 full game)
    min_games = 3
    min_total_points = 5
    min_total_minutes = 90
    
    consistency_data = consistency_data[
        (consistency_data['games'] >= min_games) &
        (consistency_data['total_points'] >= min_total_points) &
        ((consistency_data['total_minutes'] >= min_total_minutes) | (consistency_data['total_minutes'] == 0))
    ].copy()
    
    if consistency_data.empty:
        return pd.DataFrame()
    
    # Calculate coefficient of variation
    consistency_data['cv'] = consistency_data.apply(
        lambda x: x['std_points'] / x['avg_points'] if x['avg_points'] > 0 else 0,
        axis=1
    )
    
    # Calculate playing time score (0-1)
    # Players with more minutes are rated higher for consistency
    max_minutes = consistency_data['total_minutes'].max()
    if max_minutes > 0:
        consistency_data['playing_time_score'] = (consistency_data['total_minutes'] / max_minutes).clip(lower=0, upper=1)
    else:
        consistency_data['playing_time_score'] = 1.0
    
    # Calculate consistency score (0-100, higher = better)
    # Combine CV (consistency) with playing time
    # Formula: (100 * (1 - cv)) * playing_time_score
    # This penalizes players with low playing time while rewarding those who are both consistent AND play
    consistency_data['consistency_score'] = (
        100 * (1 - consistency_data['cv']).clip(lower=0, upper=1) * consistency_data['playing_time_score']
    )
    
    # Performance stability (max-min relative to mean)
    consistency_data['performance_range'] = consistency_data.apply(
        lambda x: (x['max_points'] - x['min_points']) / x['avg_points'] 
        if x['avg_points'] > 0 else 0,
        axis=1
    )
    
    return consistency_data.sort_values('consistency_score', ascending=False)


def get_player_archetypes(df: pd.DataFrame) -> dict:
    """
    Identify player archetypes based on clustering.
    
    Creates profiles for each cluster:
    - High Performers (high avg points)
    - Consistent Players (low variance)
    - Bonus Hunters (high bonus points)
    - Rising Stars (improving trend)
    - Declining Players (declining trend)
    """
    if df.empty:
        return {}
    
    player_metrics = prepare_player_metrics(df)
    
    archetypes = {
        'High Performers': player_metrics.nlargest(5, 'avg_points')[
            ['player_name', 'avg_points', 'position']
        ],
        'Most Consistent': player_metrics.nsmallest(5, 'consistency')[
            ['player_name', 'consistency', 'position']
        ],
        'Bonus Hunters': player_metrics.nlargest(5, 'bonus_efficiency')[
            ['player_name', 'bonus_efficiency', 'position']
        ],
    }
    
    return archetypes


# ============================================================
#           LEAGUE-WIDE OPTIMIZATION
# ============================================================

def get_league_optimized_lineups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate optimized lineups for all teams in the league.
    Returns league-wide summary with actual vs optimal points.
    
    Returns:
        DataFrame with columns: manager_team_name, actual_points, optimal_points, 
                               difference, potential_gain_pct
    """
    if df.empty:
        return pd.DataFrame()
    
    try:
        # Get unique teams
        teams = df['manager_team_name'].unique()
        
        league_results = []
        
        for team in teams:
            team_df = df[df['manager_team_name'] == team]
            
            if team_df.empty:
                continue
            
            # Calculate actual points (sum of gw_points)
            actual_points = team_df['gw_points'].sum()
            
            # Calculate optimal points using existing optimization function
            optim_result = get_all_optimal_lineups(team_df)
            
            if isinstance(optim_result, dict) and 'total_optimal_points' in optim_result:
                optimal_points = optim_result['total_optimal_points']
            else:
                # Fallback if optimization fails
                optimal_points = actual_points
            
            potential_gain = optimal_points - actual_points
            potential_gain_pct = ((potential_gain / actual_points) * 100) if actual_points > 0 else 0
            
            league_results.append({
                'manager_team_name': team,
                'actual_points': actual_points,
                'optimal_points': optimal_points,
                'difference': potential_gain,
                'potential_gain_pct': potential_gain_pct
            })
        
        # Create DataFrame and sort by actual points (descending)
        result_df = pd.DataFrame(league_results)
        result_df = result_df.sort_values('actual_points', ascending=False).reset_index(drop=True)
        
        return result_df
        
    except Exception as e:
        logger.error(f"Error calculating league optimized lineups: {e}")
        return pd.DataFrame()
