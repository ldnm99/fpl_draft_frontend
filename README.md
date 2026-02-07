# ⚽ FPL Draft Dashboard

A **Streamlit-based web application** for tracking and analyzing Fantasy Premier League (FPL) draft league performance with **Medallion Architecture** data pipeline integration.

## 🎯 Features

- **Dashboard Overview** - League standings, upcoming fixtures, and deadline countdown
- **Medallion Architecture** - Gold layer star schema with fact/dimension tables
- **Manager Pages** - Individual dashboards for each manager with detailed statistics
- **Performance Tracking** - Gameweek-by-gameweek points progression and comparisons
- **Player Analytics** - Top performers, clustering, and positional analysis
- **FPL-Style Pitch Visualization** - Enhanced squad view with fixtures and formations
- **Data Refresh** - Manual refresh button and ETL pipeline trigger
- **Interactive Visualizations** - Plotly charts for trends and insights

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Supabase account with storage bucket
- GitHub account for ETL pipeline

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ldnm99/fpl_draft_frontend.git
   cd fpl_draft_frontend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Supabase credentials
   ```

4. **Create Streamlit secrets**
   ```bash
   mkdir -p ~/.streamlit
   # Add SUPABASE_URL, SUPABASE_KEY, TOKEN_STREAMLIT to ~/.streamlit/secrets.toml
   ```

5. **Run the app**
   ```bash
   streamlit run menu.py
   ```

   The app opens at `http://localhost:8501`

## 📁 Project Structure

```
FPL_frontend/
├── menu.py                     # Main entry point
├── core/                       # Core application logic
│   ├── medallion_data_loader.py  # Gold layer data loader
│   ├── data_utils.py            # Data processing
│   ├── visuals_utils.py         # Visualizations
│   ├── pitch_visualization.py   # Pitch display
│   └── injury_utils.py          # Injury tracking
├── pages/                      # Streamlit pages
│   ├── Overall.py              # League overview
│   ├── Current Gameweek.py     # GW analysis
│   ├── Fixtures.py             # Upcoming fixtures
│   ├── Players Data.py         # Player analytics
│   └── [Manager].py            # Individual dashboards
├── config/                     # Configuration
│   └── supabase_client.py      # Supabase setup
├── Data/                       # Local CSV files
│   ├── gameweeks.csv
│   └── fixtures.csv
├── docs/                       # Documentation
│   ├── README.md               # Detailed docs
│   ├── SETUP.md                # Setup guide
│   ├── ARCHITECTURE.md         # Technical design
│   ├── MEDALLION_MIGRATION.md  # Migration guide
│   └── API_REFERENCE.md        # Function docs
└── requirements.txt            # Dependencies
```

## 🏗️ Architecture

### Data Flow
```
FPL API → ETL Pipeline → Supabase Gold Layer → Frontend Dashboard
                              ↓
                     Dimensions + Facts
                              ↓
                    Backward-Compatible Views
```

### Medallion Schema
- **Gold Layer**: Star schema with fact and dimension tables
- **Dimensions**: Players, teams, managers, gameweeks
- **Facts**: Player gameweek performance, manager performance
- **Auto-detection**: Fallback to legacy if medallion unavailable

## 📊 Key Functions

### Data Loading
```python
from core.data_utils import load_data_auto

# Smart loader with medallion/legacy fallback
df, standings, gameweeks, fixtures = load_data_auto(supabase)
```

### Visualization
```python
from core.visuals_utils import display_overview

display_overview(df, standings, "Manager Name")
```

## 🔄 Data Refresh

Use the **"🔄 Refresh Data"** button to:
- Clear all caches
- Reload fresh data from Supabase
- Update all visualizations

Or trigger ETL pipeline:
1. Click **"▶️ Run ETL Pipeline"**
2. Wait 30-60 seconds
3. Click **"🔄 Refresh Data"**

## 📖 Documentation

- **[SETUP.md](docs/SETUP.md)** - Detailed setup and deployment
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Technical design
- **[MEDALLION_MIGRATION.md](docs/MEDALLION_MIGRATION.md)** - Schema migration guide
- **[API_REFERENCE.md](docs/API_REFERENCE.md)** - Function reference
- **[CHANGELOG.md](docs/CHANGELOG.md)** - Version history

## 🌐 Deployment

### Streamlit Cloud
1. Push to GitHub
2. Connect repo on [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in "Advanced settings"
4. Deploy!

See [SETUP.md](docs/SETUP.md) for details.

## 🐛 Troubleshooting

**Data not loading?**
- Check Supabase credentials
- Verify files exist in storage bucket
- Click "🔄 Refresh Data"

**Pages not loading?**
- Check `pages/` directory
- Restart Streamlit app

See [SETUP.md](docs/SETUP.md#troubleshooting) for more.

## 🤝 Contributing

1. Create feature branch
2. Make changes with clear commits
3. Test locally
4. Submit pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📝 Recent Updates (v2.0.0 - Feb 2026)

- ✅ Medallion architecture integration
- ✅ Enhanced FPL-style pitch visualization
- ✅ Column name refactoring (180+ updates)
- ✅ Data refresh system
- ✅ Backend compatibility layer
- ✅ Visualization bug fixes

See [CHANGELOG.md](docs/CHANGELOG.md) for details.

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) - Web framework
- [Plotly](https://plotly.com/) - Visualizations
- [Supabase](https://supabase.com/) - Cloud database
- [FPL API](https://fantasy.premierleague.com/api/) - Data source

---

**Version:** 2.0.0  
**Last Updated:** February 7, 2026  
**Status:** ✅ Production Ready
