import os
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
import warnings
warnings.filterwarnings('ignore')

from core.data_utils import load_data_supabase, get_all_optimal_lineups, get_manager_data
from supabase import create_client
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY

# Load data
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df = load_data_supabase(supabase)

# Test with Blue Lock XI
manager_name = "Blue Lock XI"
manager_df = get_manager_data(df, manager_name)

print(f"Total rows for {manager_name}: {len(manager_df)}")
print(f"Unique gameweeks: {sorted(manager_df['gameweek_num'].unique())}")
print(f"Unique players: {manager_df['player_name'].nunique()}")

# Calculate actual points directly
actual_direct = manager_df[manager_df['team_position'] <= 11]['gw_points'].sum()
print(f"\nDirect calculation (team_position <= 11): {actual_direct}")

# Get via get_all_optimal_lineups
gw_results = get_all_optimal_lineups(manager_df)
actual_via_function = gw_results['actual_points'].sum()
print(f"Via get_all_optimal_lineups sum: {actual_via_function}")

print("\nGameweek breakdown:")
print(gw_results[['gameweek', 'actual_points', 'optimal_points']])

# Check for duplicates per gameweek
print("\n--- Checking for duplicates ---")
for gw in sorted(manager_df['gameweek_num'].unique())[:3]:  # First 3 gameweeks
    gw_data = manager_df[manager_df['gameweek_num'] == gw]
    starting = gw_data[gw_data['team_position'] <= 11]
    print(f"GW {gw}: Total rows={len(gw_data)}, Starting XI rows={len(starting)}, Sum of points={starting['gw_points'].sum()}")
