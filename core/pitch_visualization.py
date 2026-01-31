# ============================================================
#       SQUAD PITCH VISUALIZATION
# ============================================================

import pandas as pd
import streamlit as st
from PIL import Image
import os
from pathlib import Path
import base64
from io import BytesIO


def get_assets_path():
    """Get the assets directory path, handling both local and Streamlit contexts."""
    possible_paths = [
        "assets",
        os.path.join(os.path.dirname(__file__), "..", "assets"),
        os.path.join(Path.cwd(), "assets"),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return "assets"


def get_player_kit_image(team_name: str) -> Image.Image:
    """Get the kit image for a player's team."""
    try:
        assets_path = get_assets_path()
        players_path = os.path.join(assets_path, "players")
        
        kit_path = os.path.join(players_path, f"{team_name}.png")
        if os.path.exists(kit_path):
            return Image.open(kit_path).convert("RGBA")
        
        return None
    except Exception as e:
        return None


def get_image_base64(image_path):
    """Convert image to base64"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


def get_kit_base64(team_name):
    """Get kit image as base64"""
    try:
        kit = get_player_kit_image(team_name)
        if kit:
            buffer = BytesIO()
            kit.save(buffer, format="PNG")
            return base64.b64encode(buffer.getvalue()).decode()
    except:
        pass
    return None


def display_squad_pitch(manager_df: pd.DataFrame):
    """Display squad overlaid on pitch with kit images positioned by role"""
    st.header("⚽ Squad on the Pitch", divider="rainbow")
    
    try:
        # Get latest gameweek
        latest_gw = manager_df['gw'].max()
        squad_df = manager_df[manager_df['gw'] == latest_gw].copy()
        
        if squad_df.empty:
            st.error("ERROR: No squad data for current gameweek.")
            return
        
        # Get pitch background
        assets_path = get_assets_path()
        pitch_path = os.path.join(assets_path, "fpl_pitch.jpg")
        
        if not os.path.exists(pitch_path):
            st.error("Pitch background not found")
            return
        
        # Separate starting XI and bench
        starting_xi = squad_df[squad_df['team_position'] <= 11].copy()
        bench = squad_df[squad_df['team_position'] > 11].copy()
        
        # Position coordinates on pitch (as percentage of image width/height)
        position_coords = {
            'GK': [(50, 8)],
            'DEF': [(15, 25), (35, 22), (50, 20), (65, 22), (85, 25)],
            'MID': [(20, 45), (35, 48), (50, 50), (65, 48), (80, 45)],
            'FWD': [(30, 70), (50, 72), (70, 70)],
        }
        
        # Build HTML with overlay
        html_content = f"""
        <div style="position: relative; width: 100%; display: inline-block;">
            <img src="data:image/jpeg;base64,{get_image_base64(pitch_path)}" style="width: 100%; display: block;">
        """
        
        # Add starting XI overlays
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            players = starting_xi[starting_xi['position'] == pos].sort_values('full_name')
            coords = position_coords.get(pos, [])
            
            for idx, (_, player) in enumerate(players.iterrows()):
                if idx < len(coords):
                    x_pct, y_pct = coords[idx]
                    points = int(player['gw_points'])
                    color = "#2ecc71" if points > 0 else "#e74c3c"
                    
                    # Get kit image
                    kit_base64 = get_kit_base64(player['real_team'])
                    kit_html = f'<img src="data:image/png;base64,{kit_base64}" style="width: 60px; height: 80px; object-fit: cover; border-radius: 3px;">' if kit_base64 else '<div style="width: 60px; height: 80px; background: #ccc; display: flex; align-items: center; justify-content: center; border-radius: 3px;">🎽</div>'
                    
                    html_content += f"""
                    <div style="position: absolute; left: {x_pct}%; top: {y_pct}%; transform: translate(-50%, -50%); text-align: center;">
                        {kit_html}
                        <div style="background: rgba(0,0,0,0.8); color: white; padding: 2px 6px; margin-top: 3px; border-radius: 3px; font-size: 10px; font-weight: bold; white-space: nowrap; width: 70px; overflow: hidden; text-overflow: ellipsis;">
                            {player['full_name'][:12]}
                        </div>
                        <div style="background: {color}; color: white; padding: 2px 6px; margin-top: 1px; border-radius: 3px; font-size: 9px; font-weight: bold;">
                            {points}
                        </div>
                    </div>
                    """
        
        # Close pitch container and add bench section
        html_content += """
        </div>
        <div style="background: #2d5016; padding: 15px; margin-top: 10px; border-radius: 5px;">
            <div style="color: white; font-weight: bold; margin-bottom: 10px;">Bench:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 15px;">
        """
        
        for _, player in bench.iterrows():
            points = int(player['gw_points'])
            color = "#2ecc71" if points > 0 else "#e74c3c"
            kit_base64 = get_kit_base64(player['real_team'])
            kit_html = f'<img src="data:image/png;base64,{kit_base64}" style="width: 50px; height: 70px; object-fit: cover; border-radius: 2px;">' if kit_base64 else '<div style="width: 50px; height: 70px; background: #ccc; display: flex; align-items: center; justify-content: center; border-radius: 2px;">🎽</div>'
            
            html_content += f"""
            <div style="text-align: center;">
                {kit_html}
                <div style="background: rgba(0,0,0,0.8); color: white; padding: 2px 4px; margin-top: 3px; border-radius: 2px; font-size: 9px; font-weight: bold; white-space: nowrap; width: 60px; overflow: hidden; text-overflow: ellipsis;">
                    {player['full_name'][:10]}
                </div>
                <div style="background: {color}; color: white; padding: 2px 4px; margin-top: 1px; border-radius: 2px; font-size: 8px; font-weight: bold;">
                    {points}
                </div>
            </div>
            """
        
        html_content += """
            </div>
        </div>
        <div style="color: #999; font-size: 12px; margin-top: 10px; text-align: center;">
            🎮 Gameweek {gw} - Kit images show player's real team
        </div>
        """.format(gw=int(latest_gw))
        
        st.markdown(html_content, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error displaying pitch: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
