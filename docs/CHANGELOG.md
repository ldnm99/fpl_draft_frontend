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
