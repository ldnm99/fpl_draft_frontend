# ⚽ FPL Draft Dashboard

A **Streamlit-based web application** for tracking and analyzing Fantasy Premier League (FPL) draft league performance. Monitor team standings, gameweek stats, player performance, and upcoming fixtures in a centralized dashboard.

## 🎯 Features

- **Dashboard Overview** - League standings, upcoming fixtures, and deadline countdown
- **Manager Pages** - Individual dashboards for each manager with detailed statistics
- **Performance Tracking** - Gameweek-by-gameweek points progression and comparisons
- **Player Analytics** - Top performers, player progression over time, positional analysis
- **Data Updates** - Trigger ETL pipeline directly from the UI to refresh data from FPL API
- **Interactive Visualizations** - Plotly charts for points trends, position distribution, and more

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip or conda
- Supabase account with storage bucket
- GitHub account for ETL pipeline

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/ldnm99/fpl_draft_frontend.git
   cd fpl_draft_frontend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (see [SETUP.md](SETUP.md))
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Create Streamlit secrets** (for local development)
   ```bash
   mkdir -p ~/.streamlit
   cat > ~/.streamlit/secrets.toml << EOF
   SUPABASE_URL = "your_supabase_url"
   SUPABASE_KEY = "your_supabase_key"
   TOKEN_STREAMLIT = "your_github_token"
   EOF
   ```

6. **Run the app**
   ```bash
   streamlit run menu.py
   ```

   The app will open at `http://localhost:8501`

## 📁 Project Structure

```
FPL_frontend/
├── menu.py                 # Main entry point (page navigation)
├── data_utils.py           # Data loading and transformation functions
├── visuals_utils.py        # Visualization and chart functions
├── supabase_client.py      # Supabase client initialization
├── pages/                  # Individual manager and feature pages
│   ├── Overall.py         # League overview dashboard
│   ├── Current Gameweek.py # Current gameweek details
│   ├── Fixtures.py        # Upcoming fixtures
│   ├── Players Data.py    # Player analysis
│   └── [Manager].py       # Individual manager dashboards
├── Data/                   # Local CSV files
│   ├── gameweeks.csv      # Gameweek definitions
│   └── fixtures.csv       # Match fixtures
├── assets/                # Static files (images, etc.)
└── docs/                  # Documentation
```

## 🔧 Configuration

Key environment variables (set in `.streamlit/secrets.toml`):

| Variable | Description | Required |
|----------|-------------|----------|
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_KEY` | Supabase public API key | Yes |
| `TOKEN_STREAMLIT` | GitHub personal access token | Yes |

Data files location:
- `Data/gameweeks.csv` - Gameweek schedule and deadlines
- `Data/fixtures.csv` - FPL match fixtures

Supabase storage bucket contents:
- `gw_data.parquet` - Player gameweek stats
- `league_standings.csv` - Manager standings and points

## 📊 Key Functions

### Data Loading (`data_utils.py`)
- `load_data_supabase()` - Load all data from Supabase and local files
- `get_next_gameweek()` - Get the upcoming gameweek
- `get_upcoming_fixtures()` - Get fixtures for next gameweek
- `get_manager_data()` - Filter data for a specific manager

### Data Analysis (`data_utils.py`)
- `get_starting_lineup()` - Get only starting XI players
- `calculate_team_gw_points()` - Points per team per gameweek
- `get_team_total_points()` - Total points for each manager
- `get_top_performers()` - Top N players for a manager

### Visualizations (`visuals_utils.py`)
- `display_overview()` - Manager season overview with charts
- `display_performance_trend()` - Points progression vs league average
- `display_latest_gw()` - Current gameweek lineup
- `display_top_performers()` - Best performing players
- `display_player_progression()` - Player points over time

## 🔄 Data Flow

```
FPL API (External)
    ↓
GitHub Actions ETL (backend repo)
    ↓
Supabase Storage (Cloud DB)
    ↓
Streamlit Dashboard (Frontend)
    ↑
User triggers ETL via UI
```

For detailed architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## 🌐 Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create new app from repository
4. Set secrets in "Advanced settings":
   ```
   SUPABASE_URL = "..."
   SUPABASE_KEY = "..."
   TOKEN_STREAMLIT = "..."
   ```
5. Deploy!

See [SETUP.md](SETUP.md) for detailed Streamlit Cloud setup.

## 📖 Documentation

- [SETUP.md](SETUP.md) - Detailed setup instructions and troubleshooting
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture and design decisions
- [API_REFERENCE.md](API_REFERENCE.md) - Function documentation and usage examples

## 🐛 Troubleshooting

**Issue: "Secrets not found" error**
- Ensure `.streamlit/secrets.toml` exists in your home directory
- Check that all required keys are present

**Issue: Data not loading**
- Verify Supabase credentials are correct
- Check that files exist in Supabase storage bucket
- Ensure `Data/gameweeks.csv` and `Data/fixtures.csv` exist locally

**Issue: "No upcoming gameweeks"**
- This is expected when FPL season is not active
- Check gameweeks.csv has data for current/upcoming season

**Issue: Pages not loading**
- Ensure page file exists in `pages/` directory
- Check filename matches manager name exactly
- Restart Streamlit app

See [SETUP.md](SETUP.md) for more troubleshooting.

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with clear commits
3. Test locally before pushing
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 Data Schema

### Player Data (gw_data.parquet)
```
- gw: int (gameweek number)
- manager_team_name: str (team name of manager)
- full_name: str (player name)
- real_team: str (player's real FPL team)
- position: str (DEF/MID/FWD/GK)
- team_position: int (1-15, 1-11 are starting XI)
- gw_points: float (points scored in gameweek)
- gw_defensive_contribution: int (tackles, interceptions, etc.)
```

### Standings (league_standings.csv)
```
- team_name: str (manager team name)
- total_points: float (season total points)
- last_updated: timestamp
```

### Gameweeks (Data/gameweeks.csv)
```
- id: int
- name: str (e.g., "GW 1")
- deadline_time: datetime
- average_entry_points: float
```

### Fixtures (Data/fixtures.csv)
```
- event: int (gameweek number)
- team_h_name: str (home team)
- team_a_name: str (away team)
- kickoff_time: datetime
- team_h_difficulty: int (1-5 difficulty rating)
- team_a_difficulty: int (1-5 difficulty rating)
```

## 📞 Support

For issues or questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review [SETUP.md](SETUP.md) for detailed info
3. Open an issue on GitHub

## 📄 License

[Specify your license here]

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Data visualization with [Plotly](https://plotly.com/)
- Cloud database: [Supabase](https://supabase.com/)
- FPL data from [FPL API](https://fantasy.premierleague.com/api/)

---

**Last Updated:** January 2026  
**Version:** 1.0.0
