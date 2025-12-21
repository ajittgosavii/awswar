"""
Input Validation Module for AWS WAF Scanner Enterprise
=======================================================
Provides comprehensive input validation and sanitization.

Usage:
    from validation import validate_aws_account_id, validate_region, sanitize_input
"""

import re
from typing import Optional, List, Any, Union
from dataclasses import dataclass
from enum import Enum

from logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

# AWS Patterns
AWS_ACCOUNT_ID_PATTERN = re.compile(r'^\d{12}$')
AWS_REGION_PATTERN = re.compile(r'^[a-z]{2}-[a-z]+-\d+$')
AWS_ARN_PATTERN = re.compile(r'^arn:aws[a-z\-]*:[a-z0-9\-]+:[a-z0-9\-]*:\d{12}:.+$')
AWS_ROLE_NAME_PATTERN = re.compile(r'^[\w+=,.@-]{1,64}$')
AWS_S3_BUCKET_PATTERN = re.compile(r'^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$')
AWS_TAG_KEY_PATTERN = re.compile(r'^[\w\s_.:/=+\-@]{1,128}$')
AWS_TAG_VALUE_PATTERN = re.compile(r'^[\w\s_.:/=+\-@]{0,256}$')

# Security Patterns
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
SAFE_STRING_PATTERN = re.compile(r'^[\w\s\-_.@#$%&*()+=,;:!?\'"]+$')
SQL_INJECTION_PATTERNS = [
    re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)', re.IGNORECASE),
    re.compile(r'(--|;|/\*|\*/|@@|@)', re.IGNORECASE),
    re.compile(r'(\bOR\b\s+\d+\s*=\s*\d+|\bAND\b\s+\d+\s*=\s*\d+)', re.IGNORECASE),
]
XSS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'javascript:', re.IGNORECASE),
    re.compile(r'on\w+\s*=', re.IGNORECASE),
]

# Valid AWS Regions
VALID_AWS_REGIONS = {
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'af-south-1', 'ap-east-1', 'ap-south-1', 'ap-south-2',
    'ap-southeast-1', 'ap-southeast-2', 'ap-southeast-3', 'ap-southeast-4',
    'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
    'ca-central-1', 'eu-central-1', 'eu-central-2',
    'eu-west-1', 'eu-west-2', 'eu-west-3',
    'eu-south-1', 'eu-south-2', 'eu-north-1',
    'il-central-1', 'me-south-1', 'me-central-1',
    'sa-east-1',
}


# ============================================================================
# VALIDATION RESULT
# ============================================================================

class ValidationSeverity(Enum):
    """Severity level for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    value: Any = None
    errors: List[str] = None
    warnings: List[str] = None
    sanitized_value: Any = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        self.warnings.append(message)


# ============================================================================
# AWS VALIDATORS
# ============================================================================

def validate_aws_account_id(account_id: str) -> ValidationResult:
    """
    Validate AWS account ID format.
    
    Args:
        account_id: The account ID to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=account_id)
    
    if not account_id:
        result.add_error("Account ID is required")
        return result
    
    # Remove any whitespace
    cleaned = str(account_id).strip()
    result.sanitized_value = cleaned
    
    if not AWS_ACCOUNT_ID_PATTERN.match(cleaned):
        result.add_error("Account ID must be exactly 12 digits")
        
    return result


def validate_region(region: str) -> ValidationResult:
    """
    Validate AWS region name.
    
    Args:
        region: The region to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=region)
    
    if not region:
        result.add_error("Region is required")
        return result
    
    cleaned = str(region).strip().lower()
    result.sanitized_value = cleaned
    
    if not AWS_REGION_PATTERN.match(cleaned):
        result.add_error(f"Invalid region format: {region}")
    elif cleaned not in VALID_AWS_REGIONS:
        result.add_warning(f"Region '{cleaned}' is not in known regions list")
    
    return result


def validate_arn(arn: str, service: str = None) -> ValidationResult:
    """
    Validate AWS ARN format.
    
    Args:
        arn: The ARN to validate
        service: Optional specific service to validate against
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=arn)
    
    if not arn:
        result.add_error("ARN is required")
        return result
    
    cleaned = str(arn).strip()
    result.sanitized_value = cleaned
    
    if not AWS_ARN_PATTERN.match(cleaned):
        result.add_error(f"Invalid ARN format: {arn}")
    elif service:
        parts = cleaned.split(':')
        if len(parts) >= 3 and parts[2] != service:
            result.add_error(f"ARN is not for service '{service}'")
    
    return result


def validate_role_arn(role_arn: str) -> ValidationResult:
    """Validate AWS IAM role ARN."""
    result = validate_arn(role_arn, service='iam')
    
    if result.is_valid and ':role/' not in role_arn:
        result.add_error("ARN must be an IAM role ARN")
    
    return result


def validate_s3_bucket_name(bucket_name: str) -> ValidationResult:
    """
    Validate S3 bucket name.
    
    Args:
        bucket_name: The bucket name to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=bucket_name)
    
    if not bucket_name:
        result.add_error("Bucket name is required")
        return result
    
    cleaned = str(bucket_name).strip().lower()
    result.sanitized_value = cleaned
    
    if len(cleaned) < 3 or len(cleaned) > 63:
        result.add_error("Bucket name must be between 3 and 63 characters")
    
    if not AWS_S3_BUCKET_PATTERN.match(cleaned):
        result.add_error("Invalid bucket name format")
    
    if '..' in cleaned:
        result.add_error("Bucket name cannot contain consecutive periods")
    
    if cleaned.startswith('xn--') or cleaned.endswith('-s3alias'):
        result.add_error("Bucket name cannot start with 'xn--' or end with '-s3alias'")
    
    return result


def validate_tag(key: str, value: str) -> ValidationResult:
    """
    Validate AWS resource tag.
    
    Args:
        key: Tag key
        value: Tag value
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value={'key': key, 'value': value})
    
    if not key:
        result.add_error("Tag key is required")
        return result
    
    if not AWS_TAG_KEY_PATTERN.match(key):
        result.add_error(f"Invalid tag key format: {key}")
    
    if value and not AWS_TAG_VALUE_PATTERN.match(value):
        result.add_error(f"Invalid tag value format: {value}")
    
    if key.lower().startswith('aws:'):
        result.add_error("Tag key cannot start with 'aws:'")
    
    return result


# ============================================================================
# SECURITY VALIDATORS
# ============================================================================

def validate_email(email: str) -> ValidationResult:
    """
    Validate email address format.
    
    Args:
        email: The email to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=email)
    
    if not email:
        result.add_error("Email is required")
        return result
    
    cleaned = str(email).strip().lower()
    result.sanitized_value = cleaned
    
    if not EMAIL_PATTERN.match(cleaned):
        result.add_error("Invalid email format")
    
    if len(cleaned) > 254:
        result.add_error("Email address too long")
    
    return result


def check_sql_injection(value: str) -> ValidationResult:
    """
    Check for potential SQL injection patterns.
    
    Args:
        value: The string to check
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=value)
    
    if not value:
        return result
    
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            result.add_error("Potential SQL injection detected")
            logger.warning(f"SQL injection pattern detected in input: {value[:50]}...")
            break
    
    return result


def check_xss(value: str) -> ValidationResult:
    """
    Check for potential XSS patterns.
    
    Args:
        value: The string to check
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=value)
    
    if not value:
        return result
    
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            result.add_error("Potential XSS detected")
            logger.warning(f"XSS pattern detected in input: {value[:50]}...")
            break
    
    return result


# ============================================================================
# SANITIZATION FUNCTIONS
# ============================================================================

def sanitize_string(value: str, max_length: int = 1000, allow_newlines: bool = False) -> str:
    """
    Sanitize a string input by removing potentially dangerous characters.
    
    Args:
        value: The string to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters
        
    Returns:
        Sanitized string
    """
    if not value:
        return ""
    
    # Convert to string and strip whitespace
    result = str(value).strip()
    
    # Truncate to max length
    if len(result) > max_length:
        result = result[:max_length]
        logger.warning(f"Input truncated from {len(value)} to {max_length} characters")
    
    # Remove control characters except newlines if allowed
    if allow_newlines:
        result = ''.join(c for c in result if c.isprintable() or c in '\n\r\t')
    else:
        result = ''.join(c for c in result if c.isprintable() or c == '\t')
    
    # Escape HTML entities
    result = result.replace('&', '&amp;')
    result = result.replace('<', '&lt;')
    result = result.replace('>', '&gt;')
    result = result.replace('"', '&quot;')
    result = result.replace("'", '&#x27;')
    
    return result


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return "unnamed"
    
    # Remove path components
    filename = str(filename).strip()
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = filename.replace('..', '_')
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Only allow safe characters
    safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-')
    filename = ''.join(c if c in safe_chars else '_' for c in filename)
    
    # Ensure not empty
    if not filename or filename.startswith('.'):
        filename = 'file_' + filename
    
    return filename[:255]  # Max filename length


def sanitize_json_input(data: dict) -> dict:
    """
    Recursively sanitize all string values in a dictionary.
    
    Args:
        data: The dictionary to sanitize
        
    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        # Sanitize key
        safe_key = sanitize_string(str(key), max_length=100)
        
        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[safe_key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[safe_key] = sanitize_json_input(value)
        elif isinstance(value, list):
            sanitized[safe_key] = [
                sanitize_json_input(item) if isinstance(item, dict)
                else sanitize_string(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[safe_key] = value
    
    return sanitized


# ============================================================================
# COMPOSITE VALIDATORS
# ============================================================================

def validate_assessment_input(data: dict) -> ValidationResult:
    """
    Validate WAF assessment input data.
    
    Args:
        data: Assessment input dictionary
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=data)
    
    # Required fields
    if not data.get('workload_name'):
        result.add_error("Workload name is required")
    
    if not data.get('account_id'):
        result.add_error("Account ID is required")
    else:
        account_result = validate_aws_account_id(data['account_id'])
        if not account_result.is_valid:
            result.errors.extend(account_result.errors)
    
    # Optional fields with validation
    if data.get('regions'):
        for region in data['regions']:
            region_result = validate_region(region)
            if not region_result.is_valid:
                result.errors.extend(region_result.errors)
    
    if data.get('email'):
        email_result = validate_email(data['email'])
        if not email_result.is_valid:
            result.errors.extend(email_result.errors)
    
    # Security checks
    for field in ['workload_name', 'description', 'notes']:
        if field in data and data[field]:
            sql_result = check_sql_injection(data[field])
            xss_result = check_xss(data[field])
            result.errors.extend(sql_result.errors)
            result.errors.extend(xss_result.errors)
    
    result.is_valid = len(result.errors) == 0
    return result


def validate_scan_config(config: dict) -> ValidationResult:
    """
    Validate scan configuration.
    
    Args:
        config: Scan configuration dictionary
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True, value=config)
    
    # Validate regions
    regions = config.get('regions', [])
    if not regions:
        result.add_error("At least one region is required")
    else:
        for region in regions:
            region_result = validate_region(region)
            if not region_result.is_valid:
                result.errors.extend(region_result.errors)
    
    # Validate accounts if multi-account
    accounts = config.get('accounts', [])
    for account in accounts:
        if 'account_id' in account:
            acc_result = validate_aws_account_id(account['account_id'])
            if not acc_result.is_valid:
                result.errors.extend(acc_result.errors)
        
        if 'role_arn' in account:
            role_result = validate_role_arn(account['role_arn'])
            if not role_result.is_valid:
                result.errors.extend(role_result.errors)
    
    result.is_valid = len(result.errors) == 0
    return result


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'ValidationResult',
    'ValidationSeverity',
    'validate_aws_account_id',
    'validate_region',
    'validate_arn',
    'validate_role_arn',
    'validate_s3_bucket_name',
    'validate_tag',
    'validate_email',
    'check_sql_injection',
    'check_xss',
    'sanitize_string',
    'sanitize_filename',
    'sanitize_json_input',
    'validate_assessment_input',
    'validate_scan_config',
    'VALID_AWS_REGIONS',
]
