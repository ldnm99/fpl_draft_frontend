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
