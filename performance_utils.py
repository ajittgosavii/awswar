"""
Performance Optimization Module
===============================
Provides caching, lazy loading, and performance utilities for Streamlit apps.

Key Features:
- Lazy module imports (only load when needed)
- Cached data and resource management
- Session state optimization
- Performance monitoring
"""

import streamlit as st
import time
import functools
from typing import Dict, Any, Callable, Optional, TypeVar, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import importlib
import sys

# Type variable for generic functions
T = TypeVar('T')


# ============================================================================
# LAZY MODULE LOADER
# ============================================================================

class LazyModuleLoader:
    """
    Lazy loader for heavy modules - only imports when actually needed.
    
    Usage:
        loader = LazyModuleLoader()
        pandas = loader.get('pandas')  # Only imports when called
    """
    
    _instances: Dict[str, Any] = {}
    _load_times: Dict[str, float] = {}
    
    @classmethod
    def get(cls, module_name: str) -> Any:
        """
        Get a module, importing it lazily if not already loaded.
        
        Args:
            module_name: Name of module to import
            
        Returns:
            The imported module
        """
        if module_name not in cls._instances:
            start = time.time()
            cls._instances[module_name] = importlib.import_module(module_name)
            cls._load_times[module_name] = time.time() - start
        
        return cls._instances[module_name]
    
    @classmethod
    def get_load_times(cls) -> Dict[str, float]:
        """Get load times for all lazily loaded modules"""
        return cls._load_times.copy()
    
    @classmethod
    def preload(cls, modules: List[str]):
        """Preload a list of modules (useful for background loading)"""
        for module in modules:
            cls.get(module)


# Convenience function
def lazy_import(module_name: str) -> Any:
    """Lazily import a module"""
    return LazyModuleLoader.get(module_name)


# ============================================================================
# STREAMLIT CACHING HELPERS
# ============================================================================

def cached_data(ttl_seconds: int = 300, show_spinner: bool = True):
    """
    Decorator for caching data with TTL.
    
    Args:
        ttl_seconds: Time-to-live in seconds (default 5 minutes)
        show_spinner: Whether to show loading spinner
        
    Usage:
        @cached_data(ttl_seconds=600)
        def get_expensive_data():
            return compute_something()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return st.cache_data(ttl=ttl_seconds, show_spinner=show_spinner)(func)
    return decorator


def cached_resource(ttl_seconds: int = 3600):
    """
    Decorator for caching resources (connections, clients, etc.).
    
    Args:
        ttl_seconds: Time-to-live in seconds (default 1 hour)
        
    Usage:
        @cached_resource()
        def get_database_connection():
            return create_connection()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        return st.cache_resource(ttl=ttl_seconds)(func)
    return decorator


# ============================================================================
# SESSION STATE MANAGER
# ============================================================================

@dataclass
class CacheEntry:
    """Entry in the session state cache"""
    value: Any
    created_at: datetime
    ttl_seconds: int
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        if self.ttl_seconds <= 0:
            return False  # Never expires
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class SessionStateManager:
    """
    Efficient session state management with TTL support.
    
    Features:
    - Automatic expiration
    - Default values
    - Bulk operations
    - Performance tracking
    """
    
    _CACHE_PREFIX = '_cached_'
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Initialize session state with defaults"""
        if cls._initialized:
            return
        
        defaults = {
            '_perf_initialized': True,
            '_perf_start_time': time.time(),
            '_perf_tab_loads': {},
            '_cache_hits': 0,
            '_cache_misses': 0,
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
        
        cls._initialized = True
    
    @classmethod
    def get(cls, key: str, default: Any = None, ttl_seconds: int = 0) -> Any:
        """
        Get a value from session state with optional caching.
        
        Args:
            key: State key
            default: Default value if not found
            ttl_seconds: Cache TTL (0 = no expiration)
        """
        cls.initialize()
        
        cache_key = f"{cls._CACHE_PREFIX}{key}"
        
        if cache_key in st.session_state:
            entry: CacheEntry = st.session_state[cache_key]
            if not entry.is_expired:
                st.session_state['_cache_hits'] = st.session_state.get('_cache_hits', 0) + 1
                return entry.value
            else:
                # Expired, remove it
                del st.session_state[cache_key]
        
        st.session_state['_cache_misses'] = st.session_state.get('_cache_misses', 0) + 1
        return default
    
    @classmethod
    def set(cls, key: str, value: Any, ttl_seconds: int = 0):
        """
        Set a value in session state with optional TTL.
        
        Args:
            key: State key
            value: Value to store
            ttl_seconds: Cache TTL (0 = no expiration)
        """
        cls.initialize()
        
        cache_key = f"{cls._CACHE_PREFIX}{key}"
        st.session_state[cache_key] = CacheEntry(
            value=value,
            created_at=datetime.utcnow(),
            ttl_seconds=ttl_seconds
        )
    
    @classmethod
    def delete(cls, key: str):
        """Delete a key from session state"""
        cache_key = f"{cls._CACHE_PREFIX}{key}"
        if cache_key in st.session_state:
            del st.session_state[cache_key]
    
    @classmethod
    def clear_expired(cls):
        """Clear all expired cache entries"""
        keys_to_delete = []
        
        for key in st.session_state:
            if key.startswith(cls._CACHE_PREFIX):
                entry = st.session_state[key]
                if isinstance(entry, CacheEntry) and entry.is_expired:
                    keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del st.session_state[key]
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Get cache statistics"""
        cls.initialize()
        
        hits = st.session_state.get('_cache_hits', 0)
        misses = st.session_state.get('_cache_misses', 0)
        total = hits + misses
        
        return {
            'cache_hits': hits,
            'cache_misses': misses,
            'hit_rate': (hits / total * 100) if total > 0 else 0,
            'total_requests': total
        }


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """
    Monitor and track application performance.
    """
    
    @staticmethod
    def start_timer(name: str):
        """Start a named timer"""
        if '_perf_timers' not in st.session_state:
            st.session_state['_perf_timers'] = {}
        st.session_state['_perf_timers'][name] = time.time()
    
    @staticmethod
    def stop_timer(name: str) -> float:
        """Stop a named timer and return elapsed time"""
        if '_perf_timers' not in st.session_state:
            return 0.0
        
        start_time = st.session_state['_perf_timers'].get(name)
        if start_time is None:
            return 0.0
        
        elapsed = time.time() - start_time
        
        # Store in history
        if '_perf_history' not in st.session_state:
            st.session_state['_perf_history'] = {}
        
        if name not in st.session_state['_perf_history']:
            st.session_state['_perf_history'][name] = []
        
        st.session_state['_perf_history'][name].append(elapsed)
        
        # Keep only last 100 measurements
        if len(st.session_state['_perf_history'][name]) > 100:
            st.session_state['_perf_history'][name] = \
                st.session_state['_perf_history'][name][-100:]
        
        return elapsed
    
    @staticmethod
    def track_tab_load(tab_name: str, load_time: float):
        """Track tab loading time"""
        if '_perf_tab_loads' not in st.session_state:
            st.session_state['_perf_tab_loads'] = {}
        
        if tab_name not in st.session_state['_perf_tab_loads']:
            st.session_state['_perf_tab_loads'][tab_name] = []
        
        st.session_state['_perf_tab_loads'][tab_name].append(load_time)
    
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get all performance metrics"""
        metrics = {
            'uptime_seconds': 0,
            'tab_loads': {},
            'avg_response_times': {}
        }
        
        if '_perf_start_time' in st.session_state:
            metrics['uptime_seconds'] = time.time() - st.session_state['_perf_start_time']
        
        if '_perf_tab_loads' in st.session_state:
            for tab, times in st.session_state['_perf_tab_loads'].items():
                if times:
                    metrics['tab_loads'][tab] = {
                        'avg': sum(times) / len(times),
                        'min': min(times),
                        'max': max(times),
                        'count': len(times)
                    }
        
        if '_perf_history' in st.session_state:
            for name, times in st.session_state['_perf_history'].items():
                if times:
                    metrics['avg_response_times'][name] = sum(times) / len(times)
        
        return metrics


# ============================================================================
# TAB LAZY LOADER
# ============================================================================

def lazy_tab(tab_name: str, render_func: Callable, *args, **kwargs):
    """
    Render a tab lazily - only executes render function when tab is active.
    
    Args:
        tab_name: Name of the tab for tracking
        render_func: Function to render the tab content
        *args, **kwargs: Arguments to pass to render_func
    """
    PerformanceMonitor.start_timer(f"tab_{tab_name}")
    
    try:
        render_func(*args, **kwargs)
    finally:
        load_time = PerformanceMonitor.stop_timer(f"tab_{tab_name}")
        PerformanceMonitor.track_tab_load(tab_name, load_time)


# ============================================================================
# CACHED AWS OPERATIONS
# ============================================================================

@st.cache_resource(ttl=300)
def get_cached_aws_session():
    """
    Get cached AWS session (5 minute TTL).
    
    Returns:
        boto3.Session or None if not configured
    """
    try:
        import boto3
        session = boto3.Session()
        # Validate session
        sts = session.client('sts')
        sts.get_caller_identity()
        return session
    except Exception:
        return None


@st.cache_data(ttl=300)
def get_cached_account_info() -> Optional[Dict[str, str]]:
    """
    Get cached AWS account info (5 minute TTL).
    
    Returns:
        Dict with account_id and arn, or None
    """
    session = get_cached_aws_session()
    if session is None:
        return None
    
    try:
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        return {
            'account_id': identity['Account'],
            'arn': identity['Arn'],
            'user_id': identity['UserId']
        }
    except Exception:
        return None


@st.cache_data(ttl=600)
def get_cached_regions() -> List[str]:
    """
    Get cached list of AWS regions (10 minute TTL).
    
    Returns:
        List of region names
    """
    session = get_cached_aws_session()
    if session is None:
        return ['us-east-1', 'us-west-2', 'eu-west-1']  # Defaults
    
    try:
        ec2 = session.client('ec2', region_name='us-east-1')
        response = ec2.describe_regions()
        return [r['RegionName'] for r in response['Regions']]
    except Exception:
        return ['us-east-1', 'us-west-2', 'eu-west-1']


# ============================================================================
# STREAMLIT PAGE CONFIG HELPER
# ============================================================================

def configure_page(
    title: str = "AWS WAF Scanner",
    icon: str = "🔍",
    layout: str = "wide",
    initial_sidebar_state: str = "expanded"
):
    """
    Configure Streamlit page with performance optimizations.
    
    Should be called at the very beginning of the app.
    """
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state
    )
    
    # Initialize session state manager
    SessionStateManager.initialize()
    
    # Clean up expired cache entries periodically
    SessionStateManager.clear_expired()


# ============================================================================
# RENDER PERFORMANCE DASHBOARD
# ============================================================================

def render_performance_dashboard():
    """Render a performance monitoring dashboard (for admin use)"""
    st.subheader("📊 Performance Metrics")
    
    metrics = PerformanceMonitor.get_metrics()
    cache_stats = SessionStateManager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Uptime", f"{metrics['uptime_seconds']:.0f}s")
    
    with col2:
        st.metric("Cache Hit Rate", f"{cache_stats['hit_rate']:.1f}%")
    
    with col3:
        st.metric("Cache Hits", cache_stats['cache_hits'])
    
    with col4:
        st.metric("Cache Misses", cache_stats['cache_misses'])
    
    if metrics['tab_loads']:
        st.markdown("#### Tab Load Times")
        for tab, stats in metrics['tab_loads'].items():
            st.write(f"**{tab}**: avg={stats['avg']*1000:.0f}ms, "
                    f"min={stats['min']*1000:.0f}ms, max={stats['max']*1000:.0f}ms")
    
    # Module load times
    load_times = LazyModuleLoader.get_load_times()
    if load_times:
        st.markdown("#### Module Load Times")
        for module, load_time in sorted(load_times.items(), key=lambda x: -x[1]):
            st.write(f"**{module}**: {load_time*1000:.0f}ms")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'LazyModuleLoader',
    'lazy_import',
    'cached_data',
    'cached_resource',
    'SessionStateManager',
    'PerformanceMonitor',
    'lazy_tab',
    'get_cached_aws_session',
    'get_cached_account_info',
    'get_cached_regions',
    'configure_page',
    'render_performance_dashboard',
]
