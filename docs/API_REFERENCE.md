# 📚 API Reference

Complete function documentation for the FPL Dashboard.

---

## data_utils.py

### Data Loading

#### `load_data_supabase(supabase, bucket="data", gw_data_file="gw_data.parquet", standings_file="league_standings.csv", local_gameweeks="Data/gameweeks.csv", local_fixtures="Data/fixtures.csv")`

Loads all required data from Supabase and local files.

**Parameters:**
- `supabase` (Client): Supabase client instance
- `bucket` (str): Storage bucket name. Default: `"data"`
- `gw_data_file` (str): Parquet file name in Supabase. Default: `"gw_data.parquet"`
- `standings_file` (str): CSV file name in Supabase. Default: `"league_standings.csv"`
- `local_gameweeks` (str): Local CSV file path. Default: `"Data/gameweeks.csv"`
- `local_fixtures` (str): Local CSV file path. Default: `"Data/fixtures.csv"`

**Returns:**
- `Tuple[DataFrame, DataFrame, DataFrame, DataFrame]`: `(gw_data, standings, gameweeks, fixtures)`

**Raises:**
- `FileNotFoundError`: If local CSV files don't exist

**Example:**
```python
from supabase import create_client
from supabase_client import SUPABASE_URL, SUPABASE_KEY
from data_utils import load_data_supabase

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_supabase(supabase)

print(f"Loaded {len(df)} player records")
print(f"Loaded {len(standings)} teams")
```

---

### Gameweek Functions

#### `get_next_gameweek(gameweeks: pd.DataFrame, now: datetime = None) -> pd.DataFrame`

Returns the next upcoming gameweek.

**Parameters:**
- `gameweeks` (DataFrame): Gameweeks data from `load_data_supabase()`
- `now` (datetime, optional): Current time for comparison. Default: `datetime.now(timezone.utc)`

**Returns:**
- `DataFrame`: Single row with next gameweek (empty if none found)

**Example:**
```python
from datetime import datetime, timezone
from data_utils import get_next_gameweek

next_gw = get_next_gameweek(gameweeks)

if not next_gw.empty:
    print(f"Next: {next_gw.iloc[0]['name']}")
    print(f"Deadline: {next_gw.iloc[0]['deadline_time']}")
else:
    print("No upcoming gameweeks")
```

---

#### `get_upcoming_fixtures(fixtures: pd.DataFrame, next_gw: pd.DataFrame) -> pd.DataFrame`

Returns fixtures for the next gameweek.

**Parameters:**
- `fixtures` (DataFrame): Fixtures data from `load_data_supabase()`
- `next_gw` (DataFrame): Output from `get_next_gameweek()`

**Returns:**
- `DataFrame`: Fixtures with columns `[Home, Away, Kickoff, team_h_difficulty, team_a_difficulty]`
- Empty DataFrame if `next_gw` is empty

**Example:**
```python
from data_utils import get_next_gameweek, get_upcoming_fixtures

next_gw = get_next_gameweek(gameweeks)
upcoming = get_upcoming_fixtures(fixtures, next_gw)

print(upcoming[["Home", "Away", "Kickoff"]])
# Output:
#         Home              Away                 Kickoff
# 0     Arsenal         Leicester  Friday, 11 August 2023 20:00 BST
```

---

### Manager Filtering

#### `get_manager_data(df: pd.DataFrame, manager_name: str) -> pd.DataFrame`

Filters data for a specific manager.

**Parameters:**
- `df` (DataFrame): Player gameweek data from `load_data_supabase()`
- `manager_name` (str): Manager team name to filter by

**Returns:**
- `DataFrame`: All rows for manager
- Empty DataFrame if manager not found

**Example:**
```python
from data_utils import get_manager_data

manager_df = get_manager_data(df, "Blue Lock XI")
print(f"Records for manager: {len(manager_df)}")
print(manager_df[["gw", "full_name", "gw_points"]].head())
```

---

### Squad Analysis

#### `get_starting_lineup(df: pd.DataFrame) -> pd.DataFrame`

Filters to only starting XI players (team_position 1-11).

**Parameters:**
- `df` (DataFrame): Player data (full or filtered)

**Returns:**
- `DataFrame`: Starting XI only

**Example:**
```python
from data_utils import get_starting_lineup

starting = get_starting_lineup(df)
print(f"Starting XI: {len(starting)} records")

bench = df[df["team_position"] > 11]
print(f"Bench: {len(bench)} records")
```

---

### Aggregation Functions

#### `calculate_team_gw_points(starting_players: pd.DataFrame) -> pd.DataFrame`

Creates pivot table: Teams × Gameweeks with total points.

**Parameters:**
- `starting_players` (DataFrame): Starting XI only (use `get_starting_lineup()`)

**Returns:**
- `DataFrame`: 
  - Index: Manager team names
  - Columns: Gameweek numbers (1, 2, 3, ..., "Total")
  - Values: Points per gameweek

**Example:**
```python
from data_utils import get_starting_lineup, calculate_team_gw_points

starting = get_starting_lineup(df)
team_points = calculate_team_gw_points(starting)

print(team_points)
# Output:
#                      1     2     3  Total
# Blue Lock XI       65.0  72.0  58.0  195.0
# Magic FC           60.0  65.0  70.0  195.0

# Best gameweek per team
best_gw = team_points.drop("Total", axis=1).idxmax(axis=1)
print(best_gw)
```

---

#### `get_teams_avg_points(team_gw_points: pd.DataFrame) -> pd.DataFrame`

Average points per team across gameweeks.

**Parameters:**
- `team_gw_points` (DataFrame): Output from `calculate_team_gw_points()`

**Returns:**
- `DataFrame`:
  - Columns: `["team_name", "avg_points"]`
  - Sorted by avg_points descending

**Example:**
```python
from data_utils import get_teams_avg_points

avg_points = get_teams_avg_points(team_points)
print(avg_points)
# Output:
#          team_name  avg_points
# 0      Magic FC         65.00
# 1      Blue Lock XI      64.83
```

---

#### `get_team_total_points(starting_players: pd.DataFrame) -> pd.DataFrame`

Total points for each manager across entire season.

**Parameters:**
- `starting_players` (DataFrame): Starting XI only

**Returns:**
- `DataFrame`:
  - Columns: `["Team", "Total Points"]`
  - Sorted by Total Points descending
  - Index reset

**Example:**
```python
from data_utils import get_team_total_points

totals = get_team_total_points(starting)
print(totals)
# Output:
#              Team  Total Points
# 0      Blue Lock XI        195.0
# 1         Magic FC        190.0
```

---

#### `points_per_player_position(starting_players: pd.DataFrame) -> pd.DataFrame`

Total points by position (GK, DEF, MID, FWD).

**Parameters:**
- `starting_players` (DataFrame): Starting XI only

**Returns:**
- `DataFrame`:
  - Columns: `["position", "gw_points"]`

**Example:**
```python
from data_utils import points_per_player_position

pos_points = points_per_player_position(starting)
print(pos_points)
# Output:
#   position  gw_points
# 0       GK       20.0
# 1      DEF      145.0
# 2      MID      230.0
# 3      FWD      100.0
```

---

### Player Performance

#### `get_top_performers(manager_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame`

Top N performing players (single gameweek basis).

**Parameters:**
- `manager_df` (DataFrame): Manager-filtered data (use `get_manager_data()`)
- `top_n` (int): Number of results. Default: `10`

**Returns:**
- `DataFrame`:
  - Columns: `["Gameweek", "Player", "Team", "Points", "Benched"]`
  - Sorted by Points descending
  - Limited to top_n rows

**Example:**
```python
from data_utils import get_manager_data, get_top_performers

manager_df = get_manager_data(df, "Blue Lock XI")
top_10 = get_top_performers(manager_df, top_n=10)

print(top_10)
# Output:
#    Gameweek           Player Team  Points Benched
# 0        1  Erling Haaland  MCI      15   False
# 1        2  Phil Foden       MCI      14   False
```

---

#### `get_player_progression(manager_df: pd.DataFrame) -> pd.DataFrame`

Player points progression over gameweeks.

**Parameters:**
- `manager_df` (DataFrame): Manager-filtered data

**Returns:**
- `DataFrame`:
  - Index: Player names
  - Columns: Gameweek numbers (1, 2, 3, ...)
  - Values: Points per gameweek (0 if not in squad)

**Example:**
```python
from data_utils import get_player_progression

progression = get_player_progression(manager_df)
print(progression)
# Output:
#                    1   2   3   4
# Erling Haaland    15  12  14   0
# Phil Foden        10  14  12  13

# Best performing player overall
best_player = progression.sum(axis=1).idxmax()
print(f"Best player: {best_player}")
```

---

## visuals_utils.py

### Display Functions

#### `display_overview(manager_name: str, manager_df: pd.DataFrame) -> None`

Displays manager season overview with statistics.

**Parameters:**
- `manager_name` (str): Manager team name
- `manager_df` (DataFrame): Manager-filtered data

**Displays:**
- 📊 Team Points by Gameweek (table)
- 📈 Average Points Metric
- 🥧 Points Distribution by Position (pie chart)

**Example:**
```python
from data_utils import load_data_supabase, get_manager_data
from visuals_utils import display_overview
import streamlit as st
from supabase import create_client
from supabase_client import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, _, _, _ = load_data_supabase(supabase)

manager_df = get_manager_data(df, "Blue Lock XI")
display_overview("Blue Lock XI", manager_df)
```

---

#### `display_performance_trend(manager_name: str, df: pd.DataFrame) -> pd.DataFrame`

Line chart: Manager points vs league average.

**Parameters:**
- `manager_name` (str): Manager team name
- `df` (DataFrame): Full player data

**Returns:**
- `DataFrame`: Manager points per gameweek

**Displays:**
- 📈 Line chart with dual series:
  - Manager points (solid line)
  - League average (dashed line)

**Example:**
```python
from visuals_utils import display_performance_trend

manager_points = display_performance_trend("Blue Lock XI", df)
print(manager_points)
# Output:
#    gameweek  manager_points  avg_points
# 0        1            65.0        60.5
# 1        2            72.0        62.3
```

---

#### `display_latest_gw(manager_df: pd.DataFrame) -> None`

Shows latest gameweek squad and points.

**Parameters:**
- `manager_df` (DataFrame): Manager-filtered data

**Displays:**
- 🎯 Table with columns: `[Player, Team, Squad Position, Points]`
- Sorted by squad position (1-15)

**Example:**
```python
from visuals_utils import display_latest_gw

display_latest_gw(manager_df)
```

---

#### `display_top_performers(manager_df: pd.DataFrame) -> pd.DataFrame`

Shows top 10 performing players (single GW basis).

**Parameters:**
- `manager_df` (DataFrame): Manager-filtered data

**Returns:**
- `DataFrame`: Top performers table

**Displays:**
- ⭐ Table with top players

**Example:**
```python
from visuals_utils import display_top_performers

top_df = display_top_performers(manager_df)
```

---

#### `display_player_progression(manager_df: pd.DataFrame) -> None`

Line chart showing each player's points over gameweeks.

**Parameters:**
- `manager_df` (DataFrame): Manager-filtered data

**Displays:**
- 📊 Multi-line chart (one line per player)

**Example:**
```python
from visuals_utils import display_player_progression

display_player_progression(manager_df)
```

---

#### `display_other_stats(manager_points: pd.DataFrame, top_performances: pd.DataFrame) -> None`

Key statistics metrics.

**Parameters:**
- `manager_points` (DataFrame): Output from `display_performance_trend()`
- `top_performances` (DataFrame): Output from `display_top_performers()`

**Displays (3 metrics):**
- 🏆 Top Scorer (player name + points)
- 🥇 Best Gameweek (GW number + points)
- 📉 Toughest Gameweek (GW number + points)

**Example:**
```python
from visuals_utils import display_other_stats

display_other_stats(manager_points, top_df)
```

---

### Helper Functions

#### `calc_defensive_points(row: pd.Series) -> pd.Series`

Calculates bonus points for defensive contributions.

**Parameters:**
- `row` (Series): Player record with columns:
  - `position` (DEF/MID/FWD/GK)
  - `gw_defensive_contribution` (int)

**Returns:**
- `Series` with:
  - `def_points` (int): 2 if threshold met, else 0
  - `progress` (float): 0-1 progress toward threshold
  - `total_contributions` (int): Defensive action count

**Rules:**
- Defenders: 2 pts at ≥10 contributions
- Midfielders: 2 pts at ≥12 contributions
- Forwards/GK: 0 pts (ineligible)

**Example:**
```python
from visuals_utils import calc_defensive_points

row = manager_df.iloc[0]
bonus = calc_defensive_points(row)
print(f"Defensive Points: {bonus['def_points']}")
print(f"Progress: {bonus['progress']:.1%}")
```

---

## supabase_client.py

#### `SUPABASE_URL`
Supabase project URL from secrets.

#### `SUPABASE_KEY`
Supabase public API key from secrets.

#### `supabase`
Initialized Supabase client.

**Example:**
```python
from supabase_client import supabase

# List files in storage bucket
files = supabase.storage.from_("data").list()
print(files)

# Download file
data = supabase.storage.from_("data").download("gw_data.parquet")
```

---

## Streamlit Integration

### Common Streamlit Components Used

#### `st.cache_data`
Caches `load_data_supabase()` result for performance.

```python
@st.cache_data
def load_data_supabase(...):
    # Cached - runs only once per session
    ...
```

#### `st.session_state`
Stores current page selection.

```python
if st.button("Manager"):
    st.session_state["current_page"] = manager_name
    st.switch_page(f"pages/{manager_name}.py")
```

#### `st.dataframe`
Displays DataFrames with interactivity.

```python
st.dataframe(df, use_container_width=True, hide_index=True)
```

#### `st.plotly_chart`
Displays Plotly charts.

```python
fig = px.line(...)
st.plotly_chart(fig, use_container_width=True)
```

---

## Data Type Reference

### Column Names by DataFrame

**gw_data:**
```python
["gw", "manager_team_name", "full_name", "real_team", 
 "position", "team_position", "gw_points", 
 "gw_defensive_contribution"]
```

**standings:**
```python
["team_name", "total_points", "last_updated"]
```

**gameweeks:**
```python
["id", "name", "deadline_time", "average_entry_points", "finished"]
```

**fixtures:**
```python
["event", "team_h_name", "team_a_name", "kickoff_time", 
 "team_h_difficulty", "team_a_difficulty"]
```

---

## Error Handling Examples

### Safe Data Loading

```python
from data_utils import load_data_supabase
import streamlit as st

try:
    df, standings, gameweeks, fixtures = load_data_supabase(supabase)
except FileNotFoundError as e:
    st.error(f"Missing required file: {e}")
except Exception as e:
    st.error(f"Failed to load data: {e}")
```

### Empty DataFrame Handling

```python
from data_utils import get_manager_data

manager_df = get_manager_data(df, unknown_manager)

if manager_df.empty:
    st.warning("No data found for this manager")
else:
    # Process data
    ...
```

---

**Last Updated:** January 2026  
**Version:** 1.0.0
