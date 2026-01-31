# ============================================================
#           INJURY & STATUS TRACKING
# ============================================================

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone


def get_squad_status(manager_df: pd.DataFrame, latest_gw_only: bool = True) -> pd.DataFrame:
    """
    Get injury/status information for a manager's squad.
    
    Returns DataFrame with:
    - Player name, position, team
    - Status (Healthy, At Risk, Injured, Suspended, Unknown)
    - Chance of playing next round (%)
    - Injury news summary
    - Days until return (if available)
    """
    if manager_df.empty:
        return pd.DataFrame()
    
    # Get latest gameweek if specified
    if latest_gw_only:
        latest_gw = manager_df['gw'].max()
        squad_df = manager_df[manager_df['gw'] == latest_gw].copy()
    else:
        squad_df = manager_df.copy()
    
    if squad_df.empty:
        return pd.DataFrame()
    
    # Get unique players (remove duplicates)
    players_df = squad_df.drop_duplicates(subset=['full_name', 'player_id']).copy()
    
    # Determine status
    status_list = []
    for _, player in players_df.iterrows():
        chance = player.get('chance_of_playing_next_round', None)
        news = player.get('news', None)
        
        if pd.isna(chance) or chance is None:
            status = '✅ Healthy'
            risk_level = 0
        elif chance == 0:
            status = '🚨 Out'
            risk_level = 3
        elif chance < 50:
            status = '⚠️ Doubtful'
            risk_level = 2
        elif chance < 100:
            status = '🟡 At Risk'
            risk_level = 1
        else:
            status = '✅ Healthy'
            risk_level = 0
        
        status_list.append({
            'full_name': player.get('full_name', 'Unknown'),
            'position': player.get('position', 'N/A'),
            'real_team': player.get('real_team', 'N/A'),
            'team_position': player.get('team_position', 15),  # 15+ = bench
            'gw_points': player.get('gw_points', 0),
            'status': status,
            'risk_level': risk_level,
            'chance_of_playing': chance if pd.notna(chance) else 100,
            'news': news if pd.notna(news) else 'No updates',
            'news_return': player.get('news_return', None),
            'is_starting': player.get('team_position', 15) <= 11
        })
    
    result_df = pd.DataFrame(status_list)
    
    # Sort by risk level (highest first), then by starting status
    result_df = result_df.sort_values(
        by=['risk_level', 'is_starting'], 
        ascending=[False, False]
    ).reset_index(drop=True)
    
    return result_df


def get_at_risk_players(manager_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get only players with injury concerns (chance of playing < 100%).
    Focused on starting XI.
    """
    squad_status = get_squad_status(manager_df, latest_gw_only=True)
    
    if squad_status.empty:
        return pd.DataFrame()
    
    # Filter: At risk players who are in starting XI
    at_risk = squad_status[
        (squad_status['is_starting'] == True) & 
        (squad_status['chance_of_playing'] < 100)
    ].copy()
    
    return at_risk


def get_injury_summary(manager_df: pd.DataFrame) -> dict:
    """
    Get summary statistics about injuries in the squad.
    """
    squad_status = get_squad_status(manager_df, latest_gw_only=True)
    
    if squad_status.empty:
        return {
            'total_players': 0,
            'healthy': 0,
            'at_risk': 0,
            'out': 0,
            'starting_at_risk': 0
        }
    
    return {
        'total_players': len(squad_status),
        'healthy': len(squad_status[squad_status['chance_of_playing'] == 100]),
        'at_risk': len(squad_status[(squad_status['chance_of_playing'] < 100) & (squad_status['chance_of_playing'] > 0)]),
        'out': len(squad_status[squad_status['chance_of_playing'] == 0]),
        'starting_at_risk': len(squad_status[(squad_status['is_starting']) & (squad_status['chance_of_playing'] < 100)])
    }
