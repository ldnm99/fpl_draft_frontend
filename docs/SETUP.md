# 🛠️ Setup & Deployment Guide

## Table of Contents
1. [Local Development Setup](#local-development-setup)
2. [Streamlit Cloud Deployment](#streamlit-cloud-deployment)
3. [Configuration Guide](#configuration-guide)
4. [Troubleshooting](#troubleshooting)

---

## Local Development Setup

### Step 1: Prerequisites

Ensure you have:
- **Python 3.8 or higher** (check with `python --version`)
- **Git** installed
- **pip** or **conda** for package management
- A **Supabase account** (free tier available)
- A **GitHub account** for ETL integration

### Step 2: Clone Repository

```bash
git clone https://github.com/ldnm99/fpl_draft_frontend.git
cd fpl_draft_frontend
```

### Step 3: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` - Web framework
- `pandas` - Data processing
- `plotly` - Visualizations
- `supabase` - Database client
- `requests` - HTTP library
- `python-dotenv` - Environment variables
- `pyarrow` - Parquet support

### Step 5: Set Up Supabase

1. **Create Supabase Project**
   - Go to [supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose organization and configure project
   - Wait for setup to complete

2. **Create Storage Bucket**
   - Go to Storage tab
   - Click "Create new bucket"
   - Name: `data` (or your preference)
   - **Important**: Uncheck "Make it private" (set to public)

3. **Get API Credentials**
   - Go to Settings → API
   - Copy `Project URL` (SUPABASE_URL)
   - Copy `anon public` key (SUPABASE_KEY)

4. **Upload Data Files to Supabase**
   - In Storage bucket, create folder `data`
   - Upload `gw_data.parquet` (from backend ETL)
   - Upload `league_standings.csv` (from backend ETL)

### Step 6: Set Up GitHub Token

1. **Create Personal Access Token**
   - Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scope: `repo` (for repository access)
   - Copy the token immediately (you won't see it again)

2. **Create FPL-ETL Repository Dispatch**
   - The backend repo must accept `repository_dispatch` events
   - Set event type: `run_pipeline`
   - Ensure workflow exists in `.github/workflows/`

### Step 7: Configure Local Secrets

**Create Streamlit secrets file:**

```bash
# On macOS/Linux:
mkdir -p ~/.streamlit
cat > ~/.streamlit/secrets.toml << 'EOF'
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_anon_public_key"
TOKEN_STREAMLIT = "your_github_token"
EOF

# On Windows (PowerShell):
mkdir -Path $env:APPDATA\.streamlit -Force
$content = @"
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_anon_public_key"
TOKEN_STREAMLIT = "your_github_token"
"@
$content | Out-File -Encoding utf8 $env:APPDATA\.streamlit\secrets.toml
```

**Replace with your actual values:**
- `your-project.supabase.co` → Your Supabase URL
- `your_anon_public_key` → Your Supabase API key
- `your_github_token` → Your GitHub personal access token

### Step 8: Prepare Local Data Files

The app requires two CSV files in the `Data/` directory:

**Data/gameweeks.csv:**
```
id,name,deadline_time,average_entry_points,finished
1,GW 1,2023-08-11 18:00:00+00:00,45.3,false
2,GW 2,2023-08-18 18:00:00+00:00,52.1,false
```

**Data/fixtures.csv:**
```
event,team_h_name,team_a_name,kickoff_time,team_h_difficulty,team_a_difficulty
1,Arsenal,Leicester,2023-08-12 15:00:00+00:00,1,1
1,Man City,Nottingham,2023-08-12 15:00:00+00:00,1,1
```

*Note: These files should be updated from the FPL API by your backend ETL pipeline*

### Step 9: Run the Application

```bash
streamlit run menu.py
```

The app will open automatically at `http://localhost:8501`

**You should see:**
- ⚽ Fantasy Premier League Draft Dashboard
- Navigation buttons for each manager
- League standings and upcoming fixtures
- ETL Pipeline control button

---

## Streamlit Cloud Deployment

### Step 1: Deploy Repository to GitHub

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

### Step 2: Create Streamlit Cloud Account

1. Go to [Streamlit Cloud](https://streamlit.io/cloud)
2. Click "Sign up with GitHub"
3. Authorize Streamlit access to your repositories

### Step 3: Create New App

1. Click "New app" in Streamlit Cloud dashboard
2. Select repository: `username/fpl_draft_frontend`
3. Select branch: `main`
4. Select main file: `menu.py`
5. Click "Deploy"

**Streamlit will build and deploy your app** (takes 2-3 minutes)

### Step 4: Configure Secrets

1. Go to app settings (gear icon)
2. Click "Secrets"
3. Add secrets in TOML format:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your_anon_public_key"
TOKEN_STREAMLIT = "your_github_token"
```

### Step 5: Verify Deployment

1. Wait for "App is running"
2. Click the app URL to open
3. Test functionality:
   - ✅ Data loads correctly
   - ✅ Navigation works
   - ✅ Charts render
   - ✅ ETL button triggers

### Step 6: Set Up Automatic Redeployment (Optional)

Streamlit Cloud automatically redeploys on GitHub push:
- Make changes locally
- Commit and push to `main`
- Streamlit Cloud detects change
- App redeploys automatically

---

## Configuration Guide

### Environment Variables

Create `.env` file in project root for local development:

```bash
# .env file
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_public_key
TOKEN_STREAMLIT=your_github_token

# Optional: Data file paths
GW_DATA_FILE=gw_data.parquet
STANDINGS_FILE=league_standings.csv
LOCAL_GAMEWEEKS=Data/gameweeks.csv
LOCAL_FIXTURES=Data/fixtures.csv

# Optional: ETL settings
ETL_OWNER=ldnm99
ETL_REPO=FPL-ETL
ETL_EVENT_TYPE=run_pipeline
```

*Note: Use `.env` only for local development. For Streamlit Cloud, use "Secrets" in app settings.*

### Streamlit Configuration

Create `.streamlit/config.toml` for Streamlit settings:

```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "minimal"

[logger]
level = "info"

[client]
maxUploadSize = 200
```

---

## Troubleshooting

### Problem: "Secrets not found"

**Error Message:**
```
KeyError: SUPABASE_URL
StreamlitAPIException: No secrets file found
```

**Solution:**
1. Ensure `~/.streamlit/secrets.toml` exists
2. Check all required keys are present
3. Verify file location (varies by OS):
   - **macOS/Linux**: `~/.streamlit/secrets.toml`
   - **Windows**: `%APPDATA%\.streamlit\secrets.toml`

**Verify:**
```bash
# On macOS/Linux:
cat ~/.streamlit/secrets.toml

# On Windows:
type %APPDATA%\.streamlit\secrets.toml
```

---

### Problem: "Connection refused" to Supabase

**Error Message:**
```
ConnectionError: Failed to connect to Supabase
requests.exceptions.ConnectionError: HTTPSConnectionPool
```

**Causes & Solutions:**
1. **Wrong Supabase URL**
   - Check SUPABASE_URL in secrets.toml
   - Should be like: `https://xxxxx.supabase.co`

2. **Firewall blocking connection**
   - Check if you can access Supabase URL in browser
   - Disable VPN if using one
   - Check corporate firewall/proxy settings

3. **Supabase project inactive**
   - Log into Supabase dashboard
   - Verify project is "active"
   - Check project region is correct

**Debug:**
```python
import requests
url = "https://your-project.supabase.co"
response = requests.head(url)
print(response.status_code)  # Should be 200
```

---

### Problem: "FileNotFoundError: Data/gameweeks.csv"

**Error Message:**
```
FileNotFoundError: Local file not found: Data/gameweeks.csv
```

**Causes & Solutions:**
1. **File doesn't exist**
   - Check `Data/` directory exists: `ls Data/` or `dir Data\`
   - Create if missing: `mkdir Data`

2. **Wrong file path**
   - Check current working directory: `pwd` or `cd`
   - Run from project root: `cd fpl_draft_frontend`

3. **File is empty or corrupted**
   - Check file size: `ls -lh Data/gameweeks.csv`
   - Verify CSV format: `head Data/gameweeks.csv`

**Solution:**
```bash
# Create sample files if missing
mkdir -p Data

cat > Data/gameweeks.csv << 'EOF'
id,name,deadline_time,average_entry_points,finished
1,GW 1,2023-08-11 18:00:00+00:00,45.3,false
EOF

cat > Data/fixtures.csv << 'EOF'
event,team_h_name,team_a_name,kickoff_time,team_h_difficulty,team_a_difficulty
1,Arsenal,Leicester,2023-08-12 15:00:00+00:00,1,1
EOF
```

---

### Problem: "No upcoming gameweeks found"

**Display Message:**
```
🏁 No upcoming gameweeks found.
```

**Causes & Solutions:**
1. **FPL season not active**
   - Expected during off-season
   - Gameweeks.csv has no future deadlines

2. **Deadline times in past**
   - Update Data/gameweeks.csv with current season dates
   - Ensure UTC timezone for all times

3. **Time zone mismatch**
   - Verify system time is correct
   - Check UTC offset: `date` or `date /t`

**Solution:**
```bash
# Update gameweeks.csv with current season data
# Get data from: https://fantasy.premierleague.com/api/
# Or from your backend ETL pipeline
```

---

### Problem: "Page not found" when clicking manager button

**Error Message:**
```
StreamlitException: Page script can't be found. Script: pages/Blue Lock XI.py
```

**Causes & Solutions:**
1. **Page file doesn't exist**
   - Check `pages/` directory: `ls pages/`
   - File must match manager name exactly

2. **Filename encoding issue**
   - Avoid special characters in manager names
   - Use ASCII-safe names on Windows

3. **Pages not loading from data**
   - Check standings.csv contains team_name column
   - Verify manager names match between data and files

**Solution:**
```bash
# List existing pages
ls -la pages/

# Manually create page if missing
cat > "pages/Your Manager.py" << 'EOF'
import streamlit as st
from data_utils import get_manager_data, load_data_supabase
from visuals_utils import *
from supabase import create_client
from supabase_client import SUPABASE_URL, SUPABASE_KEY

st.set_page_config(layout="wide")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
df, _, _, _ = load_data_supabase(supabase)

manager_name = "Your Manager"
manager_df = get_manager_data(df, manager_name)

st.title(f"⚽ {manager_name}")
display_overview(manager_name, manager_df)
display_performance_trend(manager_name, df)
display_latest_gw(manager_df)
display_top_performers(manager_df)
EOF
```

---

### Problem: "Invalid GitHub token"

**Error Message:**
```
Error triggering pipeline: 401
Bad credentials
```

**Causes & Solutions:**
1. **Token expired or revoked**
   - Create new token: https://github.com/settings/tokens
   - Update TOML_STREAMLIT in secrets

2. **Wrong token**
   - Verify token in GitHub settings
   - Ensure not truncated in copy-paste

3. **Repository not accessible**
   - Check token has `repo` scope
   - Verify backend repo exists: ldnm99/FPL-ETL

4. **Workflow not configured**
   - Check backend repo has `.github/workflows/` with `repository_dispatch` trigger
   - Verify event type is `run_pipeline`

**Debug:**
```python
import requests

TOKEN = "your_github_token"
headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}"
}
payload = {
    "event_type": "run_pipeline",
    "client_payload": {"triggered_by": "test"}
}

r = requests.post(
    "https://api.github.com/repos/ldnm99/FPL-ETL/dispatches",
    json=payload,
    headers=headers
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
```

---

### Problem: Slow page load times

**Symptom:**
```
Page takes >5 seconds to load
```

**Causes:**
1. **Large Supabase downloads**
   - Check file sizes in Supabase Storage
   - Consider splitting data by season

2. **Network latency**
   - Check internet connection speed
   - Try deploying to Streamlit Cloud (closer servers)

3. **Inefficient data processing**
   - Profile with `streamlit profile report`
   - Check for duplicate DataFrame operations

**Solutions:**
```bash
# Monitor cache effectiveness
streamlit run menu.py --logger.level=debug

# Check file sizes
du -h gw_data.parquet league_standings.csv

# Profile performance
streamlit profile -p menu.py
```

---

### Problem: "Insufficient permissions" on Streamlit Cloud

**Symptoms:**
- App stuck on "Building"
- Deployment fails
- Logs show permission errors

**Solutions:**
1. **Reconnect GitHub**
   - Go to app settings
   - Click "Manage GitHub connection"
   - Re-authorize

2. **Check repository is public**
   - Go to GitHub repo Settings
   - Verify not private

3. **Clear Streamlit cache**
   - Delete `.streamlit/cache` directory
   - Redeploy app

---

## Advanced Configuration

### Custom Styling

Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#FF6B6B"      # Red
backgroundColor = "#1a1a1a"  # Dark
secondaryBackgroundColor = "#2d2d2d"
font = "monospace"
```

### Disable Streamlit Features

```toml
[client]
showErrorDetails = false
toolbarMode = "viewer"  # Hide Streamlit menu
```

### Memory Limits

For Streamlit Cloud or self-hosted:
```bash
# Limit to 512MB
streamlit run menu.py --logger.level=warning --client.maxUploadSize=50
```

---

## Next Steps

1. **Set up the backend ETL pipeline** (FPL-ETL repo)
2. **Configure scheduled data updates** (GitHub Actions cron)
3. **Add more visualizations** (new pages or charts)
4. **Set up monitoring** (error tracking, performance)
5. **Implement authentication** (for private leagues)

---

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Supabase Documentation](https://supabase.com/docs)
- [Plotly Reference](https://plotly.com/python/)
- [FPL API Documentation](https://fantasy.premierleague.com/api/)
- [GitHub Actions Dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch)

---

**Last Updated:** January 2026  
**Tested On:** Python 3.8+, Streamlit 1.28+, macOS/Windows/Linux
