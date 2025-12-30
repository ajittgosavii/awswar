"""
Performance Optimization Module for AWS WAF Scanner Enterprise
==============================================================
Version: 1.0.0

This module provides caching, lazy loading, and performance monitoring
utilities to significantly improve application responsiveness.

Import this module at the top of streamlit_app.py and use the provided
decorators and utilities.

Usage:
    from performance_optimizations import (
        lazy_import,
        cache_scan_result,
        get_client_manager,
        PerformanceMonitor,
        get_app_state
    )
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass, field
from functools import wraps, lru_cache
import time
import hashlib
import logging

logger = logging.getLogger(__name__)

# Type variable for generic returns
T = TypeVar('T')


# ============================================================================
# LAZY IMPORT SYSTEM
# ============================================================================

class LazyImporter:
    """
    Lazy module importer that defers imports until first use.
    Dramatically reduces startup time by only loading modules when needed.
    """
    
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._loaders: Dict[str, Callable] = {}
    
    def register(self, name: str, loader: Callable[[], Any]) -> None:
        """Register a lazy loader for a module"""
        self._loaders[name] = loader
    
    def get(self, name: str) -> Any:
        """Get a module, loading it if necessary"""
        if name not in self._modules:
            if name not in self._loaders:
                raise KeyError(f"No loader registered for module: {name}")
            
            try:
                start = time.time()
                self._modules[name] = self._loaders[name]()
                elapsed = time.time() - start
                logger.info(f"Lazy loaded {name} in {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"Failed to load {name}: {e}")
                raise
        
        return self._modules[name]
    
    def is_loaded(self, name: str) -> bool:
        """Check if a module is already loaded"""
        return name in self._modules
    
    def clear(self, name: Optional[str] = None) -> None:
        """Clear cached modules"""
        if name:
            self._modules.pop(name, None)
        else:
            self._modules.clear()


# Global lazy importer instance
_lazy_importer = LazyImporter()


def lazy_import(module_path: str, attribute: Optional[str] = None):
    """
    Decorator to create a lazy-loaded module getter.
    
    Usage:
        @lazy_import('unified_dashboard', 'render_unified_dashboard')
        def get_dashboard_renderer():
            pass
        
        # Later, when needed:
        renderer = get_dashboard_renderer()
        renderer()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @st.cache_resource
        def wrapper():
            try:
                module = __import__(module_path, fromlist=[attribute] if attribute else [])
                if attribute:
                    return getattr(module, attribute)
                return module
            except ImportError as e:
                logger.error(f"Failed to import {module_path}: {e}")
                return None
        return wrapper
    return decorator


# Pre-registered lazy loaders for common modules
def setup_lazy_loaders():
    """Register lazy loaders for all heavy modules"""
    
    @st.cache_resource
    def load_unified_dashboard():
        from unified_dashboard import render_unified_dashboard
        return render_unified_dashboard
    
    @st.cache_resource
    def load_waf_scanner():
        from waf_scanner_integrated import render_integrated_waf_scanner
        return render_integrated_waf_scanner
    
    @st.cache_resource
    def load_architecture_designer():
        from architecture_designer_integrated import render_architecture_designer_integrated
        return render_architecture_designer_integrated
    
    @st.cache_resource
    def load_eks_module():
        from eks_modernization_integrated import render_eks_modernization_integrated
        return render_eks_modernization_integrated
    
    @st.cache_resource
    def load_finops():
        from modules_finops import FinOpsEnterpriseModule
        return FinOpsEnterpriseModule
    
    @st.cache_resource
    def load_ai_lens():
        from ai_lens_module import render_ai_lens_tab
        return render_ai_lens_tab
    
    @st.cache_resource
    def load_remediation():
        from remediation_engine_integrated import render_remediation_engine
        return render_remediation_engine
    
    @st.cache_resource
    def load_compliance():
        from compliance_module import ComplianceModule
        return ComplianceModule
    
    @st.cache_resource
    def load_landscape_scanner():
        from landscape_scanner import AWSLandscapeScanner
        return AWSLandscapeScanner
    
    return {
        'unified_dashboard': load_unified_dashboard,
        'waf_scanner': load_waf_scanner,
        'architecture_designer': load_architecture_designer,
        'eks_module': load_eks_module,
        'finops': load_finops,
        'ai_lens': load_ai_lens,
        'remediation': load_remediation,
        'compliance': load_compliance,
        'landscape_scanner': load_landscape_scanner,
    }


# ============================================================================
# SCAN RESULT CACHING
# ============================================================================

@dataclass
class CachedResult:
    """Container for cached scan results with TTL"""
    data: Any
    timestamp: datetime
    ttl_seconds: int
    
    def is_valid(self) -> bool:
        """Check if cache is still valid"""
        if self.data is None:
            return False
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed < self.ttl_seconds


class ScanResultCache:
    """
    Session-state based cache for scan results.
    Automatically expires entries based on TTL.
    """
    
    CACHE_KEY = '_scan_result_cache'
    
    @classmethod
    def _get_cache(cls) -> Dict[str, CachedResult]:
        """Get or create the cache dict in session state"""
        if cls.CACHE_KEY not in st.session_state:
            st.session_state[cls.CACHE_KEY] = {}
        return st.session_state[cls.CACHE_KEY]
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get a cached value if valid"""
        cache = cls._get_cache()
        if key in cache and cache[key].is_valid():
            return cache[key].data
        return None
    
    @classmethod
    def set(cls, key: str, data: Any, ttl_seconds: int = 300) -> None:
        """Set a cached value with TTL"""
        cache = cls._get_cache()
        cache[key] = CachedResult(
            data=data,
            timestamp=datetime.now(),
            ttl_seconds=ttl_seconds
        )
    
    @classmethod
    def invalidate(cls, key: Optional[str] = None) -> None:
        """Invalidate cache entries"""
        cache = cls._get_cache()
        if key:
            cache.pop(key, None)
        else:
            cache.clear()
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """Remove expired entries, return count removed"""
        cache = cls._get_cache()
        expired = [k for k, v in cache.items() if not v.is_valid()]
        for key in expired:
            del cache[key]
        return len(expired)


def cache_scan_result(ttl_seconds: int = 300, key_prefix: str = ""):
    """
    Decorator to cache scan function results in session state.
    
    Args:
        ttl_seconds: Time-to-live for cached results (default 5 minutes)
        key_prefix: Optional prefix for cache key
    
    Usage:
        @cache_scan_result(ttl_seconds=600)
        def scan_iam_users(session):
            iam = session.client('iam')
            return iam.list_users()['Users']
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Generate cache key from function name and arguments
            # Skip 'self' argument if present
            cache_args = args[1:] if args and hasattr(args[0], '__class__') else args
            key_parts = [key_prefix, func.__name__, str(cache_args), str(sorted(kwargs.items()))]
            cache_key = hashlib.md5('_'.join(key_parts).encode()).hexdigest()
            
            # Check cache first
            cached = ScanResultCache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)
            ScanResultCache.set(cache_key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator


# ============================================================================
# AWS CLIENT MANAGER WITH CONNECTION POOLING
# ============================================================================

class AWSClientManager:
    """
    Singleton manager for boto3 clients with connection pooling.
    Reuses clients to avoid repeated connection setup.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._clients: Dict[str, Any] = {}
        self._session = None
        self._config = None
        self._initialized = True
        
        # Configure boto3 with connection pooling
        try:
            from botocore.config import Config
            self._config = Config(
                max_pool_connections=25,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                connect_timeout=5,
                read_timeout=30
            )
        except ImportError:
            logger.warning("botocore not available, using default config")
    
    def set_session(self, session) -> None:
        """Set the boto3 session (clears client cache)"""
        self._session = session
        self._clients.clear()
    
    def get_client(self, service_name: str, region: str = 'us-east-1'):
        """Get or create a cached boto3 client"""
        cache_key = f"{service_name}_{region}"
        
        if cache_key not in self._clients:
            if self._session is None:
                import boto3
                self._session = boto3.Session()
            
            kwargs = {'region_name': region}
            if self._config:
                kwargs['config'] = self._config
            
            self._clients[cache_key] = self._session.client(service_name, **kwargs)
        
        return self._clients[cache_key]
    
    def get_resource(self, service_name: str, region: str = 'us-east-1'):
        """Get or create a cached boto3 resource"""
        cache_key = f"resource_{service_name}_{region}"
        
        if cache_key not in self._clients:
            if self._session is None:
                import boto3
                self._session = boto3.Session()
            
            kwargs = {'region_name': region}
            if self._config:
                kwargs['config'] = self._config
            
            self._clients[cache_key] = self._session.resource(service_name, **kwargs)
        
        return self._clients[cache_key]
    
    def clear_clients(self) -> None:
        """Clear all cached clients"""
        self._clients.clear()


@st.cache_resource
def get_client_manager() -> AWSClientManager:
    """Get the singleton AWS client manager"""
    return AWSClientManager()


# ============================================================================
# APPLICATION STATE MANAGEMENT
# ============================================================================

@dataclass
class AppState:
    """
    Structured application state container.
    Provides type-safe access to common state variables.
    """
    
    # Authentication state
    authenticated: bool = False
    user_info: Optional[Dict] = None
    user_role: str = "viewer"
    
    # AWS connection state
    aws_connected: bool = False
    demo_mode: bool = True
    connected_accounts: List[Dict] = field(default_factory=list)
    current_region: str = "us-east-1"
    
    # UI state
    current_tab: str = "Dashboard"
    sidebar_expanded: bool = True
    
    # Scan state
    last_scan_time: Optional[datetime] = None
    total_findings: int = 0
    critical_findings: int = 0
    waf_score: int = 0
    compliance_score: int = 0
    
    # Performance metrics
    page_load_times: List[Dict] = field(default_factory=list)
    api_call_count: int = 0


def get_app_state() -> AppState:
    """Get or create the application state"""
    if '_app_state' not in st.session_state:
        st.session_state._app_state = AppState()
    return st.session_state._app_state


def update_app_state(**kwargs) -> None:
    """Update application state attributes"""
    state = get_app_state()
    for key, value in kwargs.items():
        if hasattr(state, key):
            setattr(state, key, value)


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

class PerformanceMonitor:
    """
    Track and display performance metrics.
    Helps identify slow operations.
    """
    
    METRICS_KEY = '_perf_metrics'
    
    def __init__(self):
        if self.METRICS_KEY not in st.session_state:
            st.session_state[self.METRICS_KEY] = {
                'operations': [],
                'api_calls': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'start_time': datetime.now()
            }
    
    @property
    def metrics(self) -> Dict:
        return st.session_state[self.METRICS_KEY]
    
    def track(self, operation_name: str):
        """
        Context manager to track operation timing.
        
        Usage:
            monitor = PerformanceMonitor()
            with monitor.track("Load Dashboard"):
                render_dashboard()
        """
        monitor = self
        
        class Timer:
            def __enter__(self):
                self.start = time.time()
                return self
            
            def __exit__(self, *args):
                elapsed = time.time() - self.start
                monitor.metrics['operations'].append({
                    'name': operation_name,
                    'duration': elapsed,
                    'timestamp': datetime.now().isoformat()
                })
                # Keep only last 50 operations
                if len(monitor.metrics['operations']) > 50:
                    monitor.metrics['operations'] = monitor.metrics['operations'][-50:]
        
        return Timer()
    
    def record_api_call(self) -> None:
        """Record an API call"""
        self.metrics['api_calls'] += 1
    
    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self) -> None:
        """Record a cache miss"""
        self.metrics['cache_misses'] += 1
    
    def get_cache_hit_rate(self) -> float:
        """Get cache hit rate as percentage"""
        total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        if total == 0:
            return 0.0
        return (self.metrics['cache_hits'] / total) * 100
    
    def render_sidebar_widget(self) -> None:
        """Render performance metrics in sidebar"""
        with st.sidebar.expander("⚡ Performance Metrics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("API Calls", self.metrics['api_calls'])
                st.metric("Cache Hit Rate", f"{self.get_cache_hit_rate():.1f}%")
            
            with col2:
                uptime = datetime.now() - self.metrics['start_time']
                st.metric("Session Time", f"{uptime.seconds // 60}m")
                st.metric("Operations", len(self.metrics['operations']))
            
            # Show slowest operations
            if self.metrics['operations']:
                st.markdown("**Slowest Operations:**")
                sorted_ops = sorted(
                    self.metrics['operations'],
                    key=lambda x: x['duration'],
                    reverse=True
                )[:5]
                for op in sorted_ops:
                    st.text(f"{op['name']}: {op['duration']:.2f}s")
    
    def reset(self) -> None:
        """Reset all metrics"""
        st.session_state[self.METRICS_KEY] = {
            'operations': [],
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'start_time': datetime.now()
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def render_loading_placeholder(message: str = "Loading..."):
    """Show a loading placeholder while content loads"""
    with st.spinner(message):
        placeholder = st.empty()
        return placeholder


def debounce_button(key: str, cooldown_seconds: float = 1.0) -> bool:
    """
    Prevent rapid button clicks by adding a cooldown.
    
    Usage:
        if debounce_button("scan_button"):
            perform_scan()
    """
    last_click_key = f"_last_click_{key}"
    now = time.time()
    
    last_click = st.session_state.get(last_click_key, 0)
    if now - last_click < cooldown_seconds:
        return False
    
    st.session_state[last_click_key] = now
    return True


def batch_process(items: List[Any], batch_size: int, processor: Callable) -> List[Any]:
    """
    Process items in batches to avoid overwhelming the UI.
    
    Args:
        items: List of items to process
        batch_size: Number of items per batch
        processor: Function to process each item
    
    Returns:
        List of processed results
    """
    results = []
    total = len(items)
    progress = st.progress(0, text="Processing...")
    
    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]
        for item in batch:
            results.append(processor(item))
        
        progress.progress((i + batch_size) / total, text=f"Processing {min(i + batch_size, total)}/{total}...")
    
    progress.progress(1.0, text="Complete!")
    return results


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_performance_optimizations():
    """
    Initialize all performance optimization systems.
    Call this once at the start of your app.
    """
    # Setup lazy loaders
    loaders = setup_lazy_loaders()
    
    # Initialize app state
    get_app_state()
    
    # Create performance monitor
    monitor = PerformanceMonitor()
    
    # Cleanup expired cache entries
    expired = ScanResultCache.cleanup_expired()
    if expired > 0:
        logger.info(f"Cleaned up {expired} expired cache entries")
    
    return {
        'loaders': loaders,
        'monitor': monitor,
        'client_manager': get_client_manager()
    }


# Export main components
__all__ = [
    'lazy_import',
    'setup_lazy_loaders',
    'cache_scan_result',
    'ScanResultCache',
    'AWSClientManager',
    'get_client_manager',
    'AppState',
    'get_app_state',
    'update_app_state',
    'PerformanceMonitor',
    'render_loading_placeholder',
    'debounce_button',
    'batch_process',
    'initialize_performance_optimizations',
]
