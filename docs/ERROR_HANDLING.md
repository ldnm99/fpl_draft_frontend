# Error Handling Implementation Guide

## Overview

Comprehensive error handling has been added to the FPL Dashboard to ensure reliability and graceful failure. This guide explains the error handling implementation.

---

## Components

### 1. **error_handler.py** - Main Error Handling Module

A new module providing error handling utilities with:

#### Custom Exceptions

```python
SupabaseError              # Base exception for Supabase errors
SupabaseConnectionError    # Connection failures
SupabaseDownloadError      # Download/parse failures
DataValidationError        # Data validation failures
ConfigurationError         # Configuration issues
```

**Usage:**
```python
from error_handler import SupabaseError, safe_download_file

try:
    data = safe_download_file(supabase, "data", "file.csv")
except SupabaseDownloadError as e:
    print(f"Download failed: {e}")
```

#### Retry Decorator

Automatically retries failed operations:

```python
@retry_on_failure(max_retries=3, delay=1.0)
def risky_operation():
    # Will retry up to 3 times with 1-second delays
    return result
```

#### Validation Functions

```python
# Validate Supabase client
validate_supabase_client(supabase)

# Validate data structure
validate_dataframe(df, "Players", required_columns=["name", "points"], min_rows=1)

# Safe file download with error handling
safe_download_file(supabase, bucket, filename, file_type="csv")
```

#### Streamlit UI Display

Error messages displayed in UI:

```python
display_error(Exception("Data load failed"), "Error loading data")
display_warning("Limited data available")
display_info("Data loaded successfully")
```

#### Error Handler Context Manager

```python
with ErrorHandler("Loading data", show_ui=True) as handler:
    result = load_data_supabase(supabase)
    
if handler.error:
    # Handle error...
    pass
```

#### Safe Operation Wrapper

Execute function with automatic error handling:

```python
result = safe_operation(
    load_data_supabase,
    supabase,
    context="Loading data",
    default_return=None,
    show_error=True
)
```

---

## Implementation

### data_utils.py Changes

**Before:**
```python
def _download_parquet(supabase, bucket, file_name):
    data = supabase.storage.from_(bucket).download(file_name)
    return pd.read_parquet(io.BytesIO(data))
```

**After:**
```python
def _download_parquet(supabase, bucket, file_name):
    """Download and parse parquet file with error handling."""
    try:
        data = safe_download_file(supabase, bucket, file_name, "parquet")
        if not data:
            raise SupabaseDownloadError(f"No data received for {file_name}")
        
        df = pd.read_parquet(io.BytesIO(data))
        logger.info(f"Parsed parquet: {file_name} ({len(df)} rows)")
        return df
        
    except Exception as e:
        if isinstance(e, SupabaseDownloadError):
            raise
        logger.error(f"Parsing failed: {str(e)}")
        raise SupabaseDownloadError(f"Failed to parse {file_name}: {str(e)}")
```

**Key Improvements:**
- ✅ Try-catch wraps download and parse
- ✅ Validates data received
- ✅ Logs operations
- ✅ Provides context in error messages
- ✅ Data validation checks

### menu.py Changes

**Before:**
```python
df, standings, gameweeks, fixtures = load_data_supabase(supabase)
```

**After:**
```python
df = None
standings = None
gameweeks = None
fixtures = None

with st.spinner("📊 Loading data..."):
    try:
        df, standings, gameweeks, fixtures = load_data_supabase(supabase)
        display_info("✅ Data loaded successfully")
    except Exception as e:
        display_error(e, "Failed to load data")
        st.stop()

# Verify each dataset
if df is None or df.empty:
    display_warning("No player data available")
    st.stop()
```

**Key Improvements:**
- ✅ Error handling with try-catch
- ✅ Loading spinner
- ✅ User-friendly error messages
- ✅ Data validation after load
- ✅ Graceful app stop on critical errors

---

## Error Handling Layers

### Layer 1: Supabase Operations

```python
# safe_download_file() handles:
- Connection timeouts
- Missing files
- Empty responses
- Parse errors
- Invalid bucket names
```

### Layer 2: Data Processing

```python
# _convert_datetime_columns() handles:
- Missing columns
- Invalid date formats
- Timezone conversion errors
```

### Layer 3: Data Validation

```python
# validate_dataframe() checks:
- Empty DataFrames
- Minimum row counts
- Required columns
- Data types
```

### Layer 4: Streamlit UI

```python
# Display functions handle:
- Formatting errors nicely
- Logging for debugging
- User-friendly messages
- Graceful degradation
```

---

## Logging

Integrated Python logging for debugging:

```python
logger = get_logger(__name__)

logger.info("Loading data from Supabase")
logger.warning("File not found, using fallback")
logger.error("Download failed", exc_info=True)
```

**Log Messages Include:**
- Operation start/completion
- Warning messages
- Error details with stack traces
- Performance metrics

**Access Logs:**
- Terminal output when running `streamlit run menu.py`
- Use `--logger.level=debug` for verbose output

---

## Error Recovery Strategies

### 1. Graceful Degradation

```python
# Show available data, warn about missing parts
if standings.empty:
    display_warning("No standings data")
else:
    # Display standings
```

### 2. Retry with Backoff

```python
@retry_on_failure(max_retries=3, delay=2.0)
def download_data():
    # Retries up to 3 times with increasing delay
    return supabase.storage.download(...)
```

### 3. User Feedback

```python
with st.spinner("Loading..."):
    # User sees spinner during operations
    result = load_data()

if error:
    st.error("Failed to load data")  # Clear error message
```

---

## Testing Error Handling

### Simulating Errors

**Test Supabase connection error:**
```python
# Stop Supabase temporarily
# App will display: "Failed to load data: Connection refused"
```

**Test missing file:**
```python
# Remove file from Supabase
# App will display: "Failed to download file.csv: Not found"
```

**Test data validation:**
```python
# Upload DataFrame without required columns
# App will display: "GW Data missing required columns: [name]"
```

---

## Best Practices

### When Adding New Features

1. **Wrap Supabase calls:**
   ```python
   try:
       data = safe_download_file(supabase, bucket, filename)
   except SupabaseDownloadError as e:
       display_error(e, "Loading data")
   ```

2. **Validate data:**
   ```python
   validate_dataframe(df, "MyData", required_columns=["id", "name"])
   ```

3. **Log operations:**
   ```python
   logger = get_logger(__name__)
   logger.info("Starting operation")
   ```

4. **Display user feedback:**
   ```python
   display_info("Operation completed")
   display_warning("Limited data available")
   ```

---

## Configuration

### Logging Level

Change logging level in `error_handler.py`:

```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

Or via command line:
```bash
streamlit run menu.py --logger.level=debug
```

### Retry Configuration

Customize retry behavior:

```python
@retry_on_failure(max_retries=5, delay=2.0)  # Retry 5 times, 2s delay
def download_important_data():
    ...
```

---

## Monitoring & Debugging

### Enable Debug Logging

```bash
# Show all debug messages
streamlit run menu.py --logger.level=debug
```

### View Error Details

Check terminal output for:
```
2026-01-24 17:30:45 - error_handler - ERROR - Failed to download file: [detailed error]
```

### Identify Bottlenecks

```python
import time
start = time.time()
result = load_data_supabase(supabase)
duration = time.time() - start
logger.info(f"Load completed in {duration:.2f}s")
```

---

## Migration Guide

### Existing Code

If you have Supabase calls elsewhere:

**Old way:**
```python
data = supabase.storage.from_("data").download("file.csv")
df = pd.read_csv(io.BytesIO(data))
```

**New way:**
```python
from error_handler import safe_download_file, SupabaseDownloadError

try:
    data = safe_download_file(supabase, "data", "file.csv")
    df = pd.read_csv(io.BytesIO(data))
except SupabaseDownloadError as e:
    logger.error(f"Failed to load: {e}")
    raise
```

---

## Troubleshooting

### App crashes silently

**Problem:** App stops without error message
**Solution:** Check terminal for errors with `--logger.level=debug`

### Timeouts on Supabase calls

**Problem:** Requests take too long
**Solution:** Check network connection, increase timeout in `trigger_pipeline()`:
```python
r = requests.post(..., timeout=20)  # 20 seconds
```

### Data validation fails

**Problem:** "Missing required columns" error
**Solution:** Check Supabase file format and columns match schema

---

## Future Improvements

- [ ] Add exponential backoff for retries
- [ ] Implement circuit breaker pattern
- [ ] Add error tracking/alerting
- [ ] Create error analytics dashboard
- [ ] Add automatic error recovery
- [ ] Implement data caching for failures

---

## Summary

Error handling improvements provide:

✅ **Reliability** - Graceful failure instead of crashes  
✅ **Debugging** - Comprehensive logging for troubleshooting  
✅ **User Experience** - Clear error messages and feedback  
✅ **Robustness** - Data validation and automatic retries  
✅ **Maintainability** - Centralized error handling logic  

The app is now production-ready for handling failures gracefully!

---

**Last Updated:** January 24, 2026  
**Version:** 1.0.0
