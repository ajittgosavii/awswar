"""
Startup Optimization for Streamlit Apps
=======================================
Quick fixes for slow-loading Streamlit applications.

Apply these optimizations to dramatically improve startup time.
"""

import streamlit as st
from typing import Callable, Any
import functools


# ============================================================================
# FRAGMENT DECORATOR FOR TABS
# ============================================================================

def tab_fragment(func: Callable) -> Callable:
    """
    Decorator that makes a tab render as a Streamlit fragment.
    This prevents the tab from re-rendering when other parts of the app change.
    
    Usage:
        @tab_fragment
        def render_my_tab():
            st.write("This tab renders independently")
    """
    @st.fragment
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


# ============================================================================
# CONDITIONAL IMPORT HELPER
# ============================================================================

def import_when_needed(module_name: str, func_name: str = None):
    """
    Import a module only when the returned function is called.
    
    Usage:
        render_expensive = import_when_needed('expensive_module', 'render')
        # Later, when actually needed:
        render_expensive()
    """
    def loader(*args, **kwargs):
        import importlib
        module = importlib.import_module(module_name)
        if func_name:
            func = getattr(module, func_name)
            return func(*args, **kwargs)
        return module
    return loader


# ============================================================================
# QUICK PERFORMANCE FIXES
# ============================================================================

def apply_performance_fixes():
    """
    Apply common performance fixes to Streamlit apps.
    Call this at the start of your app.
    """
    
    # 1. Initialize session state efficiently
    if '_perf_init' not in st.session_state:
        st.session_state._perf_init = True
        
        # Pre-set common session state keys to avoid repeated checks
        defaults = {
            'app_loaded': True,
            'demo_mode': True,
            'scan_results': None,
            'last_tab': None,
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    # 2. Clear any stale cache entries
    # (Streamlit handles this, but explicit call can help)


# ============================================================================
# LOADING INDICATOR
# ============================================================================

def show_loading_indicator():
    """Show a loading indicator while the app initializes"""
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; height: 200px;">
            <div style="text-align: center;">
                <div class="spinner" style="
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #007CC3;
                    border-radius: 50%;
                    width: 40px;
                    height: 40px;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px auto;
                "></div>
                <p>Loading AWS WAF Scanner...</p>
            </div>
        </div>
        <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """, unsafe_allow_html=True)
    return placeholder


def hide_loading_indicator(placeholder):
    """Hide the loading indicator"""
    placeholder.empty()


# ============================================================================
# PROFILING HELPER
# ============================================================================

class AppProfiler:
    """Simple profiler for Streamlit apps"""
    
    _timers = {}
    
    @classmethod
    def start(cls, name: str):
        """Start a named timer"""
        import time
        cls._timers[name] = time.time()
    
    @classmethod
    def stop(cls, name: str) -> float:
        """Stop a timer and return elapsed time in ms"""
        import time
        if name not in cls._timers:
            return 0
        elapsed = (time.time() - cls._timers[name]) * 1000
        del cls._timers[name]
        return elapsed
    
    @classmethod
    def log(cls, name: str):
        """Stop a timer and log the result"""
        elapsed = cls.stop(name)
        if elapsed > 100:  # Only log slow operations (>100ms)
            st.toast(f"⏱️ {name}: {elapsed:.0f}ms", icon="⏱️")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'tab_fragment',
    'import_when_needed',
    'apply_performance_fixes',
    'show_loading_indicator',
    'hide_loading_indicator',
    'AppProfiler',
]
