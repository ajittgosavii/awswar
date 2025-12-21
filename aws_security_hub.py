"""
AWS Security Hub Integration Module
====================================
Provides Security Hub integration for fetching findings across accounts.

This module separates Security Hub logic from the UI to avoid circular imports.

Usage:
    from aws_security_hub import SecurityHubClient, fetch_security_hub_findings
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from collections import defaultdict
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

from logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AccountFindings:
    """Findings summary for an AWS account"""
    account_id: str
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    total: int = 0
    passed: int = 0
    failed: int = 0
    resources: Dict[str, int] = field(default_factory=dict)
    findings: List[Dict] = field(default_factory=list)
    
    def add_finding(self, finding: Dict):
        """Add a finding and update counts"""
        self.total += 1
        
        severity = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
        if severity == 'CRITICAL':
            self.critical += 1
        elif severity == 'HIGH':
            self.high += 1
        elif severity == 'MEDIUM':
            self.medium += 1
        elif severity == 'LOW':
            self.low += 1
        
        compliance_status = finding.get('Compliance', {}).get('Status', 'FAILED')
        if compliance_status == 'PASSED':
            self.passed += 1
        else:
            self.failed += 1
        
        # Track resource types
        for resource in finding.get('Resources', []):
            resource_type = resource.get('Type', 'Unknown')
            service = self._simplify_resource_type(resource_type)
            self.resources[service] = self.resources.get(service, 0) + 1
        
        self.findings.append(finding)
    
    def _simplify_resource_type(self, resource_type: str) -> str:
        """Simplify AWS resource type to service name"""
        type_mapping = {
            'Ec2': 'EC2', 'Rds': 'RDS', 'S3': 'S3', 'Lambda': 'Lambda',
            'Iam': 'IAM', 'Kms': 'KMS', 'Sns': 'SNS', 'Sqs': 'SQS',
            'CloudTrail': 'CloudTrail', 'CloudWatch': 'CloudWatch',
            'Elb': 'ELB', 'Ecs': 'ECS', 'Eks': 'EKS', 'DynamoDB': 'DynamoDB'
        }
        
        for key, value in type_mapping.items():
            if key in resource_type:
                return value
        return 'Other'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'account_id': self.account_id,
            'critical': self.critical,
            'high': self.high,
            'medium': self.medium,
            'low': self.low,
            'total': self.total,
            'passed': self.passed,
            'failed': self.failed,
            'resources': dict(self.resources),
            'findings_count': len(self.findings)
        }


@dataclass
class SecurityHubCredentials:
    """Credentials for Security Hub access"""
    access_key: str
    secret_key: str
    region: str = 'us-east-1'
    session_token: Optional[str] = None
    
    def create_session(self) -> boto3.Session:
        """Create boto3 session from credentials"""
        kwargs = {
            'aws_access_key_id': self.access_key,
            'aws_secret_access_key': self.secret_key,
            'region_name': self.region
        }
        if self.session_token:
            kwargs['aws_session_token'] = self.session_token
        
        return boto3.Session(**kwargs)


# ============================================================================
# SECURITY HUB CLIENT
# ============================================================================

class SecurityHubClient:
    """
    Client for interacting with AWS Security Hub.
    
    Usage:
        client = SecurityHubClient(credentials)
        findings = client.get_all_findings()
    """
    
    def __init__(self, session: boto3.Session = None, credentials: SecurityHubCredentials = None):
        """
        Initialize Security Hub client.
        
        Args:
            session: Existing boto3 session
            credentials: Security Hub credentials (used if session not provided)
        """
        if session:
            self.session = session
        elif credentials:
            self.session = credentials.create_session()
        else:
            self.session = boto3.Session()
        
        self._client = None
    
    @property
    def client(self):
        """Get or create Security Hub client"""
        if self._client is None:
            self._client = self.session.client('securityhub')
        return self._client
    
    def get_all_findings(
        self,
        severity_filter: List[str] = None,
        max_results: int = 1000,
        include_passed: bool = False,
        progress_callback: callable = None
    ) -> Dict[str, AccountFindings]:
        """
        Fetch all findings from Security Hub, grouped by account.
        
        Args:
            severity_filter: List of severity levels to include (CRITICAL, HIGH, MEDIUM, LOW)
            max_results: Maximum findings to fetch
            include_passed: Include PASSED compliance findings
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary mapping account IDs to AccountFindings
        """
        logger.info("Fetching Security Hub findings...")
        
        # Build filters
        filters = {
            'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
            'WorkflowStatus': [
                {'Value': 'NEW', 'Comparison': 'EQUALS'},
                {'Value': 'NOTIFIED', 'Comparison': 'EQUALS'}
            ]
        }
        
        if severity_filter:
            filters['SeverityLabel'] = [
                {'Value': sev, 'Comparison': 'EQUALS'} 
                for sev in severity_filter
            ]
        
        if not include_passed:
            filters['ComplianceStatus'] = [
                {'Value': 'FAILED', 'Comparison': 'EQUALS'}
            ]
        
        # Fetch findings
        account_findings: Dict[str, AccountFindings] = {}
        total_fetched = 0
        
        try:
            paginator = self.client.get_paginator('get_findings')
            page_iterator = paginator.paginate(
                Filters=filters,
                MaxResults=min(100, max_results)
            )
            
            for page_num, page in enumerate(page_iterator):
                findings = page.get('Findings', [])
                
                for finding in findings:
                    if total_fetched >= max_results:
                        break
                    
                    account_id = finding.get('AwsAccountId', 'Unknown')
                    
                    if account_id not in account_findings:
                        account_findings[account_id] = AccountFindings(account_id=account_id)
                    
                    account_findings[account_id].add_finding(finding)
                    total_fetched += 1
                
                if progress_callback:
                    progress_callback(total_fetched, max_results)
                
                if total_fetched >= max_results:
                    break
            
            logger.info(f"Fetched {total_fetched} findings from {len(account_findings)} accounts")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            logger.error(f"Security Hub error: {error_code} - {e}")
            raise
        except NoCredentialsError:
            logger.error("No AWS credentials available")
            raise
        
        return account_findings
    
    def get_finding_aggregates(self, group_by: str = 'SeverityLabel') -> Dict[str, int]:
        """
        Get aggregated finding counts.
        
        Args:
            group_by: Field to group by (SeverityLabel, ComplianceStatus, etc.)
            
        Returns:
            Dictionary of counts by group
        """
        try:
            response = self.client.get_finding_aggregator()
            # Process aggregation response
            aggregates = {}
            
            for agg in response.get('FindingAggregators', []):
                key = agg.get('GroupByAttribute', 'Unknown')
                count = agg.get('Count', 0)
                aggregates[key] = count
            
            return aggregates
            
        except ClientError as e:
            logger.error(f"Failed to get aggregates: {e}")
            return {}
    
    def get_enabled_standards(self) -> List[Dict]:
        """Get list of enabled security standards"""
        try:
            response = self.client.get_enabled_standards()
            return response.get('StandardsSubscriptions', [])
        except ClientError as e:
            logger.error(f"Failed to get standards: {e}")
            return []
    
    def get_insight_results(self, insight_arn: str) -> Dict:
        """Get results for a Security Hub insight"""
        try:
            response = self.client.get_insight_results(InsightArn=insight_arn)
            return response.get('InsightResults', {})
        except ClientError as e:
            logger.error(f"Failed to get insight: {e}")
            return {}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def fetch_security_hub_findings(
    access_key: str = None,
    secret_key: str = None,
    region: str = 'us-east-1',
    session: boto3.Session = None,
    severity_filter: List[str] = None,
    max_results: int = 1000
) -> Dict[str, AccountFindings]:
    """
    Convenience function to fetch Security Hub findings.
    
    Args:
        access_key: AWS access key (optional if session provided)
        secret_key: AWS secret key (optional if session provided)
        region: AWS region
        session: Existing boto3 session
        severity_filter: List of severity levels
        max_results: Maximum findings
        
    Returns:
        Dictionary mapping account IDs to findings
    """
    if session:
        client = SecurityHubClient(session=session)
    elif access_key and secret_key:
        creds = SecurityHubCredentials(
            access_key=access_key,
            secret_key=secret_key,
            region=region
        )
        client = SecurityHubClient(credentials=creds)
    else:
        client = SecurityHubClient()
    
    return client.get_all_findings(
        severity_filter=severity_filter,
        max_results=max_results
    )


def convert_findings_to_legacy_format(
    findings: Dict[str, AccountFindings]
) -> Dict[str, Dict]:
    """
    Convert AccountFindings to legacy dictionary format for backward compatibility.
    
    Args:
        findings: Dictionary of AccountFindings objects
        
    Returns:
        Dictionary in legacy format
    """
    return {
        account_id: af.to_dict()
        for account_id, af in findings.items()
    }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'AccountFindings',
    'SecurityHubCredentials',
    'SecurityHubClient',
    'fetch_security_hub_findings',
    'convert_findings_to_legacy_format',
]
