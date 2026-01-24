# 🤝 Contributing Guide

Thank you for interest in contributing to the FPL Draft Dashboard! This guide will help you get started.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch**: `git checkout -b feature/your-feature-name`
4. **Make your changes**
5. **Commit with clear messages**: `git commit -m "feat: Add new feature"`
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request** with detailed description

## Development Workflow

### 1. Set Up Development Environment

```bash
# Clone and navigate
git clone https://github.com/YOUR-USERNAME/fpl_draft_frontend.git
cd fpl_draft_frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies + dev dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # (once created)
```

### 2. Creating a New Feature

**Feature Development Checklist:**

- [ ] Create feature branch from `main`
- [ ] Implement feature
- [ ] Add docstrings and comments
- [ ] Test locally
- [ ] Update relevant documentation
- [ ] Commit with descriptive message
- [ ] Push and create PR

### 3. Code Style & Standards

#### Python Style Guide

Follow **PEP 8** with these preferences:

**Line Length**: Max 88 characters (Black formatter standard)

```python
# Good: Readable, well-formatted
def get_manager_data(df: pd.DataFrame, manager_name: str) -> pd.DataFrame:
    """Filter data for specific manager."""
    return df[df["manager_team_name"] == manager_name]

# Bad: Too long or unclear
def get_manager_data(df,manager_name):
    return df[df["manager_team_name"]==manager_name]
```

**Imports**: Group and sort

```python
# Good: stdlib → third-party → local
import os
from datetime import datetime

import pandas as pd
import streamlit as st

from data_utils import get_manager_data
```

**Functions**: Clear names and docstrings

```python
# Good: Google-style docstring
def calculate_team_gw_points(starting_players: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate total points per team per gameweek.
    
    Args:
        starting_players: DataFrame with starting XI only
        
    Returns:
        Pivot table with teams × gameweeks
        
    Example:
        >>> team_points = calculate_team_gw_points(df)
        >>> team_points.loc["Blue Lock XI", 1]
        65.0
    """
    ...
```

#### Streamlit Best Practices

```python
# Good: Cached expensive operations
@st.cache_data
def load_data_supabase(supabase):
    """Load data once per session."""
    ...

# Good: Use session_state for page state
if st.button("Navigate"):
    st.session_state["page"] = "new_page"
    st.switch_page("pages/new_page.py")

# Bad: Avoid loading data on every rerun
def load_data():
    """This runs on EVERY interaction!"""
    data = supabase.storage.from_("data").download(...)
```

### 4. Commit Messages

Follow **Conventional Commits**:

```
feat: Add player search functionality
fix: Resolve dashboard caching issue
docs: Update API reference
refactor: Extract duplicate code to utils
test: Add tests for data_utils
chore: Update dependencies
```

**Good Commit Messages:**
```
✅ feat: Add player search with position filter
✅ fix: Handle empty DataFrame in get_top_performers
✅ docs: Add CONTRIBUTING.md guide

❌ update stuff
❌ fix bug
❌ changes
```

### 5. Testing

#### Writing Tests (Once Test Suite Exists)

Create test files in `tests/` directory:

```python
# tests/test_data_utils.py
import pytest
import pandas as pd
from data_utils import get_manager_data, get_starting_lineup

def test_get_manager_data():
    """Test filtering data by manager."""
    df = pd.DataFrame({
        "manager_team_name": ["Blue Lock XI", "Magic FC", "Blue Lock XI"],
        "full_name": ["Player A", "Player B", "Player C"]
    })
    
    result = get_manager_data(df, "Blue Lock XI")
    
    assert len(result) == 2
    assert all(result["manager_team_name"] == "Blue Lock XI")

def test_get_starting_lineup():
    """Test filtering to starting XI only."""
    df = pd.DataFrame({
        "team_position": [1, 5, 11, 12, 15]  # 1-11 are XI, 12-15 are bench
    })
    
    result = get_starting_lineup(df)
    
    assert len(result) == 3
    assert max(result["team_position"]) == 11
```

**Run Tests:**
```bash
pytest
pytest tests/test_data_utils.py -v
pytest --cov=.  # Coverage report
```

### 6. Documentation

#### Update Documentation When:
- Adding new functions
- Changing existing behavior
- Adding new pages or features
- Fixing documented bugs

#### Files to Update:
- `README.md` - User-facing overview
- `ARCHITECTURE.md` - Technical design
- `SETUP.md` - Setup/deployment changes
- `API_REFERENCE.md` - Function documentation
- Code docstrings - Implementation details

**Documentation Template:**
```python
def new_function(param1: str, param2: int) -> pd.DataFrame:
    """
    Brief one-line description.
    
    Longer description explaining what it does, when to use it,
    and any important considerations.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: If input is invalid
        
    Example:
        >>> result = new_function("example", 42)
        >>> print(result)
        ...
    """
    pass
```

## PR Review Checklist

Before submitting a PR, verify:

### Code Quality
- [ ] Code follows PEP 8 style guide
- [ ] Functions have docstrings
- [ ] Complex logic has comments
- [ ] No hardcoded values (use config)
- [ ] Imports are organized and sorted
- [ ] No unused imports or variables

### Functionality
- [ ] Feature works as intended
- [ ] Tested locally
- [ ] No errors or warnings
- [ ] Edge cases handled
- [ ] Empty data handled gracefully

### Documentation
- [ ] README updated (if needed)
- [ ] Docstrings added/updated
- [ ] Comments added for complex logic
- [ ] API_REFERENCE.md updated (if adding functions)

### Git & Commits
- [ ] Branch name describes feature
- [ ] Commits are logical and atomic
- [ ] Commit messages are descriptive
- [ ] No merge conflicts
- [ ] No sensitive data committed (.env, secrets)

## Feature Ideas & Issues

### Found a Bug?

1. **Check existing issues** first
2. **Create issue** with:
   - Clear title
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Error logs/screenshots

**Good Bug Report:**
```
Title: Manager pages fail to load with special characters

Steps to Reproduce:
1. Create manager with name "John's Team"
2. Click on manager button
3. Page fails to load

Expected: Manager page displays
Actual: StreamlitException: Page script can't be found

Error: FileNotFoundError: pages/John's Team.py
```

### Have a Feature Idea?

1. **Open a discussion** or issue
2. **Describe the use case**
3. **Explain expected behavior**
4. **Discuss implementation approach**

**Good Feature Request:**
```
Title: Add export to CSV functionality

Use Case: Users want to download their team's stats for analysis

Proposed Solution:
- Add "Export" button on manager pages
- Export all visible data to CSV
- Include timestamp in filename

Questions: Should we also support PDF export?
```

## Development Resources

### Project Structure
```
FPL_frontend/
├── data_utils.py           # Data loading & processing
├── visuals_utils.py        # Visualizations & charts
├── supabase_client.py      # Database client
├── menu.py                 # Main entry point
├── pages/                  # Page scripts
├── Data/                   # Local data files
├── tests/                  # Test suite (planned)
└── docs/                   # Documentation
    ├── README.md
    ├── ARCHITECTURE.md
    ├── SETUP.md
    └── API_REFERENCE.md
```

### Useful Commands

```bash
# Run app locally
streamlit run menu.py

# Debug mode
streamlit run menu.py --logger.level=debug

# Run tests
pytest

# Check code style
black --check .
flake8 .
mypy .

# Format code
black .
isort .
```

### Dependencies

Check `requirements.txt` for versions. Common libraries:

- **streamlit** - Web UI framework
- **pandas** - Data processing
- **plotly** - Visualizations
- **supabase** - Database client
- **python-dotenv** - Environment variables
- **requests** - HTTP requests
- **pyarrow** - Parquet files

### Helpful Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pandas API Reference](https://pandas.pydata.org/docs/)
- [Plotly Python](https://plotly.com/python/)
- [PEP 8 Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [Git Workflow](https://git-scm.com/book/en/v2)

## Code Review Process

When a PR is submitted:

1. **Automated checks** run (once CI/CD is set up)
   - Code style/lint
   - Type checking
   - Tests

2. **Maintainers review** code
   - Functionality
   - Code quality
   - Documentation
   - Architecture fit

3. **Feedback provided**
   - Requested changes
   - Suggestions for improvement
   - Questions for clarification

4. **Author updates** PR
   - Address feedback
   - Push updates
   - PR auto-updates

5. **Approval & Merge**
   - Maintainer approves
   - PR merged to main
   - Feature deployed!

## Development Tips

### Debugging Streamlit Apps

```python
# Use print statements (shown in terminal)
print(f"DataFrame shape: {df.shape}")
print(df.head())

# Use st.write for on-screen debugging
st.write(f"Debug: {value}")
st.dataframe(df)

# Use st.stop() to halt execution
if error_condition:
    st.error("Error!")
    st.stop()
```

### Working with Supabase

```python
# List storage files
files = supabase.storage.from_("data").list()

# Download file
data = supabase.storage.from_("data").download("gw_data.parquet")

# Upload file
with open("file.csv", "rb") as f:
    supabase.storage.from_("data").upload("file.csv", f)
```

### Performance Optimization

```python
# Cache expensive operations
@st.cache_data
def expensive_calculation(df):
    return df.groupby(...).sum()

# Use query optimization
filtered = df[df["manager"] == selected][["name", "points"]]
# Better than: filtered = df.loc[:, ["name", "points", "all_columns"]]

# Lazy load data
if selected_manager:
    manager_data = get_manager_data(df, selected_manager)
# Don't load all manager data upfront
```

## Community Guidelines

### Be Respectful
- Use inclusive language
- Assume good intent
- Give constructive feedback
- Welcome diverse perspectives

### Ask Questions
- No question is too basic
- Use discussions for questions
- Help others who ask questions
- Share knowledge

### Stay Positive
- Celebrate contributions
- Help with feedback
- Learn from mistakes
- Improve together

---

**Thank you for contributing! We appreciate your help in making FPL Dashboard better. 🙌**

Last Updated: January 2026
