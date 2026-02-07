"""
Medallion Architecture Data Loader for FPL Dashboard.

This module loads data from the Gold layer (star schema) with dimensions and facts.
"""
import io
import pandas as pd
from typing import Dict, Tuple
from core.error_handler import (
    SupabaseError,
    SupabaseDownloadError,
    DataValidationError,
    safe_download_file,
    validate_dataframe,
    validate_supabase_client,
    get_logger
)

logger = get_logger(__name__)

# ============================================================
#                   GOLD LAYER PATHS
# ============================================================
GOLD_DIMENSIONS = {
    'players': 'gold/dimensions/dim_players.parquet',
    'clubs': 'gold/dimensions/dim_clubs.parquet',
    'gameweeks': 'gold/dimensions/dim_gameweeks.parquet',
    'managers': 'gold/dimensions/dim_managers.parquet',
    'fixtures': 'gold/dimensions/dim_fixtures.parquet',
}

GOLD_FACTS = {
    'player_performance': 'gold/facts/fact_player_performance.parquet',
    'manager_picks': 'gold/facts/fact_manager_picks.parquet',
    'seasonal_stats': 'gold/facts/fact_player_seasonal_stats.parquet',
    'manager_gw_performance': 'gold/facts/manager_gameweek_performance.parquet',
}

# Legacy paths (for backward compatibility)
GOLD_LEGACY = {
    'gw_data_full': 'gold/gw_data_full.parquet',
    'manager_performance': 'gold/manager_performance.parquet',
    'player_season_stats': 'gold/player_season_stats.parquet',
}


# ============================================================
#                   DOWNLOAD HELPERS
# ============================================================
def _download_parquet(supabase, bucket: str, file_path: str, file_name: str = None) -> pd.DataFrame:
    """Download and parse parquet file from Supabase."""
    display_name = file_name or file_path.split('/')[-1]
    
    try:
        data = safe_download_file(supabase, bucket, file_path, "parquet")
        
        if not data:
            raise SupabaseDownloadError(f"No data received for {display_name}")
        
        df = pd.read_parquet(io.BytesIO(data))
        logger.info(f"Loaded {display_name}: {len(df)} rows, {len(df.columns)} columns")
        return df
        
    except Exception as e:
        if isinstance(e, SupabaseDownloadError):
            raise
        logger.error(f"Failed to load {display_name}: {str(e)}")
        raise SupabaseDownloadError(f"Failed to parse {display_name}: {str(e)}")


# ============================================================
#                   LOAD DIMENSIONS
# ============================================================
def load_dimensions(supabase, bucket: str = "data") -> Dict[str, pd.DataFrame]:
    """
    Load all dimension tables from Gold layer.
    
    Returns:
        Dictionary with dimension names as keys and DataFrames as values
    """
    validate_supabase_client(supabase)
    logger.info("Loading dimension tables...")
    
    dimensions = {}
    
    for dim_name, path in GOLD_DIMENSIONS.items():
        try:
            df = _download_parquet(supabase, bucket, path, f"dim_{dim_name}")
            validate_dataframe(df, f"dim_{dim_name}", min_rows=1)
            dimensions[dim_name] = df
        except Exception as e:
            logger.error(f"Failed to load dimension {dim_name}: {str(e)}")
            raise SupabaseError(f"Failed to load dim_{dim_name}: {str(e)}")
    
    logger.info(f"Successfully loaded {len(dimensions)} dimension tables")
    return dimensions


# ============================================================
#                   LOAD FACTS
# ============================================================
def load_facts(supabase, bucket: str = "data") -> Dict[str, pd.DataFrame]:
    """
    Load all fact tables from Gold layer.
    
    Returns:
        Dictionary with fact names as keys and DataFrames as values
    """
    validate_supabase_client(supabase)
    logger.info("Loading fact tables...")
    
    facts = {}
    
    for fact_name, path in GOLD_FACTS.items():
        try:
            df = _download_parquet(supabase, bucket, path, f"fact_{fact_name}")
            validate_dataframe(df, f"fact_{fact_name}", min_rows=1)
            facts[fact_name] = df
        except Exception as e:
            logger.error(f"Failed to load fact {fact_name}: {str(e)}")
            raise SupabaseError(f"Failed to load fact_{fact_name}: {str(e)}")
    
    logger.info(f"Successfully loaded {len(facts)} fact tables")
    return facts


# ============================================================
#                   LOAD COMPLETE GOLD LAYER
# ============================================================
def load_gold_layer(supabase, bucket: str = "data") -> Tuple[Dict[str, pd.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Load complete Gold layer with all dimensions and facts.
    
    Returns:
        Tuple of (dimensions_dict, facts_dict)
    """
    logger.info("Loading complete Gold layer (medallion schema)...")
    
    try:
        dimensions = load_dimensions(supabase, bucket)
        facts = load_facts(supabase, bucket)
        
        logger.info("✅ Gold layer loaded successfully")
        return dimensions, facts
        
    except Exception as e:
        logger.error(f"Failed to load Gold layer: {str(e)}")
        raise


# ============================================================
#                   CREATE DENORMALIZED VIEWS
# ============================================================
def create_player_performance_view(
    dimensions: Dict[str, pd.DataFrame],
    facts: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Create denormalized view of player performance with all dimensions joined.
    
    This recreates the legacy gw_data_full format for backward compatibility.
    """
    logger.info("Creating player performance view...")
    
    try:
        # Start with fact table
        df = facts['player_performance'].copy()
        
        # Join dimensions
        df = df.merge(
            dimensions['players'][['player_id', 'player_name', 'position']],
            on='player_id',
            how='left'
        )
        
        df = df.merge(
            dimensions['clubs'][['club_id', 'club_name', 'short_name']],
            on='club_id',
            how='left'
        )
        
        df = df.merge(
            dimensions['gameweeks'][['gameweek_id', 'gameweek_number', 'deadline_time']],
            on='gameweek_id',
            how='left'
        )
        
        logger.info(f"Created player performance view: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to create player performance view: {str(e)}")
        raise DataValidationError(f"Failed to create player performance view: {str(e)}")


def create_manager_picks_view(
    dimensions: Dict[str, pd.DataFrame],
    facts: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Create denormalized view of manager picks with dimensions joined.
    """
    logger.info("Creating manager picks view...")
    
    try:
        df = facts['manager_picks'].copy()
        
        # Join dimensions
        df = df.merge(
            dimensions['players'][['player_id', 'player_name', 'position']],
            on='player_id',
            how='left'
        )
        
        df = df.merge(
            dimensions['managers'][['manager_id', 'manager_name', 'team_name']],
            on='manager_id',
            how='left'
        )
        
        df = df.merge(
            dimensions['gameweeks'][['gameweek_id', 'gameweek_number']],
            on='gameweek_id',
            how='left'
        )
        
        logger.info(f"Created manager picks view: {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to create manager picks view: {str(e)}")
        raise DataValidationError(f"Failed to create manager picks view: {str(e)}")


def create_manager_standings(
    dimensions: Dict[str, pd.DataFrame],
    facts: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Create league standings from manager gameweek performance.
    """
    logger.info("Creating manager standings...")
    
    try:
        df = facts['manager_gw_performance'].copy()
        
        # Handle both old and new column names from backend
        # Backend may have 'manager_team_name' or 'team_name'
        team_name_col = 'team_name' if 'team_name' in df.columns else 'manager_team_name'
        
        # Aggregate total points per manager
        standings = df.groupby(['manager_id', 'first_name', 'last_name', team_name_col]).agg({
            'gw_points': 'sum',
        }).reset_index()
        
        standings = standings.rename(columns={
            'gw_points': 'total_points',
            'first_name': 'manager_first_name',
            'last_name': 'manager_last_name',
            team_name_col: 'team_name'  # Normalize to 'team_name'
        })
        
        standings = standings.sort_values('total_points', ascending=False).reset_index(drop=True)
        standings['rank'] = standings.index + 1
        
        logger.info(f"Created manager standings: {len(standings)} managers")
        return standings
        
    except Exception as e:
        logger.error(f"Failed to create manager standings: {str(e)}")
        raise DataValidationError(f"Failed to create manager standings: {str(e)}")


# ============================================================
#                   COLUMN NORMALIZATION
# ============================================================
def normalize_backend_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize backend column names to frontend expected names.
    
    The backend Gold layer may use slightly different column names.
    This function maps them to the expected frontend names.
    """
    # Column mapping: backend_name -> frontend_name
    column_map = {
        'manager_team_name': 'team_name',  # Manager's team name
        'player_position': 'player_position',  # Already correct
        'gameweek_num': 'gameweek_num',  # Already correct
        'player_name': 'player_name',  # Already correct
        'short_name': 'short_name',  # Already correct
    }
    
    # Only rename columns that exist
    rename_dict = {old: new for old, new in column_map.items() if old in df.columns and old != new}
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
        logger.debug(f"Normalized columns: {rename_dict}")
    
    return df


# ============================================================
#                   BACKWARD COMPATIBLE LOADER
# ============================================================
def load_data_medallion(
    supabase,
    bucket: str = "data",
    local_gameweeks: str = "Data/gameweeks.csv",
    local_fixtures: str = "Data/fixtures.csv"
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load data using medallion schema (Gold layer).
    
    Returns same format as legacy load_data_supabase():
        (gw_data_df, standings_df, gameweeks_df, fixtures_df)
    
    Uses medallion schema column names (e.g., gameweek_num, player_name, gw_points).
    """
    logger.info("Loading data from medallion schema (Gold layer)...")
    
    try:
        # Load Gold layer
        dimensions, facts = load_gold_layer(supabase, bucket)
        
        # Use manager_gw_performance fact which already has player data joined
        gw_data = facts['manager_gw_performance'].copy()
        
        # Normalize backend column names to frontend expected names
        gw_data = normalize_backend_columns(gw_data)
        
        # Ensure position column exists for sorting/display
        if 'position' not in gw_data.columns:
            gw_data['position'] = range(1, len(gw_data) + 1)
        
        standings = create_manager_standings(dimensions, facts)
        
        # Load gameweeks and fixtures locally (they have deadline times and other info)
        import os
        if os.path.exists(local_gameweeks):
            gameweeks = pd.read_csv(local_gameweeks)
            if "deadline_time" in gameweeks.columns:
                gameweeks["deadline_time"] = pd.to_datetime(gameweeks["deadline_time"], utc=True)
        else:
            # Fallback to dimension table
            gameweeks = dimensions['gameweeks'].rename(columns={
                'gameweek_num': 'id',
            })
            gameweeks['name'] = 'Gameweek ' + gameweeks['id'].astype(str)
        
        if os.path.exists(local_fixtures):
            fixtures = pd.read_csv(local_fixtures)
            if "kickoff_time" in fixtures.columns:
                fixtures["kickoff_time"] = pd.to_datetime(fixtures["kickoff_time"], utc=True)
        else:
            # Fallback to dimension table
            fixtures = dimensions['fixtures'].copy()
        
        logger.info("✅ Medallion data loaded successfully with new column names")
        return gw_data, standings, gameweeks, fixtures
        
    except Exception as e:
        logger.error(f"Failed to load medallion data: {str(e)}")
        raise SupabaseError(f"Failed to load data from Gold layer: {str(e)}")
