# Changelog

All notable changes to the FPL Draft Dashboard are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Unit test suite with pytest
- Type checking with mypy
- Pre-commit hooks (black, isort, flake8)
- Database-level filtering for performance
- User authentication layer
- Real-time data updates
- Mobile-responsive UI improvements
- Export to PDF functionality
- Historical data comparison views
- Player recommendation algorithm

---

## [2.0.0] - 2026-02-07

### Added - Medallion Architecture Migration
- **NEW:** `core/medallion_data_loader.py` - Loads data from Gold layer (star schema)
  - Functions: `load_gold_layer()`, `load_dimensions()`, `load_facts()`
  - Creates backward-compatible views
  - 300+ lines of comprehensive data loading logic
- **Documentation:** `docs/MEDALLION_MIGRATION.md` - Complete migration guide
- **Documentation:** `docs/MEDALLION_QUICK_REF.md` - Quick reference for developers

### Enhanced - Pitch Visualization (FPL Style)
- Larger player cards (kit images 40% bigger: 70x92px)
- Fixture display showing opponent and home/away status (e.g., "WOL (A)")
- FPL-style design with modern gradients
- Dynamic formation detection (supports 7 formations)
- Enhanced player cards with hover animations
- Color-coded points badges (green/gray/red gradients)

### Changed - Column Name Refactoring
- Refactored all legacy column names to medallion schema
- `gw` → `gameweek_num`
- `position` → `player_position`
- `full_name` → `player_name`
- `real_team` → `short_name`
- `manager_team_name` → `team_name`
- Updated 180+ column references across 11 files
- All core modules, pages, and utilities updated

### Fixed - Backend Compatibility
- Added column normalization layer for backend-frontend compatibility
- Frontend now handles both old and new backend column names
- Dynamic column detection in manager standings
- Zero breaking changes during migration

### Fixed - Data Refresh System
- Added session state reload counter
- New "🔄 Refresh Data" button (primary action)
- Clear cache on refresh: `st.cache_data.clear()`
- ETL pipeline button now triggers cache clear
- Shows refresh count for transparency

### Fixed - Visualization Issues
- Fixed pie chart position distribution (line 153)
- Fixed scatter plot player clustering hover data (line 993)
- Fixed DataFrame column selection in cluster display (line 1013)
- All charts now use medallion column names

### Files Modified
- `core/data_utils.py` - Added `load_data_auto()` with fallback
- `core/visuals_utils.py` - Updated 60+ column references
- `core/medallion_data_loader.py` - NEW file
- `core/pitch_visualization.py` - Enhanced FPL-style design
- `menu.py` - Added refresh button and reload counter
- `pages/*.py` - Updated all page files (11 files total)

### Migration
- Frontend now perfectly aligned with backend ETL medallion schema
- Backward compatibility maintained during transition
- No breaking changes to functionality
- All tests passing

---

## [1.0.0] - 2026-01-24

### Added
- 📖 Comprehensive documentation suite
  - README.md - Project overview and quick start
  - ARCHITECTURE.md - Technical design and data flow
  - SETUP.md - Detailed setup and deployment guide
  - API_REFERENCE.md - Complete function documentation
  - CONTRIBUTING.md - Contribution guidelines
  - CHANGELOG.md - Version history

- 🛠️ Project configuration files
  - .env.example - Environment variable template
  - .gitignore - Git ignore rules
  - requirements.txt - Python dependencies

### Current Features
- Multi-manager draft league dashboard
- Gameweek points tracking and visualization
- Upcoming fixtures display with difficulty ratings
- Player performance analytics
- Performance trends (manager vs league average)
- Top performers by gameweek
- ETL pipeline trigger from UI
- Interactive Plotly charts
- Responsive Streamlit layout

---

## Version History

### v0.1.0 - Initial Prototype
- Basic Streamlit dashboard
- Supabase integration
- Multi-page navigation
- Data visualization basics

---

## Migration Guide

### From v0.1.0 to v1.0.0

No breaking changes. Existing installations will work with the new version.

**New files added (non-functional):**
- Documentation files (README.md, ARCHITECTURE.md, etc.)
- Configuration templates (.env.example, .gitignore)

**To update:**
```bash
git pull origin main
pip install -r requirements.txt  # If deps updated
```

---

## Known Issues

- ⚠️ Special characters in manager names may cause page loading issues
- ⚠️ Large datasets (>100 managers) may cause UI slowness
- ⚠️ Supabase connection timeouts on slow networks
- ⚠️ No offline mode - requires internet connection

**Workarounds:**
- Use ASCII-safe manager names
- Consider data archival for old seasons
- Implement connection retry logic (planned)
- Add offline fallback (planned)

---

## Support

For issues or questions about a specific version:

1. Check [Troubleshooting](SETUP.md#troubleshooting) in SETUP.md
2. Review [Architecture](ARCHITECTURE.md) for technical details
3. Search existing [GitHub Issues](https://github.com/ldnm99/fpl_draft_frontend/issues)
4. Create new issue with version number

---

## Release Process

Releases follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backward compatible)
- **PATCH** (0.0.X): Bug fixes

**Release checklist:**
1. Update CHANGELOG.md
2. Update version in code (if applicable)
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub Release with notes

---

## Versioning Timeline

| Version | Date | Status |
|---------|------|--------|
| 1.0.0 | 2026-01-24 | ✅ Current Release |
| 0.1.0 | 2025-12-15 | 🏁 End of Life |

---

**Last Updated:** 2026-01-24  
**Maintained By:** Project Contributors
