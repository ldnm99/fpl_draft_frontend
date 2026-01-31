# ============================================================
#       SQUAD PITCH VISUALIZATION
# ============================================================

import pandas as pd
import streamlit as st
from PIL import Image
import os
from pathlib import Path


def get_assets_path():
    """Get the assets directory path, handling both local and Streamlit contexts."""
    # Try multiple possible paths
    possible_paths = [
        "assets",
        os.path.join(os.path.dirname(__file__), "..", "assets"),
        os.path.join(Path.cwd(), "assets"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return "assets"  # Fallback


def get_player_kit_image(team_name: str) -> Image.Image:
    """Get the kit image for a player's team."""
    try:
        assets_path = get_assets_path()
        players_path = os.path.join(assets_path, "players")
        
        # Try exact match first
        kit_path = os.path.join(players_path, f"{team_name}.png")
        if os.path.exists(kit_path):
            return Image.open(kit_path).convert("RGBA")
        
        # Return None if not found
        return None
    except Exception as e:
        return None

def display_squad_pitch(manager_df: pd.DataFrame):
    """
    Display the squad pitch visualization in Streamlit using team kits.
    Organized by position in rows.
    """
    st.header("⚽ Squad on the Pitch", divider="rainbow")
    
    if manager_df.empty:
        st.info("No data available.")
        return
    
    try:
        # Get latest gameweek
        latest_gw = manager_df['gw'].max()
        squad_df = manager_df[manager_df['gw'] == latest_gw].copy()
        
        if squad_df.empty:
            st.info("No squad data for current gameweek.")
            return
        
        # Organize by position
        positions = ['GK', 'DEF', 'MID', 'FWD']
        
        # Display pitch background if available
        assets_path = get_assets_path()
        pitch_path = os.path.join(assets_path, "fpl_pitch.jpg")
        
        if os.path.exists(pitch_path):
            st.image(pitch_path, use_container_width=True)
        
        st.write("---")
        
        # Display starting XI
        st.subheader("Starting XI")
        
        for pos in positions:
            players = squad_df[
                (squad_df['position'] == pos) & 
                (squad_df['team_position'] <= 11)
            ].sort_values('full_name')
            
            if len(players) > 0:
                st.write(f"**{pos}** ({len(players)} players)")
                
                # Create columns for each player
                cols = st.columns(min(len(players), 5))
                
                for idx, (_, player) in enumerate(players.iterrows()):
                    with cols[idx % len(cols)]:
                        # Try to display kit image
                        kit = get_player_kit_image(player['real_team'])
                        
                        if kit:
                            # Resize kit for display
                            kit = kit.resize((80, 120))
                            st.image(kit, caption=f"{player['full_name']}\n{int(player['gw_points'])} pts", use_column_width=True)
                        else:
                            # Fallback: just show text
                            st.write(f"🟢 {player['full_name']}")
                            st.write(f"**{int(player['gw_points'])} pts**")
        
        st.write("---")
        
        # Display bench
        bench_players = squad_df[squad_df['team_position'] > 11].sort_values('full_name')
        
        if len(bench_players) > 0:
            st.subheader(f"Bench ({len(bench_players)} players)")
            
            cols = st.columns(min(len(bench_players), 5))
            
            for idx, (_, player) in enumerate(bench_players.iterrows()):
                with cols[idx % len(cols)]:
                    kit = get_player_kit_image(player['real_team'])
                    
                    if kit:
                        kit = kit.resize((60, 90))
                        st.image(kit, caption=f"{player['full_name']}\n{int(player['gw_points'])} pts", use_column_width=True)
                    else:
                        st.write(f"🔘 {player['full_name']}")
                        st.write(f"**{int(player['gw_points'])} pts**")
        
        st.write("---")
        st.caption(f"GW {int(latest_gw)} - Kit images show player's real team")
        
    except Exception as e:
        st.error(f"Error displaying pitch: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
