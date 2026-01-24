# 🏗️ Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│                    (Streamlit Frontend)                          │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               │ HTTP/WebSocket
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    STREAMLIT APPLICATION                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ menu.py (Main Entry Point)                                 │ │
│  │  - Page navigation                                         │ │
│  │  - Dashboard overview                                      │ │
│  │  - ETL pipeline trigger                                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────┬──────────────────┬────────────────────────┐│
│  │  pages/         │ data_utils.py    │ visuals_utils.py       ││
│  │  ├─ Overall.py  │ ├─ Data Loading  │ ├─ Charts             ││
│  │  ├─ Fixtures.py │ ├─ Filtering     │ ├─ Visualizations    ││
│  │  └─ [Managers]  │ └─ Aggregations  │ └─ Formatting        ││
│  └─────────────────┴──────────────────┴────────────────────────┘│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
        ┌─────────────────────┐  ┌──────────────────┐
        │  SUPABASE (Cloud)   │  │  LOCAL STORAGE   │
        │                     │  │                  │
        │ ┌─────────────────┐ │  │ ┌──────────────┐ │
        │ │ Storage Bucket: │ │  │ │ Data/        │ │
        │ │ - gw_data.pqt  │ │  │ │ ├─ gameweeks │ │
        │ │ - standings.csv │ │  │ │ └─ fixtures  │ │
        │ └─────────────────┘ │  │ └──────────────┘ │
        └─────────────────────┘  └──────────────────┘
```

---

## Module Architecture

### 1. **menu.py** - Application Entry Point
**Purpose**: Main dashboard and page navigation hub

**Key Functions**:
- Loads all required data on startup
- Displays league overview and standings
- Manages page navigation via session state
- Provides ETL pipeline trigger button

**Dependencies**: 
- Streamlit
- data_utils
- supabase_client

**Data Flow**:
```
User Opens App
    ↓
menu.py loads data (supabase + local)
    ↓
Display overview dashboard
    ↓
User selects manager → switch_page()
    ↓
Manager page loads with filtered data
```

---

### 2. **data_utils.py** - Data Operations Layer
**Purpose**: All data loading, filtering, and transformation logic

**Submodules**:

#### **Loading Functions**
```python
load_data_supabase(supabase, bucket, ...)
    ├─ _download_parquet()      # Get gw_data from cloud
    ├─ _download_csv()          # Get standings from cloud
    ├─ pd.read_csv()            # Get gameweeks locally
    └─ pd.read_csv()            # Get fixtures locally
```

**Data Contract**:
- Returns: Tuple[DataFrame, DataFrame, DataFrame, DataFrame]
- Raises: FileNotFoundError, ConnectionError (on Supabase failure)

#### **Filtering Functions**
```python
get_manager_data(df, manager_name)
    → DataFrame with manager's players only

get_starting_lineup(df)
    → DataFrame filtered to positions 1-11 (starting XI)

get_next_gameweek(gameweeks, now)
    → DataFrame with next upcoming gameweek
```

#### **Aggregation Functions**
```python
calculate_team_gw_points(starting_players)
    → Pivot table: Teams × Gameweeks with points

get_team_total_points(starting_players)
    → Summary: Team Name | Total Points

get_top_performers(manager_df, top_n)
    → Top N players by points (single gameweek)

get_player_progression(manager_df)
    → Pivot table: Players × Gameweeks
```

**Error Handling**:
- Returns empty DataFrame on invalid input
- No exceptions thrown (fail gracefully)
- Timezone-aware datetime handling

---

### 3. **visuals_utils.py** - Visualization Components
**Purpose**: Reusable visualization and chart functions

**Display Functions**:
```python
display_overview(manager_name, manager_df)
    → Shows: Points table, avg points metric, position pie chart

display_performance_trend(manager_name, df)
    → Shows: Line chart comparing manager vs league average

display_latest_gw(manager_df)
    → Shows: Table with latest gameweek lineup

display_top_performers(manager_df)
    → Shows: Table of top 10 performers

display_player_progression(manager_df)
    → Shows: Line chart of player points over time

display_other_stats(manager_points, top_performances)
    → Shows: Metrics for best player, best GW, worst GW
```

**Helper Functions**:
```python
calc_defensive_points(row)
    → Calculate bonus points for defensive contributions
```

**Dependencies**:
- Streamlit (st.metric, st.dataframe, st.plotly_chart)
- Plotly (px.pie, px.line)
- data_utils (for data transformations)

---

### 4. **supabase_client.py** - Cloud Database Connector
**Purpose**: Initialize and configure Supabase client

**Contents**:
```python
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
```

**Used By**: menu.py, Overall.py, and all pages

**Future**: Could be expanded with:
- Error retry logic
- Connection pooling
- Rate limiting
- Logging

---

### 5. **pages/** - Individual Page Components

#### **pages/Overall.py** - League Overview
Displays aggregate league statistics and filters

**Key Features**:
- Gameweek range slider filter
- Manager selection dropdown
- Team points pivot table
- Average points visualization

**Data Flow**:
```
Load all data
    ↓
Apply filters (GW range, manager)
    ↓
Calculate aggregations
    ↓
Display charts and tables
```

#### **pages/[Manager].py** - Individual Manager Dashboards
Displays detailed stats for each manager (e.g., "Blue Lock XI.py")

**Dynamic Generation**: Created for each unique manager in standings

**Sections**:
1. Season Overview (points table, metrics)
2. Performance Trend (line chart vs league)
3. Latest GW Lineup (player table)
4. Top Performers (best players)
5. Player Progression (heatmap-style)
6. Other Stats (best/worst gameweek)

**Design Pattern**: Modular display functions called sequentially

---

## Data Models

### DataFrame Schemas

#### **Player Gameweek Data** (gw_data.parquet)
```
Schema:
├─ gw: int32                              # Gameweek number
├─ manager_team_name: string              # Manager's team name
├─ full_name: string                      # Player name
├─ real_team: string                      # Player's actual FPL team
├─ position: string (DEF/MID/FWD/GK)     # Player position
├─ team_position: int32 (1-15)           # Squad position (1-11 are XI)
├─ gw_points: float32                     # Points scored in GW
└─ gw_defensive_contribution: int32       # Defensive actions count

Sample:
   gw  manager_team_name  full_name       real_team  position  team_position  gw_points
   1   Blue Lock XI       Erling Haaland  MCI       FWD      1              15
   1   Blue Lock XI       Raheem Sterling MCI       MID      2              12
```

#### **League Standings** (league_standings.csv)
```
Schema:
├─ team_name: string                      # Manager's team name
├─ total_points: float                    # Season total points
└─ last_updated: datetime                 # Last update timestamp

Sample:
   team_name          total_points
   Blue Lock XI       324.5
   Magic FC           298.2
```

#### **Gameweeks** (Data/gameweeks.csv)
```
Schema:
├─ id: int                                # Gameweek ID
├─ name: string (e.g., "GW 1")           # Display name
├─ deadline_time: datetime (UTC)          # Transfer deadline
├─ average_entry_points: float            # FPL average for GW
└─ finished: boolean                      # If gameweek completed

Sample:
   id  name   deadline_time           average_entry_points
   1   GW 1   2023-08-11 18:00 UTC   45.3
   2   GW 2   2023-08-18 18:00 UTC   52.1
```

#### **Fixtures** (Data/fixtures.csv)
```
Schema:
├─ event: int                             # Gameweek number
├─ team_h_name: string                    # Home team name
├─ team_a_name: string                    # Away team name
├─ kickoff_time: datetime                 # Match start time
├─ team_h_difficulty: int (1-5)          # Home difficulty rating
└─ team_a_difficulty: int (1-5)          # Away difficulty rating

Sample:
   event  team_h_name  team_a_name  kickoff_time          team_h_difficulty
   1      Arsenal      Leicester    2023-08-12 15:00      1
   1      Man City     Nottingham   2023-08-12 15:00      1
```

---

## Data Flow Processes

### Process 1: Application Startup
```
1. User opens app (menu.py)
   ↓
2. load_data_supabase() called
   ├─ Download gw_data.parquet from Supabase
   ├─ Download league_standings.csv from Supabase
   ├─ Read Data/gameweeks.csv locally
   └─ Read Data/fixtures.csv locally
   ↓
3. Streamlit caches result (@st.cache_data)
   ↓
4. Display overview dashboard
   ├─ Show league standings
   ├─ Show upcoming fixtures
   └─ Show countdown to deadline
   ↓
5. Manager buttons generated dynamically
```

### Process 2: Page Navigation
```
1. User clicks manager button
   ↓
2. st.session_state["current_page"] = manager_name
   ↓
3. st.switch_page(f"pages/{manager_name}.py")
   ↓
4. Manager page script executes
   ├─ Load data (from cache if available)
   ├─ Filter to manager_team_name = selected
   ├─ Call display functions from visuals_utils
   └─ Render charts and tables
```

### Process 3: ETL Trigger
```
1. User clicks "Run ETL Pipeline" button
   ↓
2. trigger_pipeline() sends GitHub API request
   ├─ POST to /repos/{OWNER}/{REPO}/dispatches
   ├─ Event type: "run_pipeline"
   └─ Headers: Authorization Bearer {TOKEN}
   ↓
3. GitHub Actions workflow triggered (on backend repo)
   ├─ Fetch data from FPL API
   ├─ Transform and aggregate
   └─ Upload to Supabase Storage
   ↓
4. st.cache_data.clear() clears local cache
   ↓
5. User refreshes page to see updated data
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Web UI framework |
| **Visualization** | Plotly | Interactive charts |
| **Data Processing** | Pandas | DataFrame operations |
| **Cloud Database** | Supabase | File storage and API |
| **Data Format** | Parquet/CSV | Efficient data storage |
| **Orchestration** | GitHub Actions | Backend ETL pipeline |
| **Language** | Python 3.8+ | Core language |

---

## Caching Strategy

### Current Implementation
- **Streamlit Cache**: `@st.cache_data` on `load_data_supabase()`
  - Caches raw DataFrames from Supabase
  - Clears when user clicks "Run ETL Pipeline"
  - TTL: Session-based (cleared on restart)

### Data Freshness
- **Parquet File**: Updated by ETL pipeline (backend)
- **CSV Files**: Static local files
- **Cache Invalidation**: Manual via UI button

---

## Future Improvements

### Scalability
- [ ] Implement database-level filtering (Supabase queries)
- [ ] Add pagination for large tables
- [ ] Use st.query_params for shareable URLs
- [ ] Implement lazy loading for manager pages

### Reliability
- [ ] Add retry logic to Supabase downloads
- [ ] Implement logging system
- [ ] Add data validation schema
- [ ] Create backup data sources

### Performance
- [ ] Profile with py_spy
- [ ] Optimize pivot table operations
- [ ] Pre-compute aggregations
- [ ] Use concurrent downloads

### Maintainability
- [ ] Centralize configuration
- [ ] Add unit tests
- [ ] Add type hints
- [ ] Extract duplicated code
- [ ] Create reusable Streamlit components

---

## Deployment Considerations

### Streamlit Cloud
- Automatic deployment from GitHub
- Secrets managed in cloud settings
- No infrastructure to maintain
- Limited to 1GB RAM per app

### Self-Hosted
- Docker container for portability
- More control over resources
- Manual scaling required
- Additional DevOps overhead

### Data Sources
- Supabase: Requires internet connection
- Local files: Must be in GitHub repo or Docker image
- Consider CDN for large files

---

## Security Architecture

### Secrets Management
- Credentials stored in Streamlit secrets (not in code)
- GitHub token scoped to dispatch events only
- Supabase key restricted to read storage only

### Data Access
- Supabase RLS not currently used (public bucket)
- Consider adding row-level security for production
- Authentication layer recommended for shared deployments

### API Security
- GitHub token not exposed in frontend
- Supabase key is public (but restricted to storage)
- Consider API gateway for sensitive operations

---

## Testing Strategy

### Unit Tests (Recommended)
```python
test_data_utils.py
├─ test_get_manager_data()
├─ test_get_starting_lineup()
├─ test_calculate_team_gw_points()
└─ test_empty_dataframe_handling()

test_visuals_utils.py
├─ test_display_overview()
└─ test_calc_defensive_points()
```

### Integration Tests
```python
test_integration.py
├─ test_full_data_pipeline()
├─ test_page_navigation()
└─ test_etl_trigger()
```

### Load Testing
- Simulate multiple concurrent users
- Monitor Supabase API limits
- Test cache effectiveness

---

## Monitoring & Observability

### Metrics to Track
- Page load time (target < 2s)
- API response time (Supabase)
- Cache hit rate
- Error frequency
- User session duration

### Logging
- Data load errors
- API failures
- User actions (navigation, filters)
- Performance metrics

### Alerts
- Supabase connection failures
- GitHub API errors
- Missing data files
- Page load timeout

---

**Last Updated:** January 2026  
**Architecture Version:** 1.0
