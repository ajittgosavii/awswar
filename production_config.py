"""
Production Configuration Module
================================
Centralized configuration management for AWS WAF Scanner Enterprise.

All application settings are managed through this module to ensure
consistency and easy configuration across environments.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json

from logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# ENVIRONMENT
# ============================================================================

class Environment(Enum):
    """Application environment"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


def get_environment() -> Environment:
    """Determine current environment"""
    env_str = os.environ.get('APP_ENVIRONMENT', 'development').lower()
    
    env_map = {
        'development': Environment.DEVELOPMENT,
        'dev': Environment.DEVELOPMENT,
        'staging': Environment.STAGING,
        'stage': Environment.STAGING,
        'production': Environment.PRODUCTION,
        'prod': Environment.PRODUCTION,
        'testing': Environment.TESTING,
        'test': Environment.TESTING,
    }
    
    return env_map.get(env_str, Environment.DEVELOPMENT)


# ============================================================================
# CONFIGURATION CLASSES
# ============================================================================

@dataclass
class AppConfig:
    """Main application configuration"""
    
    # Application
    app_name: str = "AWS WAF Scanner Enterprise"
    app_version: str = "5.0.0"
    environment: Environment = field(default_factory=get_environment)
    debug: bool = False
    
    # Features
    demo_mode_enabled: bool = True
    ai_features_enabled: bool = True
    multi_account_enabled: bool = True
    authentication_required: bool = False
    
    # UI Settings
    theme_primary_color: str = "#007CC3"  # Infosys Blue
    show_debug_info: bool = False
    max_upload_size_mb: int = 200
    
    # Performance
    cache_ttl_seconds: int = 300
    max_concurrent_scans: int = 5
    scan_timeout_seconds: int = 600
    
    # Limits
    max_accounts_per_scan: int = 50
    max_regions_per_scan: int = 20
    max_findings_display: int = 1000
    
    def __post_init__(self):
        # Set debug based on environment
        if self.environment in (Environment.DEVELOPMENT, Environment.TESTING):
            self.debug = True
            self.show_debug_info = True


@dataclass
class AWSConfig:
    """AWS-specific configuration"""
    
    # Regions
    default_region: str = "us-east-1"
    enabled_regions: List[str] = field(default_factory=lambda: [
        'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-west-2', 'eu-central-1',
        'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1'
    ])
    
    # Services to scan
    enabled_services: List[str] = field(default_factory=lambda: [
        'ec2', 's3', 'rds', 'iam', 'lambda', 'cloudformation',
        'cloudwatch', 'sns', 'sqs', 'dynamodb', 'eks', 'ecs',
        'elasticache', 'elasticsearch', 'kms', 'secretsmanager',
        'vpc', 'elb', 'elbv2', 'route53', 'cloudfront', 'waf'
    ])
    
    # API Settings
    max_retries: int = 3
    timeout_seconds: int = 30
    rate_limit_delay: float = 0.1
    
    # AssumeRole
    default_role_name: str = "WAFScannerRole"
    session_duration: int = 3600


@dataclass  
class AIConfig:
    """AI/Claude configuration"""
    
    enabled: bool = True
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 4096
    temperature: float = 0.3
    
    # Rate limiting
    requests_per_minute: int = 50
    tokens_per_minute: int = 100000
    
    # Features
    auto_insights_enabled: bool = True
    architecture_analysis_enabled: bool = True
    remediation_suggestions_enabled: bool = True


@dataclass
class DatabaseConfig:
    """Database configuration"""
    
    backend: str = "sqlite"  # sqlite, firebase, firestore, memory
    
    # SQLite
    sqlite_path: str = "data/waf_scanner.db"
    
    # Firebase
    firebase_url: str = ""
    firebase_project_id: str = ""
    
    # Connection
    connection_timeout: int = 30
    max_connections: int = 10


@dataclass
class SecurityConfig:
    """Security configuration"""
    
    # Authentication
    require_authentication: bool = False
    session_timeout_minutes: int = 60
    max_failed_logins: int = 5
    lockout_duration_minutes: int = 15
    
    # RBAC
    default_role: str = "viewer"
    admin_emails: List[str] = field(default_factory=list)
    
    # Secrets
    mask_account_ids: bool = True
    mask_arns: bool = False
    
    # Audit
    audit_logging_enabled: bool = True


@dataclass
class ComplianceConfig:
    """Compliance framework configuration"""
    
    enabled_frameworks: List[str] = field(default_factory=lambda: [
        'AWS_WAF',
        'CIS_AWS_FOUNDATIONS',
        'PCI_DSS',
        'HIPAA',
        'SOC2',
        'ISO27001',
        'GDPR'
    ])
    
    # WAF Pillars
    waf_pillars: List[str] = field(default_factory=lambda: [
        'Operational Excellence',
        'Security',
        'Reliability',
        'Performance Efficiency',
        'Cost Optimization',
        'Sustainability'
    ])
    
    # Scoring
    passing_score_threshold: float = 70.0
    critical_finding_threshold: int = 0


# ============================================================================
# MAIN CONFIGURATION
# ============================================================================

@dataclass
class ProductionConfig:
    """Complete production configuration"""
    
    app: AppConfig = field(default_factory=AppConfig)
    aws: AWSConfig = field(default_factory=AWSConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    
    @classmethod
    def from_env(cls) -> 'ProductionConfig':
        """Create configuration from environment variables"""
        config = cls()
        
        # App settings
        config.app.debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        config.app.demo_mode_enabled = os.environ.get('DEMO_MODE', 'true').lower() == 'true'
        
        # AWS settings
        config.aws.default_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        
        # AI settings
        config.ai.enabled = os.environ.get('AI_ENABLED', 'true').lower() == 'true'
        config.ai.model = os.environ.get('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')
        
        # Database settings
        config.database.backend = os.environ.get('DB_BACKEND', 'sqlite')
        config.database.sqlite_path = os.environ.get('SQLITE_PATH', 'data/waf_scanner.db')
        
        # Security settings
        config.security.require_authentication = os.environ.get('REQUIRE_AUTH', 'false').lower() == 'true'
        
        return config
    
    @classmethod
    def from_streamlit_secrets(cls) -> 'ProductionConfig':
        """Create configuration from Streamlit secrets"""
        config = cls()
        
        try:
            import streamlit as st
            
            # App settings
            app_secrets = st.secrets.get('app', {})
            config.app.demo_mode_enabled = app_secrets.get('default_to_demo', True)
            config.security.require_authentication = app_secrets.get('require_auth', False)
            
            # AWS settings
            aws_secrets = st.secrets.get('aws', {})
            config.aws.default_region = aws_secrets.get('default_region', 'us-east-1')
            
        except Exception as e:
            logger.debug(f"Could not load Streamlit secrets: {e}")
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        from dataclasses import asdict
        return asdict(self)
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check AWS regions
        for region in self.aws.enabled_regions:
            if not region.startswith(('us-', 'eu-', 'ap-', 'sa-', 'ca-', 'me-', 'af-')):
                issues.append(f"Invalid region format: {region}")
        
        # Check thresholds
        if self.compliance.passing_score_threshold < 0 or self.compliance.passing_score_threshold > 100:
            issues.append("Passing score threshold must be between 0 and 100")
        
        # Check timeouts
        if self.app.scan_timeout_seconds < 60:
            issues.append("Scan timeout should be at least 60 seconds")
        
        return issues


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_config: Optional[ProductionConfig] = None


def get_config() -> ProductionConfig:
    """Get or create the global configuration"""
    global _config
    
    if _config is None:
        # Try Streamlit secrets first, then environment
        try:
            _config = ProductionConfig.from_streamlit_secrets()
        except Exception:
            _config = ProductionConfig.from_env()
        
        # Validate
        issues = _config.validate()
        if issues:
            for issue in issues:
                logger.warning(f"Configuration issue: {issue}")
    
    return _config


def reload_config():
    """Reload configuration"""
    global _config
    _config = None
    return get_config()


# ============================================================================
# FEATURE FLAGS
# ============================================================================

class FeatureFlags:
    """Feature flags for gradual rollout"""
    
    @staticmethod
    def is_enabled(feature: str) -> bool:
        """Check if a feature is enabled"""
        config = get_config()
        
        feature_map = {
            'demo_mode': config.app.demo_mode_enabled,
            'ai_insights': config.ai.enabled and config.ai.auto_insights_enabled,
            'multi_account': config.app.multi_account_enabled,
            'authentication': config.security.require_authentication,
            'audit_logging': config.security.audit_logging_enabled,
            'architecture_analysis': config.ai.architecture_analysis_enabled,
            'remediation_suggestions': config.ai.remediation_suggestions_enabled,
        }
        
        return feature_map.get(feature, False)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'Environment',
    'get_environment',
    'AppConfig',
    'AWSConfig',
    'AIConfig',
    'DatabaseConfig',
    'SecurityConfig',
    'ComplianceConfig',
    'ProductionConfig',
    'get_config',
    'reload_config',
    'FeatureFlags',
]
