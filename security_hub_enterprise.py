"""
Enterprise Security Hub Integration for AWS Organizations (500+ Accounts)
==========================================================================

Architecture Overview:
- Uses Security Hub Delegated Administrator pattern
- Single API connection to aggregator account
- Cross-region finding aggregation
- Efficient pagination for large-scale deployments
- Caching and batching for performance

Version: 1.0.0
"""

import streamlit as st
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, List, Optional, Any, Generator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class SecurityHubRegion(Enum):
    """Supported aggregation regions"""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    EU_CENTRAL_1 = "eu-central-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"
    AP_NORTHEAST_1 = "ap-northeast-1"

@dataclass
class SecurityHubConfig:
    """Configuration for enterprise Security Hub"""
    aggregation_region: str = "us-east-1"
    max_findings_per_request: int = 100
    pagination_batch_size: int = 100
    cache_ttl_seconds: int = 300  # 5 minutes
    enable_cross_region: bool = True
    parallel_workers: int = 5
    finding_age_days: int = 90

# ============================================================================
# ENTERPRISE SECURITY HUB MANAGER
# ============================================================================

class EnterpriseSecurityHubManager:
    """
    Enterprise-scale Security Hub management for 500+ AWS accounts.
    
    Key Features:
    1. Delegated Administrator pattern - single connection point
    2. Automatic pagination for large result sets
    3. Finding aggregation and summarization
    4. Caching for performance
    5. Parallel processing for multi-region queries
    """
    
    def __init__(self, session: boto3.Session = None, config: SecurityHubConfig = None):
        self.config = config or SecurityHubConfig()
        self.session = session
        self._cache = {}
        self._cache_timestamps = {}
        self._securityhub_client = None
        self._organizations_client = None
    
    # ============================================================================
    # CONNECTION MANAGEMENT
    # ============================================================================
    
    def connect(self, 
                access_key: str = None, 
                secret_key: str = None, 
                region: str = None,
                role_arn: str = None,
                session_name: str = "SecurityHubEnterprise") -> Dict[str, Any]:
        """
        Connect to Security Hub Delegated Administrator account.
        
        For 500+ accounts, you should connect to the DELEGATED ADMIN account,
        not individual member accounts. This gives you aggregated findings.
        
        Options:
        1. Direct credentials (access_key/secret_key)
        2. AssumeRole to delegated admin (role_arn)
        3. Existing boto3 session
        """
        try:
            region = region or self.config.aggregation_region
            
            # Option 1: Use existing session
            if self.session:
                logger.info("Using existing boto3 session")
            
            # Option 2: AssumeRole (recommended for cross-account)
            elif role_arn:
                logger.info(f"Assuming role: {role_arn}")
                sts = boto3.client('sts')
                assumed = sts.assume_role(
                    RoleArn=role_arn,
                    RoleSessionName=session_name,
                    DurationSeconds=3600
                )
                creds = assumed['Credentials']
                self.session = boto3.Session(
                    aws_access_key_id=creds['AccessKeyId'],
                    aws_secret_access_key=creds['SecretAccessKey'],
                    aws_session_token=creds['SessionToken'],
                    region_name=region
                )
            
            # Option 3: Direct credentials
            elif access_key and secret_key:
                self.session = boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region
                )
            
            # Option 4: Default credential chain
            else:
                self.session = boto3.Session(region_name=region)
            
            # Initialize clients
            self._securityhub_client = self.session.client('securityhub', region_name=region)
            
            # Validate connection
            hub_info = self._securityhub_client.describe_hub()
            
            # Check if this is the administrator account
            admin_info = self._get_administrator_status()
            
            # Get account identity
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            
            return {
                "success": True,
                "account_id": identity['Account'],
                "hub_arn": hub_info.get('HubArn', ''),
                "region": region,
                "is_administrator": admin_info.get('is_administrator', False),
                "administrator_id": admin_info.get('administrator_id'),
                "auto_enable_controls": hub_info.get('AutoEnableControls', False),
                "subscribed_at": str(hub_info.get('SubscribedAt', ''))
            }
            
        except NoCredentialsError:
            return {"success": False, "error": "No valid AWS credentials found"}
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            
            if error_code == 'InvalidAccessException':
                return {"success": False, "error": "Security Hub is not enabled. Enable it first in the AWS Console."}
            
            return {"success": False, "error": f"{error_code}: {error_msg}"}
        except Exception as e:
            return {"success": False, "error": f"Connection failed: {str(e)}"}
    
    def _get_administrator_status(self) -> Dict[str, Any]:
        """Check if current account is Security Hub administrator"""
        try:
            # Try to get administrator account (will fail if WE are the admin)
            response = self._securityhub_client.get_administrator_account()
            admin = response.get('Administrator', {})
            
            if admin:
                return {
                    "is_administrator": False,
                    "administrator_id": admin.get('AccountId'),
                    "invitation_id": admin.get('InvitationId'),
                    "status": admin.get('MemberStatus')
                }
            
            return {"is_administrator": True, "administrator_id": None}
            
        except ClientError as e:
            # If no administrator, we might BE the administrator
            if 'No administrator' in str(e) or 'not a member' in str(e).lower():
                return {"is_administrator": True, "administrator_id": None}
            return {"is_administrator": False, "administrator_id": None}
    
    # ============================================================================
    # MEMBER ACCOUNT MANAGEMENT (500+ Accounts)
    # ============================================================================
    
    def get_all_member_accounts(self, 
                                only_enabled: bool = True,
                                include_details: bool = False) -> Generator[Dict, None, None]:
        """
        Retrieve ALL member accounts with efficient pagination.
        
        For 500+ accounts, this uses a generator to avoid memory issues.
        Results are yielded in batches as they're retrieved from AWS.
        
        Args:
            only_enabled: Only return accounts with ENABLED status
            include_details: Include additional account metadata
            
        Yields:
            Dict with account_id, email, status, and optional details
        """
        if not self._securityhub_client:
            logger.error("Not connected to Security Hub")
            return
        
        try:
            paginator = self._securityhub_client.get_paginator('list_members')
            
            page_config = {
                'MaxResults': self.config.pagination_batch_size
            }
            
            if only_enabled:
                page_config['OnlyAssociated'] = True
            
            total_count = 0
            
            for page in paginator.paginate(**page_config):
                members = page.get('Members', [])
                
                for member in members:
                    total_count += 1
                    
                    account_data = {
                        "account_id": member.get('AccountId', ''),
                        "email": member.get('Email', ''),
                        "status": member.get('MemberStatus', 'UNKNOWN'),
                        "invited_at": str(member.get('InvitedAt', '')),
                        "updated_at": str(member.get('UpdatedAt', ''))
                    }
                    
                    if include_details:
                        account_data["administrator_id"] = member.get('AdministratorId', '')
                        account_data["master_id"] = member.get('MasterId', '')  # Legacy
                    
                    yield account_data
            
            logger.info(f"Retrieved {total_count} member accounts")
            
        except ClientError as e:
            logger.error(f"Failed to list member accounts: {e}")
            raise
    
    def get_member_accounts_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all member accounts.
        Optimized for 500+ accounts.
        """
        cache_key = "member_accounts_summary"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        summary = {
            "total_accounts": 0,
            "enabled_accounts": 0,
            "pending_accounts": 0,
            "disabled_accounts": 0,
            "by_status": {},
            "accounts_list": []  # Limited list for display
        }
        
        display_limit = 100  # Only store first 100 for UI display
        
        for account in self.get_all_member_accounts(only_enabled=False):
            summary["total_accounts"] += 1
            
            status = account.get("status", "UNKNOWN")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            if status == "ENABLED":
                summary["enabled_accounts"] += 1
            elif status in ["INVITED", "CREATED"]:
                summary["pending_accounts"] += 1
            else:
                summary["disabled_accounts"] += 1
            
            # Keep limited list for UI
            if len(summary["accounts_list"]) < display_limit:
                summary["accounts_list"].append(account)
        
        self._set_cache(cache_key, summary)
        return summary
    
    # ============================================================================
    # FINDINGS AGGREGATION (Enterprise Scale)
    # ============================================================================
    
    def get_aggregated_findings(self,
                                severity_filter: List[str] = None,
                                account_ids: List[str] = None,
                                product_names: List[str] = None,
                                compliance_status: str = None,
                                max_results: int = None,
                                sort_by: str = "SeverityLabel",
                                sort_order: str = "desc") -> Generator[Dict, None, None]:
        """
        Get aggregated findings from ALL member accounts.
        
        For 500+ accounts, Security Hub aggregator automatically collects
        findings from all members. We just query the aggregator.
        
        This uses a generator for memory efficiency with large result sets.
        
        Args:
            severity_filter: List of severities ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            account_ids: Filter to specific accounts (optional)
            product_names: Filter by product (GuardDuty, Inspector, etc.)
            compliance_status: PASSED, FAILED, WARNING, NOT_AVAILABLE
            max_results: Limit total results (None = all)
            sort_by: Field to sort by
            sort_order: "asc" or "desc"
            
        Yields:
            Finding dictionaries
        """
        if not self._securityhub_client:
            logger.error("Not connected to Security Hub")
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
        
        if account_ids:
            filters['AwsAccountId'] = [
                {'Value': acc, 'Comparison': 'EQUALS'} 
                for acc in account_ids
            ]
        
        if product_names:
            filters['ProductName'] = [
                {'Value': prod, 'Comparison': 'EQUALS'} 
                for prod in product_names
            ]
        
        if compliance_status:
            filters['ComplianceStatus'] = [
                {'Value': compliance_status, 'Comparison': 'EQUALS'}
            ]
        
        # Sort criteria
        sort_criteria = [
            {'Field': sort_by, 'SortOrder': sort_order.upper()}
        ]
        
        try:
            paginator = self._securityhub_client.get_paginator('get_findings')
            
            total_yielded = 0
            
            for page in paginator.paginate(
                Filters=filters,
                SortCriteria=sort_criteria,
                PaginationConfig={'PageSize': self.config.max_findings_per_request}
            ):
                findings = page.get('Findings', [])
                
                for finding in findings:
                    if max_results and total_yielded >= max_results:
                        return
                    
                    yield self._parse_finding(finding)
                    total_yielded += 1
            
            logger.info(f"Retrieved {total_yielded} findings")
            
        except ClientError as e:
            logger.error(f"Failed to get findings: {e}")
            raise
    
    def _parse_finding(self, finding: Dict) -> Dict:
        """Parse raw finding into clean structure"""
        resources = finding.get('Resources', [{}])
        primary_resource = resources[0] if resources else {}
        
        return {
            "id": finding.get('Id', ''),
            "arn": finding.get('ProductArn', ''),
            "account_id": finding.get('AwsAccountId', ''),
            "region": finding.get('Region', ''),
            "title": finding.get('Title', ''),
            "description": finding.get('Description', ''),
            "severity": finding.get('Severity', {}).get('Label', 'INFORMATIONAL'),
            "severity_normalized": finding.get('Severity', {}).get('Normalized', 0),
            "product_name": finding.get('ProductName', ''),
            "company_name": finding.get('CompanyName', ''),
            "resource_type": primary_resource.get('Type', 'Unknown'),
            "resource_id": primary_resource.get('Id', 'Unknown'),
            "resource_region": primary_resource.get('Region', ''),
            "compliance_status": finding.get('Compliance', {}).get('Status', 'NOT_AVAILABLE'),
            "workflow_status": finding.get('Workflow', {}).get('Status', 'NEW'),
            "record_state": finding.get('RecordState', 'ACTIVE'),
            "generator_id": finding.get('GeneratorId', ''),
            "created_at": finding.get('CreatedAt', ''),
            "updated_at": finding.get('UpdatedAt', ''),
            "first_observed_at": finding.get('FirstObservedAt', ''),
            "last_observed_at": finding.get('LastObservedAt', ''),
            "remediation": finding.get('Remediation', {}).get('Recommendation', {}).get('Text', ''),
            "remediation_url": finding.get('Remediation', {}).get('Recommendation', {}).get('Url', ''),
            "types": finding.get('Types', []),
            "source_url": finding.get('SourceUrl', '')
        }
    
    def get_findings_summary(self, 
                            group_by: str = "severity",
                            include_by_account: bool = True,
                            include_by_product: bool = True) -> Dict[str, Any]:
        """
        Get aggregated findings summary across all 500+ accounts.
        
        This is optimized to minimize API calls while providing
        comprehensive summary data.
        """
        cache_key = f"findings_summary_{group_by}"
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]
        
        summary = {
            "total_findings": 0,
            "by_severity": {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "INFORMATIONAL": 0
            },
            "by_status": {
                "NEW": 0,
                "NOTIFIED": 0,
                "RESOLVED": 0,
                "SUPPRESSED": 0
            },
            "by_compliance": {
                "PASSED": 0,
                "FAILED": 0,
                "WARNING": 0,
                "NOT_AVAILABLE": 0
            },
            "by_account": {},
            "by_product": {},
            "by_resource_type": {},
            "critical_findings": [],  # Store first 50 critical
            "recent_findings": []     # Store 20 most recent
        }
        
        critical_limit = 50
        recent_limit = 20
        
        for finding in self.get_aggregated_findings():
            summary["total_findings"] += 1
            
            # By severity
            severity = finding.get("severity", "INFORMATIONAL")
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # By workflow status
            status = finding.get("workflow_status", "NEW")
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # By compliance
            compliance = finding.get("compliance_status", "NOT_AVAILABLE")
            summary["by_compliance"][compliance] = summary["by_compliance"].get(compliance, 0) + 1
            
            # By account
            if include_by_account:
                account_id = finding.get("account_id", "Unknown")
                if account_id not in summary["by_account"]:
                    summary["by_account"][account_id] = {"total": 0, "critical": 0, "high": 0}
                summary["by_account"][account_id]["total"] += 1
                if severity == "CRITICAL":
                    summary["by_account"][account_id]["critical"] += 1
                elif severity == "HIGH":
                    summary["by_account"][account_id]["high"] += 1
            
            # By product
            if include_by_product:
                product = finding.get("product_name", "Unknown")
                summary["by_product"][product] = summary["by_product"].get(product, 0) + 1
            
            # By resource type
            resource_type = finding.get("resource_type", "Unknown")
            summary["by_resource_type"][resource_type] = summary["by_resource_type"].get(resource_type, 0) + 1
            
            # Store critical findings
            if severity == "CRITICAL" and len(summary["critical_findings"]) < critical_limit:
                summary["critical_findings"].append(finding)
            
            # Store recent (first N are most recent due to default sort)
            if len(summary["recent_findings"]) < recent_limit:
                summary["recent_findings"].append(finding)
        
        # Calculate derived metrics
        total = summary["total_findings"]
        if total > 0:
            summary["critical_percentage"] = round(summary["by_severity"]["CRITICAL"] / total * 100, 2)
            summary["high_percentage"] = round(summary["by_severity"]["HIGH"] / total * 100, 2)
            summary["compliance_rate"] = round(
                summary["by_compliance"]["PASSED"] / 
                (summary["by_compliance"]["PASSED"] + summary["by_compliance"]["FAILED"]) * 100, 2
            ) if (summary["by_compliance"]["PASSED"] + summary["by_compliance"]["FAILED"]) > 0 else 0
        
        # Top 10 accounts by findings
        summary["top_accounts_by_findings"] = sorted(
            summary["by_account"].items(),
            key=lambda x: x[1]["total"],
            reverse=True
        )[:10]
        
        self._set_cache(cache_key, summary)
        return summary
    
    # ============================================================================
    # COMPLIANCE STANDARDS
    # ============================================================================
    
    def get_enabled_standards(self) -> List[Dict]:
        """Get all enabled security standards"""
        if not self._securityhub_client:
            return []
        
        try:
            standards = []
            paginator = self._securityhub_client.get_paginator('get_enabled_standards')
            
            for page in paginator.paginate():
                for std in page.get('StandardsSubscriptions', []):
                    standards.append({
                        "arn": std.get('StandardsArn', ''),
                        "subscription_arn": std.get('StandardsSubscriptionArn', ''),
                        "status": std.get('StandardsStatus', ''),
                        "status_reason": std.get('StandardsStatusReason', {}).get('Code', '')
                    })
            
            return standards
            
        except ClientError as e:
            logger.error(f"Failed to get standards: {e}")
            return []
    
    def get_standards_control_status(self, standards_arn: str) -> Dict[str, Any]:
        """Get control status for a specific standard"""
        if not self._securityhub_client:
            return {}
        
        try:
            controls = {"passed": 0, "failed": 0, "unknown": 0, "disabled": 0, "controls": []}
            
            paginator = self._securityhub_client.get_paginator('describe_standards_controls')
            
            for page in paginator.paginate(StandardsSubscriptionArn=standards_arn):
                for control in page.get('Controls', []):
                    status = control.get('ControlStatus', 'UNKNOWN')
                    
                    if status == 'ENABLED':
                        # Check compliance
                        compliance = control.get('ControlStatusUpdatedAt')
                        controls["passed"] += 1  # Simplified
                    elif status == 'DISABLED':
                        controls["disabled"] += 1
                    else:
                        controls["unknown"] += 1
                    
                    controls["controls"].append({
                        "id": control.get('ControlId', ''),
                        "title": control.get('Title', ''),
                        "status": status,
                        "severity": control.get('SeverityRating', ''),
                        "description": control.get('Description', '')
                    })
            
            return controls
            
        except ClientError as e:
            logger.error(f"Failed to get control status: {e}")
            return {}
    
    # ============================================================================
    # CACHING UTILITIES
    # ============================================================================
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache or key not in self._cache_timestamps:
            return False
        
        age = time.time() - self._cache_timestamps[key]
        return age < self.config.cache_ttl_seconds
    
    def _set_cache(self, key: str, value: Any):
        """Set cached value with timestamp"""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache = {}
        self._cache_timestamps = {}


# ============================================================================
# STREAMLIT UI COMPONENT
# ============================================================================

def render_enterprise_security_hub_dashboard():
    """Render the enterprise Security Hub dashboard for 500+ accounts"""
    
    st.markdown("## 🏢 Enterprise Security Hub Dashboard")
    st.caption("Aggregated security findings across 500+ AWS accounts")
    
    # Initialize manager
    if 'security_hub_manager' not in st.session_state:
        st.session_state['security_hub_manager'] = EnterpriseSecurityHubManager()
    
    manager = st.session_state['security_hub_manager']
    
    # Connection section
    with st.expander("🔐 Connection Settings", expanded=not st.session_state.get('sh_enterprise_connected')):
        st.info("""
        **For 500+ accounts, connect to your Security Hub Delegated Administrator account.**
        
        This provides:
        - ✅ Aggregated findings from ALL member accounts
        - ✅ Single API connection point
        - ✅ Automatic cross-region aggregation
        - ✅ Centralized compliance view
        """)
        
        connection_method = st.radio(
            "Connection Method",
            ["Direct Credentials", "Assume Role (Recommended)", "Use Environment/IAM"],
            key="sh_connection_method"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if connection_method == "Direct Credentials":
                access_key = st.text_input("Access Key ID", type="password", key="sh_ent_access_key")
                secret_key = st.text_input("Secret Access Key", type="password", key="sh_ent_secret_key")
                role_arn = None
            elif connection_method == "Assume Role (Recommended)":
                role_arn = st.text_input(
                    "Delegated Admin Role ARN",
                    placeholder="arn:aws:iam::ACCOUNT_ID:role/SecurityHubReadOnly",
                    key="sh_ent_role_arn"
                )
                access_key = None
                secret_key = None
            else:
                access_key = None
                secret_key = None
                role_arn = None
        
        with col2:
            aggregation_region = st.selectbox(
                "Aggregation Region",
                [r.value for r in SecurityHubRegion],
                key="sh_ent_region"
            )
            
            st.markdown("**Required Permissions:**")
            st.code("""securityhub:DescribeHub
securityhub:GetFindings
securityhub:ListMembers
securityhub:GetEnabledStandards
securityhub:GetAdministratorAccount""", language="text")
        
        if st.button("🔗 Connect to Delegated Admin", use_container_width=True, key="sh_ent_connect_btn"):
            with st.spinner("Connecting to Security Hub Aggregator..."):
                result = manager.connect(
                    access_key=access_key if connection_method == "Direct Credentials" else None,
                    secret_key=secret_key if connection_method == "Direct Credentials" else None,
                    role_arn=role_arn if connection_method == "Assume Role (Recommended)" else None,
                    region=aggregation_region
                )
                
                if result.get("success"):
                    st.session_state['sh_enterprise_connected'] = True
                    st.session_state['sh_enterprise_info'] = result
                    st.success(f"✅ Connected to account {result['account_id']}")
                    
                    if result.get('is_administrator'):
                        st.success("🎯 This is the Security Hub Administrator account - you have aggregated access!")
                    else:
                        st.warning(f"⚠️ This is a member account. Administrator: {result.get('administrator_id')}")
                    
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'Connection failed')}")
    
    # Main dashboard (only if connected)
    if st.session_state.get('sh_enterprise_connected'):
        info = st.session_state.get('sh_enterprise_info', {})
        
        # Connection status bar
        st.markdown(f"""
        <div style="padding: 10px; background: linear-gradient(135deg, #1B5E20, #2E7D32); 
                    border-radius: 10px; color: white; margin-bottom: 20px;">
            <span style="font-weight: bold;">✅ Connected</span> | 
            Account: <code>{info.get('account_id', 'N/A')}</code> | 
            Region: <code>{info.get('region', 'N/A')}</code> |
            Administrator: {'✅ Yes' if info.get('is_administrator') else '❌ No'}
        </div>
        """, unsafe_allow_html=True)
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "👥 Member Accounts",
            "🔍 Findings",
            "📋 Compliance"
        ])
        
        with tab1:
            render_overview_tab(manager)
        
        with tab2:
            render_member_accounts_tab(manager)
        
        with tab3:
            render_findings_tab(manager)
        
        with tab4:
            render_compliance_tab(manager)
        
        # Disconnect button
        st.markdown("---")
        if st.button("❌ Disconnect", key="sh_ent_disconnect_btn"):
            st.session_state['sh_enterprise_connected'] = False
            st.session_state.pop('sh_enterprise_info', None)
            st.session_state.pop('security_hub_manager', None)
            st.rerun()


def render_overview_tab(manager: EnterpriseSecurityHubManager):
    """Render overview tab with summary metrics"""
    
    st.markdown("### 📊 Security Posture Overview")
    
    with st.spinner("Loading aggregated findings from 500+ accounts..."):
        try:
            # Get member summary
            member_summary = manager.get_member_accounts_summary()
            
            # Get findings summary
            findings_summary = manager.get_findings_summary()
            
            # Top metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "Total Accounts",
                    member_summary.get('total_accounts', 0),
                    f"{member_summary.get('enabled_accounts', 0)} enabled"
                )
            
            with col2:
                st.metric(
                    "Total Findings",
                    f"{findings_summary.get('total_findings', 0):,}"
                )
            
            with col3:
                critical = findings_summary.get('by_severity', {}).get('CRITICAL', 0)
                st.metric(
                    "Critical",
                    critical,
                    delta=None,
                    delta_color="inverse"
                )
            
            with col4:
                high = findings_summary.get('by_severity', {}).get('HIGH', 0)
                st.metric(
                    "High",
                    high
                )
            
            with col5:
                compliance_rate = findings_summary.get('compliance_rate', 0)
                st.metric(
                    "Compliance Rate",
                    f"{compliance_rate:.1f}%"
                )
            
            # Severity breakdown
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Findings by Severity")
                severity_data = findings_summary.get('by_severity', {})
                for sev, count in severity_data.items():
                    color = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠',
                        'MEDIUM': '🟡',
                        'LOW': '🟢',
                        'INFORMATIONAL': '🔵'
                    }.get(sev, '⚪')
                    st.markdown(f"{color} **{sev}**: {count:,}")
            
            with col2:
                st.markdown("#### Top Products")
                product_data = findings_summary.get('by_product', {})
                sorted_products = sorted(product_data.items(), key=lambda x: x[1], reverse=True)[:5]
                for product, count in sorted_products:
                    st.markdown(f"• **{product}**: {count:,}")
            
            # Top accounts by findings
            st.markdown("---")
            st.markdown("#### 🏆 Top 10 Accounts by Finding Count")
            
            top_accounts = findings_summary.get('top_accounts_by_findings', [])
            if top_accounts:
                for i, (account_id, stats) in enumerate(top_accounts, 1):
                    critical_badge = f"🔴 {stats['critical']}" if stats['critical'] > 0 else ""
                    high_badge = f"🟠 {stats['high']}" if stats['high'] > 0 else ""
                    
                    st.markdown(
                        f"**{i}.** `{account_id}` - {stats['total']:,} findings "
                        f"{critical_badge} {high_badge}"
                    )
            
        except Exception as e:
            st.error(f"Error loading overview: {str(e)}")


def render_member_accounts_tab(manager: EnterpriseSecurityHubManager):
    """Render member accounts tab"""
    
    st.markdown("### 👥 Member Accounts")
    
    with st.spinner("Loading member accounts..."):
        try:
            summary = manager.get_member_accounts_summary()
            
            # Status metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Accounts", summary.get('total_accounts', 0))
            with col2:
                st.metric("Enabled", summary.get('enabled_accounts', 0))
            with col3:
                st.metric("Pending", summary.get('pending_accounts', 0))
            with col4:
                st.metric("Disabled", summary.get('disabled_accounts', 0))
            
            # Status breakdown
            st.markdown("#### Status Breakdown")
            for status, count in summary.get('by_status', {}).items():
                st.markdown(f"• **{status}**: {count}")
            
            # Accounts list (limited for performance)
            st.markdown("---")
            st.markdown(f"#### Account List (showing first {len(summary.get('accounts_list', []))})")
            
            accounts_list = summary.get('accounts_list', [])
            
            if accounts_list:
                # Create dataframe for display
                import pandas as pd
                df = pd.DataFrame(accounts_list)
                df = df[['account_id', 'email', 'status', 'updated_at']]
                df.columns = ['Account ID', 'Email', 'Status', 'Last Updated']
                
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No member accounts found. This might be a standalone account.")
                
        except Exception as e:
            st.error(f"Error loading accounts: {str(e)}")


def render_findings_tab(manager: EnterpriseSecurityHubManager):
    """Render findings exploration tab"""
    
    st.markdown("### 🔍 Findings Explorer")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.multiselect(
            "Severity",
            ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"],
            default=["CRITICAL", "HIGH"],
            key="sh_findings_severity"
        )
    
    with col2:
        max_results = st.slider("Max Results", 10, 500, 100, key="sh_max_results")
    
    with col3:
        sort_order = st.selectbox("Sort", ["desc", "asc"], key="sh_sort_order")
    
    if st.button("🔍 Search Findings", use_container_width=True, key="sh_search_findings_btn"):
        with st.spinner("Searching across all accounts..."):
            try:
                findings = list(manager.get_aggregated_findings(
                    severity_filter=severity_filter if severity_filter else None,
                    max_results=max_results,
                    sort_order=sort_order
                ))
                
                st.success(f"Found {len(findings)} findings")
                
                # Display findings
                for finding in findings[:50]:  # Display first 50
                    severity = finding.get('severity', 'UNKNOWN')
                    color = {
                        'CRITICAL': '#F44336',
                        'HIGH': '#FF9800',
                        'MEDIUM': '#2196F3',
                        'LOW': '#4CAF50'
                    }.get(severity, '#666')
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 10px; border-left: 4px solid {color}; 
                                    background: #f5f5f5; margin-bottom: 10px; border-radius: 5px;">
                            <span style="background: {color}; color: white; padding: 2px 6px; 
                                        border-radius: 3px; font-size: 11px;">{severity}</span>
                            <strong style="margin-left: 10px;">{finding.get('title', 'N/A')}</strong>
                            <br><small>
                                Account: <code>{finding.get('account_id', 'N/A')}</code> | 
                                Resource: {finding.get('resource_type', 'N/A')} | 
                                Product: {finding.get('product_name', 'N/A')}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Error searching findings: {str(e)}")


def render_compliance_tab(manager: EnterpriseSecurityHubManager):
    """Render compliance standards tab"""
    
    st.markdown("### 📋 Compliance Standards")
    
    with st.spinner("Loading compliance standards..."):
        try:
            standards = manager.get_enabled_standards()
            
            if not standards:
                st.warning("No security standards enabled. Enable standards in Security Hub console.")
                return
            
            st.success(f"Found {len(standards)} enabled standards")
            
            for std in standards:
                arn = std.get('arn', '')
                # Extract friendly name from ARN
                std_name = arn.split('/')[-2] if '/' in arn else arn
                status = std.get('status', 'UNKNOWN')
                
                status_icon = '✅' if status == 'READY' else '⏳' if status == 'PENDING' else '❌'
                
                with st.expander(f"{status_icon} {std_name} ({status})"):
                    st.code(arn)
                    
                    if std.get('status_reason'):
                        st.caption(f"Status reason: {std['status_reason']}")
                    
        except Exception as e:
            st.error(f"Error loading standards: {str(e)}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Enterprise Security Hub", layout="wide")
    render_enterprise_security_hub_dashboard()
