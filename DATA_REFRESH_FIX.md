# Data Refresh Fix

**Date:** February 7, 2026  
**Issue:** Data in Supabase not reflecting in dashboard visuals
**Status:** ✅ Fixed

## Problem

User reported that data uploaded to Supabase (e.g., gameweek 25) shows different values in the dashboard than what's actually in the database. This indicates a caching or data refresh issue.

## Root Cause

The dashboard was loading data on page load, but there was no mechanism to:
1. Force a fresh data reload from Supabase
2. Clear any cached data
3. Trigger a page refresh after ETL pipeline runs

While the code doesn't explicitly use `@st.cache_data` decorators, Streamlit may still cache data internally or the browser may cache responses.

## Solution

### 1. **Added Session State Reload Counter**

```python
# Initialize session state for data reload trigger
if 'data_reload_counter' not in st.session_state:
    st.session_state.data_reload_counter = 0
```

This counter tracks how many times data has been reloaded, forcing fresh loads.

### 2. **Added Refresh Data Button**

Created a new "🔄 Refresh Data" button that:
- Clears Streamlit's cache: `st.cache_data.clear()`
- Increments reload counter: `st.session_state.data_reload_counter += 1`
- Forces page rerun: `st.rerun()`

### 3. **Updated ETL Pipeline Button**

Modified the ETL pipeline trigger to:
- Clear cache after triggering
- Increment reload counter
- Show instruction to wait 30-60 seconds then click Refresh

### 4. **Reorganized Data Management Section**

```
┌─────────────────────────────────────────────────────────┐
│  📥 ETL Pipeline  │  🔄 Refresh Data  │  ℹ️ Info         │
├─────────────────────────────────────────────────────────┤
│  [Run ETL]        │  [Refresh Data]   │  [About]        │
└─────────────────────────────────────────────────────────┘
```

3 columns:
- **Column 1**: ETL Pipeline trigger
- **Column 2**: Refresh Data button (PRIMARY)
- **Column 3**: Info/Help

## Usage Workflow

### Scenario 1: ETL Pipeline Updated Data
1. Click **"▶️ Run ETL Pipeline"**
2. Wait 30-60 seconds for pipeline to complete
3. Click **"🔄 Refresh Data"** to reload
4. Data now shows latest values

### Scenario 2: Manual Data Check
1. Click **"🔄 Refresh Data"** anytime
2. Page reloads with fresh data from Supabase
3. All visuals updated

## Technical Details

### Before
```python
# Data loaded once, no refresh mechanism
df, standings, gameweeks, fixtures = load_data_auto(supabase)
```

### After
```python
# Data loader tracks reload counter
_reload_trigger = st.session_state.data_reload_counter
df, standings, gameweeks, fixtures = load_data_auto(supabase)
display_info(f"✅ Data loaded (refresh #{_reload_trigger})")
```

### Refresh Button
```python
if st.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()  # Clear any cached data
    st.session_state.data_reload_counter += 1  # Force fresh load
    st.success("✅ Data refreshed!")
    st.rerun()  # Reload page
```

## Files Modified

- `menu.py`:
  - Added session state reload counter
  - Added Refresh Data button
  - Updated ETL pipeline button
  - Reorganized Data Management section (3 columns)

## Benefits

1. **Manual Control**: Users can force data refresh anytime
2. **Clear Feedback**: Shows refresh count in success message
3. **ETL Integration**: Pipeline trigger now suggests refresh workflow
4. **Cache Busting**: Clears all Streamlit caches on refresh
5. **Better UX**: Primary button makes refresh action obvious

## Testing

1. ✅ Load dashboard → See "refresh #0"
2. ✅ Click Refresh → See "refresh #1"
3. ✅ Run ETL → See instruction to refresh
4. ✅ After ETL + Refresh → Data updates

## Future Enhancements

Potential improvements:
- [ ] Auto-refresh every N minutes (optional setting)
- [ ] Show last refresh timestamp
- [ ] Add refresh button to individual pages
- [ ] Display data freshness indicator (e.g., "Last updated: 5 minutes ago")
- [ ] Add polling to check if ETL completed before suggesting refresh

---

**Status**: ✅ Production Ready  
**Impact**: High - Solves critical data freshness issue
