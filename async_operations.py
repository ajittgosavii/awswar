"""
Async Operations Module
=======================
Provides async/await functionality for parallel multi-account AWS scanning.

This module enables:
- Concurrent scanning of multiple AWS accounts
- Parallel region scanning within accounts
- Async AWS API calls with proper throttling
- Progress tracking for async operations
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
import threading

# Import core utilities
try:
    from logging_config import get_logger
    from aws_utils import retry_with_backoff, handle_aws_error
except ImportError:
    import logging
    def get_logger(name): return logging.getLogger(name)
    def retry_with_backoff(*args, **kwargs):
        def decorator(func): return func
        return decorator
    def handle_aws_error(e, op): return {'error': str(e)}

logger = get_logger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AsyncConfig:
    """Configuration for async operations"""
    max_concurrent_accounts: int = 5
    max_concurrent_regions: int = 10
    max_concurrent_services: int = 20
    api_call_delay: float = 0.1  # Delay between API calls to avoid throttling
    timeout_seconds: int = 300
    retry_failed: bool = True
    progress_callback: Optional[Callable[[str, float], None]] = None


# ============================================================================
# PROGRESS TRACKING
# ============================================================================

@dataclass
class ScanProgress:
    """Tracks progress of async scanning operations"""
    total_accounts: int = 0
    completed_accounts: int = 0
    total_regions: int = 0
    completed_regions: int = 0
    total_services: int = 0
    completed_services: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def account_progress(self) -> float:
        """Progress percentage for accounts (0-100)"""
        if self.total_accounts == 0:
            return 0
        return (self.completed_accounts / self.total_accounts) * 100
    
    @property
    def overall_progress(self) -> float:
        """Overall progress percentage (0-100)"""
        if self.total_services == 0:
            return self.account_progress
        return (self.completed_services / self.total_services) * 100
    
    @property
    def elapsed_seconds(self) -> float:
        """Elapsed time in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    @property
    def estimated_remaining(self) -> float:
        """Estimated remaining time in seconds"""
        if self.overall_progress == 0:
            return 0
        rate = self.elapsed_seconds / self.overall_progress
        remaining_progress = 100 - self.overall_progress
        return rate * remaining_progress
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'total_accounts': self.total_accounts,
            'completed_accounts': self.completed_accounts,
            'total_regions': self.total_regions,
            'completed_regions': self.completed_regions,
            'total_services': self.total_services,
            'completed_services': self.completed_services,
            'account_progress': self.account_progress,
            'overall_progress': self.overall_progress,
            'elapsed_seconds': self.elapsed_seconds,
            'estimated_remaining': self.estimated_remaining,
            'error_count': len(self.errors)
        }


# ============================================================================
# ASYNC SCANNER BASE
# ============================================================================

class AsyncScanner:
    """
    Base class for async AWS scanning operations.
    
    Provides:
    - Concurrent execution with configurable limits
    - Progress tracking
    - Error handling and retry logic
    - Rate limiting to avoid AWS throttling
    """
    
    def __init__(self, config: AsyncConfig = None):
        """Initialize async scanner"""
        self.config = config or AsyncConfig()
        self.progress = ScanProgress()
        self._lock = threading.Lock()
        self._semaphore: Optional[asyncio.Semaphore] = None
    
    async def _init_semaphores(self):
        """Initialize semaphores for concurrency control"""
        self._account_semaphore = asyncio.Semaphore(self.config.max_concurrent_accounts)
        self._region_semaphore = asyncio.Semaphore(self.config.max_concurrent_regions)
        self._service_semaphore = asyncio.Semaphore(self.config.max_concurrent_services)
    
    def _update_progress(self, field: str, increment: int = 1):
        """Thread-safe progress update"""
        with self._lock:
            current = getattr(self.progress, field, 0)
            setattr(self.progress, field, current + increment)
            
            # Call progress callback if configured
            if self.config.progress_callback:
                self.config.progress_callback(
                    field, 
                    self.progress.overall_progress
                )
    
    def _add_error(self, error: Dict[str, Any]):
        """Thread-safe error recording"""
        with self._lock:
            self.progress.errors.append(error)
    
    async def _rate_limited_call(self, coro: Coroutine) -> Any:
        """Execute a coroutine with rate limiting"""
        async with self._service_semaphore:
            await asyncio.sleep(self.config.api_call_delay)
            return await coro
    
    async def scan_accounts(
        self,
        accounts: List[Dict[str, Any]],
        scan_function: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scan multiple accounts concurrently.
        
        Args:
            accounts: List of account configurations
            scan_function: Function to call for each account
            **kwargs: Additional arguments for scan_function
            
        Returns:
            Aggregated results from all accounts
        """
        await self._init_semaphores()
        
        self.progress = ScanProgress(
            total_accounts=len(accounts),
            start_time=datetime.utcnow()
        )
        
        results = {}
        
        # Create tasks for all accounts
        tasks = [
            self._scan_account_wrapper(account, scan_function, **kwargs)
            for account in accounts
        ]
        
        # Execute concurrently with timeout
        try:
            completed = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_seconds
            )
            
            for account, result in zip(accounts, completed):
                account_id = account.get('id', account.get('account_id', 'unknown'))
                if isinstance(result, Exception):
                    self._add_error({
                        'account_id': account_id,
                        'error': str(result),
                        'type': type(result).__name__
                    })
                    results[account_id] = {'error': str(result)}
                else:
                    results[account_id] = result
                    
        except asyncio.TimeoutError:
            logger.error(f"Scan timed out after {self.config.timeout_seconds}s")
            self._add_error({
                'error': 'Scan timeout',
                'timeout_seconds': self.config.timeout_seconds
            })
        
        return {
            'results': results,
            'progress': self.progress.to_dict()
        }
    
    async def _scan_account_wrapper(
        self,
        account: Dict[str, Any],
        scan_function: Callable,
        **kwargs
    ) -> Any:
        """Wrapper for scanning a single account with concurrency control"""
        async with self._account_semaphore:
            account_id = account.get('id', account.get('account_id', 'unknown'))
            logger.info(f"Starting scan for account {account_id}")
            
            try:
                # Check if scan_function is async
                if asyncio.iscoroutinefunction(scan_function):
                    result = await scan_function(account, **kwargs)
                else:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, 
                        lambda: scan_function(account, **kwargs)
                    )
                
                self._update_progress('completed_accounts')
                return result
                
            except Exception as e:
                logger.error(f"Error scanning account {account_id}: {e}")
                self._add_error({
                    'account_id': account_id,
                    'error': str(e),
                    'type': type(e).__name__
                })
                raise


# ============================================================================
# MULTI-REGION ASYNC SCANNER
# ============================================================================

class MultiRegionAsyncScanner(AsyncScanner):
    """
    Async scanner for multi-region operations within a single account.
    """
    
    async def scan_regions(
        self,
        session,  # boto3 Session
        regions: List[str],
        scan_function: Callable,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scan multiple regions concurrently.
        
        Args:
            session: boto3 Session object
            regions: List of region names
            scan_function: Function to call for each region
            **kwargs: Additional arguments for scan_function
            
        Returns:
            Results keyed by region
        """
        await self._init_semaphores()
        
        self.progress.total_regions = len(regions)
        
        tasks = [
            self._scan_region_wrapper(session, region, scan_function, **kwargs)
            for region in regions
        ]
        
        results = {}
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for region, result in zip(regions, completed):
            if isinstance(result, Exception):
                self._add_error({
                    'region': region,
                    'error': str(result)
                })
                results[region] = {'error': str(result)}
            else:
                results[region] = result
        
        return results
    
    async def _scan_region_wrapper(
        self,
        session,
        region: str,
        scan_function: Callable,
        **kwargs
    ) -> Any:
        """Wrapper for scanning a single region"""
        async with self._region_semaphore:
            try:
                if asyncio.iscoroutinefunction(scan_function):
                    result = await scan_function(session, region, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: scan_function(session, region, **kwargs)
                    )
                
                self._update_progress('completed_regions')
                return result
                
            except Exception as e:
                logger.error(f"Error scanning region {region}: {e}")
                raise


# ============================================================================
# SERVICE SCANNER
# ============================================================================

class ServiceAsyncScanner(AsyncScanner):
    """
    Async scanner for multiple AWS services.
    """
    
    async def scan_services(
        self,
        session,
        region: str,
        services: List[str],
        scan_functions: Dict[str, Callable],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Scan multiple services concurrently.
        
        Args:
            session: boto3 Session
            region: AWS region
            services: List of service names to scan
            scan_functions: Dict mapping service name to scan function
            **kwargs: Additional arguments
            
        Returns:
            Results keyed by service
        """
        await self._init_semaphores()
        
        self.progress.total_services = len(services)
        
        tasks = []
        for service in services:
            if service in scan_functions:
                tasks.append(
                    self._scan_service_wrapper(
                        session, region, service, 
                        scan_functions[service], **kwargs
                    )
                )
        
        results = {}
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for service, result in zip(services, completed):
            if isinstance(result, Exception):
                results[service] = {'error': str(result)}
            else:
                results[service] = result
        
        return results
    
    async def _scan_service_wrapper(
        self,
        session,
        region: str,
        service: str,
        scan_function: Callable,
        **kwargs
    ) -> Any:
        """Wrapper for scanning a single service"""
        async with self._service_semaphore:
            await asyncio.sleep(self.config.api_call_delay)
            
            try:
                if asyncio.iscoroutinefunction(scan_function):
                    result = await scan_function(session, region, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: scan_function(session, region, **kwargs)
                    )
                
                self._update_progress('completed_services')
                return result
                
            except Exception as e:
                logger.error(f"Error scanning service {service}: {e}")
                raise


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def run_async(coro: Coroutine) -> Any:
    """
    Run an async coroutine from sync code.
    
    Handles event loop creation/reuse appropriately.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, use nest_asyncio pattern
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create one
        return asyncio.run(coro)


def async_scan_accounts(
    accounts: List[Dict[str, Any]],
    scan_function: Callable,
    config: AsyncConfig = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to scan multiple accounts asynchronously.
    
    Args:
        accounts: List of account configurations
        scan_function: Function to scan each account
        config: Async configuration
        **kwargs: Additional arguments
        
    Returns:
        Aggregated scan results
    """
    scanner = AsyncScanner(config)
    return run_async(scanner.scan_accounts(accounts, scan_function, **kwargs))


def async_scan_regions(
    session,
    regions: List[str],
    scan_function: Callable,
    config: AsyncConfig = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to scan multiple regions asynchronously.
    """
    scanner = MultiRegionAsyncScanner(config)
    return run_async(scanner.scan_regions(session, regions, scan_function, **kwargs))


# ============================================================================
# DECORATOR FOR ASYNC AWS CALLS
# ============================================================================

def async_aws_call(max_concurrent: int = 10, delay: float = 0.1):
    """
    Decorator to make AWS calls async-friendly with rate limiting.
    
    Usage:
        @async_aws_call(max_concurrent=5)
        def describe_instances(ec2_client, region):
            return ec2_client.describe_instances()
    """
    def decorator(func):
        semaphore = asyncio.Semaphore(max_concurrent)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                await asyncio.sleep(delay)
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        
        return wrapper
    return decorator


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AsyncConfig',
    'ScanProgress',
    'AsyncScanner',
    'MultiRegionAsyncScanner',
    'ServiceAsyncScanner',
    'run_async',
    'async_scan_accounts',
    'async_scan_regions',
    'async_aws_call',
]
