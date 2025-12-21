"""
Centralized Application Configuration
======================================
Single source of truth for all application configuration.

Usage:
    from app_config import config, get_config
    
    api_key = config.anthropic_api_key
    is_demo = config.demo_mode
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import streamlit as st

from logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class Environment(Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class AuthProvider(Enum):
    """Authentication provider"""
    NONE = "none"
    FIREBASE = "firebase"
    AZURE_AD = "azure_ad"


class DatabaseBackend(Enum):
    """Database backend type"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FIREBASE = "firebase"
    FIRESTORE = "firestore"


# ============================================================================
# CONFIGURATION CLASS
# ============================================================================

@dataclass
class AppConfig:
    """
    Application configuration with environment variable and secrets support.
    
    Configuration is loaded in priority order:
    1. Streamlit secrets
    2. Environment variables
    3. Default values
    """
    
    # Application settings
    app_name: str = "AWS WAF Scanner Enterprise"
    app_version: str = "5.0.0"
    environment: Environment = Environment.PRODUCTION
    debug: bool = False
    
    # Demo mode
    demo_mode: bool = False
    default_to_demo: bool = False
    
    # Authentication
    auth_provider: AuthProvider = AuthProvider.FIREBASE
    require_auth: bool = True
    allow_guest_mode: bool = False
    
    # Database
    db_backend: DatabaseBackend = DatabaseBackend.SQLITE
    sqlite_path: str = "data/waf_scanner.db"
    
    # AWS settings
    aws_default_region: str = "us-east-1"
    aws_regions: List[str] = field(default_factory=lambda: [
        "us-east-1", "us-east-2", "us-west-1", "us-west-2",
        "eu-west-1", "eu-west-2", "eu-central-1",
        "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
    ])
    aws_scan_timeout: int = 300  # seconds
    aws_max_retries: int = 3
    
    # AI settings
    anthropic_api_key: Optional[str] = None
    ai_model: str = "claude-3-sonnet-20240229"
    ai_max_tokens: int = 4096
    ai_temperature: float = 0.3
    
    # Firebase settings
    firebase_api_key: Optional[str] = None
    firebase_project_id: Optional[str] = None
    firebase_auth_domain: Optional[str] = None
    firebase_database_url: Optional[str] = None
    
    # Azure AD settings
    azure_client_id: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    
    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        'ai_insights': True,
        'pdf_reports': True,
        'multi_account': True,
        'security_hub': True,
        'architecture_designer': True,
        'unified_workflow': True,
        'dark_mode': False,
    })
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "logs"
    
    # Limits
    max_findings_per_scan: int = 1000
    max_accounts: int = 100
    max_concurrent_scans: int = 5
    session_timeout_minutes: int = 60
    
    def __post_init__(self):
        """Load configuration from environment and secrets"""
        self._load_from_secrets()
        self._load_from_env()
        self._validate()
    
    def _load_from_secrets(self):
        """Load configuration from Streamlit secrets"""
        try:
            secrets = st.secrets
            
            # App settings
            if 'app' in secrets:
                self.require_auth = secrets.app.get('require_auth', self.require_auth)
                self.allow_guest_mode = secrets.app.get('allow_guest_mode', self.allow_guest_mode)
                self.default_to_demo = secrets.app.get('default_to_demo', self.default_to_demo)
            
            # Anthropic API key
            if 'ANTHROPIC_API_KEY' in secrets:
                self.anthropic_api_key = secrets.ANTHROPIC_API_KEY
            elif 'anthropic' in secrets:
                self.anthropic_api_key = secrets.anthropic.get('api_key')
            
            # AWS settings
            if 'aws' in secrets:
                self.aws_default_region = secrets.aws.get('default_region', self.aws_default_region)
            
            # Firebase settings
            if 'firebase' in secrets:
                self.firebase_api_key = secrets.firebase.get('api_key')
                self.firebase_project_id = secrets.firebase.get('project_id')
                if 'web_config' in secrets.firebase:
                    self.firebase_auth_domain = secrets.firebase.web_config.get('authDomain')
                    self.firebase_database_url = secrets.firebase.web_config.get('databaseURL')
            
            # Azure AD settings
            if 'azure' in secrets:
                self.azure_client_id = secrets.azure.get('client_id')
                self.azure_tenant_id = secrets.azure.get('tenant_id')
                self.azure_client_secret = secrets.azure.get('client_secret')
            
            logger.debug("Loaded configuration from Streamlit secrets")
            
        except Exception as e:
            logger.debug(f"Could not load from secrets: {e}")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Environment
        env_str = os.environ.get('APP_ENV', 'production').lower()
        if env_str in [e.value for e in Environment]:
            self.environment = Environment(env_str)
        
        self.debug = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes')
        
        # Demo mode
        self.demo_mode = os.environ.get('DEMO_MODE', '').lower() in ('true', '1', 'yes')
        
        # API keys (environment overrides secrets)
        if os.environ.get('ANTHROPIC_API_KEY'):
            self.anthropic_api_key = os.environ['ANTHROPIC_API_KEY']
        
        # AWS
        if os.environ.get('AWS_DEFAULT_REGION'):
            self.aws_default_region = os.environ['AWS_DEFAULT_REGION']
        
        # Database
        if os.environ.get('DB_BACKEND'):
            db_str = os.environ['DB_BACKEND'].lower()
            if db_str in [b.value for b in DatabaseBackend]:
                self.db_backend = DatabaseBackend(db_str)
        
        if os.environ.get('SQLITE_PATH'):
            self.sqlite_path = os.environ['SQLITE_PATH']
        
        # Logging
        if os.environ.get('LOG_LEVEL'):
            self.log_level = os.environ['LOG_LEVEL'].upper()
        
        if os.environ.get('LOG_DIR'):
            self.log_dir = os.environ['LOG_DIR']
        
        logger.debug("Loaded configuration from environment variables")
    
    def _validate(self):
        """Validate configuration"""
        errors = []
        
        # Check required settings for production
        if self.environment == Environment.PRODUCTION:
            if self.debug:
                logger.warning("Debug mode enabled in production")
            
            if not self.require_auth and not self.demo_mode:
                logger.warning("Authentication disabled in production without demo mode")
        
        # Validate AI settings
        if self.features.get('ai_insights') and not self.anthropic_api_key:
            logger.warning("AI insights enabled but no API key configured")
        
        # Validate Firebase settings
        if self.auth_provider == AuthProvider.FIREBASE:
            if not self.firebase_api_key:
                logger.warning("Firebase auth configured but no API key")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature, False)
    
    def get_aws_session_config(self) -> Dict[str, Any]:
        """Get boto3 session configuration"""
        return {
            'region_name': self.aws_default_region,
            'retries': {
                'max_attempts': self.aws_max_retries,
                'mode': 'adaptive'
            }
        }
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI configuration for API calls"""
        return {
            'api_key': self.anthropic_api_key,
            'model': self.ai_model,
            'max_tokens': self.ai_max_tokens,
            'temperature': self.ai_temperature,
        }
    
    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Convert to dictionary (optionally excluding secrets)"""
        data = {
            'app_name': self.app_name,
            'app_version': self.app_version,
            'environment': self.environment.value,
            'debug': self.debug,
            'demo_mode': self.demo_mode,
            'auth_provider': self.auth_provider.value,
            'require_auth': self.require_auth,
            'db_backend': self.db_backend.value,
            'aws_default_region': self.aws_default_region,
            'features': self.features,
            'log_level': self.log_level,
        }
        
        if include_secrets:
            data['anthropic_api_key'] = self.anthropic_api_key
            data['firebase_api_key'] = self.firebase_api_key
        
        return data


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the singleton configuration instance"""
    global _config_instance
    
    if _config_instance is None:
        _config_instance = AppConfig()
        logger.info(f"Configuration loaded: {_config_instance.environment.value} mode")
    
    return _config_instance


def reset_config():
    """Reset configuration (for testing)"""
    global _config_instance
    _config_instance = None


# Convenience alias
config = get_config()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'Environment',
    'AuthProvider', 
    'DatabaseBackend',
    'AppConfig',
    'get_config',
    'reset_config',
    'config',
]
