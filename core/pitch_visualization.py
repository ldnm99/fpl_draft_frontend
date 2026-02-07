# ============================================================
#       ENHANCED SQUAD PITCH VISUALIZATION (FPL Style)
# ============================================================

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
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
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None


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


def get_formation_positions(formation: str = "4-4-2"):
    """
    Get player positions based on formation.
    Returns coordinates as percentage of pitch dimensions.
    """
    formations = {
        "4-4-2": {
            'GK': [(50, 5)],
            'DEF': [(20, 20), (40, 18), (60, 18), (80, 20)],
            'MID': [(20, 45), (40, 48), (60, 48), (80, 45)],
            'FWD': [(35, 75), (65, 75)]
        },
        "3-5-2": {
            'GK': [(50, 5)],
            'DEF': [(25, 18), (50, 16), (75, 18)],
            'MID': [(15, 40), (30, 48), (50, 50), (70, 48), (85, 40)],
            'FWD': [(35, 75), (65, 75)]
        },
        "3-4-3": {
            'GK': [(50, 5)],
            'DEF': [(25, 18), (50, 16), (75, 18)],
            'MID': [(20, 45), (40, 48), (60, 48), (80, 45)],
            'FWD': [(25, 75), (50, 78), (75, 75)]
        },
        "4-3-3": {
            'GK': [(50, 5)],
            'DEF': [(20, 20), (40, 18), (60, 18), (80, 20)],
            'MID': [(25, 48), (50, 50), (75, 48)],
            'FWD': [(25, 75), (50, 78), (75, 75)]
        },
        "4-5-1": {
            'GK': [(50, 5)],
            'DEF': [(20, 20), (40, 18), (60, 18), (80, 20)],
            'MID': [(15, 40), (30, 48), (50, 50), (70, 48), (85, 40)],
            'FWD': [(50, 78)]
        },
        "5-4-1": {
            'GK': [(50, 5)],
            'DEF': [(15, 20), (30, 18), (50, 16), (70, 18), (85, 20)],
            'MID': [(20, 48), (40, 50), (60, 50), (80, 48)],
            'FWD': [(50, 78)]
        },
        "5-3-2": {
            'GK': [(50, 5)],
            'DEF': [(15, 20), (30, 18), (50, 16), (70, 18), (85, 20)],
            'MID': [(25, 50), (50, 52), (75, 50)],
            'FWD': [(35, 75), (65, 75)]
        }
    }
    
    return formations.get(formation, formations["4-4-2"])


def detect_formation(starting_xi: pd.DataFrame) -> str:
    """Detect formation based on number of players in each position."""
    position_counts = starting_xi['player_position'].value_counts()
    
    gk = position_counts.get('GK', 0)
    def_count = position_counts.get('DEF', 0)
    mid = position_counts.get('MID', 0)
    fwd = position_counts.get('FWD', 0)
    
    formation = f"{def_count}-{mid}-{fwd}"
    return formation


def display_squad_pitch(manager_df: pd.DataFrame):
    """Display squad on pitch with FPL-style design"""
    st.header("⚽ Squad on the Pitch", divider="rainbow")
    
    try:
        # Get latest gameweek
        latest_gw = manager_df['gameweek_num'].max()
        squad_df = manager_df[manager_df['gameweek_num'] == latest_gw].copy()
        
        if squad_df.empty:
            st.error("ERROR: No squad data for current gameweek.")
            return
        
        # Get pitch background
        assets_path = get_assets_path()
        pitch_path = os.path.join(assets_path, "fpl_pitch.jpg")
        
        pitch_bg_base64 = None
        if os.path.exists(pitch_path):
            pitch_bg_base64 = get_image_base64(pitch_path)
        
        # Separate starting XI and bench
        starting_xi = squad_df[squad_df['team_position'] <= 11].copy()
        bench = squad_df[squad_df['team_position'] > 11].copy()
        
        # Detect formation
        formation = detect_formation(starting_xi)
        position_coords = get_formation_positions(formation)
        
        # Build enhanced HTML with FPL styling
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            .pitch-container {{
                position: relative;
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                background: linear-gradient(to bottom, #37003c 0%, #37003c 100%);
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            }}
            
            .pitch-wrapper {{
                position: relative;
                width: 100%;
                padding-bottom: 130%; /* Aspect ratio for vertical pitch */
                background: {f'url(data:image/jpeg;base64,{pitch_bg_base64})' if pitch_bg_base64 else 'linear-gradient(180deg, #5eb84d 0%, #63b852 50%, #5eb84d 100%)'};
                background-size: cover;
                background-position: center;
                border-radius: 4px;
                overflow: hidden;
            }}
            
            .pitch-field {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }}
            
            .player-element {{
                position: absolute;
                transform: translate(-50%, -50%);
                text-align: center;
                cursor: pointer;
                transition: transform 0.2s;
            }}
            
            .player-element:hover {{
                transform: translate(-50%, -50%) scale(1.1);
                z-index: 100;
            }}
            
            .player-shirt {{
                width: 50px;
                height: 66px;
                object-fit: contain;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                margin-bottom: 4px;
            }}
            
            .player-name {{
                background: rgba(0, 0, 0, 0.85);
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                white-space: nowrap;
                max-width: 80px;
                overflow: hidden;
                text-overflow: ellipsis;
                margin: 0 auto 2px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .player-points {{
                background: linear-gradient(135deg, #00ff87 0%, #60efff 100%);
                color: #000;
                padding: 3px 10px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                display: inline-block;
            }}
            
            .player-points.negative {{
                background: linear-gradient(135deg, #ff4757 0%, #ff6348 100%);
                color: white;
            }}
            
            .player-points.zero {{
                background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
                color: white;
            }}
            
            .bench-section {{
                background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                padding: 20px;
                margin-top: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .bench-title {{
                color: #fff;
                font-weight: 700;
                font-size: 14px;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            .bench-players {{
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                justify-content: center;
            }}
            
            .bench-player {{
                text-align: center;
                transition: transform 0.2s;
            }}
            
            .bench-player:hover {{
                transform: scale(1.05);
            }}
            
            .bench-shirt {{
                width: 45px;
                height: 60px;
                object-fit: contain;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
                margin-bottom: 4px;
            }}
            
            .formation-badge {{
                background: rgba(255,255,255,0.2);
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 15px;
                backdrop-filter: blur(10px);
            }}
            
            .gameweek-badge {{
                color: rgba(255,255,255,0.8);
                font-size: 12px;
                text-align: center;
                margin-top: 15px;
            }}
        </style>
        </head>
        <body style="margin: 0; padding: 0; background: transparent;">
        <div class="pitch-container">
            <div class="formation-badge">Formation: {formation}</div>
            <div class="pitch-wrapper">
                <div class="pitch-field">
        """
        
        # Add starting XI players
        for pos in ['GK', 'DEF', 'MID', 'FWD']:
            players = starting_xi[starting_xi['player_position'] == pos].sort_values('team_position')
            coords = position_coords.get(pos, [])
            
            for idx, (_, player) in enumerate(players.iterrows()):
                if idx < len(coords):
                    x_pct, y_pct = coords[idx]
                    points = player['gw_points']
                    
                    # Determine points class
                    if points > 0:
                        points_class = ""
                    elif points == 0:
                        points_class = "zero"
                    else:
                        points_class = "negative"
                    
                    # Get kit image
                    kit_base64 = get_kit_base64(player['short_name'])
                    
                    if kit_base64:
                        shirt_html = f'<img src="data:image/png;base64,{kit_base64}" class="player-shirt" alt="{player["short_name"]}">'
                    else:
                        shirt_html = f'<div class="player-shirt" style="background: #667eea; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px;">⚽</div>'
                    
                    player_name = str(player['player_name']).split()[-1] if len(str(player['player_name']).split()) > 1 else str(player['player_name'])
                    
                    html_content += f"""
                    <div class="player-element" style="left: {x_pct}%; top: {y_pct}%;">
                        {shirt_html}
                        <div class="player-name">{player_name[:12]}</div>
                        <div class="player-points {points_class}">{int(points)}</div>
                    </div>
                    """
        
        # Close pitch field
        html_content += """
                </div>
            </div>
        """
        
        # Add bench section
        if not bench.empty:
            html_content += """
            <div class="bench-section">
                <div class="bench-title">⬇️ Bench</div>
                <div class="bench-players">
            """
            
            for _, player in bench.iterrows():
                points = player['gw_points']
                points_class = "" if points > 0 else ("zero" if points == 0 else "negative")
                
                kit_base64 = get_kit_base64(player['short_name'])
                
                if kit_base64:
                    shirt_html = f'<img src="data:image/png;base64,{kit_base64}" class="bench-shirt" alt="{player["short_name"]}">'
                else:
                    shirt_html = f'<div class="bench-shirt" style="background: #95a5a6; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px;">⚽</div>'
                
                player_name = str(player['player_name']).split()[-1] if len(str(player['player_name']).split()) > 1 else str(player['player_name'])
                
                html_content += f"""
                <div class="bench-player">
                    {shirt_html}
                    <div class="player-name">{player_name[:10]}</div>
                    <div class="player-points {points_class}">{int(points)}</div>
                </div>
                """
            
            html_content += """
                </div>
            </div>
            """
        
        # Add gameweek badge
        html_content += f"""
            <div class="gameweek-badge">
                🎮 Gameweek {int(latest_gw)}
            </div>
        </div>
        </body>
        </html>
        """
        
        # Use components.html for better rendering
        components.html(html_content, height=1100, scrolling=False)
        
    except Exception as e:
        st.error(f"Error displaying pitch: {str(e)}")
        import traceback
        st.write(traceback.format_exc())
