# Project Structure Guide

## Overview

The FPL Dashboard project is organized into logical folders for maintainability and scalability.

```
FPL_frontend/
├── README.md                 # Project overview (start here!)
├── menu.py                   # Main entry point (Streamlit app)
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
│
├── config/                  # Configuration modules
│   ├── __init__.py
│   └── supabase_client.py  # Supabase client initialization
│
├── core/                    # Core application logic
│   ├── __init__.py
│   ├── medallion_data_loader.py  # Gold layer data loader (NEW v2.0)
│   ├── data_utils.py       # Data loading & processing
│   ├── visuals_utils.py    # Visualizations & charts
│   ├── pitch_visualization.py  # FPL-style pitch display
│   ├── injury_utils.py     # Injury tracking
│   └── error_handler.py    # Error handling & logging
│
├── pages/                   # Streamlit page scripts
│   ├── Overall.py          # League overview dashboard
│   ├── Current Gameweek.py # Current gameweek details
│   ├── Fixtures.py         # Upcoming fixtures
│   ├── Players Data.py     # Player analysis
│   └── [Manager].py        # Individual manager dashboards
│
├── utils/                   # Utility modules
│   └── __init__.py
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── test_data_utils.py
│   └── test_error_handler.py
│
├── Data/                    # Local data files
│   ├── gameweeks.csv       # Gameweek schedule
│   └── fixtures.csv        # Match fixtures
│
├── docs/                    # Documentation
│   ├── README.md           # Detailed project documentation
│   ├── SETUP.md            # Setup & deployment guide
│   ├── ARCHITECTURE.md     # Technical design
│   ├── MEDALLION_MIGRATION.md  # Medallion architecture guide
│   ├── MEDALLION_QUICK_REF.md  # Quick reference
│   ├── API_REFERENCE.md    # Function documentation
│   ├── CONTRIBUTING.md     # Contribution guidelines
│   ├── ERROR_HANDLING.md   # Error handling guide
│   ├── CHANGELOG.md        # Version history
│   ├── QUICKREF.md         # Quick reference
│   └── DOCS_INDEX.md       # Documentation index
│
├── assets/                  # Static files
│   └── [images, logos, etc.]
│
└── .devcontainer/          # Dev container config
    └── devcontainer.json
```

---

## Folder Descriptions

### **config/** - Configuration Modules
Central place for all configuration and client initialization.

**Files:**
- `supabase_client.py` - Supabase client setup

**Usage:**
```python
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY
```

---

### **core/** - Core Application Logic
Main business logic and utilities.

**Files:**
- `data_utils.py` - Data loading, filtering, aggregation functions
- `visuals_utils.py` - Chart and visualization functions
- `error_handler.py` - Error handling, logging, validation

**Usage:**
```python
from core.data_utils import load_data_supabase, get_manager_data
from core.visuals_utils import display_overview
from core.error_handler import validate_dataframe, display_error
```

---

### **pages/** - Streamlit Page Scripts
Individual page implementations for Streamlit multi-page app.

**Files:**
- `Overall.py` - League-wide statistics
- `Current Gameweek.py` - Current GW details
- `Fixtures.py` - Upcoming fixtures
- `Players Data.py` - Player statistics
- Individual manager pages (dynamically created)

**Note:** Streamlit requires pages/ folder at project root.

---

### **utils/** - Utility Modules (Future)
Helper functions and utilities for various tasks.

**Planned:**
- `formatting.py` - Data formatting utilities
- `calculations.py` - Complex calculations
- `constants.py` - Project constants

---

### **tests/** - Test Suite (Future)
Unit and integration tests for the project.

**Structure:**
```
tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
└── fixtures/      # Test data
```

---

### **Data/** - Local Data Files
CSV files for gameweeks and fixtures (loaded locally, not from Supabase).

**Files:**
- `gameweeks.csv` - Gameweek definitions and deadlines
- `fixtures.csv` - Match fixtures with difficulty ratings

---

### **docs/** - Documentation
Complete project documentation.

**Files:**
- `README.md` - Project overview & quick start
- `SETUP.md` - Detailed setup & deployment
- `ARCHITECTURE.md` - Technical architecture
- `API_REFERENCE.md` - Function documentation
- `CONTRIBUTING.md` - Contribution guidelines
- `ERROR_HANDLING.md` - Error handling guide
- `CHANGELOG.md` - Version history
- `QUICKREF.md` - Quick reference
- `DOCS_INDEX.md` - Documentation index

**Access:** All documentation is version-controlled and included in repo.

---

### **assets/** - Static Files
Images, logos, and other static resources.

---

### **.devcontainer/** - Development Container
Docker configuration for consistent development environment.

---

## Environment Setup

### .env File Structure

```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_public_key

# GitHub Configuration
TOKEN_STREAMLIT=your_github_personal_access_token

# Data Files
GW_DATA_FILE=gw_data.parquet
STANDINGS_FILE=league_standings.csv
LOCAL_GAMEWEEKS=Data/gameweeks.csv
LOCAL_FIXTURES=Data/fixtures.csv

# Storage
STORAGE_BUCKET=data

# ETL Settings
ETL_OWNER=ldnm99
ETL_REPO=FPL-ETL
ETL_EVENT_TYPE=run_pipeline

# Application
DEBUG=false
LOG_LEVEL=info
CACHE_TTL=3600
```

### .env File Location

The `.env` file should be in the **project root**:
```
C:\Users\lourencomarvao\FPL_frontend\.env
```

### Git Protection

The `.env` file is **automatically ignored** by Git (added to `.gitignore`).

---

## Import Patterns

### From config/
```python
from config.supabase_client import SUPABASE_URL, SUPABASE_KEY
```

### From core/
```python
from core.data_utils import load_data_supabase, get_manager_data
from core.visuals_utils import display_overview
from core.error_handler import display_error, validate_dataframe
```

### From pages/
Streamlit automatically loads pages from `pages/` folder.

---

## File Organization Rules

### ✅ DO:
- Put business logic in `core/`
- Put configuration in `config/`
- Put Streamlit pages in `pages/`
- Put documentation in `docs/`
- Keep `.env` in project root
- Keep `menu.py` as entry point

### ❌ DON'T:
- Put large files in root directory
- Mix utilities with pages
- Duplicate utility functions
- Add secrets to version control
- Import from pages outside pages/

---

## Adding New Files

### New Utility Function
1. Add to appropriate file in `core/`
2. Update `core/__init__.py` if needed
3. Import from `core/module_name`

### New Page
1. Create `pages/PageName.py`
2. Update imports to use `core.`, `config.`
3. Streamlit auto-loads it

### New Configuration
1. Add to `config/`
2. Export from `config/__init__.py`
3. Import from `config.module`

### New Utility Module
1. Add to `utils/`
2. Update `utils/__init__.py`
3. Import from `utils.module`

---

## Module Dependencies

```
pages/ 
  ↓
menu.py
  ↓
├── core/
│   ├── data_utils.py
│   ├── visuals_utils.py
│   └── error_handler.py
│
└── config/
    └── supabase_client.py
```

**Direction:** Outer → Inner (pages depend on core)

---

## Running the App

From project root:
```bash
# Run the app
streamlit run menu.py

# Debug mode
streamlit run menu.py --logger.level=debug

# Development with file watching
streamlit run menu.py --reload
```

---

## Project Growth Plan

### Current Structure
- ✅ Organized into logical folders
- ✅ Central configuration
- ✅ Modular core logic
- ✅ Separate pages
- ✅ Documentation in docs/
- ✅ Environment variables in .env

### Future Enhancements
- [ ] Add `utils/` helper modules
- [ ] Create comprehensive test suite in `tests/`
- [ ] Add `pyproject.toml` for modern Python packaging
- [ ] Create `scripts/` for maintenance scripts
- [ ] Add `notebooks/` for data exploration (Jupyter)
- [ ] Create `migrations/` for database schema changes

---

## Troubleshooting

### Import Errors
**Problem:** `ModuleNotFoundError: No module named 'core'`

**Solution:** 
- Ensure running from project root: `cd FPL_frontend`
- Check `core/__init__.py` exists
- Verify import path: `from core.data_utils import ...`

### .env Not Loading
**Problem:** Environment variables not available

**Solution:**
- Install `python-dotenv`: `pip install python-dotenv`
- Ensure `.env` is in project root
- Check Streamlit secrets: `st.secrets.get("KEY")`

### Page Import Errors
**Problem:** Pages can't import from core

**Solution:**
- Update page imports to use `from core.` prefix
- Check file locations match imports
- Restart Streamlit app

---

## Summary

The project is now organized into:
- **config/** - Configuration & clients
- **core/** - Business logic & utilities
- **pages/** - Streamlit pages
- **utils/** - Future utility modules
- **tests/** - Future test suite
- **Data/** - Local CSV files
- **docs/** - All documentation
- **.env** - Environment variables (local)
- **.gitignore** - Protects secrets

This structure provides:
✅ Clear separation of concerns  
✅ Easy to navigate  
✅ Scalable for growth  
✅ Follows Python best practices  
✅ Ready for team collaboration  

---

## What's New in v2.0.0 (Feb 2026)

✅ **Medallion Architecture** - Gold layer integration with star schema  
✅ **Enhanced Visualizations** - FPL-style pitch display  
✅ **Column Refactoring** - 180+ updates for consistency  
✅ **Data Refresh System** - Manual refresh and cache clearing  
✅ **Better Documentation** - Root README.md and updated guides  

See [CHANGELOG.md](docs/CHANGELOG.md) for full details.

---

**Last Updated:** February 7, 2026  
**Version:** 2.0.0
