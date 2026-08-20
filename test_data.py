"""Quick test to check what data Supabase is serving"""
import sys
import os
sys.path.insert(0, 'core')
from supabase import create_client
from dotenv import load_dotenv
from error_handler import safe_download_file
import pandas as pd
import io

# Initialize Supabase
load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase = create_client(url, key)

# Download the parquet file directly
data = safe_download_file(supabase, "data", "gold/gw_data_full.parquet", "parquet")
df = pd.read_parquet(io.BytesIO(data))

# Check columns
print(f"\n=== COLUMNS IN DATA ({len(df.columns)} total) ===")
print(df.columns.tolist())

# Check if we have backend or frontend column names
if 'gameweek_num' in df.columns:
    gw_col = 'gameweek_num'
    pts_col = 'gw_points'
elif 'gameweek' in df.columns:
    gw_col = 'gameweek'
    pts_col = 'gw_points'
elif 'event' in df.columns:
    gw_col = 'event'
    pts_col = 'total_points'
else:
    print("Cannot find gameweek column!")
    gw_col = None
    
if gw_col:
    # Check Salah's GW25 data
    salah_gw25 = df[(df['player_id'] == 381) & (df[gw_col] == 25)]
    print(f'\n=== SALAH GW25 DATA (from Supabase Gold layer) ===')
    if not salah_gw25.empty:
        print(salah_gw25[[col for col in ['player_name', 'web_name', 'name', gw_col, pts_col, 'gw_minutes'] if col in df.columns]].to_string(index=False))
    else:
        print("NO DATA FOUND FOR SALAH IN GW25!")
    
    # Check how many gameweeks total
    print(f'\nTotal rows: {len(df)}')
    print(f'Total gameweeks in data: {df[gw_col].nunique()}')
    print(f'Gameweeks: {sorted(df[gw_col].unique())}')
    
    # Check Liverpool players in GW25
    liverpool_gw25 = df[(df[gw_col] == 25) & (df['team'] == 'Liverpool')]
    print(f'\n=== LIVERPOOL PLAYERS GW25 ({len(liverpool_gw25)} rows) ===')
    print(liverpool_gw25[['name', 'gw_points', 'gw_minutes']].sort_values('gw_points', ascending=False).head(10).to_string(index=False))

