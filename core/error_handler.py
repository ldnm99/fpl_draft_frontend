# ============================================================
#                   ERROR HANDLING MODULE
# ============================================================

import logging
from typing import Optional, Callable, Any
from functools import wraps
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
#                   CUSTOM EXCEPTIONS
# ============================================================

class SupabaseError(Exception):
    """Base exception for Supabase-related errors."""
    pass


class SupabaseConnectionError(SupabaseError):
    """Raised when connection to Supabase fails."""
    pass


class SupabaseDownloadError(SupabaseError):
    """Raised when downloading data from Supabase fails."""
    pass


class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


# ============================================================
#                   RETRY DECORATOR
# ============================================================

def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries (seconds)
        
    Example:
        @retry_on_failure(max_retries=3, delay=2.0)
        def risky_operation():
            ...
    """
    import time
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"Failed after {max_retries} attempts: {str(e)}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed. "
                        f"Retrying in {delay}s... Error: {str(e)}"
                    )
                    time.sleep(delay)
        return wrapper
    return decorator


# ============================================================
#                   SUPABASE HELPERS
# ============================================================

def validate_supabase_client(supabase) -> bool:
    """
    Validate that Supabase client is properly initialized.
    
    Args:
        supabase: Supabase client instance
        
    Returns:
        True if valid, False otherwise
        
    Raises:
        ConfigurationError: If client is invalid
    """
    if supabase is None:
        raise ConfigurationError("Supabase client is None")
    
    if not hasattr(supabase, 'storage'):
        raise ConfigurationError("Supabase client missing storage attribute")
    
    return True


def validate_bucket_exists(supabase, bucket: str) -> bool:
    """
    Check if Supabase bucket exists.
    
    Args:
        supabase: Supabase client instance
        bucket: Bucket name to check
        
    Returns:
        True if bucket exists
        
    Raises:
        SupabaseConnectionError: If cannot verify bucket
    """
    try:
        supabase.storage.from_(bucket).list()
        return True
    except Exception as e:
        logger.error(f"Bucket validation failed: {str(e)}")
        raise SupabaseConnectionError(
            f"Cannot access bucket '{bucket}': {str(e)}"
        )


def safe_download_file(
    supabase,
    bucket: str,
    file_name: str,
    file_type: str = "csv"
) -> Optional[bytes]:
    """
    Safely download file from Supabase with error handling.
    
    Args:
        supabase: Supabase client instance
        bucket: Bucket name
        file_name: File name to download
        file_type: File type for error context
        
    Returns:
        File data as bytes, or None if failed
        
    Raises:
        SupabaseDownloadError: If download fails after retries
    """
    try:
        logger.info(f"Downloading {file_type} file: {file_name} from {bucket}")
        
        data = supabase.storage.from_(bucket).download(file_name)
        
        if not data:
            raise SupabaseDownloadError(f"Downloaded data is empty for {file_name}")
        
        logger.info(f"Successfully downloaded {file_name}")
        return data
        
    except Exception as e:
        logger.error(f"Failed to download {file_name}: {str(e)}")
        raise SupabaseDownloadError(
            f"Failed to download {file_name}: {str(e)}"
        )


# ============================================================
#                   DATA VALIDATION
# ============================================================

def validate_dataframe(
    df,
    name: str,
    required_columns: list = None,
    min_rows: int = 0
) -> bool:
    """
    Validate that a DataFrame has required structure.
    
    Args:
        df: DataFrame to validate
        name: DataFrame name for error messages
        required_columns: List of required column names
        min_rows: Minimum number of rows required
        
    Returns:
        True if valid
        
    Raises:
        DataValidationError: If validation fails
    """
    if df is None or df.empty:
        if min_rows > 0:
            raise DataValidationError(f"{name} is empty")
        return True
    
    if len(df) < min_rows:
        raise DataValidationError(
            f"{name} has {len(df)} rows, expected at least {min_rows}"
        )
    
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise DataValidationError(
                f"{name} missing required columns: {missing}. "
                f"Available columns: {list(df.columns)}"
            )
    
    logger.info(f"Validated {name}: {len(df)} rows, {len(df.columns)} columns")
    return True


# ============================================================
#                   STREAMLIT ERROR DISPLAY
# ============================================================

def display_error(error: Exception, context: str = "Error") -> None:
    """
    Display error in Streamlit UI with appropriate styling.
    
    Args:
        error: Exception to display
        context: Context string for error message
    """
    error_msg = str(error)
    logger.error(f"{context}: {error_msg}")
    
    st.error(f"❌ {context}: {error_msg}")


def display_warning(message: str) -> None:
    """
    Display warning in Streamlit UI.
    
    Args:
        message: Warning message
    """
    logger.warning(message)
    st.warning(f"⚠️ {message}")


def display_info(message: str) -> None:
    """
    Display info in Streamlit UI.
    
    Args:
        message: Info message
    """
    logger.info(message)
    st.info(f"ℹ️ {message}")


# ============================================================
#                   ERROR CONTEXT MANAGER
# ============================================================

class ErrorHandler:
    """Context manager for handling errors gracefully."""
    
    def __init__(self, context: str = "Operation", show_ui: bool = True):
        """
        Initialize error handler.
        
        Args:
            context: Description of operation for error messages
            show_ui: Whether to display errors in Streamlit UI
        """
        self.context = context
        self.show_ui = show_ui
        self.error = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.error = exc_val
            logger.error(f"{self.context} failed: {str(exc_val)}", exc_info=True)
            
            if self.show_ui:
                display_error(exc_val, self.context)
            
            # Return False to re-raise the exception
            return False
        
        return True


# ============================================================
#                   SAFE OPERATION WRAPPER
# ============================================================

def safe_operation(
    func: Callable,
    *args,
    context: str = "Operation",
    default_return: Any = None,
    show_error: bool = True,
    **kwargs
) -> Any:
    """
    Execute function safely with error handling.
    
    Args:
        func: Function to execute
        *args: Positional arguments for function
        context: Description of operation for error messages
        default_return: Value to return if operation fails
        show_error: Whether to display error in UI
        **kwargs: Keyword arguments for function
        
    Returns:
        Function result or default_return if error occurs
        
    Example:
        result = safe_operation(
            load_data, 
            supabase, 
            context="Loading data",
            default_return=None
        )
    """
    try:
        logger.info(f"Starting: {context}")
        result = func(*args, **kwargs)
        logger.info(f"Completed: {context}")
        return result
        
    except Exception as e:
        logger.error(f"{context} failed: {str(e)}", exc_info=True)
        
        if show_error:
            display_error(e, context)
        
        return default_return


# ============================================================
#                   LOGGING UTILITIES
# ============================================================

def log_operation_metrics(operation: str, duration: float, success: bool) -> None:
    """
    Log operation metrics for monitoring.
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        success: Whether operation succeeded
    """
    status = "✓ SUCCESS" if success else "✗ FAILED"
    logger.info(f"{operation}: {status} ({duration:.2f}s)")


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get or create logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
