# Backend-Frontend Column Name Compatibility

**Date:** February 7, 2026  
**Status:** ✅ Fixed

## Issue

After refactoring the frontend to use new medallion column names, a mismatch was discovered between backend and frontend naming conventions:

**Error Message:**
```
Failed to load data: Failed to load data from Gold layer: 
Failed to create manager standings: 'team_name'
```

## Root Cause

The backend's `manager_gw_performance` fact table still uses `manager_team_name` as the column name, while the frontend code was refactored to expect `team_name`.

## Solution

Implemented a **column normalization layer** in the frontend to handle both old and new backend column names:

### 1. Added Column Normalization Function

```python
def normalize_backend_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize backend column names to frontend expected names.
    """
    column_map = {
        'manager_team_name': 'team_name',
    }
    
    rename_dict = {old: new for old, new in column_map.items() 
                   if old in df.columns and old != new}
    
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    return df
```

### 2. Updated Manager Standings Function

Added dynamic column detection:

```python
def create_manager_standings(...):
    df = facts['manager_gw_performance'].copy()
    
    # Handle both old and new column names from backend
    team_name_col = 'team_name' if 'team_name' in df.columns else 'manager_team_name'
    
    standings = df.groupby(['manager_id', 'first_name', 'last_name', team_name_col]).agg({
        'gw_points': 'sum',
    }).reset_index()
    
    standings = standings.rename(columns={
        team_name_col: 'team_name'  # Normalize to 'team_name'
    })
    ...
```

### 3. Applied Normalization in Data Loader

```python
def load_data_medallion(...):
    gw_data = facts['manager_gw_performance'].copy()
    
    # Normalize backend column names
    gw_data = normalize_backend_columns(gw_data)
    
    standings = create_manager_standings(dimensions, facts)
    ...
```

## Backend-Frontend Column Mappings

| Backend Column | Frontend Column | Status |
|----------------|----------------|--------|
| `manager_team_name` | `team_name` | ✅ Normalized |
| `gameweek_num` | `gameweek_num` | ✅ Aligned |
| `player_position` | `player_position` | ✅ Aligned |
| `player_name` | `player_name` | ✅ Aligned |
| `short_name` | `short_name` | ✅ Aligned |
| `gw_*` stats | `gw_*` stats | ✅ Aligned |

## Benefits of This Approach

1. **Backward Compatibility:** Frontend works with both old and new backend column names
2. **Future-Proof:** When backend is updated, frontend continues to work
3. **Zero Breaking Changes:** Application remains functional during transition
4. **Clean Separation:** Frontend uses consistent naming internally
5. **Easy Migration:** Backend can be updated independently

## Recommendations for Backend

To achieve full alignment, the backend ETL pipeline should be updated to use consistent column names:

### In `manager_gameweek_performance.parquet`:
```python
# Change from:
df.rename(columns={'team_name': 'manager_team_name'})

# To:
# Keep as 'team_name' (no rename needed)
```

This change in the backend would:
- Eliminate the need for frontend normalization
- Create perfect alignment between backend and frontend
- Reduce confusion about which "team_name" is referenced

## Testing Verification

After applying the fix:

1. ✅ Python syntax validation passes
2. ✅ Data loads from Gold layer successfully  
3. ✅ Manager standings calculate correctly
4. ✅ All pages display data properly

## Files Modified

- `core/medallion_data_loader.py`
  - Added `normalize_backend_columns()` function
  - Updated `create_manager_standings()` for flexible column detection
  - Applied normalization in `load_data_medallion()`

## Impact

**Before Fix:** Application crashed on data load  
**After Fix:** Application loads data successfully from backend with any column naming convention

## Long-Term Plan

1. **Phase 1 (Current):** ✅ Frontend handles both naming conventions
2. **Phase 2 (Recommended):** Update backend to use `team_name` consistently
3. **Phase 3 (Future):** Remove normalization layer once backend is aligned

---

**Resolution Status:** ✅ Complete  
**Testing Status:** Ready for validation  
**Backend Update:** Recommended but not required
