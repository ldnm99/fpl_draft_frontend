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
    """Get the kit image for a player's team using short_name."""
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
    All defenders and midfielders are in straight lines.
    Adjusted for more compact spacing.
    """
    formations = {
        "4-4-2": {
            'GK': [(50, 15)],
            'DEF': [(20, 30), (40, 30), (60, 30), (80, 30)],
            'MID': [(20, 48), (40, 48), (60, 48), (80, 48)],
            'FWD': [(35, 72), (65, 72)]
        },
        "3-5-2": {
            'GK': [(50, 15)],
            'DEF': [(25, 30), (50, 30), (75, 30)],
            'MID': [(15, 48), (30, 48), (50, 48), (70, 48), (85, 48)],
            'FWD': [(35, 72), (65, 72)]
        },
        "3-4-3": {
            'GK': [(50, 15)],
            'DEF': [(25, 30), (50, 30), (75, 30)],
            'MID': [(20, 48), (40, 48), (60, 48), (80, 48)],
            'FWD': [(25, 72), (50, 72), (75, 72)]
        },
        "4-3-3": {
            'GK': [(50, 15)],
            'DEF': [(20, 30), (40, 30), (60, 30), (80, 30)],
            'MID': [(25, 48), (50, 48), (75, 48)],
            'FWD': [(25, 72), (50, 72), (75, 72)]
        },
        "4-5-1": {
            'GK': [(50, 15)],
            'DEF': [(20, 30), (40, 30), (60, 30), (80, 30)],
            'MID': [(15, 48), (30, 48), (50, 48), (70, 48), (85, 48)],
            'FWD': [(50, 72)]
        },
        "5-4-1": {
            'GK': [(50, 15)],
            'DEF': [(15, 30), (30, 30), (50, 30), (70, 30), (85, 30)],
            'MID': [(20, 48), (40, 48), (60, 48), (80, 48)],
            'FWD': [(50, 72)]
        },
        "5-3-2": {
            'GK': [(50, 15)],
            'DEF': [(15, 30), (30, 30), (50, 30), (70, 30), (85, 30)],
            'MID': [(25, 48), (50, 48), (75, 48)],
            'FWD': [(35, 72), (65, 72)]
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


def get_fixture_display(player_row: pd.Series) -> str:
    """
    Get fixture display string (e.g., 'WOL (A)' or 'ARS (H)').
    Checks for opponent and home/away columns in the data.
    """
    # Check for various possible column names for opponent
    opponent_col = None
    for col in ['opponent_short_name', 'opponent', 'opp_team_short_name', 'opponent_team']:
        if col in player_row.index and pd.notna(player_row.get(col)):
            opponent_col = col
            break
    
    # Check for home/away indicator
    was_home_col = None
    for col in ['was_home', 'is_home', 'home_away']:
        if col in player_row.index:
            was_home_col = col
            break
    
    # Build fixture string
    if opponent_col:
        opponent = str(player_row[opponent_col])[:3].upper()  # Limit to 3 chars
        
        if was_home_col:
            is_home = player_row[was_home_col]
            if isinstance(is_home, str):
                location = '(H)' if is_home.lower() in ['h', 'home'] else '(A)'
            else:
                location = '(H)' if is_home else '(A)'
        else:
            location = ''
        
        return f"{opponent} {location}".strip()
    
    return ""  # No fixture info available


def display_squad_pitch(manager_df: pd.DataFrame):
    """Display squad on pitch with FPL-style design"""
    st.header("⚽ Squad on the Pitch", divider="rainbow")
    
    try:
        # Initialize session state for selected gameweek
        if 'selected_gw_pitch' not in st.session_state:
            st.session_state.selected_gw_pitch = manager_df['gameweek_num'].max()
        
        # Get available gameweeks
        available_gws = sorted(manager_df['gameweek_num'].unique())
        min_gw = min(available_gws)
        max_gw = max(available_gws)
        
        # FPL-style gameweek pager
        st.markdown("""
        <style>
            .stButton > button {
                background: linear-gradient(135deg, #37003c 0%, #2d0032 100%);
                color: white;
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 14px;
                border-radius: 6px;
                transition: all 0.2s;
            }
            .stButton > button:hover:not(:disabled) {
                background: linear-gradient(135deg, #4a0050 0%, #37003c 100%);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            }
            .stButton > button:disabled {
                opacity: 0.4;
                cursor: not-allowed;
            }
            .gw-heading-container {
                text-align: center;
                padding: 12px;
                background: linear-gradient(135deg, #00ff87 0%, #60efff 100%);
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }
            .gw-heading-text {
                color: #37003c;
                font-size: 20px;
                font-weight: 700;
                margin: 0;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Create pager layout
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            prev_disabled = st.session_state.selected_gw_pitch <= min_gw
            if st.button("◀ Previous", key="prev_gw_pitch", use_container_width=True, 
                        disabled=prev_disabled):
                current_idx = available_gws.index(st.session_state.selected_gw_pitch)
                if current_idx > 0:
                    st.session_state.selected_gw_pitch = available_gws[current_idx - 1]
                    st.rerun()
        
        with col2:
            st.markdown(f"""
            <div class="gw-heading-container">
                <h3 class="gw-heading-text">Gameweek {int(st.session_state.selected_gw_pitch)}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            next_disabled = st.session_state.selected_gw_pitch >= max_gw
            if st.button("Next ▶", key="next_gw_pitch", use_container_width=True,
                        disabled=next_disabled):
                current_idx = available_gws.index(st.session_state.selected_gw_pitch)
                if current_idx < len(available_gws) - 1:
                    st.session_state.selected_gw_pitch = available_gws[current_idx + 1]
                    st.rerun()
        
        # Get squad for selected gameweek
        selected_gw = st.session_state.selected_gw_pitch
        squad_df = manager_df[manager_df['gameweek_num'] == selected_gw].copy()
        
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
        
        # Calculate total gameweek points
        total_gw_points = int(squad_df['gw_points'].sum())
        
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
            
            .points-scoreboard {{
                background: linear-gradient(135deg, #00ff87 0%, #60efff 100%);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                text-align: center;
            }}
            
            .points-heading {{
                color: #37003c;
                font-size: 14px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin: 0 0 8px 0;
            }}
            
            .points-value {{
                color: #37003c;
                font-size: 48px;
                font-weight: 900;
                line-height: 1;
                margin: 0;
            }}
            
            .points-label {{
                color: rgba(55, 0, 60, 0.7);
                font-size: 12px;
                font-weight: 600;
                margin-top: 4px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
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
                width: 70px;
                height: 92px;
                object-fit: contain;
                filter: drop-shadow(0 3px 6px rgba(0,0,0,0.4));
                margin-bottom: 6px;
            }}
            
            .player-name {{
                background: rgba(0, 0, 0, 0.85);
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: 600;
                white-space: nowrap;
                max-width: 100px;
                overflow: hidden;
                text-overflow: ellipsis;
                margin: 0 auto 3px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            }}
            
            .player-fixture {{
                background: rgba(255, 255, 255, 0.15);
                color: #fff;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
                font-weight: 500;
                margin: 0 auto 3px;
                display: inline-block;
                backdrop-filter: blur(5px);
            }}
            
            .player-points {{
                background: linear-gradient(135deg, #00ff87 0%, #60efff 100%);
                color: #000;
                padding: 4px 12px;
                border-radius: 14px;
                font-size: 15px;
                font-weight: 700;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
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
                width: 60px;
                height: 79px;
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
            <div class="points-scoreboard">
                <h4 class="points-heading">Gameweek Points</h4>
                <div class="points-value">{total_gw_points}</div>
                <div class="points-label">Total Points GW {int(selected_gw)}</div>
            </div>
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
                    
                    # Get kit image using short_name
                    kit_base64 = get_kit_base64(player['short_name'])
                    
                    if kit_base64:
                        shirt_html = f'<img src="data:image/png;base64,{kit_base64}" class="player-shirt" alt="{player["short_name"]}">'
                    else:
                        shirt_html = f'<div class="player-shirt" style="background: #667eea; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-size: 20px;">⚽</div>'
                    
                    player_name = str(player['player_name']).split()[-1] if len(str(player['player_name']).split()) > 1 else str(player['player_name'])
                    fixture_display = get_fixture_display(player)
                    
                    # Build fixture HTML if available
                    fixture_html = f'<div class="player-fixture">{fixture_display}</div>' if fixture_display else ''
                    
                    html_content += f"""
                    <div class="player-element" style="left: {x_pct}%; top: {y_pct}%;">
                        {shirt_html}
                        <div class="player-name">{player_name[:12]}</div>
                        {fixture_html}
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
                
                # Get kit image using short_name
                kit_base64 = get_kit_base64(player['short_name'])
                
                if kit_base64:
                    shirt_html = f'<img src="data:image/png;base64,{kit_base64}" class="bench-shirt" alt="{player["short_name"]}">'
                else:
                    shirt_html = f'<div class="bench-shirt" style="background: #95a5a6; border-radius: 3px; display: flex; align-items: center; justify-content: center; color: white; font-size: 18px;">⚽</div>'
                
                player_name = str(player['player_name']).split()[-1] if len(str(player['player_name']).split()) > 1 else str(player['player_name'])
                fixture_display = get_fixture_display(player)
                fixture_html = f'<div class="player-fixture">{fixture_display}</div>' if fixture_display else ''
                
                html_content += f"""
                <div class="bench-player">
                    {shirt_html}
                    <div class="player-name">{player_name[:10]}</div>
                    {fixture_html}
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
                🎮 Gameweek {int(selected_gw)}
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
