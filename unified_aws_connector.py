"""
Unified AWS Connection Manager with WAF Pillar Alignment
=========================================================

Provides three connection strategies based on scale and constraints:

1. SINGLE ACCOUNT - Direct connection to one AWS account
2. MULTI-ACCOUNT - AssumeRole across multiple accounts (up to 500)
3. SECURITY HUB - Aggregated findings for 500+ accounts or API constraints

All findings are automatically mapped to AWS Well-Architected Framework pillars.

Version: 2.0.0
Author: AWS WAF Scanner Enterprise
"""

import streamlit as st
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional, Any, Generator, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import json
import time

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS AND CONFIGURATION
# ============================================================================

class ConnectionMode(Enum):
    """Available connection modes"""
    SINGLE_ACCOUNT = "single"
    MULTI_ACCOUNT = "multi"
    SECURITY_HUB = "security_hub"

class WAFPillar(Enum):
    """AWS Well-Architected Framework Pillars"""
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"

@dataclass
class ConnectionConfig:
    """Configuration for AWS connections"""
    mode: ConnectionMode = ConnectionMode.SINGLE_ACCOUNT
    region: str = "us-east-1"
    max_concurrent_accounts: int = 10
    api_rate_limit_per_second: float = 5.0
    cache_ttl_seconds: int = 300
    retry_attempts: int = 3
    timeout_seconds: int = 30

@dataclass
class AccountCredentials:
    """Credentials for an AWS account"""
    account_id: str
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    role_arn: Optional[str] = None
    external_id: Optional[str] = None
    session_token: Optional[str] = None
    region: str = "us-east-1"
    alias: Optional[str] = None

# ============================================================================
# WAF PILLAR MAPPING - CRITICAL FOR ALIGNMENT
# ============================================================================

class WAFPillarMapper:
    """
    Maps AWS findings to Well-Architected Framework pillars.
    
    This ensures all security findings, compliance results, and resource
    assessments are properly categorized by WAF pillar for scoring.
    """
    
    # Security Hub finding types to WAF pillars
    FINDING_TYPE_TO_PILLAR = {
        # Security Pillar
        "Software and Configuration Checks": WAFPillar.SECURITY,
        "TTPs": WAFPillar.SECURITY,
        "Effects": WAFPillar.SECURITY,
        "Unusual Behaviors": WAFPillar.SECURITY,
        "Sensitive Data Identifications": WAFPillar.SECURITY,
        
        # Operational Excellence
        "Software and Configuration Checks/AWS Security Best Practices": WAFPillar.OPERATIONAL_EXCELLENCE,
        "Patch": WAFPillar.OPERATIONAL_EXCELLENCE,
        
        # Reliability
        "Reachability": WAFPillar.RELIABILITY,
        "Software and Configuration Checks/Industry and Regulatory Standards": WAFPillar.RELIABILITY,
        
        # Cost Optimization
        "Cost": WAFPillar.COST_OPTIMIZATION,
        "Unused": WAFPillar.COST_OPTIMIZATION,
        
        # Performance
        "Performance": WAFPillar.PERFORMANCE_EFFICIENCY,
    }
    
    # AWS Service to primary WAF pillar mapping
    SERVICE_TO_PILLAR = {
        # Security Services → Security Pillar
        "guardduty": WAFPillar.SECURITY,
        "securityhub": WAFPillar.SECURITY,
        "inspector": WAFPillar.SECURITY,
        "macie": WAFPillar.SECURITY,
        "iam": WAFPillar.SECURITY,
        "kms": WAFPillar.SECURITY,
        "waf": WAFPillar.SECURITY,
        "shield": WAFPillar.SECURITY,
        "cognito": WAFPillar.SECURITY,
        "secrets-manager": WAFPillar.SECURITY,
        "acm": WAFPillar.SECURITY,
        
        # Operational Services → Operational Excellence
        "cloudwatch": WAFPillar.OPERATIONAL_EXCELLENCE,
        "cloudtrail": WAFPillar.OPERATIONAL_EXCELLENCE,
        "config": WAFPillar.OPERATIONAL_EXCELLENCE,
        "ssm": WAFPillar.OPERATIONAL_EXCELLENCE,
        "cloudformation": WAFPillar.OPERATIONAL_EXCELLENCE,
        "servicecatalog": WAFPillar.OPERATIONAL_EXCELLENCE,
        "organizations": WAFPillar.OPERATIONAL_EXCELLENCE,
        "health": WAFPillar.OPERATIONAL_EXCELLENCE,
        
        # Reliability Services → Reliability Pillar
        "backup": WAFPillar.RELIABILITY,
        "route53": WAFPillar.RELIABILITY,
        "elasticloadbalancing": WAFPillar.RELIABILITY,
        "autoscaling": WAFPillar.RELIABILITY,
        "rds": WAFPillar.RELIABILITY,
        "dynamodb": WAFPillar.RELIABILITY,
        "s3": WAFPillar.RELIABILITY,
        "sns": WAFPillar.RELIABILITY,
        "sqs": WAFPillar.RELIABILITY,
        
        # Performance Services → Performance Efficiency
        "elasticache": WAFPillar.PERFORMANCE_EFFICIENCY,
        "cloudfront": WAFPillar.PERFORMANCE_EFFICIENCY,
        "lambda": WAFPillar.PERFORMANCE_EFFICIENCY,
        "ec2": WAFPillar.PERFORMANCE_EFFICIENCY,
        "ecs": WAFPillar.PERFORMANCE_EFFICIENCY,
        "eks": WAFPillar.PERFORMANCE_EFFICIENCY,
        
        # Cost Services → Cost Optimization
        "ce": WAFPillar.COST_OPTIMIZATION,
        "budgets": WAFPillar.COST_OPTIMIZATION,
        "cur": WAFPillar.COST_OPTIMIZATION,
        "pricing": WAFPillar.COST_OPTIMIZATION,
        "savingsplans": WAFPillar.COST_OPTIMIZATION,
        
        # Sustainability
        "compute-optimizer": WAFPillar.SUSTAINABILITY,
        "customer-carbon-footprint": WAFPillar.SUSTAINABILITY,
    }
    
    # Security Hub compliance standards to WAF pillars
    STANDARD_TO_PILLARS = {
        "aws-foundational-security-best-practices": [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
        "cis-aws-foundations-benchmark": [WAFPillar.SECURITY],
        "pci-dss": [WAFPillar.SECURITY, WAFPillar.RELIABILITY],
        "nist-800-53": [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE, WAFPillar.RELIABILITY],
        "soc2": [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
        "hipaa": [WAFPillar.SECURITY, WAFPillar.RELIABILITY],
        "gdpr": [WAFPillar.SECURITY],
    }
    
    # Resource type to WAF pillar
    RESOURCE_TYPE_TO_PILLAR = {
        # Security resources
        "AwsIamUser": WAFPillar.SECURITY,
        "AwsIamRole": WAFPillar.SECURITY,
        "AwsIamPolicy": WAFPillar.SECURITY,
        "AwsKmsKey": WAFPillar.SECURITY,
        "AwsSecretsManagerSecret": WAFPillar.SECURITY,
        "AwsWafWebAcl": WAFPillar.SECURITY,
        "AwsSecurityGroup": WAFPillar.SECURITY,
        "AwsNetworkAcl": WAFPillar.SECURITY,
        
        # Reliability resources
        "AwsRdsDbInstance": WAFPillar.RELIABILITY,
        "AwsRdsDbCluster": WAFPillar.RELIABILITY,
        "AwsS3Bucket": WAFPillar.RELIABILITY,
        "AwsDynamoDbTable": WAFPillar.RELIABILITY,
        "AwsElbLoadBalancer": WAFPillar.RELIABILITY,
        "AwsElbv2LoadBalancer": WAFPillar.RELIABILITY,
        "AwsAutoScalingGroup": WAFPillar.RELIABILITY,
        "AwsBackupBackupPlan": WAFPillar.RELIABILITY,
        
        # Performance resources
        "AwsEc2Instance": WAFPillar.PERFORMANCE_EFFICIENCY,
        "AwsLambdaFunction": WAFPillar.PERFORMANCE_EFFICIENCY,
        "AwsEcsCluster": WAFPillar.PERFORMANCE_EFFICIENCY,
        "AwsEksCluster": WAFPillar.PERFORMANCE_EFFICIENCY,
        "AwsCloudFrontDistribution": WAFPillar.PERFORMANCE_EFFICIENCY,
        "AwsElastiCacheCluster": WAFPillar.PERFORMANCE_EFFICIENCY,
        
        # Operational resources
        "AwsCloudTrailTrail": WAFPillar.OPERATIONAL_EXCELLENCE,
        "AwsCloudWatchAlarm": WAFPillar.OPERATIONAL_EXCELLENCE,
        "AwsConfigRule": WAFPillar.OPERATIONAL_EXCELLENCE,
        "AwsSsmDocument": WAFPillar.OPERATIONAL_EXCELLENCE,
    }
    
    @classmethod
    def map_finding_to_pillar(cls, finding: Dict) -> WAFPillar:
        """
        Map a Security Hub finding to a WAF pillar.
        Uses multiple signals for accurate mapping.
        """
        # Try finding types first
        finding_types = finding.get('types', finding.get('Types', []))
        for ftype in finding_types:
            for pattern, pillar in cls.FINDING_TYPE_TO_PILLAR.items():
                if pattern.lower() in ftype.lower():
                    return pillar
        
        # Try resource type
        resources = finding.get('resources', finding.get('Resources', []))
        if resources:
            resource_type = resources[0].get('Type', '')
            if resource_type in cls.RESOURCE_TYPE_TO_PILLAR:
                return cls.RESOURCE_TYPE_TO_PILLAR[resource_type]
        
        # Try product/service name
        product = finding.get('product_name', finding.get('ProductName', '')).lower()
        for service, pillar in cls.SERVICE_TO_PILLAR.items():
            if service in product:
                return pillar
        
        # Try generator ID (contains service info)
        generator = finding.get('generator_id', finding.get('GeneratorId', '')).lower()
        for service, pillar in cls.SERVICE_TO_PILLAR.items():
            if service in generator:
                return pillar
        
        # Default to Security pillar for unmapped findings
        return WAFPillar.SECURITY
    
    @classmethod
    def map_service_to_pillar(cls, service_name: str) -> WAFPillar:
        """Map an AWS service name to a WAF pillar"""
        service_lower = service_name.lower().replace('amazon ', '').replace('aws ', '')
        return cls.SERVICE_TO_PILLAR.get(service_lower, WAFPillar.OPERATIONAL_EXCELLENCE)
    
    @classmethod
    def get_pillar_weights(cls) -> Dict[WAFPillar, float]:
        """Get default weights for pillar scoring"""
        return {
            WAFPillar.SECURITY: 0.25,
            WAFPillar.RELIABILITY: 0.20,
            WAFPillar.OPERATIONAL_EXCELLENCE: 0.20,
            WAFPillar.PERFORMANCE_EFFICIENCY: 0.15,
            WAFPillar.COST_OPTIMIZATION: 0.10,
            WAFPillar.SUSTAINABILITY: 0.10,
        }


# ============================================================================
# UNIFIED AWS CONNECTOR
# ============================================================================

class UnifiedAWSConnector:
    """
    Unified AWS Connector supporting three connection modes:
    
    1. SINGLE_ACCOUNT - Direct connection to one account
    2. MULTI_ACCOUNT - AssumeRole across multiple accounts
    3. SECURITY_HUB - Aggregated findings from 500+ accounts
    
    All findings are automatically aligned to WAF pillars.
    """
    
    def __init__(self, config: ConnectionConfig = None):
        self.config = config or ConnectionConfig()
        self._sessions: Dict[str, boto3.Session] = {}
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._connected_accounts: List[AccountCredentials] = []
        self._security_hub_client = None
        self._pillar_mapper = WAFPillarMapper()
    
    # ========================================================================
    # CONNECTION MODE SELECTION UI
    # ========================================================================
    
    @staticmethod
    def render_connection_selector() -> ConnectionMode:
        """Render UI for selecting connection mode"""
        
        st.markdown("## 🔌 AWS Connection Strategy")
        
        st.markdown("""
        Choose the best connection strategy based on your environment:
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="padding: 20px; background: linear-gradient(135deg, #1565C0, #1976D2); 
                        border-radius: 15px; color: white; height: 280px;">
                <h3>🔹 Single Account</h3>
                <p><strong>Best for:</strong></p>
                <ul>
                    <li>1 AWS account</li>
                    <li>Quick assessments</li>
                    <li>Development/testing</li>
                </ul>
                <p><strong>Pros:</strong> Simple setup</p>
                <p><strong>Cons:</strong> Limited scope</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="padding: 20px; background: linear-gradient(135deg, #7B1FA2, #9C27B0); 
                        border-radius: 15px; color: white; height: 280px;">
                <h3>🔸 Multi-Account</h3>
                <p><strong>Best for:</strong></p>
                <ul>
                    <li>2-500 accounts</li>
                    <li>Organizations</li>
                    <li>Detailed scanning</li>
                </ul>
                <p><strong>Pros:</strong> Full control</p>
                <p><strong>Cons:</strong> More API calls</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="padding: 20px; background: linear-gradient(135deg, #C62828, #D32F2F); 
                        border-radius: 15px; color: white; height: 280px;">
                <h3>🔺 Security Hub</h3>
                <p><strong>Best for:</strong></p>
                <ul>
                    <li>500+ accounts</li>
                    <li>API rate limits</li>
                    <li>Aggregated view</li>
                </ul>
                <p><strong>Pros:</strong> Scalable</p>
                <p><strong>Cons:</strong> Requires setup</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Selection
        mode_options = {
            "🔹 Single Account (1 account)": ConnectionMode.SINGLE_ACCOUNT,
            "🔸 Multi-Account (2-500 accounts)": ConnectionMode.MULTI_ACCOUNT,
            "🔺 Security Hub (500+ accounts / API constraints)": ConnectionMode.SECURITY_HUB
        }
        
        selected = st.radio(
            "Select Connection Mode",
            list(mode_options.keys()),
            key="connection_mode_selector"
        )
        
        return mode_options[selected]
    
    # ========================================================================
    # SINGLE ACCOUNT CONNECTION
    # ========================================================================
    
    def connect_single_account(self,
                               access_key: str = None,
                               secret_key: str = None,
                               region: str = None,
                               session_token: str = None,
                               profile_name: str = None) -> Dict[str, Any]:
        """
        Connect to a single AWS account.
        
        Options:
        1. Access key + Secret key
        2. Session token (temporary credentials)
        3. Profile name (from ~/.aws/credentials)
        4. Environment variables / IAM role (default)
        """
        try:
            region = region or self.config.region
            
            # Build session based on provided credentials
            if access_key and secret_key:
                session_kwargs = {
                    'aws_access_key_id': access_key,
                    'aws_secret_access_key': secret_key,
                    'region_name': region
                }
                if session_token:
                    session_kwargs['aws_session_token'] = session_token
                session = boto3.Session(**session_kwargs)
            elif profile_name:
                session = boto3.Session(profile_name=profile_name, region_name=region)
            else:
                session = boto3.Session(region_name=region)
            
            # Validate connection
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            account_id = identity['Account']
            
            # Store session
            self._sessions[account_id] = session
            self._connected_accounts = [AccountCredentials(
                account_id=account_id,
                region=region,
                alias=f"Account-{account_id[-4:]}"
            )]
            
            self.config.mode = ConnectionMode.SINGLE_ACCOUNT
            
            return {
                "success": True,
                "mode": "SINGLE_ACCOUNT",
                "account_id": account_id,
                "arn": identity['Arn'],
                "user_id": identity['UserId'],
                "region": region,
                "account_count": 1
            }
            
        except NoCredentialsError:
            return {"success": False, "error": "No valid AWS credentials found"}
        except ClientError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Connection failed: {str(e)}"}
    
    # ========================================================================
    # MULTI-ACCOUNT CONNECTION
    # ========================================================================
    
    def connect_multi_account(self,
                              accounts: List[AccountCredentials],
                              management_session: boto3.Session = None,
                              use_organizations: bool = False,
                              cross_account_role: str = "OrganizationAccountAccessRole") -> Dict[str, Any]:
        """
        Connect to multiple AWS accounts using AssumeRole.
        
        Options:
        1. Explicit account list with role ARNs
        2. Auto-discover from AWS Organizations
        
        Args:
            accounts: List of AccountCredentials with role_arn for each account
            management_session: Session for management account (for Organizations)
            use_organizations: Auto-discover accounts from Organizations
            cross_account_role: Role name to assume in each account
        """
        connected = []
        failed = []
        
        try:
            # Option 1: Auto-discover from Organizations
            if use_organizations and management_session:
                accounts = self._discover_organization_accounts(
                    management_session, 
                    cross_account_role
                )
            
            if not accounts:
                return {"success": False, "error": "No accounts provided or discovered"}
            
            # Connect to each account in parallel
            with ThreadPoolExecutor(max_workers=self.config.max_concurrent_accounts) as executor:
                future_to_account = {
                    executor.submit(self._connect_to_account, acc): acc 
                    for acc in accounts
                }
                
                for future in as_completed(future_to_account):
                    account = future_to_account[future]
                    try:
                        result = future.result()
                        if result['success']:
                            connected.append(result)
                            self._connected_accounts.append(account)
                        else:
                            failed.append({
                                "account_id": account.account_id,
                                "error": result.get('error', 'Unknown error')
                            })
                    except Exception as e:
                        failed.append({
                            "account_id": account.account_id,
                            "error": str(e)
                        })
            
            self.config.mode = ConnectionMode.MULTI_ACCOUNT
            
            return {
                "success": len(connected) > 0,
                "mode": "MULTI_ACCOUNT",
                "connected_count": len(connected),
                "failed_count": len(failed),
                "total_accounts": len(accounts),
                "connected_accounts": connected,
                "failed_accounts": failed
            }
            
        except Exception as e:
            return {"success": False, "error": f"Multi-account connection failed: {str(e)}"}
    
    def _discover_organization_accounts(self, 
                                        session: boto3.Session, 
                                        role_name: str) -> List[AccountCredentials]:
        """Discover all accounts in AWS Organization"""
        accounts = []
        
        try:
            org = session.client('organizations')
            paginator = org.get_paginator('list_accounts')
            
            for page in paginator.paginate():
                for account in page['Accounts']:
                    if account['Status'] == 'ACTIVE':
                        accounts.append(AccountCredentials(
                            account_id=account['Id'],
                            role_arn=f"arn:aws:iam::{account['Id']}:role/{role_name}",
                            alias=account.get('Name', account['Id'])
                        ))
            
            logger.info(f"Discovered {len(accounts)} accounts from Organizations")
            
        except ClientError as e:
            logger.error(f"Failed to discover accounts: {e}")
        
        return accounts
    
    def _connect_to_account(self, account: AccountCredentials) -> Dict[str, Any]:
        """Connect to a single account via AssumeRole"""
        try:
            # Get base session for assuming role
            base_session = boto3.Session()
            sts = base_session.client('sts')
            
            # Assume role
            assume_kwargs = {
                'RoleArn': account.role_arn,
                'RoleSessionName': f"WAFScanner-{account.account_id}",
                'DurationSeconds': 3600
            }
            
            if account.external_id:
                assume_kwargs['ExternalId'] = account.external_id
            
            assumed = sts.assume_role(**assume_kwargs)
            creds = assumed['Credentials']
            
            # Create session with assumed credentials
            session = boto3.Session(
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretAccessKey'],
                aws_session_token=creds['SessionToken'],
                region_name=account.region or self.config.region
            )
            
            # Validate
            identity = session.client('sts').get_caller_identity()
            
            # Store session
            self._sessions[account.account_id] = session
            
            return {
                "success": True,
                "account_id": account.account_id,
                "alias": account.alias,
                "arn": identity['Arn'],
                "region": account.region or self.config.region
            }
            
        except ClientError as e:
            return {"success": False, "account_id": account.account_id, "error": str(e)}
    
    # ========================================================================
    # SECURITY HUB CONNECTION (500+ Accounts)
    # ========================================================================
    
    def connect_security_hub(self,
                            access_key: str = None,
                            secret_key: str = None,
                            role_arn: str = None,
                            region: str = None) -> Dict[str, Any]:
        """
        Connect to Security Hub aggregator for 500+ accounts.
        
        This connects to the DELEGATED ADMINISTRATOR account which has
        aggregated findings from all member accounts.
        
        Args:
            access_key: Access key for delegated admin (or leave empty for role)
            secret_key: Secret key for delegated admin
            role_arn: Role ARN to assume into delegated admin account
            region: Aggregation region (default: us-east-1)
        """
        try:
            region = region or self.config.region
            
            # Build session
            if role_arn:
                # AssumeRole to delegated admin
                sts = boto3.client('sts')
                assumed = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName="WAFScanner-SecurityHub",
                    DurationSeconds=3600
                )
                creds = assumed['Credentials']
                session = boto3.Session(
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken'],
                    region_name=region
                )
            elif access_key and secret_key:
                session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
            else:
                session = boto3.Session(region_name=region)
            
            # Initialize Security Hub client
            self._security_hub_client = session.client('securityhub', region_name=region)
            
            # Validate Security Hub is enabled
            hub_info = self._security_hub_client.describe_hub()
            
            # Get member count
            member_count = 0
            try:
                paginator = self._security_hub_client.get_paginator('list_members')
                for page in paginator.paginate():
                    member_count += len(page.get('Members', []))
            except ClientError:
                pass  # Might not be admin account
            
            # Store primary session
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            self._sessions['security_hub'] = session
            
            self.config.mode = ConnectionMode.SECURITY_HUB
            
            return {
                "success": True,
                "mode": "SECURITY_HUB",
                "account_id": identity['Account'],
                "hub_arn": hub_info.get('HubArn', ''),
                "region": region,
                "member_accounts": member_count,
                "auto_enable": hub_info.get('AutoEnableControls', False),
                "message": f"Connected to Security Hub with {member_count} member accounts"
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'InvalidAccessException':
                return {"success": False, "error": "Security Hub is not enabled in this account/region"}
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Security Hub connection failed: {str(e)}"}
    
    # ========================================================================
    # UNIFIED FINDINGS RETRIEVAL WITH WAF ALIGNMENT
    # ========================================================================
    
    def get_findings(self,
                    severity_filter: List[str] = None,
                    pillar_filter: WAFPillar = None,
                    max_results: int = None) -> Generator[Dict, None, None]:
        """
        Get findings from connected accounts, aligned to WAF pillars.
        
        Automatically uses the appropriate method based on connection mode:
        - SINGLE_ACCOUNT: Direct service scanning
        - MULTI_ACCOUNT: Parallel scanning across accounts
        - SECURITY_HUB: Aggregated findings API
        
        All findings include 'waf_pillar' field for pillar alignment.
        """
        if self.config.mode == ConnectionMode.SECURITY_HUB:
            yield from self._get_security_hub_findings(severity_filter, pillar_filter, max_results)
        elif self.config.mode == ConnectionMode.MULTI_ACCOUNT:
            yield from self._get_multi_account_findings(severity_filter, pillar_filter, max_results)
        else:
            yield from self._get_single_account_findings(severity_filter, pillar_filter, max_results)
    
    def _get_security_hub_findings(self,
                                   severity_filter: List[str] = None,
                                   pillar_filter: WAFPillar = None,
                                   max_results: int = None) -> Generator[Dict, None, None]:
        """Get findings from Security Hub with WAF pillar mapping"""
        
        if not self._security_hub_client:
            logger.error("Security Hub not connected")
            return
        
        # Build filters
        filters = {
            'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}]
        }
        
        if severity_filter:
            filters['SeverityLabel'] = [
                {'Value': sev, 'Comparison': 'EQUALS'} 
                for sev in severity_filter
            ]
        
        try:
            paginator = self._security_hub_client.get_paginator('get_findings')
            count = 0
            
            for page in paginator.paginate(
                Filters=filters,
                SortCriteria=[{'Field': 'SeverityLabel', 'SortOrder': 'desc'}],
                PaginationConfig={'PageSize': 100}
            ):
                for finding in page.get('Findings', []):
                    if max_results and count >= max_results:
                        return
                    
                    # Parse and add WAF pillar
                    parsed = self._parse_security_hub_finding(finding)
                    
                    # Apply pillar filter if specified
                    if pillar_filter and parsed['waf_pillar'] != pillar_filter.value:
                        continue
                    
                    yield parsed
                    count += 1
                    
        except ClientError as e:
            logger.error(f"Failed to get Security Hub findings: {e}")
    
    def _parse_security_hub_finding(self, finding: Dict) -> Dict:
        """Parse Security Hub finding and map to WAF pillar"""
        resources = finding.get('Resources', [{}])
        primary_resource = resources[0] if resources else {}
        
        # Map to WAF pillar
        waf_pillar = self._pillar_mapper.map_finding_to_pillar(finding)
        
        return {
            # Identification
            "id": finding.get('Id', ''),
            "arn": finding.get('ProductArn', ''),
            "account_id": finding.get('AwsAccountId', ''),
            "region": finding.get('Region', ''),
            
            # Finding details
            "title": finding.get('Title', ''),
            "description": finding.get('Description', ''),
            "severity": finding.get('Severity', {}).get('Label', 'INFORMATIONAL'),
            "severity_score": finding.get('Severity', {}).get('Normalized', 0),
            
            # Source
            "product_name": finding.get('ProductName', ''),
            "company_name": finding.get('CompanyName', ''),
            "generator_id": finding.get('GeneratorId', ''),
            
            # Resource
            "resource_type": primary_resource.get('Type', 'Unknown'),
            "resource_id": primary_resource.get('Id', 'Unknown'),
            "resource_region": primary_resource.get('Region', ''),
            
            # Status
            "compliance_status": finding.get('Compliance', {}).get('Status', 'NOT_AVAILABLE'),
            "workflow_status": finding.get('Workflow', {}).get('Status', 'NEW'),
            "record_state": finding.get('RecordState', 'ACTIVE'),
            
            # Timestamps
            "created_at": finding.get('CreatedAt', ''),
            "updated_at": finding.get('UpdatedAt', ''),
            
            # Remediation
            "remediation": finding.get('Remediation', {}).get('Recommendation', {}).get('Text', ''),
            "remediation_url": finding.get('Remediation', {}).get('Recommendation', {}).get('Url', ''),
            
            # WAF PILLAR ALIGNMENT
            "waf_pillar": waf_pillar.value,
            "waf_pillar_enum": waf_pillar,
            "types": finding.get('Types', []),
        }
    
    def _get_multi_account_findings(self,
                                    severity_filter: List[str] = None,
                                    pillar_filter: WAFPillar = None,
                                    max_results: int = None) -> Generator[Dict, None, None]:
        """Get findings from multiple accounts in parallel"""
        
        all_findings = []
        
        def scan_account(account_id: str, session: boto3.Session):
            """Scan a single account"""
            findings = []
            
            # Scan different services based on pillar
            services_to_scan = self._get_services_for_pillar(pillar_filter)
            
            for service in services_to_scan:
                try:
                    service_findings = self._scan_service(session, service, severity_filter)
                    findings.extend(service_findings)
                except Exception as e:
                    logger.warning(f"Failed to scan {service} in {account_id}: {e}")
            
            return account_id, findings
        
        # Parallel scan
        with ThreadPoolExecutor(max_workers=self.config.max_concurrent_accounts) as executor:
            futures = {
                executor.submit(scan_account, acc_id, session): acc_id
                for acc_id, session in self._sessions.items()
            }
            
            count = 0
            for future in as_completed(futures):
                try:
                    account_id, findings = future.result()
                    for finding in findings:
                        if max_results and count >= max_results:
                            return
                        
                        finding['account_id'] = account_id
                        yield finding
                        count += 1
                        
                except Exception as e:
                    logger.error(f"Error scanning account: {e}")
    
    def _get_single_account_findings(self,
                                     severity_filter: List[str] = None,
                                     pillar_filter: WAFPillar = None,
                                     max_results: int = None) -> Generator[Dict, None, None]:
        """Get findings from single account"""
        
        if not self._sessions:
            logger.error("No account connected")
            return
        
        account_id = list(self._sessions.keys())[0]
        session = self._sessions[account_id]
        
        services_to_scan = self._get_services_for_pillar(pillar_filter)
        
        count = 0
        for service in services_to_scan:
            try:
                findings = self._scan_service(session, service, severity_filter)
                for finding in findings:
                    if max_results and count >= max_results:
                        return
                    
                    finding['account_id'] = account_id
                    yield finding
                    count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to scan {service}: {e}")
    
    def _get_services_for_pillar(self, pillar: WAFPillar = None) -> List[str]:
        """Get list of services to scan for a pillar"""
        
        pillar_services = {
            WAFPillar.SECURITY: ['guardduty', 'inspector', 'iam', 'securityhub'],
            WAFPillar.RELIABILITY: ['rds', 's3', 'backup', 'elasticloadbalancing'],
            WAFPillar.OPERATIONAL_EXCELLENCE: ['cloudwatch', 'cloudtrail', 'config', 'ssm'],
            WAFPillar.PERFORMANCE_EFFICIENCY: ['ec2', 'lambda', 'elasticache', 'cloudfront'],
            WAFPillar.COST_OPTIMIZATION: ['ce', 'budgets'],
            WAFPillar.SUSTAINABILITY: ['compute-optimizer'],
        }
        
        if pillar:
            return pillar_services.get(pillar, [])
        
        # Return all services for all pillars
        all_services = []
        for services in pillar_services.values():
            all_services.extend(services)
        return list(set(all_services))
    
    def _scan_service(self, session: boto3.Session, service: str, severity_filter: List[str] = None) -> List[Dict]:
        """Scan a specific AWS service for findings"""
        
        findings = []
        
        # Service-specific scanning logic
        if service == 'guardduty':
            findings.extend(self._scan_guardduty(session))
        elif service == 'inspector':
            findings.extend(self._scan_inspector(session))
        elif service == 'config':
            findings.extend(self._scan_config(session))
        elif service == 'iam':
            findings.extend(self._scan_iam(session))
        # Add more service scanners as needed
        
        # Apply severity filter
        if severity_filter:
            findings = [f for f in findings if f.get('severity') in severity_filter]
        
        return findings
    
    def _scan_guardduty(self, session: boto3.Session) -> List[Dict]:
        """Scan GuardDuty for findings"""
        findings = []
        
        try:
            gd = session.client('guardduty')
            
            # Get detector
            detectors = gd.list_detectors().get('DetectorIds', [])
            if not detectors:
                return findings
            
            detector_id = detectors[0]
            
            # Get findings
            finding_ids = gd.list_findings(
                DetectorId=detector_id,
                MaxResults=50
            ).get('FindingIds', [])
            
            if finding_ids:
                details = gd.get_findings(
                    DetectorId=detector_id,
                    FindingIds=finding_ids
                ).get('Findings', [])
                
                for f in details:
                    severity = 'LOW'
                    if f.get('Severity', 0) >= 7:
                        severity = 'CRITICAL'
                    elif f.get('Severity', 0) >= 4:
                        severity = 'HIGH'
                    elif f.get('Severity', 0) >= 2:
                        severity = 'MEDIUM'
                    
                    findings.append({
                        'id': f.get('Id', ''),
                        'title': f.get('Title', ''),
                        'description': f.get('Description', ''),
                        'severity': severity,
                        'severity_score': f.get('Severity', 0),
                        'product_name': 'GuardDuty',
                        'resource_type': f.get('Resource', {}).get('ResourceType', 'Unknown'),
                        'resource_id': f.get('Resource', {}).get('InstanceDetails', {}).get('InstanceId', 'Unknown'),
                        'waf_pillar': WAFPillar.SECURITY.value,
                        'waf_pillar_enum': WAFPillar.SECURITY,
                        'created_at': str(f.get('CreatedAt', '')),
                        'region': f.get('Region', ''),
                    })
                    
        except Exception as e:
            logger.warning(f"GuardDuty scan error: {e}")
        
        return findings
    
    def _scan_inspector(self, session: boto3.Session) -> List[Dict]:
        """Scan Inspector for findings"""
        findings = []
        
        try:
            inspector = session.client('inspector2')
            
            response = inspector.list_findings(maxResults=50)
            
            for f in response.get('findings', []):
                findings.append({
                    'id': f.get('findingArn', ''),
                    'title': f.get('title', ''),
                    'description': f.get('description', ''),
                    'severity': f.get('severity', 'INFORMATIONAL'),
                    'product_name': 'Inspector',
                    'resource_type': f.get('resources', [{}])[0].get('type', 'Unknown'),
                    'resource_id': f.get('resources', [{}])[0].get('id', 'Unknown'),
                    'waf_pillar': WAFPillar.SECURITY.value,
                    'waf_pillar_enum': WAFPillar.SECURITY,
                    'remediation': f.get('remediation', {}).get('recommendation', {}).get('text', ''),
                })
                
        except Exception as e:
            logger.warning(f"Inspector scan error: {e}")
        
        return findings
    
    def _scan_config(self, session: boto3.Session) -> List[Dict]:
        """Scan AWS Config for compliance findings"""
        findings = []
        
        try:
            config = session.client('config')
            
            response = config.describe_compliance_by_config_rule()
            
            for rule in response.get('ComplianceByConfigRules', []):
                if rule.get('Compliance', {}).get('ComplianceType') == 'NON_COMPLIANT':
                    findings.append({
                        'id': rule.get('ConfigRuleName', ''),
                        'title': f"Non-compliant Config Rule: {rule.get('ConfigRuleName', '')}",
                        'description': 'AWS Config rule is non-compliant',
                        'severity': 'MEDIUM',
                        'product_name': 'AWS Config',
                        'resource_type': 'ConfigRule',
                        'resource_id': rule.get('ConfigRuleName', ''),
                        'waf_pillar': WAFPillar.OPERATIONAL_EXCELLENCE.value,
                        'waf_pillar_enum': WAFPillar.OPERATIONAL_EXCELLENCE,
                        'compliance_status': 'NON_COMPLIANT',
                    })
                    
        except Exception as e:
            logger.warning(f"Config scan error: {e}")
        
        return findings
    
    def _scan_iam(self, session: boto3.Session) -> List[Dict]:
        """Scan IAM for security findings"""
        findings = []
        
        try:
            iam = session.client('iam')
            
            # Check for root access keys
            response = iam.get_account_summary()
            summary = response.get('SummaryMap', {})
            
            if summary.get('AccountAccessKeysPresent', 0) > 0:
                findings.append({
                    'id': 'iam-root-access-keys',
                    'title': 'Root account has access keys',
                    'description': 'The root account should not have access keys. Use IAM users instead.',
                    'severity': 'CRITICAL',
                    'product_name': 'IAM',
                    'resource_type': 'AWS::IAM::User',
                    'resource_id': 'root',
                    'waf_pillar': WAFPillar.SECURITY.value,
                    'waf_pillar_enum': WAFPillar.SECURITY,
                    'remediation': 'Delete root account access keys and use IAM users with least privilege.',
                })
            
            # Check MFA
            if summary.get('AccountMFAEnabled', 0) == 0:
                findings.append({
                    'id': 'iam-root-mfa',
                    'title': 'Root account MFA not enabled',
                    'description': 'MFA should be enabled for the root account.',
                    'severity': 'CRITICAL',
                    'product_name': 'IAM',
                    'resource_type': 'AWS::IAM::User',
                    'resource_id': 'root',
                    'waf_pillar': WAFPillar.SECURITY.value,
                    'waf_pillar_enum': WAFPillar.SECURITY,
                    'remediation': 'Enable MFA for the root account.',
                })
                    
        except Exception as e:
            logger.warning(f"IAM scan error: {e}")
        
        return findings
    
    # ========================================================================
    # PILLAR SCORE CALCULATION
    # ========================================================================
    
    def calculate_pillar_scores(self, findings: List[Dict] = None) -> Dict[str, Any]:
        """
        Calculate WAF pillar scores based on findings.
        
        Returns scores for each pillar (0-100) based on:
        - Number of findings per pillar
        - Severity of findings
        - Compliance status
        """
        if findings is None:
            findings = list(self.get_findings(max_results=1000))
        
        # Initialize pillar data
        pillar_data = {
            pillar.value: {
                'findings_count': 0,
                'critical_count': 0,
                'high_count': 0,
                'medium_count': 0,
                'low_count': 0,
                'score': 100  # Start at 100, deduct for issues
            }
            for pillar in WAFPillar
        }
        
        # Count findings per pillar
        for finding in findings:
            pillar = finding.get('waf_pillar', WAFPillar.SECURITY.value)
            severity = finding.get('severity', 'LOW')
            
            if pillar in pillar_data:
                pillar_data[pillar]['findings_count'] += 1
                
                if severity == 'CRITICAL':
                    pillar_data[pillar]['critical_count'] += 1
                    pillar_data[pillar]['score'] -= 10
                elif severity == 'HIGH':
                    pillar_data[pillar]['high_count'] += 1
                    pillar_data[pillar]['score'] -= 5
                elif severity == 'MEDIUM':
                    pillar_data[pillar]['medium_count'] += 1
                    pillar_data[pillar]['score'] -= 2
                elif severity == 'LOW':
                    pillar_data[pillar]['low_count'] += 1
                    pillar_data[pillar]['score'] -= 0.5
        
        # Normalize scores (min 0, max 100)
        for pillar in pillar_data:
            pillar_data[pillar]['score'] = max(0, min(100, pillar_data[pillar]['score']))
        
        # Calculate overall score
        weights = self._pillar_mapper.get_pillar_weights()
        overall_score = sum(
            pillar_data[pillar.value]['score'] * weight
            for pillar, weight in weights.items()
        )
        
        return {
            'overall_score': round(overall_score, 1),
            'pillar_scores': {
                pillar: data['score'] 
                for pillar, data in pillar_data.items()
            },
            'pillar_details': pillar_data,
            'total_findings': len(findings),
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# STREAMLIT UI COMPONENTS
# ============================================================================

def render_unified_connector_ui():
    """Render the unified AWS connector UI"""
    
    st.markdown("# 🔌 AWS Connection Manager")
    
    # Initialize connector
    if 'unified_connector' not in st.session_state:
        st.session_state['unified_connector'] = UnifiedAWSConnector()
    
    connector = st.session_state['unified_connector']
    
    # Check if already connected
    if st.session_state.get('aws_connected'):
        render_connected_dashboard(connector)
        return
    
    # Mode selection
    mode = connector.render_connection_selector()
    
    st.markdown("---")
    
    # Mode-specific connection UI
    if mode == ConnectionMode.SINGLE_ACCOUNT:
        render_single_account_connection(connector)
    elif mode == ConnectionMode.MULTI_ACCOUNT:
        render_multi_account_connection(connector)
    else:
        render_security_hub_connection(connector)


def render_single_account_connection(connector: UnifiedAWSConnector):
    """Render single account connection UI"""
    
    st.markdown("### 🔹 Single Account Connection")
    
    auth_method = st.radio(
        "Authentication Method",
        ["Access Key / Secret Key", "AWS Profile", "Environment / IAM Role"],
        key="single_auth_method"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if auth_method == "Access Key / Secret Key":
            access_key = st.text_input("Access Key ID", type="password", key="single_access_key")
            secret_key = st.text_input("Secret Access Key", type="password", key="single_secret_key")
            profile_name = None
        elif auth_method == "AWS Profile":
            profile_name = st.text_input("Profile Name", value="default", key="single_profile")
            access_key = None
            secret_key = None
        else:
            access_key = None
            secret_key = None
            profile_name = None
    
    with col2:
        region = st.selectbox("Region", [
            "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
            "ap-southeast-1", "ap-northeast-1"
        ], key="single_region")
    
    if st.button("🔗 Connect", use_container_width=True, key="single_connect_btn"):
        with st.spinner("Connecting to AWS..."):
            result = connector.connect_single_account(
                access_key=access_key if auth_method == "Access Key / Secret Key" else None,
                secret_key=secret_key if auth_method == "Access Key / Secret Key" else None,
                profile_name=profile_name if auth_method == "AWS Profile" else None,
                region=region
            )
            
            if result['success']:
                st.session_state['aws_connected'] = True
                st.session_state['connection_result'] = result
                st.success(f"✅ Connected to account {result['account_id']}")
                st.rerun()
            else:
                st.error(f"❌ {result.get('error', 'Connection failed')}")


def render_multi_account_connection(connector: UnifiedAWSConnector):
    """Render multi-account connection UI"""
    
    st.markdown("### 🔸 Multi-Account Connection")
    
    discovery_method = st.radio(
        "Account Discovery",
        ["Manual Entry", "AWS Organizations (Auto-discover)"],
        key="multi_discovery"
    )
    
    if discovery_method == "Manual Entry":
        st.markdown("**Enter accounts (one per line: account_id,role_arn)**")
        accounts_text = st.text_area(
            "Accounts",
            placeholder="123456789012,arn:aws:iam::123456789012:role/CrossAccountRole\n234567890123,arn:aws:iam::234567890123:role/CrossAccountRole",
            height=150,
            key="multi_accounts_text"
        )
        
        if st.button("🔗 Connect to Accounts", use_container_width=True, key="multi_connect_btn"):
            # Parse accounts
            accounts = []
            for line in accounts_text.strip().split('\n'):
                if ',' in line:
                    parts = line.strip().split(',')
                    accounts.append(AccountCredentials(
                        account_id=parts[0].strip(),
                        role_arn=parts[1].strip() if len(parts) > 1 else None
                    ))
            
            if not accounts:
                st.error("Please enter at least one account")
                return
            
            with st.spinner(f"Connecting to {len(accounts)} accounts..."):
                result = connector.connect_multi_account(accounts=accounts)
                
                if result['success']:
                    st.session_state['aws_connected'] = True
                    st.session_state['connection_result'] = result
                    st.success(f"✅ Connected to {result['connected_count']}/{result['total_accounts']} accounts")
                    
                    if result['failed_count'] > 0:
                        with st.expander("⚠️ Failed Connections"):
                            for failed in result['failed_accounts']:
                                st.error(f"{failed['account_id']}: {failed['error']}")
                    
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'Connection failed')}")
    
    else:
        st.info("**Organizations Auto-Discovery** will scan all active accounts in your AWS Organization.")
        
        col1, col2 = st.columns(2)
        with col1:
            mgmt_access_key = st.text_input("Management Account Access Key", type="password", key="mgmt_access_key")
            mgmt_secret_key = st.text_input("Management Account Secret Key", type="password", key="mgmt_secret_key")
        with col2:
            cross_role = st.text_input("Cross-Account Role Name", value="OrganizationAccountAccessRole", key="cross_role")
        
        if st.button("🔍 Discover & Connect", use_container_width=True, key="org_connect_btn"):
            st.info("Discovering accounts from Organizations...")
            # Implementation would create management session and call connect_multi_account with use_organizations=True


def render_security_hub_connection(connector: UnifiedAWSConnector):
    """Render Security Hub connection UI"""
    
    st.markdown("### 🔺 Security Hub Connection (500+ Accounts)")
    
    st.info("""
    **For 500+ accounts or API rate limit constraints:**
    
    Connect to your Security Hub **Delegated Administrator** account.
    This provides aggregated findings from ALL member accounts with minimal API calls.
    """)
    
    auth_method = st.radio(
        "Authentication Method",
        ["AssumeRole to Delegated Admin (Recommended)", "Direct Credentials"],
        key="sh_auth_method"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if auth_method == "AssumeRole to Delegated Admin (Recommended)":
            role_arn = st.text_input(
                "Delegated Admin Role ARN",
                placeholder="arn:aws:iam::SECURITY_ACCOUNT_ID:role/SecurityHubReadOnly",
                key="sh_role_arn"
            )
            access_key = None
            secret_key = None
        else:
            access_key = st.text_input("Access Key ID", type="password", key="sh_access_key")
            secret_key = st.text_input("Secret Access Key", type="password", key="sh_secret_key")
            role_arn = None
    
    with col2:
        region = st.selectbox("Aggregation Region", [
            "us-east-1", "us-west-2", "eu-west-1", "eu-central-1",
            "ap-southeast-1", "ap-northeast-1"
        ], key="sh_region")
        
        st.markdown("**Required Permissions:**")
        st.code("securityhub:DescribeHub\nsecurityhub:GetFindings\nsecurityhub:ListMembers", language="text")
    
    if st.button("🔗 Connect to Security Hub", use_container_width=True, key="sh_connect_btn"):
        with st.spinner("Connecting to Security Hub Aggregator..."):
            result = connector.connect_security_hub(
                access_key=access_key,
                secret_key=secret_key,
                role_arn=role_arn,
                region=region
            )
            
            if result['success']:
                st.session_state['aws_connected'] = True
                st.session_state['connection_result'] = result
                st.success(f"✅ {result.get('message', 'Connected to Security Hub')}")
                st.rerun()
            else:
                st.error(f"❌ {result.get('error', 'Connection failed')}")


def render_connected_dashboard(connector: UnifiedAWSConnector):
    """Render dashboard after successful connection"""
    
    result = st.session_state.get('connection_result', {})
    mode = result.get('mode', 'UNKNOWN')
    
    # Connection status bar
    st.markdown(f"""
    <div style="padding: 15px; background: linear-gradient(135deg, #1B5E20, #2E7D32); 
                border-radius: 10px; color: white; margin-bottom: 20px;">
        <h3 style="margin: 0;">✅ Connected - {mode}</h3>
        <p style="margin: 5px 0 0 0;">
            {'Account: ' + result.get('account_id', 'N/A') if mode == 'SINGLE_ACCOUNT' else ''}
            {'Accounts: ' + str(result.get('connected_count', 0)) if mode == 'MULTI_ACCOUNT' else ''}
            {'Member Accounts: ' + str(result.get('member_accounts', 0)) if mode == 'SECURITY_HUB' else ''}
            | Region: {result.get('region', 'N/A')}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 WAF Pillar Scores", "🔍 Findings by Pillar", "📋 Raw Findings"])
    
    with tab1:
        render_pillar_scores(connector)
    
    with tab2:
        render_findings_by_pillar(connector)
    
    with tab3:
        render_raw_findings(connector)
    
    # Disconnect button
    st.markdown("---")
    if st.button("❌ Disconnect", key="disconnect_btn"):
        st.session_state['aws_connected'] = False
        st.session_state.pop('connection_result', None)
        st.session_state.pop('unified_connector', None)
        st.rerun()


def render_pillar_scores(connector: UnifiedAWSConnector):
    """Render WAF pillar scores"""
    
    st.markdown("### 📊 WAF Pillar Scores")
    
    if st.button("🔄 Calculate Scores", key="calc_scores_btn"):
        with st.spinner("Analyzing findings and calculating pillar scores..."):
            scores = connector.calculate_pillar_scores()
            st.session_state['pillar_scores'] = scores
    
    if 'pillar_scores' in st.session_state:
        scores = st.session_state['pillar_scores']
        
        # Overall score
        overall = scores['overall_score']
        grade = 'A' if overall >= 90 else 'B' if overall >= 80 else 'C' if overall >= 70 else 'D' if overall >= 60 else 'F'
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #1565C0, #7B1FA2); 
                        border-radius: 20px; color: white;">
                <h1 style="font-size: 64px; margin: 0;">{overall:.0f}</h1>
                <h2 style="margin: 0;">Grade: {grade}</h2>
                <p>Overall WAF Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Pillar scores
        st.markdown("#### Scores by Pillar")
        
        cols = st.columns(3)
        pillar_icons = {
            "Operational Excellence": "⚙️",
            "Security": "🔒",
            "Reliability": "🛡️",
            "Performance Efficiency": "⚡",
            "Cost Optimization": "💰",
            "Sustainability": "🌱"
        }
        
        for i, (pillar, score) in enumerate(scores['pillar_scores'].items()):
            with cols[i % 3]:
                color = '#4CAF50' if score >= 80 else '#FF9800' if score >= 60 else '#F44336'
                icon = pillar_icons.get(pillar, '📊')
                
                details = scores['pillar_details'].get(pillar, {})
                critical = details.get('critical_count', 0)
                high = details.get('high_count', 0)
                
                st.markdown(f"""
                <div style="padding: 15px; background: #f5f5f5; border-radius: 10px; 
                            border-left: 4px solid {color}; margin-bottom: 10px;">
                    <h4 style="margin: 0;">{icon} {pillar}</h4>
                    <h2 style="color: {color}; margin: 5px 0;">{score:.0f}/100</h2>
                    <small>🔴 {critical} Critical | 🟠 {high} High</small>
                </div>
                """, unsafe_allow_html=True)


def render_findings_by_pillar(connector: UnifiedAWSConnector):
    """Render findings grouped by WAF pillar"""
    
    st.markdown("### 🔍 Findings by WAF Pillar")
    
    # Pillar filter
    pillar_options = ["All Pillars"] + [p.value for p in WAFPillar]
    selected_pillar = st.selectbox("Filter by Pillar", pillar_options, key="uac_pillar_filter")
    
    pillar_filter = None
    if selected_pillar != "All Pillars":
        pillar_filter = WAFPillar(selected_pillar)
    
    severity_filter = st.multiselect(
        "Severity",
        ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH"],
        key="severity_filter"
    )
    
    if st.button("🔍 Load Findings", key="load_findings_btn"):
        with st.spinner("Loading findings..."):
            findings = list(connector.get_findings(
                severity_filter=severity_filter if severity_filter else None,
                pillar_filter=pillar_filter,
                max_results=200
            ))
            st.session_state['findings'] = findings
    
    if 'findings' in st.session_state:
        findings = st.session_state['findings']
        
        # Group by pillar
        by_pillar = {}
        for f in findings:
            pillar = f.get('waf_pillar', 'Unknown')
            if pillar not in by_pillar:
                by_pillar[pillar] = []
            by_pillar[pillar].append(f)
        
        for pillar, pillar_findings in by_pillar.items():
            with st.expander(f"**{pillar}** ({len(pillar_findings)} findings)"):
                for f in pillar_findings[:20]:  # Show first 20
                    severity = f.get('severity', 'LOW')
                    color = {'CRITICAL': '#F44336', 'HIGH': '#FF9800', 'MEDIUM': '#2196F3', 'LOW': '#4CAF50'}.get(severity, '#666')
                    
                    st.markdown(f"""
                    <div style="padding: 10px; border-left: 3px solid {color}; background: #f9f9f9; margin-bottom: 5px;">
                        <span style="background: {color}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">{severity}</span>
                        <strong style="margin-left: 10px;">{f.get('title', 'N/A')[:80]}</strong>
                        <br><small>Account: {f.get('account_id', 'N/A')} | Resource: {f.get('resource_type', 'N/A')}</small>
                    </div>
                    """, unsafe_allow_html=True)


def render_raw_findings(connector: UnifiedAWSConnector):
    """Render raw findings table"""
    
    st.markdown("### 📋 Raw Findings")
    
    if 'findings' in st.session_state:
        import pandas as pd
        
        findings = st.session_state['findings']
        
        if findings:
            df = pd.DataFrame([{
                'Severity': f.get('severity', 'N/A'),
                'WAF Pillar': f.get('waf_pillar', 'N/A'),
                'Title': f.get('title', 'N/A')[:50],
                'Account': f.get('account_id', 'N/A'),
                'Resource': f.get('resource_type', 'N/A'),
                'Product': f.get('product_name', 'N/A'),
            } for f in findings])
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export
            csv = df.to_csv(index=False)
            st.download_button(
                "📥 Download CSV",
                csv,
                "waf_findings.csv",
                "text/csv",
                key="download_findings"
            )
    else:
        st.info("Load findings first using the 'Findings by Pillar' tab")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="AWS Connection Manager", layout="wide")
    render_unified_connector_ui()
