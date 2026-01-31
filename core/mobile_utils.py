"""
Mobile optimization utilities for responsive Streamlit layouts.
Provides helpers for mobile-friendly column layouts and spacing.
"""

import streamlit as st


def get_columns_count() -> int:
    """
    Determine optimal column count based on screen width.
    Streamlit default is ~1200px wide, mobile is <768px.
    """
    # Streamlit doesn't expose screen width directly, so we use a heuristic
    # Based on common usage patterns
    if "is_mobile" not in st.session_state:
        # Default to assuming desktop, user can override in URL params
        st.session_state.is_mobile = False
    
    return 2 if st.session_state.is_mobile else 4


def mobile_columns(count_desktop: int, count_mobile: int = 2):
    """
    Create responsive columns that adapt to mobile/desktop.
    Usage: cols = mobile_columns(4, 2)
    """
    if "is_mobile" not in st.session_state:
        st.session_state.is_mobile = False
    
    actual_count = count_mobile if st.session_state.is_mobile else count_desktop
    return st.columns(actual_count)


def optimize_chart_height(default: int = 500, mobile: int = 350) -> int:
    """
    Return optimized chart height based on device.
    """
    if "is_mobile" not in st.session_state:
        st.session_state.is_mobile = False
    
    return mobile if st.session_state.is_mobile else default


def get_metric_columns():
    """
    Get optimal column layout for metric cards.
    Desktop: 4 columns, Mobile: 2 columns
    """
    return mobile_columns(4, 2)


def add_mobile_css():
    """
    Add CSS optimizations for mobile viewing.
    """
    css = """
    <style>
        /* Mobile optimizations */
        @media (max-width: 768px) {
            /* Larger touch targets */
            button {
                min-height: 44px !important;
                font-size: 16px !important;
            }
            
            /* Better spacing on mobile */
            .stMetric {
                padding: 10px 0 !important;
            }
            
            /* Wider input fields */
            .stSelectbox, .stMultiSelect, .stTextInput {
                width: 100% !important;
            }
            
            /* Better dataframe scrolling */
            .stDataFrame {
                font-size: 12px !important;
            }
            
            /* Reduce expander padding */
            .streamlit-expanderHeader {
                padding: 8px 12px !important;
            }
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def set_mobile_mode():
    """
    Enable mobile mode for the session.
    Call this at the top of a page if you want to force mobile layout.
    """
    st.session_state.is_mobile = True
