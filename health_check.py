"""
Health Check Module for AWS WAF Scanner Enterprise
===================================================
Provides health check endpoints and system diagnostics for production monitoring.

Usage:
    from health_check import HealthChecker, render_health_dashboard
    
    checker = HealthChecker()
    status = checker.run_all_checks()
"""

import os
import sys
import time
import platform
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# HEALTH STATUS
# ============================================================================

class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check"""
    name: str
    status: HealthStatus
    message: str = ""
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SystemHealth:
    """Overall system health status"""
    status: HealthStatus
    checks: List[HealthCheckResult]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "5.0.0"
    environment: str = "production"
    uptime_seconds: float = 0.0
    
    @property
    def healthy_count(self) -> int:
        return sum(1 for c in self.checks if c.status == HealthStatus.HEALTHY)
    
    @property
    def total_count(self) -> int:
        return len(self.checks)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'timestamp': self.timestamp,
            'version': self.version,
            'environment': self.environment,
            'uptime_seconds': self.uptime_seconds,
            'summary': f"{self.healthy_count}/{self.total_count} checks passed",
            'checks': [
                {
                    'name': c.name,
                    'status': c.status.value,
                    'message': c.message,
                    'duration_ms': c.duration_ms,
                    'details': c.details
                }
                for c in self.checks
            ]
        }


# ============================================================================
# HEALTH CHECKER
# ============================================================================

class HealthChecker:
    """
    Comprehensive health checker for the application.
    
    Checks:
    - Python environment
    - Required packages
    - AWS connectivity
    - Database connectivity
    - AI service (Anthropic)
    - File system
    - Memory usage
    """
    
    _start_time: float = time.time()
    
    def __init__(self):
        self.checks: List[HealthCheckResult] = []
    
    def run_all_checks(self) -> SystemHealth:
        """Run all health checks and return overall status"""
        self.checks = []
        
        # Run individual checks
        self.checks.append(self._check_python())
        self.checks.append(self._check_packages())
        self.checks.append(self._check_aws())
        self.checks.append(self._check_database())
        self.checks.append(self._check_ai_service())
        self.checks.append(self._check_filesystem())
        self.checks.append(self._check_memory())
        
        # Determine overall status
        statuses = [c.status for c in self.checks]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.UNKNOWN
        
        return SystemHealth(
            status=overall_status,
            checks=self.checks,
            uptime_seconds=time.time() - self._start_time
        )
    
    def _check_python(self) -> HealthCheckResult:
        """Check Python environment"""
        start = time.time()
        
        try:
            version = sys.version_info
            details = {
                'version': f"{version.major}.{version.minor}.{version.micro}",
                'platform': platform.platform(),
                'executable': sys.executable
            }
            
            # Check minimum version
            if version.major >= 3 and version.minor >= 9:
                status = HealthStatus.HEALTHY
                message = f"Python {details['version']}"
            else:
                status = HealthStatus.DEGRADED
                message = f"Python {details['version']} - recommend 3.9+"
            
            return HealthCheckResult(
                name="python",
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000,
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="python",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )
    
    def _check_packages(self) -> HealthCheckResult:
        """Check required packages are installed"""
        start = time.time()
        
        required_packages = [
            'streamlit',
            'boto3',
            'anthropic',
            'pandas',
            'reportlab'
        ]
        
        missing = []
        versions = {}
        
        for package in required_packages:
            try:
                module = __import__(package)
                versions[package] = getattr(module, '__version__', 'unknown')
            except ImportError:
                missing.append(package)
        
        if not missing:
            return HealthCheckResult(
                name="packages",
                status=HealthStatus.HEALTHY,
                message=f"All {len(required_packages)} required packages installed",
                duration_ms=(time.time() - start) * 1000,
                details={'versions': versions}
            )
        else:
            return HealthCheckResult(
                name="packages",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing packages: {', '.join(missing)}",
                duration_ms=(time.time() - start) * 1000,
                details={'missing': missing, 'installed': versions}
            )
    
    def _check_aws(self) -> HealthCheckResult:
        """Check AWS connectivity"""
        start = time.time()
        
        try:
            import boto3
            from botocore.exceptions import NoCredentialsError, ClientError
            
            session = boto3.Session()
            sts = session.client('sts')
            
            try:
                identity = sts.get_caller_identity()
                return HealthCheckResult(
                    name="aws",
                    status=HealthStatus.HEALTHY,
                    message=f"Connected to account {identity['Account']}",
                    duration_ms=(time.time() - start) * 1000,
                    details={
                        'account_id': identity['Account'],
                        'arn': identity['Arn']
                    }
                )
            except NoCredentialsError:
                return HealthCheckResult(
                    name="aws",
                    status=HealthStatus.DEGRADED,
                    message="No AWS credentials configured (Demo mode available)",
                    duration_ms=(time.time() - start) * 1000
                )
            except ClientError as e:
                return HealthCheckResult(
                    name="aws",
                    status=HealthStatus.DEGRADED,
                    message=f"AWS error: {e.response['Error']['Code']}",
                    duration_ms=(time.time() - start) * 1000
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="aws",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )
    
    def _check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        start = time.time()
        
        try:
            from database_adapter import get_database
            
            db = get_database()
            if db.is_connected():
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.HEALTHY,
                    message="Database connected",
                    duration_ms=(time.time() - start) * 1000,
                    details={'backend': type(db).__name__}
                )
            else:
                return HealthCheckResult(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Database not connected",
                    duration_ms=(time.time() - start) * 1000
                )
                
        except ImportError:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.DEGRADED,
                message="Database module not available",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )
    
    def _check_ai_service(self) -> HealthCheckResult:
        """Check AI service (Anthropic) availability"""
        start = time.time()
        
        try:
            import anthropic
            
            # Check if API key is configured
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            
            if not api_key:
                try:
                    import streamlit as st
                    api_key = st.secrets.get('ANTHROPIC_API_KEY')
                except Exception:
                    pass
            
            if api_key:
                return HealthCheckResult(
                    name="ai_service",
                    status=HealthStatus.HEALTHY,
                    message="Anthropic API configured",
                    duration_ms=(time.time() - start) * 1000
                )
            else:
                return HealthCheckResult(
                    name="ai_service",
                    status=HealthStatus.DEGRADED,
                    message="Anthropic API key not configured",
                    duration_ms=(time.time() - start) * 1000
                )
                
        except ImportError:
            return HealthCheckResult(
                name="ai_service",
                status=HealthStatus.DEGRADED,
                message="Anthropic package not installed",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="ai_service",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )
    
    def _check_filesystem(self) -> HealthCheckResult:
        """Check filesystem access"""
        start = time.time()
        
        try:
            # Check data directory
            data_dir = 'data'
            logs_dir = 'logs'
            
            writable_dirs = []
            issues = []
            
            for dir_name in [data_dir, logs_dir]:
                try:
                    os.makedirs(dir_name, exist_ok=True)
                    test_file = os.path.join(dir_name, '.health_check')
                    with open(test_file, 'w') as f:
                        f.write('test')
                    os.remove(test_file)
                    writable_dirs.append(dir_name)
                except (OSError, PermissionError) as e:
                    issues.append(f"{dir_name}: {e}")
            
            if not issues:
                return HealthCheckResult(
                    name="filesystem",
                    status=HealthStatus.HEALTHY,
                    message="All directories writable",
                    duration_ms=(time.time() - start) * 1000,
                    details={'writable': writable_dirs}
                )
            else:
                return HealthCheckResult(
                    name="filesystem",
                    status=HealthStatus.DEGRADED,
                    message=f"Some directories not writable",
                    duration_ms=(time.time() - start) * 1000,
                    details={'issues': issues, 'writable': writable_dirs}
                )
                
        except Exception as e:
            return HealthCheckResult(
                name="filesystem",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )
    
    def _check_memory(self) -> HealthCheckResult:
        """Check memory usage"""
        start = time.time()
        
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            details = {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': used_percent
            }
            
            if used_percent < 80:
                status = HealthStatus.HEALTHY
                message = f"Memory: {used_percent}% used"
            elif used_percent < 90:
                status = HealthStatus.DEGRADED
                message = f"Memory: {used_percent}% used (high)"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Memory: {used_percent}% used (critical)"
            
            return HealthCheckResult(
                name="memory",
                status=status,
                message=message,
                duration_ms=(time.time() - start) * 1000,
                details=details
            )
            
        except ImportError:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not installed",
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return HealthCheckResult(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=str(e),
                duration_ms=(time.time() - start) * 1000
            )


# ============================================================================
# STREAMLIT UI
# ============================================================================

def render_health_dashboard():
    """Render health check dashboard in Streamlit"""
    import streamlit as st
    
    st.header("🏥 System Health Dashboard")
    
    checker = HealthChecker()
    health = checker.run_all_checks()
    
    # Overall status
    status_colors = {
        HealthStatus.HEALTHY: "🟢",
        HealthStatus.DEGRADED: "🟡",
        HealthStatus.UNHEALTHY: "🔴",
        HealthStatus.UNKNOWN: "⚪"
    }
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Overall Status",
            f"{status_colors[health.status]} {health.status.value.title()}"
        )
    
    with col2:
        st.metric("Checks Passed", f"{health.healthy_count}/{health.total_count}")
    
    with col3:
        st.metric("Version", health.version)
    
    with col4:
        uptime_hours = health.uptime_seconds / 3600
        st.metric("Uptime", f"{uptime_hours:.1f}h")
    
    st.divider()
    
    # Individual checks
    st.subheader("Health Checks")
    
    for check in health.checks:
        with st.expander(
            f"{status_colors[check.status]} {check.name.title()} - {check.message}",
            expanded=check.status != HealthStatus.HEALTHY
        ):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Status:** {check.status.value}")
                st.write(f"**Message:** {check.message}")
            with col2:
                st.write(f"**Duration:** {check.duration_ms:.1f}ms")
            
            if check.details:
                st.json(check.details)
    
    # Refresh button
    if st.button("🔄 Refresh Health Checks"):
        st.rerun()


# ============================================================================
# API ENDPOINT (for external monitoring)
# ============================================================================

def get_health_status() -> Dict[str, Any]:
    """
    Get health status as JSON (for API endpoints).
    
    Returns:
        Dictionary with health status suitable for JSON serialization
    """
    checker = HealthChecker()
    health = checker.run_all_checks()
    return health.to_dict()


def get_liveness() -> Dict[str, Any]:
    """
    Simple liveness check.
    
    Returns:
        Basic alive status for Kubernetes/container probes
    """
    return {
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat()
    }


def get_readiness() -> Dict[str, Any]:
    """
    Readiness check for traffic serving.
    
    Returns:
        Readiness status for Kubernetes/container probes
    """
    checker = HealthChecker()
    health = checker.run_all_checks()
    
    # Ready if all critical checks pass
    critical_checks = ['python', 'packages']
    critical_status = [
        c.status == HealthStatus.HEALTHY
        for c in health.checks
        if c.name in critical_checks
    ]
    
    ready = all(critical_status)
    
    return {
        'ready': ready,
        'status': 'ready' if ready else 'not_ready',
        'timestamp': datetime.utcnow().isoformat()
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'HealthStatus',
    'HealthCheckResult',
    'SystemHealth',
    'HealthChecker',
    'render_health_dashboard',
    'get_health_status',
    'get_liveness',
    'get_readiness',
]
