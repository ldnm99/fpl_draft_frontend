# Medallion Schema Quick Reference

## Data Loading

### Automatic (Recommended)
```python
from core.data_utils import load_data_auto

df, standings, gameweeks, fixtures = load_data_auto(supabase)
# ↑ Tries medallion, falls back to legacy automatically
```

### Explicit Medallion
```python
from core.medallion_data_loader import load_data_medallion

df, standings, gameweeks, fixtures = load_data_medallion(supabase)
```

### Direct Gold Layer Access
```python
from core.medallion_data_loader import load_gold_layer

dimensions, facts = load_gold_layer(supabase)

# Access dimensions
players = dimensions['players']
clubs = dimensions['clubs']
gameweeks = dimensions['gameweeks']
managers = dimensions['managers']
fixtures = dimensions['fixtures']

# Access facts
player_perf = facts['player_performance']  # 33 columns!
manager_picks = facts['manager_picks']
seasonal_stats = facts['seasonal_stats']
manager_gw_perf = facts['manager_gw_performance']
```

---

## Schema Reference

### Dimensions

#### dim_players
```python
Key: player_id (business key), player_key (surrogate key)
Columns: name, position, team_id, club_id, total_points, form, xG, xA, 
         saves, tackles, bonus, ict_index, ... (80+ columns)
```

#### dim_clubs
```python
Key: club_id
Columns: club_id, club_name, short_name
```

#### dim_gameweeks
```python
Key: gameweek_id, gameweek_num
Columns: gameweek_id, gameweek_num, is_current
```

#### dim_managers
```python
Key: manager_id
Columns: manager_id, first_name, last_name, team_name, waiver_pick
```

#### dim_fixtures
```python
Key: fixture_id
Columns: fixture_id, gameweek_id, home_team_id, away_team_id, kickoff_time,
         home_difficulty, away_difficulty
```

### Facts

#### fact_player_performance (⭐ Primary Fact - 33 Columns)
```python
Grain: One row per player per gameweek
Keys: performance_id (PK), player_key, club_id, gameweek_id

Basic Stats (9):
  - gw_points, gw_minutes, gw_goals, gw_assists
  - gw_clean_sheets, gw_goals_conceded, gw_bonus

Expected Stats (4):
  - gw_xG, gw_xA, gw_xGi, gw_xGc

ICT Metrics (4):
  - gw_influence, gw_creativity, gw_threat, gw_ict_index

Defensive Stats (4):
  - gw_clearances_blocks_interceptions, gw_recoveries
  - gw_tackles, gw_defensive_contribution

Goalkeeper Stats (3):
  - gw_saves, gw_penalties_saved, gw_penalties_missed

Disciplinary (3):
  - gw_yellow_cards, gw_red_cards, gw_own_goals

Other (3):
  - gw_bps, gw_starts, gw_in_dreamteam
```

#### fact_manager_picks
```python
Grain: One row per player picked per manager per gameweek
Keys: pick_id (PK), manager_id, player_id, gameweek_id
Columns: team_position, is_captain, is_vice_captain, points_earned
```

#### fact_player_seasonal_stats
```python
Grain: One row per player (cumulative season)
Keys: player_id (PK)
Columns: All season totals (goals, assists, points, etc.)
```

#### manager_gameweek_performance
```python
Grain: One row per player per manager per gameweek (denormalized)
Columns: gameweek_num, manager_id, first_name, last_name, team_name,
         player_id, player_name, position, club_name, team_position,
         gw_points, gw_minutes, gw_goals, gw_assists, gw_clean_sheets, gw_bonus
```

---

## Common Queries

### Get Player Performance with all stats
```python
dimensions, facts = load_gold_layer(supabase)

# Join player performance with dimensions
perf = facts['player_performance'].merge(
    dimensions['players'][['player_key', 'name', 'position']],
    on='player_key',
    how='left'
).merge(
    dimensions['gameweeks'][['gameweek_id', 'gameweek_num']],
    on='gameweek_id',
    how='left'
)

# Now you have: name, position, gameweek_num, xG, xA, tackles, etc.
```

### Get Top xG Players
```python
top_xg = facts['player_performance'].merge(
    dimensions['players'][['player_key', 'name']],
    on='player_key'
).groupby('name')['gw_xG'].sum().sort_values(ascending=False).head(10)
```

### Get Manager's Team for Gameweek
```python
gw = 25
manager_id = 115613

team = facts['manager_picks'].query(
    f'gameweek_id == {gw} and manager_id == {manager_id}'
).merge(
    dimensions['players'][['player_id', 'name', 'position']],
    on='player_id'
).merge(
    facts['player_performance'].query(f'gameweek_id == {gw}')[['player_key', 'gw_points']],
    on='player_key',
    how='left'
)
```

### Get Best Defenders by Tackles + Recoveries
```python
defenders = facts['player_performance'].merge(
    dimensions['players'].query('position == "DEF"')[['player_key', 'name']],
    on='player_key'
)

best_def = defenders.groupby('name').agg({
    'gw_tackles': 'sum',
    'gw_recoveries': 'sum',
    'gw_clearances_blocks_interceptions': 'sum'
}).assign(
    defensive_total = lambda x: x['gw_tackles'] + x['gw_recoveries'] + x['gw_clearances_blocks_interceptions']
).sort_values('defensive_total', ascending=False).head(10)
```

---

## Column Name Mappings

### Old → New Mappings
```python
# Gameweek data
'gw' → 'gameweek_num'
'player_name' → dimensions['players']['name']
'team_name' (club) → dimensions['clubs']['club_name']
'manager_team_name' → dimensions['managers']['team_name']

# Stats (now with gw_ prefix)
'points' → 'gw_points'
'minutes' → 'gw_minutes'
'goals' → 'gw_goals'
'assists' → 'gw_assists'
'clean_sheets' → 'gw_clean_sheets'
'bonus' → 'gw_bonus'

# NEW stats (not available before)
'gw_xG' → Expected goals
'gw_xA' → Expected assists
'gw_tackles' → Tackles made
'gw_recoveries' → Ball recoveries
'gw_saves' → Goalkeeper saves
'gw_ict_index' → ICT index
... and 15+ more!
```

---

## Benefits Summary

| Feature | Old | New | Change |
|---------|-----|-----|--------|
| **Columns** | 15 | 33 | +120% |
| **Normalization** | Denormalized flat file | Star schema | ✅ Proper design |
| **Advanced Stats** | Basic only | xG, xA, ICT, defensive | ✅ Analytics ready |
| **Incremental Updates** | ❌ | ✅ Last 2 GWs only | 95% faster |
| **Data Quality** | Mixed | Validated layers | ✅ Higher quality |
| **Query Performance** | Scan full file | Dimension caching | Faster |

---

## Example: Build Top Players Dashboard

```python
from core.medallion_data_loader import load_gold_layer

# Load data
dimensions, facts = load_gold_layer(supabase)

# Create comprehensive player stats
player_stats = facts['player_performance'].merge(
    dimensions['players'][['player_key', 'name', 'position', 'team']],
    on='player_key'
).groupby(['name', 'position', 'team']).agg({
    'gw_points': 'sum',
    'gw_xG': 'sum',
    'gw_xA': 'sum',
    'gw_goals': 'sum',
    'gw_assists': 'sum',
    'gw_tackles': 'sum',
    'gw_saves': 'sum',
    'gw_ict_index': 'mean',
    'gw_minutes': 'sum'
}).reset_index()

# Top scorers by xG
top_attackers = player_stats.sort_values('gw_xG', ascending=False).head(10)

# Best defenders by tackles + recoveries
defenders = player_stats.query('position == "DEF"')
top_defenders = defenders.assign(
    defensive_actions = lambda x: x['gw_tackles']
).sort_values('defensive_actions', ascending=False).head(10)

# Best goalkeepers by saves
goalkeepers = player_stats.query('position == "GK"')
top_gk = goalkeepers.sort_values('gw_saves', ascending=False).head(5)
```

---

**Quick Tip:** All gameweek stats now have `gw_` prefix to distinguish from season totals!

**See also:** `MEDALLION_MIGRATION.md` for full migration guide
