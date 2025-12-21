"""
AWS Utilities Module for AWS WAF Scanner Enterprise
====================================================
Provides standardized AWS operations with:
- Retry logic with exponential backoff
- Proper pagination handling
- Consistent error handling
- Rate limiting support

Usage:
    from aws_utils import AWSClient, retry_with_backoff, paginate_aws_call
"""

import time
import functools
from typing import Dict, List, Optional, Any, Callable, Generator
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, BotoCoreError, EndpointConnectionError
from botocore.config import Config

from logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds
DEFAULT_TIMEOUT = 30  # seconds

# Retryable error codes
RETRYABLE_ERROR_CODES = {
    'ThrottlingException',
    'Throttling',
    'TooManyRequestsException',
    'RequestLimitExceeded',
    'ProvisionedThroughputExceededException',
    'ServiceUnavailable',
    'InternalError',
    'InternalServiceError',
    'RequestTimeout',
    'RequestTimeoutException',
}

# ============================================================================
# RETRY DECORATOR
# ============================================================================

def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_exceptions: tuple = (ClientError, EndpointConnectionError),
    retryable_error_codes: set = None
):
    """
    Decorator for retrying AWS operations with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retryable_exceptions: Tuple of exception types to retry
        retryable_error_codes: Set of AWS error codes to retry
    
    Usage:
        @retry_with_backoff(max_retries=3)
        def my_aws_operation():
            ...
    """
    if retryable_error_codes is None:
        retryable_error_codes = RETRYABLE_ERROR_CODES
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    # Check if error code is retryable
                    error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
                    
                    if isinstance(e, ClientError) and error_code not in retryable_error_codes:
                        logger.error(f"Non-retryable AWS error: {error_code}")
                        raise
                    
                    if attempt < max_retries:
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s delay. Error: {str(e)[:100]}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Max retries exceeded for {func.__name__}")
                        raise
                        
                except Exception as e:
                    logger.error(f"Non-retryable error in {func.__name__}: {type(e).__name__}: {e}")
                    raise
            
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================================
# PAGINATION HELPER
# ============================================================================

def paginate_aws_call(
    client_method: Callable,
    result_key: str,
    page_size: int = 100,
    **kwargs
) -> Generator[Any, None, None]:
    """
    Generator that handles AWS API pagination automatically.
    
    Args:
        client_method: The boto3 client method to call
        result_key: The key in the response containing the results
        page_size: Number of items per page
        **kwargs: Additional arguments to pass to the API call
    
    Yields:
        Individual items from paginated results
        
    Usage:
        for instance in paginate_aws_call(ec2.describe_instances, 'Reservations'):
            process(instance)
    """
    next_token = None
    
    while True:
        try:
            # Build request parameters
            params = dict(kwargs)
            if page_size:
                # Different services use different parameter names
                if 'MaxResults' not in params:
                    params['MaxResults'] = page_size
            
            if next_token:
                params['NextToken'] = next_token
            
            # Make the API call
            response = client_method(**params)
            
            # Yield results
            items = response.get(result_key, [])
            for item in items:
                yield item
            
            # Check for more pages
            next_token = response.get('NextToken')
            if not next_token:
                break
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            logger.error(f"Pagination error: {error_code} - {e}")
            raise


def paginate_with_marker(
    client_method: Callable,
    result_key: str,
    marker_key: str = 'Marker',
    **kwargs
) -> Generator[Any, None, None]:
    """
    Generator for AWS APIs that use Marker-based pagination (e.g., IAM).
    
    Args:
        client_method: The boto3 client method to call
        result_key: The key in the response containing the results
        marker_key: The key name for the pagination marker
        **kwargs: Additional arguments to pass to the API call
    """
    marker = None
    
    while True:
        params = dict(kwargs)
        if marker:
            params[marker_key] = marker
        
        response = client_method(**params)
        
        items = response.get(result_key, [])
        for item in items:
            yield item
        
        if not response.get('IsTruncated', False):
            break
        
        marker = response.get(marker_key) or response.get('NextMarker')
        if not marker:
            break


# ============================================================================
# AWS CLIENT WRAPPER
# ============================================================================

@dataclass
class AWSClientConfig:
    """Configuration for AWS client"""
    max_retries: int = DEFAULT_MAX_RETRIES
    timeout: int = DEFAULT_TIMEOUT
    max_pool_connections: int = 25


class AWSClient:
    """
    Wrapper for boto3 clients with built-in retry and error handling.
    
    Usage:
        aws = AWSClient(session)
        ec2 = aws.get_client('ec2', region='us-east-1')
        
        # With retry
        instances = aws.call_with_retry(
            ec2.describe_instances,
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
    """
    
    def __init__(self, session: boto3.Session = None, config: AWSClientConfig = None):
        """
        Initialize AWS client wrapper.
        
        Args:
            session: boto3 Session (creates default if None)
            config: Client configuration
        """
        self.session = session or boto3.Session()
        self.config = config or AWSClientConfig()
        self._clients = {}
        
        # Create boto3 config
        self._boto_config = Config(
            retries={
                'max_attempts': self.config.max_retries,
                'mode': 'adaptive'
            },
            connect_timeout=self.config.timeout,
            read_timeout=self.config.timeout,
            max_pool_connections=self.config.max_pool_connections
        )
    
    def get_client(self, service: str, region: str = None):
        """
        Get or create a boto3 client for the specified service.
        
        Args:
            service: AWS service name (e.g., 'ec2', 's3')
            region: AWS region (uses session default if None)
            
        Returns:
            boto3 client instance
        """
        cache_key = f"{service}:{region or 'default'}"
        
        if cache_key not in self._clients:
            kwargs = {'config': self._boto_config}
            if region:
                kwargs['region_name'] = region
            
            self._clients[cache_key] = self.session.client(service, **kwargs)
            logger.debug(f"Created client for {service} in {region or 'default region'}")
        
        return self._clients[cache_key]
    
    def get_resource(self, service: str, region: str = None):
        """Get a boto3 resource for the specified service."""
        kwargs = {'config': self._boto_config}
        if region:
            kwargs['region_name'] = region
        return self.session.resource(service, **kwargs)
    
    @retry_with_backoff()
    def call_with_retry(self, method: Callable, **kwargs) -> Any:
        """
        Call an AWS API method with automatic retry.
        
        Args:
            method: The boto3 client method to call
            **kwargs: Arguments to pass to the method
            
        Returns:
            API response
        """
        return method(**kwargs)
    
    def paginate(self, method: Callable, result_key: str, **kwargs) -> List[Any]:
        """
        Call an AWS API with pagination and return all results.
        
        Args:
            method: The boto3 client method to call
            result_key: The key in the response containing results
            **kwargs: Arguments to pass to the method
            
        Returns:
            List of all items from all pages
        """
        return list(paginate_aws_call(method, result_key, **kwargs))
    
    def safe_call(self, method: Callable, default: Any = None, **kwargs) -> Any:
        """
        Call an AWS API method, returning default on error.
        
        Args:
            method: The boto3 client method to call
            default: Value to return on error
            **kwargs: Arguments to pass to the method
            
        Returns:
            API response or default value
        """
        try:
            return self.call_with_retry(method, **kwargs)
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            logger.warning(f"AWS call failed ({error_code}), returning default")
            return default
        except Exception as e:
            logger.warning(f"AWS call failed ({type(e).__name__}), returning default")
            return default


# ============================================================================
# EXCEPTION HANDLING HELPERS
# ============================================================================

def handle_aws_error(e: Exception, operation: str, resource: str = None) -> Dict[str, Any]:
    """
    Standardized AWS error handling that returns a structured error dict.
    
    Args:
        e: The exception that was raised
        operation: Description of the operation that failed
        resource: Optional resource identifier
        
    Returns:
        Dictionary with error details
    """
    error_info = {
        'success': False,
        'operation': operation,
        'error_type': type(e).__name__,
        'error_message': str(e),
    }
    
    if resource:
        error_info['resource'] = resource
    
    if isinstance(e, ClientError):
        error_info['aws_error_code'] = e.response.get('Error', {}).get('Code', 'Unknown')
        error_info['aws_error_message'] = e.response.get('Error', {}).get('Message', str(e))
        error_info['request_id'] = e.response.get('ResponseMetadata', {}).get('RequestId')
    
    logger.error(f"AWS Error: {operation} - {error_info.get('aws_error_code', type(e).__name__)}: {e}")
    
    return error_info


def is_access_denied(e: Exception) -> bool:
    """Check if an exception is an access denied error."""
    if isinstance(e, ClientError):
        error_code = e.response.get('Error', {}).get('Code', '')
        return error_code in ('AccessDenied', 'AccessDeniedException', 'UnauthorizedAccess')
    return False


def is_not_found(e: Exception) -> bool:
    """Check if an exception is a resource not found error."""
    if isinstance(e, ClientError):
        error_code = e.response.get('Error', {}).get('Code', '')
        return 'NotFound' in error_code or error_code in ('NoSuchEntity', 'ResourceNotFoundException')
    return False


def is_throttling(e: Exception) -> bool:
    """Check if an exception is a throttling error."""
    if isinstance(e, ClientError):
        error_code = e.response.get('Error', {}).get('Code', '')
        return error_code in RETRYABLE_ERROR_CODES
    return False


# ============================================================================
# REGION HELPERS
# ============================================================================

def get_all_regions(session: boto3.Session = None) -> List[str]:
    """Get list of all available AWS regions."""
    session = session or boto3.Session()
    ec2 = session.client('ec2', region_name='us-east-1')
    
    try:
        response = ec2.describe_regions(AllRegions=False)
        return [r['RegionName'] for r in response.get('Regions', [])]
    except ClientError as e:
        logger.error(f"Failed to get regions: {e}")
        # Return common regions as fallback
        return [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
        ]


def get_account_id(session: boto3.Session = None) -> Optional[str]:
    """Get the AWS account ID for the current session."""
    session = session or boto3.Session()
    
    try:
        sts = session.client('sts')
        return sts.get_caller_identity()['Account']
    except ClientError as e:
        logger.error(f"Failed to get account ID: {e}")
        return None


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'retry_with_backoff',
    'paginate_aws_call',
    'paginate_with_marker',
    'AWSClient',
    'AWSClientConfig',
    'handle_aws_error',
    'is_access_denied',
    'is_not_found',
    'is_throttling',
    'get_all_regions',
    'get_account_id',
]
