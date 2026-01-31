# ============================================================
#       SQUAD PITCH VISUALIZATION
# ============================================================

import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import os


def get_player_kit_image(team_name: str, assets_path: str = "assets/players") -> Image.Image:
    """
    Get the kit image for a player's team.
    """
    try:
        # Try exact match first
        kit_path = os.path.join(assets_path, f"{team_name}.png")
        if os.path.exists(kit_path):
            return Image.open(kit_path).convert("RGBA")
        
        # Try common variations
        variations = [
            team_name.lower().replace(" ", "_"),
            team_name.lower(),
            team_name.replace(" ", ""),
        ]
        
        for var in variations:
            kit_path = os.path.join(assets_path, f"{var}.png")
            if os.path.exists(kit_path):
                return Image.open(kit_path).convert("RGBA")
        
        # Return None if not found
        return None
    except Exception as e:
        st.warning(f"Could not load kit for {team_name}: {str(e)}")
        return None


def create_pitch_visualization(manager_df: pd.DataFrame, latest_gw_only: bool = True) -> Image.Image:
    """
    Create a football pitch visualization showing the squad with kit images.
    
    Layout:
    - GK row at top
    - DEF row
    - MID row
    - FWD row
    - BENCH row at bottom
    """
    if manager_df.empty:
        return None
    
    # Get latest gameweek
    if latest_gw_only:
        latest_gw = manager_df['gw'].max()
        squad_df = manager_df[manager_df['gw'] == latest_gw].copy()
    else:
        squad_df = manager_df.copy()
    
    if squad_df.empty:
        return None
    
    # Load pitch background
    pitch_path = "assets/players/fpl_pitch/fpl_pitch.png"
    if not os.path.exists(pitch_path):
        pitch_path = "assets/fpl_pitch.jpg"
    
    try:
        pitch = Image.open(pitch_path).convert("RGB")
    except:
        # Create a simple green pitch if image not found
        pitch = Image.new("RGB", (1000, 1300), color=(34, 139, 34))
    
    pitch_width, pitch_height = pitch.size
    
    # Organize players by position
    positions = {
        'GK': squad_df[squad_df['position'] == 'GK'].sort_values('full_name'),
        'DEF': squad_df[squad_df['position'] == 'DEF'].sort_values('full_name'),
        'MID': squad_df[squad_df['position'] == 'MID'].sort_values('full_name'),
        'FWD': squad_df[squad_df['position'] == 'FWD'].sort_values('full_name'),
    }
    
    # Separate starting XI and bench
    starting_positions = {}
    bench_players = []
    
    for pos, players in positions.items():
        starting = players[players['team_position'] <= 11]
        bench = players[players['team_position'] > 11]
        starting_positions[pos] = starting
        bench_players.extend(bench.to_dict('records'))
    
    # Create the visualization
    draw = ImageDraw.Draw(pitch)
    
    # Font setup
    try:
        name_font = ImageFont.truetype("arial.ttf", 14)
        points_font = ImageFont.truetype("arial.ttf", 12)
    except:
        name_font = ImageFont.load_default()
        points_font = ImageFont.load_default()
    
    kit_size = (60, 80)  # Width, height of kit images
    spacing = 100  # Horizontal spacing between players
    row_height = 150  # Vertical spacing between rows
    
    # Y positions for each row
    rows_y = {
        'GK': 100,
        'DEF': 250,
        'MID': 450,
        'FWD': 650,
        'BENCH': 900
    }
    
    # Function to place player on pitch
    def place_players(players_list, y_pos, row_name):
        if len(players_list) == 0:
            return
        
        # Calculate spacing
        total_width = len(players_list) * spacing
        start_x = (pitch_width - total_width) // 2
        
        for idx, player in enumerate(players_list.itertuples()):
            x = start_x + idx * spacing
            
            # Get kit image
            kit = get_player_kit_image(player.real_team)
            
            if kit:
                # Resize kit
                kit = kit.resize(kit_size)
                # Paste kit onto pitch
                pitch.paste(kit, (x - kit_size[0] // 2, y_pos - kit_size[1] // 2), kit)
            else:
                # Draw placeholder circle
                draw.ellipse(
                    [x - 25, y_pos - 35, x + 25, y_pos + 45],
                    fill=(255, 0, 0),
                    outline=(0, 0, 0)
                )
            
            # Add player name
            player_name = player.full_name[:10] if len(player.full_name) > 10 else player.full_name
            name_bbox = draw.textbbox((0, 0), player_name, font=name_font)
            name_width = name_bbox[2] - name_bbox[0]
            draw.text(
                (x - name_width // 2, y_pos + 50),
                player_name,
                fill=(255, 255, 255),
                font=name_font
            )
            
            # Add points
            points_text = f"{int(player.gw_points)}pts"
            points_bbox = draw.textbbox((0, 0), points_text, font=points_font)
            points_width = points_bbox[2] - points_bbox[0]
            draw.text(
                (x - points_width // 2, y_pos + 70),
                points_text,
                fill=(255, 255, 0),
                font=points_font
            )
    
    # Place players for each row
    for pos_name in ['GK', 'DEF', 'MID', 'FWD']:
        players = starting_positions[pos_name]
        if len(players) > 0:
            place_players(players, rows_y[pos_name], pos_name)
    
    # Place bench players
    if bench_players:
        bench_df = pd.DataFrame(bench_players)
        place_players(bench_df, rows_y['BENCH'], 'BENCH')
    
    # Add title and gameweek info
    gw_text = f"Gameweek {int(latest_gw)}"
    draw.text((20, 20), gw_text, fill=(255, 255, 255), font=name_font)
    
    return pitch


def display_squad_pitch(manager_df: pd.DataFrame):
    """
    Display the squad pitch visualization in Streamlit.
    """
    st.header("⚽ Squad on the Pitch", divider="rainbow")
    
    if manager_df.empty:
        st.info("No data available.")
        return
    
    try:
        pitch_img = create_pitch_visualization(manager_df, latest_gw_only=True)
        
        if pitch_img is None:
            st.warning("Could not generate pitch visualization.")
            return
        
        st.image(pitch_img, use_container_width=True)
        
        # Add legend
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.write("🟡 **GK** - Goalkeeper")
        col2.write("🔴 **DEF** - Defenders")
        col3.write("🟣 **MID** - Midfielders")
        col4.write("⚪ **FWD** - Forwards")
        col5.write("🟢 **BENCH** - Substitutes")
        
    except Exception as e:
        st.error(f"Error generating pitch visualization: {str(e)}")
