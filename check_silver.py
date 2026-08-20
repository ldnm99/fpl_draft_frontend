import sys, os
sys.path.insert(0, 'core')
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=== Checking Silver folder in Supabase ===")
silver = supabase.storage.from_('data').list('silver')
print(f"\nSilver folder has {len(silver)} items:")
for item in silver:
    print(f"  - {item['name']} ({item.get('id', 'folder')})")

if any(item['name'] == 'gameweeks' for item in silver):
    print("\n=== Checking silver/gameweeks ===")
    gw_folder = supabase.storage.from_('data').list('silver/gameweeks')
    print(f"Found {len(gw_folder)} files")
    gw_files = [f for f in gw_folder if f['name'].startswith('gw_data')]
    print(f"GW data files: {len(gw_files)}")
    if gw_files:
        print("Latest 5 files:")
        for f in sorted(gw_files, key=lambda x: x['name'], reverse=True)[:5]:
            print(f"  {f['name']}")
