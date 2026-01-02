# Multi-Level Reporting Integration Guide
## Security Hub Approach for Multi-Account WAF Reviews

---

## Overview

This guide explains how to integrate **Multi-Level Reporting** with your existing **Security Hub + Manual Scan** approach for AWS Well-Architected Framework reviews.

**Your Approach:**
1. ✅ Manual scan input for account metadata
2. ✅ AWS Security Hub for cross-account findings aggregation  
3. ✅ **NEW:** Multi-level reporting system

**Why This Works Better:**
- ❌ **Not using AWS Organizations discovery** - avoids complexity and permission issues
- ✅ **Using Security Hub** - already aggregates findings across accounts
- ✅ **Manual input** - flexible, works with any account structure
- ✅ **Industry standard** - same approach as Fortune 500 companies

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│         YOUR MULTI-ACCOUNT WAF REVIEW ARCHITECTURE          │
└─────────────────────────────────────────────────────────────┘

INPUT LAYER (Manual + Automated)
├── Manual Account Input
│   ├── Account ID, Name, Environment
│   ├── Tier assignment (1-5)
│   ├── Compliance scope (PCI/HIPAA/SOC2)
│   └── Owner and business unit info
│
└── AWS Security Hub (Automated)
    ├── Cross-account findings aggregation
    ├── Compliance standards enabled
    ├── Severity categorization
    └── Resource identification

DATA AGGREGATION LAYER
├── SecurityHubAggregator
│   ├── Fetches findings from Security Hub
│   ├── Groups by account
│   ├── Maps to WAF pillars
│   ├── Identifies common patterns
│   └── Calculates compliance scores
│
└── WAF Assessment Integration
    ├── Auto-detection from Security Hub
    ├── Manual WAF questionnaire
    ├── AI-powered recommendations
    └── Scorecard generation

REPORTING LAYER
├── Account-Level Reports
│   ├── Development teams
│   ├── Specific findings
│   └── Remediation actions
│
├── OU-Level Reports
│   ├── Engineering managers
│   ├── Aggregated trends
│   └── Resource planning
│
├── Organizational Reports
│   ├── Executives (CTO/CISO)
│   ├── Strategic overview
│   └── Top risks
│
└── Compliance Reports
    ├── Auditors
    ├── Framework-specific
    └── Evidence collection

EXPORT FORMATS
├── PDF (all report types)
├── Word/DOCX (all report types)
├── Excel/XLSX (OU and Compliance)
└── JSON (all report types)
```

---

## Prerequisites

### AWS Security Hub Setup

**1. Enable Security Hub**
```bash
# In management account or delegated administrator
aws securityhub enable-security-hub --region us-east-1
```

**2. Enable Cross-Account Aggregation**
```bash
# Designate aggregator region
aws securityhub create-finding-aggregator \
    --region us-east-1 \
    --region-linking-mode ALL_REGIONS
```

**3. Enable Compliance Standards**
```bash
# Enable AWS Foundational Security Best Practices
aws securityhub batch-enable-standards \
    --standards-subscription-requests StandardsArn=arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0

# Enable CIS AWS Foundations Benchmark
aws securityhub batch-enable-standards \
    --standards-subscription-requests StandardsArn=arn:aws:securityhub:us-east-1::standards/cis-aws-foundations-benchmark/v/1.2.0

# Enable PCI DSS
aws securityhub batch-enable-standards \
    --standards-subscription-requests StandardsArn=arn:aws:securityhub:us-east-1::standards/pci-dss/v/3.2.1
```

**4. Integrate Member Accounts**
```bash
# Invite accounts to Security Hub
aws securityhub create-members \
    --account-details AccountId=123456789012,Email=account@example.com

# Accept invitation from member account
aws securityhub accept-invitation \
    --master-id <management-account-id> \
    --invitation-id <invitation-id>
```

### Python Dependencies

**Install Required Packages:**
```bash
pip install streamlit pandas reportlab python-docx openpyxl boto3
```

---

## Integration Steps

### Step 1: Add Multi-Level Reporting Module

**Copy the file to your project:**
```bash
cp multi_level_reporting_securityhub.py <your-project>/
```

**File location in your project:**
```
aws-waf-advisor-FINAL/
├── multi_level_reporting_securityhub.py  # ← NEW MODULE
├── aws_security.py                       # ← Existing Security Hub integration
├── pdf_report_generator_multiaccount.py  # ← Existing PDF generator
├── waf_review_module.py                  # ← Existing WAF module
└── streamlit_app.py                      # ← Main application
```

### Step 2: Update Main Application

**Edit `streamlit_app.py`:**

```python
# Add import at the top
try:
    from multi_level_reporting_securityhub import render_multi_level_reporting
    MULTI_LEVEL_REPORTING = True
except ImportError:
    MULTI_LEVEL_REPORTING = False

# Add to your navigation/menu
if MULTI_LEVEL_REPORTING:
    if selected_module == "Multi-Level Reporting":
        render_multi_level_reporting()
```

**Or create a new page:**

```python
# Create: pages/Multi_Level_Reporting.py
import streamlit as st
from multi_level_reporting_securityhub import render_multi_level_reporting

render_multi_level_reporting()
```

### Step 3: Integrate with Security Hub

**Update `aws_security.py` to export findings in compatible format:**

```python
class SecurityManager:
    # ... existing code ...
    
    def get_findings_for_reporting(self, account_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Get Security Hub findings formatted for multi-level reporting
        
        Returns findings grouped by account
        """
        findings_by_account = {}
        
        # Get all findings
        all_findings = self.list_security_findings(limit=1000)
        
        for finding in all_findings:
            # Extract account from resource ARN
            resource_id = finding.get('resource_id', '')
            account_id = self._extract_account_id(resource_id)
            
            # Filter if account_ids specified
            if account_ids and account_id not in account_ids:
                continue
            
            # Group by account
            if account_id not in findings_by_account:
                findings_by_account[account_id] = []
            
            findings_by_account[account_id].append(finding)
        
        return findings_by_account
    
    def _extract_account_id(self, arn: str) -> str:
        """Extract account ID from ARN"""
        try:
            parts = arn.split(':')
            if len(parts) >= 5:
                return parts[4]
        except:
            pass
        return "unknown"
```

### Step 4: Create Account Profile Management

**Create `account_profile_manager.py`:**

```python
"""
Account Profile Manager
Manages manual account metadata for multi-level reporting
"""

import streamlit as st
import json
from typing import List, Dict
from dataclasses import dataclass, asdict

@dataclass
class AccountProfile:
    account_id: str
    account_name: str
    environment: str
    tier: str
    owner_email: str = ""
    business_unit: str = ""
    compliance_frameworks: List[str] = None
    ou_name: str = ""
    
    def __post_init__(self):
        if self.compliance_frameworks is None:
            self.compliance_frameworks = []

class AccountProfileManager:
    """Manage account profiles for reporting"""
    
    def __init__(self):
        self.profiles_key = 'account_profiles'
        self._init_session_state()
    
    def _init_session_state(self):
        if self.profiles_key not in st.session_state:
            st.session_state[self.profiles_key] = {}
    
    def add_profile(self, profile: AccountProfile):
        """Add or update account profile"""
        st.session_state[self.profiles_key][profile.account_id] = asdict(profile)
    
    def get_profile(self, account_id: str) -> AccountProfile:
        """Get account profile"""
        profile_dict = st.session_state[self.profiles_key].get(account_id)
        if profile_dict:
            return AccountProfile(**profile_dict)
        return None
    
    def get_all_profiles(self) -> List[AccountProfile]:
        """Get all account profiles"""
        return [
            AccountProfile(**p) 
            for p in st.session_state[self.profiles_key].values()
        ]
    
    def get_profiles_by_ou(self, ou_name: str) -> List[AccountProfile]:
        """Get all profiles in an OU"""
        return [
            p for p in self.get_all_profiles()
            if p.ou_name == ou_name
        ]
    
    def get_profiles_by_compliance(self, framework: str) -> List[AccountProfile]:
        """Get profiles with specific compliance framework"""
        return [
            p for p in self.get_all_profiles()
            if framework in p.compliance_frameworks
        ]
    
    def import_from_csv(self, csv_file):
        """Import account profiles from CSV"""
        import pandas as pd
        
        df = pd.read_csv(csv_file)
        
        for _, row in df.iterrows():
            profile = AccountProfile(
                account_id=row['account_id'],
                account_name=row['account_name'],
                environment=row.get('environment', 'unknown'),
                tier=row.get('tier', 'Tier 3 - Medium'),
                owner_email=row.get('owner_email', ''),
                business_unit=row.get('business_unit', ''),
                ou_name=row.get('ou_name', '')
            )
            
            # Handle compliance frameworks (comma-separated)
            if 'compliance_frameworks' in row:
                frameworks = row['compliance_frameworks'].split(',')
                profile.compliance_frameworks = [f.strip() for f in frameworks if f.strip()]
            
            self.add_profile(profile)
    
    def export_to_csv(self) -> str:
        """Export account profiles to CSV"""
        import pandas as pd
        
        profiles = self.get_all_profiles()
        
        data = []
        for profile in profiles:
            data.append({
                'account_id': profile.account_id,
                'account_name': profile.account_name,
                'environment': profile.environment,
                'tier': profile.tier,
                'owner_email': profile.owner_email,
                'business_unit': profile.business_unit,
                'ou_name': profile.ou_name,
                'compliance_frameworks': ','.join(profile.compliance_frameworks)
            })
        
        df = pd.DataFrame(data)
        return df.to_csv(index=False)


def render_account_profile_manager():
    """UI for managing account profiles"""
    
    st.header("📝 Account Profile Manager")
    st.markdown("Manage account metadata for multi-level reporting")
    
    manager = AccountProfileManager()
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Account", "📋 View All", "📤 Import/Export"])
    
    with tab1:
        st.subheader("Add Account Profile")
        
        col1, col2 = st.columns(2)
        
        with col1:
            account_id = st.text_input("Account ID *", key="add_account_id")
            account_name = st.text_input("Account Name *", key="add_account_name")
            environment = st.selectbox("Environment", 
                ["production", "staging", "development", "test", "sandbox"],
                key="add_environment")
            tier = st.selectbox("Tier",
                ["Tier 1 - Critical", "Tier 2 - High", "Tier 3 - Medium", 
                 "Tier 4 - Infrastructure", "Tier 5 - Low"],
                key="add_tier")
        
        with col2:
            owner_email = st.text_input("Owner Email", key="add_owner")
            business_unit = st.text_input("Business Unit", key="add_bu")
            ou_name = st.text_input("OU Name", key="add_ou")
            compliance = st.multiselect("Compliance Frameworks",
                ["PCI-DSS", "HIPAA", "SOC2", "ISO 27001", "NIST CSF"],
                key="add_compliance")
        
        if st.button("➕ Add Account Profile", type="primary"):
            if account_id and account_name:
                profile = AccountProfile(
                    account_id=account_id,
                    account_name=account_name,
                    environment=environment,
                    tier=tier,
                    owner_email=owner_email,
                    business_unit=business_unit,
                    compliance_frameworks=compliance,
                    ou_name=ou_name
                )
                manager.add_profile(profile)
                st.success(f"✅ Added profile for {account_name}")
            else:
                st.error("Please provide Account ID and Name")
    
    with tab2:
        st.subheader("All Account Profiles")
        
        profiles = manager.get_all_profiles()
        
        if profiles:
            import pandas as pd
            
            df_data = []
            for p in profiles:
                df_data.append({
                    'Account ID': p.account_id,
                    'Name': p.account_name,
                    'Environment': p.environment,
                    'Tier': p.tier,
                    'OU': p.ou_name,
                    'Compliance': ', '.join(p.compliance_frameworks) if p.compliance_frameworks else 'None'
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)
            
            st.info(f"📊 Total accounts: {len(profiles)}")
        else:
            st.info("No account profiles added yet")
    
    with tab3:
        st.subheader("Import/Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Import from CSV")
            
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file:
                if st.button("📥 Import Accounts"):
                    manager.import_from_csv(uploaded_file)
                    st.success("✅ Accounts imported successfully")
            
            st.markdown("**CSV Format:**")
            st.code("""
account_id,account_name,environment,tier,owner_email,ou_name,compliance_frameworks
123456789012,prod-app-1,production,Tier 1 - Critical,team@example.com,Production OU,PCI-DSS,SOC2
234567890123,dev-app-1,development,Tier 5 - Low,dev@example.com,Development OU,
            """, language="csv")
        
        with col2:
            st.markdown("### Export to CSV")
            
            csv_data = manager.export_to_csv()
            
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"account_profiles_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
```

---

## Usage Workflow

### Workflow 1: Single Account Report

**For development teams**

```
1. Navigate to "Multi-Level Reporting" → "Account Reports"

2. Enter account details:
   - Account ID: 123456789012
   - Account Name: prod-app-1
   - Environment: production
   - Tier: Tier 1 - Critical
   - Owner: team@example.com

3. Select format: PDF / Word / JSON

4. Click "Generate Account Report"

5. System:
   - Fetches Security Hub findings for this account
   - Calculates WAF scorecard
   - Identifies immediate actions
   - Generates detailed report

6. Download report for development team
```

**Report Contains:**
- ✅ Account-specific Security Hub findings
- ✅ Severity breakdown (Critical/High/Medium/Low)
- ✅ WAF pillar scores for this account
- ✅ Immediate action items (Critical/High findings)
- ✅ Short-term actions (Medium findings)
- ✅ Long-term improvements (Low findings)
- ✅ Team-specific remediation instructions

### Workflow 2: OU Report

**For engineering managers**

```
1. Navigate to "Multi-Level Reporting" → "OU Reports"

2. Enter OU details:
   - OU Name: Production OU
   - Number of accounts: 5

3. For each account, provide:
   - Account ID and Name
   - Environment
   (or bulk import from CSV)

4. Select format: PDF / Word / Excel / JSON

5. Click "Generate OU Report"

6. System:
   - Fetches Security Hub findings for all accounts in OU
   - Aggregates findings
   - Identifies common patterns
   - Compares team performance
   - Estimates resource needs

7. Download report for manager
```

**Report Contains:**
- ✅ OU summary (total accounts, findings)
- ✅ Common issues across all OU accounts
- ✅ Team comparison (which accounts have most issues)
- ✅ Resource estimation (engineer days, costs)
- ✅ Pillar breakdown across OU
- ✅ OU-level recommendations

### Workflow 3: Executive Report

**For CTO/CISO**

```
1. Navigate to "Multi-Level Reporting" → "Executive Reports"

2. Enter organization details:
   - Organization Name: AWS Organization
   - Total accounts: 50

3. Select format: PDF / Word / JSON

4. Click "Generate Executive Report"

5. System:
   - Fetches Security Hub findings from all accounts
   - Calculates organization-wide metrics
   - Identifies top 10 risks
   - Generates strategic recommendations
   - Estimates investment needs

6. Download 1-2 page executive summary
```

**Report Contains:**
- ✅ Executive summary (1-2 pages)
- ✅ Overall risk level (CRITICAL/HIGH/MEDIUM/LOW)
- ✅ Compliance status
- ✅ Top 10 organizational risks
- ✅ Strategic recommendations
- ✅ Investment priorities
- ✅ Budget requirements
- ✅ Industry benchmarking

### Workflow 4: Compliance Report

**For auditors**

```
1. Navigate to "Multi-Level Reporting" → "Compliance Reports"

2. Select framework:
   - PCI-DSS / HIPAA / SOC2 / ISO 27001

3. Enter accounts in scope: 10

4. Select format: PDF / Word / Excel / JSON

5. Click "Generate Compliance Report"

6. System:
   - Filters Security Hub findings to compliance-scoped accounts
   - Maps findings to framework controls
   - Generates evidence collection
   - Creates gap analysis
   - Builds remediation timeline

7. Download audit-ready compliance report
```

**Report Contains:**
- ✅ Control coverage (passed/failed)
- ✅ Account-by-account compliance matrix
- ✅ Evidence by control
- ✅ Gap analysis
- ✅ Remediation timeline
- ✅ Audit trail

---

## Security Hub Mapping to WAF Pillars

### How Security Hub Findings Map to WAF

```python
Security Hub Finding → WAF Pillar Mapping:

1. SECURITY Pillar
   - S3 bucket public access
   - Unencrypted resources
   - IAM overly permissive policies
   - Security group unrestricted access
   - Missing MFA
   - Exposed credentials

2. RELIABILITY Pillar
   - No backup enabled
   - Single AZ deployment
   - No failover configuration
   - RDS not multi-AZ
   - No disaster recovery plan

3. OPERATIONAL EXCELLENCE Pillar
   - CloudTrail not enabled
   - No CloudWatch alarms
   - Missing monitoring
   - No automation
   - Poor operational procedures

4. PERFORMANCE Pillar
   - Unoptimized instance types
   - Inefficient data transfer
   - No caching configured
   - Poor network configuration

5. COST OPTIMIZATION Pillar
   - Unattached EBS volumes
   - Underutilized instances
   - No reserved instances
   - Idle resources
   - Unoptimized storage

6. SUSTAINABILITY Pillar
   - Inefficient resource usage
   - Poor instance sizing
   - Excessive carbon footprint
```

---

## Benefits of This Approach

### ✅ Advantages

**1. No Organization Discovery Complexity**
- ❌ Avoids AWS Organizations API permissions
- ❌ No delegated administrator setup needed
- ✅ Works with any account structure
- ✅ Flexible manual input

**2. Leverages Security Hub**
- ✅ Already aggregates findings across accounts
- ✅ Compliance standards built-in
- ✅ Continuous monitoring
- ✅ Industry-standard security checks

**3. Industry-Standard Reporting**
- ✅ Account-level (for teams)
- ✅ OU-level (for managers)
- ✅ Organizational (for executives)
- ✅ Compliance (for auditors)

**4. Multiple Export Formats**
- ✅ PDF (all stakeholders)
- ✅ Word (editable documentation)
- ✅ Excel (data analysis)
- ✅ JSON (automation/integration)

**5. Scalable**
- ✅ Works with 1 or 1000 accounts
- ✅ Incremental implementation
- ✅ No architectural changes needed

### ⚠️ Limitations

**1. Manual Account Management**
- Requires maintaining account metadata
- ❌ Mitigation: CSV import/export for bulk updates

**2. Security Hub Dependency**
- Requires Security Hub enabled in all accounts
- ❌ Mitigation: Gradual rollout by tier

**3. Initial Setup**
- Need to configure Security Hub cross-account
- ❌ Mitigation: One-time setup, then automated

---

## Testing Checklist

### Test 1: Account Report Generation
```
□ Add single account profile
□ Verify Security Hub integration
□ Generate PDF report
□ Generate Word report
□ Generate JSON report
□ Verify findings appear correctly
□ Check remediation actions
```

### Test 2: OU Report Generation
```
□ Add 3-5 account profiles to same OU
□ Generate OU report
□ Verify aggregation across accounts
□ Check common findings detection
□ Verify team comparison
□ Test Excel export
```

### Test 3: Executive Report
```
□ Configure organization with 10+ accounts
□ Generate executive PDF
□ Verify 1-2 page summary
□ Check strategic recommendations
□ Verify risk level calculation
□ Test benchmarking data
```

### Test 4: Compliance Report
```
□ Add accounts with compliance frameworks
□ Generate PCI-DSS report
□ Verify control mapping
□ Check compliance matrix
□ Test gap analysis
□ Verify remediation timeline
```

---

## Troubleshooting

### Issue 1: No Security Hub Findings

**Problem:** Report shows zero findings

**Solutions:**
```
1. Verify Security Hub is enabled:
   aws securityhub describe-hub

2. Check Security Hub has findings:
   aws securityhub get-findings --max-results 10

3. Verify cross-account aggregation:
   aws securityhub get-finding-aggregator

4. Check member accounts are associated:
   aws securityhub list-members
```

### Issue 2: Permission Errors

**Problem:** Cannot access Security Hub

**Solutions:**
```
1. Verify IAM permissions:
   {
     "Effect": "Allow",
     "Action": [
       "securityhub:GetFindings",
       "securityhub:DescribeHub",
       "securityhub:ListMembers",
       "securityhub:GetFindingAggregator"
     ],
     "Resource": "*"
   }

2. Run from management account or delegated admin

3. Verify Security Hub is enabled in the region
```

### Issue 3: Report Generation Fails

**Problem:** Error during report generation

**Solutions:**
```
1. Check all dependencies installed:
   pip install reportlab python-docx openpyxl pandas

2. Verify account profiles are complete

3. Check Security Hub data is accessible

4. Review error logs for specific issues
```

---

## Next Steps

1. **Deploy Multi-Level Reporting Module**
   - Copy module to your project
   - Update main application
   - Test with demo data

2. **Configure Security Hub**
   - Enable in all accounts
   - Set up cross-account aggregation
   - Enable compliance standards

3. **Create Account Profiles**
   - Use CSV import for bulk
   - Or add manually
   - Categorize by tier and compliance

4. **Generate First Reports**
   - Start with account-level
   - Then OU-level
   - Finally organizational

5. **Establish Reporting Cadence**
   - Monthly: Account reports for Tier 1
   - Quarterly: OU and Executive reports
   - Per audit: Compliance reports

---

## Summary

**Your Multi-Account WAF Reporting Solution:**

✅ **Data Source:** AWS Security Hub (cross-account)  
✅ **Input:** Manual account metadata (flexible)  
✅ **Reports:** 4 levels (Account/OU/Org/Compliance)  
✅ **Formats:** PDF, Word, Excel, JSON  
✅ **Integration:** Works with existing modules  
✅ **Industry Standard:** Matches Fortune 500 approach  

**Result:** Enterprise-grade multi-level reporting without the complexity of Organizations discovery!
