"""
Enhanced AWS Connector for Production
=====================================
Production-ready AWS connector with proper error handling, retry logic,
and integration with the new utility modules.

This replaces/enhances the existing aws_connector.py functionality.
"""

import os
import time
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

# Import new utility modules
from logging_config import get_logger, log_exception, log_aws_operation
from aws_utils import (
    AWSClient, AWSClientConfig, retry_with_backoff,
    handle_aws_error, is_access_denied, get_all_regions, get_account_id
)
from validation import validate_aws_account_id, validate_region, validate_role_arn

logger = get_logger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AWSConnectionConfig:
    """Configuration for AWS connection"""
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    session_token: Optional[str] = None
    region: str = 'us-east-1'
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    profile_name: Optional[str] = None
    session_duration: int = 3600
    
    @classmethod
    def from_streamlit_secrets(cls) -> 'AWSConnectionConfig':
        """Create configuration from Streamlit secrets"""
        try:
            aws_secrets = st.secrets.get('aws', {})
            return cls(
                access_key_id=aws_secrets.get('access_key_id'),
                secret_access_key=aws_secrets.get('secret_access_key'),
                session_token=aws_secrets.get('session_token'),
                region=aws_secrets.get('default_region', 'us-east-1'),
                role_arn=aws_secrets.get('role_arn'),
                external_id=aws_secrets.get('external_id'),
                profile_name=aws_secrets.get('profile'),
            )
        except Exception as e:
            logger.debug(f"Could not load from Streamlit secrets: {e}")
            return cls()
    
    @classmethod
    def from_environment(cls) -> 'AWSConnectionConfig':
        """Create configuration from environment variables"""
        return cls(
            access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
            secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
            session_token=os.environ.get('AWS_SESSION_TOKEN'),
            region=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            role_arn=os.environ.get('AWS_ROLE_ARN'),
            external_id=os.environ.get('AWS_EXTERNAL_ID'),
            profile_name=os.environ.get('AWS_PROFILE'),
        )


# ============================================================================
# CONNECTION RESULT
# ============================================================================

@dataclass
class ConnectionResult:
    """Result of an AWS connection attempt"""
    success: bool
    session: Optional[boto3.Session] = None
    account_id: Optional[str] = None
    identity_arn: Optional[str] = None
    user_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    regions_available: List[str] = None
    
    def __post_init__(self):
        if self.regions_available is None:
            self.regions_available = []


# ============================================================================
# PRODUCTION AWS CONNECTOR
# ============================================================================

class ProductionAWSConnector:
    """
    Production-ready AWS connector with comprehensive error handling.
    
    Features:
    - Multiple credential sources (secrets, env vars, profiles, IAM roles)
    - Automatic retry with exponential backoff
    - Session caching
    - Connection validation
    - Multi-account support via AssumeRole
    """
    
    # Session cache
    _session_cache: Dict[str, Tuple[boto3.Session, float]] = {}
    _cache_ttl: int = 300  # 5 minutes
    
    def __init__(self, config: AWSConnectionConfig = None):
        """
        Initialize the connector.
        
        Args:
            config: AWS connection configuration
        """
        self.config = config or self._load_config()
        self._session: Optional[boto3.Session] = None
        self._account_id: Optional[str] = None
        self._aws_client: Optional[AWSClient] = None
    
    def _load_config(self) -> AWSConnectionConfig:
        """Load configuration from available sources"""
        # Try Streamlit secrets first
        config = AWSConnectionConfig.from_streamlit_secrets()
        
        # Fall back to environment variables
        if not config.access_key_id:
            config = AWSConnectionConfig.from_environment()
        
        return config
    
    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def connect(self) -> ConnectionResult:
        """
        Establish AWS connection with automatic credential discovery.
        
        Returns:
            ConnectionResult with session and identity information
        """
        logger.info("Attempting AWS connection...")
        
        try:
            # Build session based on available credentials
            session = self._create_session()
            
            if session is None:
                return ConnectionResult(
                    success=False,
                    error_message="Could not create AWS session. Check credentials."
                )
            
            # Validate session by getting caller identity
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            account_id = identity['Account']
            user_id = identity['UserId']
            identity_arn = identity['Arn']
            
            logger.info(f"Connected to AWS account {account_id}")
            log_aws_operation(logger, 'get_caller_identity', 'sts', account_id=account_id)
            
            # Get available regions
            regions = get_all_regions(session)
            
            # Cache the session
            self._session = session
            self._account_id = account_id
            self._aws_client = AWSClient(session, AWSClientConfig())
            
            return ConnectionResult(
                success=True,
                session=session,
                account_id=account_id,
                identity_arn=identity_arn,
                user_id=user_id,
                regions_available=regions
            )
            
        except NoCredentialsError:
            logger.warning("No AWS credentials found")
            return ConnectionResult(
                success=False,
                error_message="No AWS credentials found. Please configure credentials.",
                error_code="NoCredentialsError"
            )
            
        except ClientError as e:
            error_info = handle_aws_error(e, "AWS connection")
            return ConnectionResult(
                success=False,
                error_message=error_info['aws_error_message'],
                error_code=error_info['aws_error_code']
            )
            
        except Exception as e:
            log_exception(logger, "AWS connection failed", e)
            return ConnectionResult(
                success=False,
                error_message=str(e),
                error_code=type(e).__name__
            )
    
    def _create_session(self) -> Optional[boto3.Session]:
        """Create boto3 session based on configuration"""
        
        # Check cache first
        cache_key = self._get_cache_key()
        if cache_key in self._session_cache:
            session, timestamp = self._session_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug("Using cached AWS session")
                return session
        
        session = None
        
        # Try explicit credentials
        if self.config.access_key_id and self.config.secret_access_key:
            logger.debug("Creating session with explicit credentials")
            session = boto3.Session(
                aws_access_key_id=self.config.access_key_id,
                aws_secret_access_key=self.config.secret_access_key,
                aws_session_token=self.config.session_token,
                region_name=self.config.region
            )
        
        # Try profile
        elif self.config.profile_name:
            logger.debug(f"Creating session with profile: {self.config.profile_name}")
            try:
                session = boto3.Session(
                    profile_name=self.config.profile_name,
                    region_name=self.config.region
                )
            except ProfileNotFound:
                logger.warning(f"Profile '{self.config.profile_name}' not found")
        
        # Try default credential chain
        else:
            logger.debug("Creating session with default credential chain")
            session = boto3.Session(region_name=self.config.region)
        
        # Handle AssumeRole if configured
        if session and self.config.role_arn:
            session = self._assume_role(session)
        
        # Cache the session
        if session:
            self._session_cache[cache_key] = (session, time.time())
        
        return session
    
    def _assume_role(self, base_session: boto3.Session) -> Optional[boto3.Session]:
        """Assume an IAM role and return new session"""
        
        # Validate role ARN
        validation = validate_role_arn(self.config.role_arn)
        if not validation.is_valid:
            logger.error(f"Invalid role ARN: {validation.errors}")
            return None
        
        logger.info(f"Assuming role: {self.config.role_arn}")
        
        try:
            sts = base_session.client('sts')
            
            assume_params = {
                'RoleArn': self.config.role_arn,
                'RoleSessionName': f'WAFScanner-{int(time.time())}',
                'DurationSeconds': self.config.session_duration
            }
            
            if self.config.external_id:
                assume_params['ExternalId'] = self.config.external_id
            
            response = sts.assume_role(**assume_params)
            credentials = response['Credentials']
            
            return boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=self.config.region
            )
            
        except ClientError as e:
            error_info = handle_aws_error(e, "AssumeRole", self.config.role_arn)
            logger.error(f"Failed to assume role: {error_info['aws_error_message']}")
            return None
    
    def _get_cache_key(self) -> str:
        """Generate cache key for session"""
        components = [
            self.config.access_key_id or 'default',
            self.config.profile_name or 'none',
            self.config.role_arn or 'none',
            self.config.region
        ]
        return ':'.join(components)
    
    @property
    def session(self) -> Optional[boto3.Session]:
        """Get the current AWS session"""
        return self._session
    
    @property
    def account_id(self) -> Optional[str]:
        """Get the current AWS account ID"""
        return self._account_id
    
    @property
    def client(self) -> Optional[AWSClient]:
        """Get the AWS client wrapper"""
        return self._aws_client
    
    def get_client(self, service: str, region: str = None):
        """
        Get a boto3 client for the specified service.
        
        Args:
            service: AWS service name
            region: AWS region (uses default if None)
        """
        if self._aws_client:
            return self._aws_client.get_client(service, region)
        elif self._session:
            return self._session.client(service, region_name=region)
        return None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the AWS connection and return diagnostic information.
        
        Returns:
            Dictionary with connection test results
        """
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'connected': False,
            'account_id': None,
            'identity': None,
            'region': self.config.region,
            'services_tested': {},
            'errors': []
        }
        
        try:
            conn = self.connect()
            
            if not conn.success:
                result['errors'].append(conn.error_message)
                return result
            
            result['connected'] = True
            result['account_id'] = conn.account_id
            result['identity'] = conn.identity_arn
            result['regions_available'] = len(conn.regions_available)
            
            # Test key services
            services_to_test = ['ec2', 's3', 'iam', 'cloudwatch']
            
            for service in services_to_test:
                try:
                    client = self.get_client(service)
                    
                    # Simple operation to test connectivity
                    if service == 'ec2':
                        client.describe_regions(DryRun=False)
                    elif service == 's3':
                        client.list_buckets()
                    elif service == 'iam':
                        client.get_account_summary()
                    elif service == 'cloudwatch':
                        client.list_dashboards()
                    
                    result['services_tested'][service] = 'OK'
                    
                except ClientError as e:
                    if is_access_denied(e):
                        result['services_tested'][service] = 'ACCESS_DENIED'
                    else:
                        result['services_tested'][service] = f'ERROR: {e.response["Error"]["Code"]}'
                        
        except Exception as e:
            result['errors'].append(str(e))
        
        return result
    
    @classmethod
    def clear_cache(cls):
        """Clear the session cache"""
        cls._session_cache.clear()
        logger.info("AWS session cache cleared")


# ============================================================================
# MULTI-ACCOUNT CONNECTOR
# ============================================================================

class MultiAccountConnector:
    """
    Connector for multi-account AWS environments.
    
    Supports:
    - AWS Organizations
    - Multiple AssumeRole configurations
    - Parallel account scanning
    """
    
    def __init__(self, base_connector: ProductionAWSConnector):
        """
        Initialize multi-account connector.
        
        Args:
            base_connector: Base connector with management account credentials
        """
        self.base_connector = base_connector
        self._account_sessions: Dict[str, boto3.Session] = {}
    
    def connect_to_account(
        self,
        account_id: str,
        role_name: str = 'WAFScannerRole',
        external_id: str = None
    ) -> ConnectionResult:
        """
        Connect to a specific AWS account via AssumeRole.
        
        Args:
            account_id: Target AWS account ID
            role_name: Name of the role to assume
            external_id: External ID for role assumption
            
        Returns:
            ConnectionResult for the target account
        """
        # Validate account ID
        validation = validate_aws_account_id(account_id)
        if not validation.is_valid:
            return ConnectionResult(
                success=False,
                error_message=f"Invalid account ID: {validation.errors}"
            )
        
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        
        logger.info(f"Connecting to account {account_id}")
        
        # Create new connector for target account
        config = AWSConnectionConfig(
            access_key_id=self.base_connector.config.access_key_id,
            secret_access_key=self.base_connector.config.secret_access_key,
            session_token=self.base_connector.config.session_token,
            region=self.base_connector.config.region,
            role_arn=role_arn,
            external_id=external_id
        )
        
        target_connector = ProductionAWSConnector(config)
        result = target_connector.connect()
        
        if result.success:
            self._account_sessions[account_id] = result.session
        
        return result
    
    def get_session_for_account(self, account_id: str) -> Optional[boto3.Session]:
        """Get cached session for an account"""
        return self._account_sessions.get(account_id)
    
    def list_organization_accounts(self) -> List[Dict[str, str]]:
        """List all accounts in the AWS Organization"""
        accounts = []
        
        if not self.base_connector.session:
            logger.warning("Base connector not connected")
            return accounts
        
        try:
            org_client = self.base_connector.get_client('organizations')
            
            paginator = org_client.get_paginator('list_accounts')
            for page in paginator.paginate():
                for account in page.get('Accounts', []):
                    if account['Status'] == 'ACTIVE':
                        accounts.append({
                            'id': account['Id'],
                            'name': account['Name'],
                            'email': account['Email'],
                            'status': account['Status']
                        })
            
            logger.info(f"Found {len(accounts)} accounts in organization")
            
        except ClientError as e:
            if is_access_denied(e):
                logger.warning("No access to AWS Organizations")
            else:
                log_exception(logger, "Failed to list organization accounts", e)
        
        return accounts


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global connector instance
_connector: Optional[ProductionAWSConnector] = None


def get_aws_connector() -> ProductionAWSConnector:
    """Get or create the global AWS connector"""
    global _connector
    if _connector is None:
        _connector = ProductionAWSConnector()
    return _connector


def get_aws_session() -> Optional[boto3.Session]:
    """Get the current AWS session (compatibility function)"""
    connector = get_aws_connector()
    if connector.session is None:
        connector.connect()
    return connector.session


def test_aws_connection() -> Tuple[bool, str]:
    """
    Test AWS connection (compatibility function).
    
    Returns:
        Tuple of (success, message)
    """
    connector = get_aws_connector()
    result = connector.connect()
    
    if result.success:
        return True, f"Connected to AWS account {result.account_id}"
    else:
        return False, result.error_message or "Connection failed"


def reset_aws_connection():
    """Reset the AWS connection"""
    global _connector
    if _connector:
        ProductionAWSConnector.clear_cache()
    _connector = None
    logger.info("AWS connection reset")


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AWSConnectionConfig',
    'ConnectionResult',
    'ProductionAWSConnector',
    'MultiAccountConnector',
    'get_aws_connector',
    'get_aws_session',
    'test_aws_connection',
    'reset_aws_connection',
]
