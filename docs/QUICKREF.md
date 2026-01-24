# 📋 Quick Reference Guide

Fast lookup for common tasks and frequently used commands.

---

## 🚀 Getting Started (5 minutes)

### 1. Clone & Setup
```bash
git clone https://github.com/ldnm99/fpl_draft_frontend.git
cd fpl_draft_frontend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Secrets
```bash
# Create ~/.streamlit/secrets.toml with:
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your_key"
TOKEN_STREAMLIT = "your_github_token"
```

### 3. Run Locally
```bash
streamlit run menu.py
# Opens http://localhost:8501
```

---

## 📚 Documentation Files

| File | Purpose | Read When |
|------|---------|-----------|
| [README.md](README.md) | Overview & features | First time setup |
| [SETUP.md](SETUP.md) | Detailed setup guide | Installing locally or deploying |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical design | Understanding codebase |
| [API_REFERENCE.md](API_REFERENCE.md) | Function docs | Using/extending functions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide | Contributing code |
| [CHANGELOG.md](CHANGELOG.md) | Version history | Checking updates |

---

## 🔍 Code Structure

```
FPL_frontend/
├── menu.py              # Main entry (page navigation)
├── data_utils.py        # Data loading & processing
├── visuals_utils.py     # Charts & visualizations
├── supabase_client.py   # Database connection
├── pages/               # Page scripts
│   ├── Overall.py      # League overview
│   ├── [Manager].py    # Individual manager pages
│   └── Fixtures.py     # Upcoming matches
└── Data/               # Local files
    ├── gameweeks.csv
    └── fixtures.csv
```

---

## 🔧 Common Commands

### Development
```bash
# Run app
streamlit run menu.py

# Debug mode
streamlit run menu.py --logger.level=debug

# Run tests (when available)
pytest

# Code formatting
black .
isort .
```

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature

# Commit changes
git add .
git commit -m "feat: Description of change"

# Push to remote
git push origin feature/your-feature

# Create pull request on GitHub
```

### Deployment
```bash
# Push to trigger Streamlit Cloud deployment
git push origin main

# Check deployment status
# Go to: https://share.streamlit.io/ldnm99/fpl_draft_frontend/main
```

---

## 📊 Key Data Functions

### Load Data
```python
from data_utils import load_data_supabase
from supabase import create_client
from supabase_client import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, standings, gameweeks, fixtures = load_data_supabase(supabase)
```

### Filter & Analyze
```python
from data_utils import (
    get_manager_data,           # Get manager's players
    get_starting_lineup,        # Get XI only (positions 1-11)
    calculate_team_gw_points,   # Points per GW table
    get_team_total_points,      # Total points per team
    get_top_performers,         # Top N players
    get_player_progression      # Points over time
)

# Get manager data
manager_df = get_manager_data(df, "Blue Lock XI")

# Get starting XI
starting = get_starting_lineup(manager_df)

# Calculate points
team_points = calculate_team_gw_points(starting)
```

### Visualize
```python
from visuals_utils import (
    display_overview,           # Overview with charts
    display_performance_trend,  # Manager vs league
    display_latest_gw,          # Current lineup
    display_top_performers,     # Best players
    display_player_progression  # Points over time
)

display_overview("Blue Lock XI", manager_df)
display_performance_trend("Blue Lock XI", df)
```

---

## 🐛 Troubleshooting

### Secrets Not Found
```bash
# Check secrets file exists:
cat ~/.streamlit/secrets.toml  # macOS/Linux
type %APPDATA%\.streamlit\secrets.toml  # Windows

# Recreate if missing
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml << EOF
SUPABASE_URL = "..."
SUPABASE_KEY = "..."
TOKEN_STREAMLIT = "..."
EOF
```

### Data Not Loading
```python
# Check connection
import requests
r = requests.head("https://xxxxx.supabase.co")
print(r.status_code)  # Should be 200

# Check files
python -c "
import pandas as pd
import os
print('gameweeks exists:', os.path.exists('Data/gameweeks.csv'))
print('fixtures exists:', os.path.exists('Data/fixtures.csv'))
"
```

### Page Not Found
```bash
# Check page files exist
ls -la pages/

# Check filename matches manager name exactly
# Filenames are case-sensitive on Linux/Mac
```

---

## 🎯 Development Workflow

### Adding a New Feature

1. **Create branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**
   - Edit relevant files
   - Add docstrings
   - Test locally

3. **Commit**
   ```bash
   git add .
   git commit -m "feat: My new feature"
   ```

4. **Push & Create PR**
   ```bash
   git push origin feature/my-feature
   # Create PR on GitHub
   ```

### Adding a New Page

1. **Create page file** in `pages/`:
   ```python
   # pages/New Page.py
   import streamlit as st
   from data_utils import load_data_supabase
   from supabase import create_client
   from supabase_client import SUPABASE_URL, SUPABASE_KEY

   st.set_page_config(layout="wide")
   supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
   df, _, _, _ = load_data_supabase(supabase)

   st.title("New Page")
   st.write("Your content here")
   ```

2. **Add navigation** in `menu.py`:
   ```python
   if st.button("New Page"):
       st.switch_page("pages/New Page.py")
   ```

3. **Test locally** and commit

---

## 📖 Python Snippets

### Filter DataFrame
```python
# Single condition
filtered = df[df["position"] == "MID"]

# Multiple conditions
filtered = df[(df["gw"] > 5) & (df["gw_points"] > 10)]

# NOT condition
filtered = df[~df["position"].isin(["GK", "DEF"])]
```

### Datetime Operations
```python
from datetime import datetime, timezone

# Current UTC time
now = datetime.now(timezone.utc)

# Parse string to datetime
deadline = pd.to_datetime("2023-08-11 18:00:00+00:00", utc=True)

# Time until deadline
remaining = deadline - now
print(f"{remaining.days} days, {remaining.seconds // 3600} hours")
```

### Streamlit Patterns
```python
# Cache expensive operations
@st.cache_data
def load_data():
    return expensive_operation()

# Session state for persistence
if "page" not in st.session_state:
    st.session_state["page"] = "home"

# Conditional display
if condition:
    st.success("Success!")
else:
    st.error("Error!")

# Columns for layout
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Title", value)
with col2:
    st.dataframe(df)
```

---

## 🌐 Environment Variables

### Required (for functionality)
```
SUPABASE_URL          # Supabase project URL
SUPABASE_KEY          # Supabase public key
TOKEN_STREAMLIT       # GitHub personal token
```

### Optional (with defaults)
```
GW_DATA_FILE          # Default: gw_data.parquet
STANDINGS_FILE        # Default: league_standings.csv
STORAGE_BUCKET        # Default: data
ETL_OWNER             # Default: ldnm99
ETL_REPO              # Default: FPL-ETL
```

---

## 🔗 Useful Links

| Resource | URL |
|----------|-----|
| GitHub Repo | https://github.com/ldnm99/fpl_draft_frontend |
| Streamlit Docs | https://docs.streamlit.io |
| Supabase Docs | https://supabase.com/docs |
| FPL API | https://fantasy.premierleague.com/api |
| Plotly Reference | https://plotly.com/python |
| Pandas Docs | https://pandas.pydata.org/docs |

---

## 📞 Getting Help

1. **Check documentation**
   - README.md - Overview
   - SETUP.md - Setup issues
   - API_REFERENCE.md - Function usage

2. **Search issues**
   - GitHub Issues: https://github.com/ldnm99/fpl_draft_frontend/issues

3. **Ask community**
   - Open new issue with details
   - Include error messages and steps to reproduce

4. **Debug locally**
   ```bash
   streamlit run menu.py --logger.level=debug
   ```

---

## 🎓 Learning Resources

### Python
- [Real Python](https://realpython.com/) - Python tutorials
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/) - Code style

### Streamlit
- [Streamlit Cheat Sheet](https://docs.streamlit.io/library/cheatsheet)
- [Streamlit Components Gallery](https://streamlit.io/gallery)

### Data Science
- [Pandas Tutorial](https://pandas.pydata.org/docs/user_guide/index.html)
- [Plotly Tutorial](https://plotly.com/python/plotly-fundamentals/)

### Git & GitHub
- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)

---

## 📋 Checklists

### Pre-Commit Checklist
- [ ] Code formatted with Black
- [ ] Imports sorted with isort
- [ ] No unused imports/variables
- [ ] Docstrings added
- [ ] Tests pass locally
- [ ] No hardcoded secrets
- [ ] Descriptive commit message

### Before Creating PR
- [ ] Feature works locally
- [ ] No breaking changes
- [ ] Documentation updated
- [ ] All tests pass
- [ ] Code reviewed (self-review)
- [ ] Commit history is clean

### Before Deploying
- [ ] PR approved
- [ ] All checks pass
- [ ] Tested on staging
- [ ] Secrets configured
- [ ] Rollback plan ready

---

## ⚡ Pro Tips

1. **Use cached data wisely**
   ```python
   @st.cache_data
   def expensive_operation():
       # Only runs once per session
       return result
   ```

2. **Avoid recomputation**
   ```python
   # Good: Cache at data loading
   @st.cache_data
   def load_data():
       return load_data_supabase(supabase)
   
   # Bad: Reload on every interaction
   df = load_data_supabase(supabase)  # SLOW!
   ```

3. **Use containers for UI organization**
   ```python
   with st.container():
       st.write("Related content")
       st.dataframe(df)
   ```

4. **Profile before optimizing**
   ```bash
   streamlit profile -p menu.py
   ```

5. **Debug with print statements**
   ```python
   print(f"DEBUG: {variable}")  # Shows in terminal
   st.write(f"DEBUG: {variable}")  # Shows on page
   ```

---

**Last Updated:** January 2026  
**Version:** 1.0.0

See [README.md](README.md) for full documentation or [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.
