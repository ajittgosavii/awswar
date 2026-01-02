# Security Hub Integration for 500+ AWS Accounts

## Executive Summary

When managing Security Hub across 500+ AWS accounts in an Organization, **you do NOT need to connect to each account individually**. AWS Security Hub supports a **Delegated Administrator** pattern that aggregates findings from all member accounts automatically.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AWS ORGANIZATION (500+ Accounts)                          │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     MANAGEMENT ACCOUNT                                  │ │
│  │  • AWS Organizations root                                               │ │
│  │  • Delegates Security Hub admin to Security Account                     │ │
│  │  • Should NOT be used for day-to-day operations                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│                     Designate Delegated Administrator                        │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │               SECURITY TOOLING ACCOUNT (Delegated Admin)                │ │
│  │                                                                          │ │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │ │
│  │  │                   SECURITY HUB AGGREGATOR                         │  │ │
│  │  │                                                                    │  │ │
│  │  │  • Aggregation Region: us-east-1 (or your choice)                 │  │ │
│  │  │  • Cross-Region Aggregation: ENABLED                              │  │ │
│  │  │  • Auto-Enable for new accounts: ENABLED                          │  │ │
│  │  │                                                                    │  │ │
│  │  │  API Endpoints:                                                    │  │ │
│  │  │  ├── GetFindings → All 500+ accounts' findings                    │  │ │
│  │  │  ├── ListMembers → All member accounts                            │  │ │
│  │  │  └── GetEnabledStandards → Compliance status                      │  │ │
│  │  └──────────────────────────────────────────────────────────────────┘  │ │
│  │                                                                          │ │
│  │  This is where our WAF Scanner connects! ◄───────────────────────────── │ │
│  │  Single API connection = All 500 accounts                                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│              Automatic Finding Aggregation (via AWS)                         │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         │                          │                          │              │
│         ▼                          ▼                          ▼              │
│  ┌─────────────┐           ┌─────────────┐           ┌─────────────┐        │
│  │  Account 1  │           │  Account 2  │    ...    │ Account 500 │        │
│  │  (Member)   │           │  (Member)   │           │  (Member)   │        │
│  │             │           │             │           │             │        │
│  │ GuardDuty   │           │ GuardDuty   │           │ GuardDuty   │        │
│  │ Inspector   │           │ Inspector   │           │ Inspector   │        │
│  │ Config      │           │ Config      │           │ Config      │        │
│  │ Macie       │           │ Macie       │           │ Macie       │        │
│  └─────────────┘           └─────────────┘           └─────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### 1. Delegated Administrator Pattern

Instead of querying 500 accounts individually, AWS Security Hub allows you to:

1. **Designate a Delegated Administrator** account
2. **Automatically aggregate** findings from all member accounts
3. **Single API endpoint** returns findings from ALL accounts
4. **Cross-region aggregation** consolidates multi-region findings

### 2. Why This Matters

| Approach | API Calls for 500 Accounts | Time | Complexity |
|----------|---------------------------|------|------------|
| Individual Account Scanning | 500+ calls | Hours | High |
| **Delegated Admin (Recommended)** | **1 call** | **Seconds** | **Low** |

### 3. What Gets Aggregated

Security Hub automatically aggregates findings from:
- **AWS GuardDuty** - Threat detection
- **Amazon Inspector** - Vulnerability scanning
- **AWS Config** - Configuration compliance
- **Amazon Macie** - Data security
- **IAM Access Analyzer** - Access analysis
- **AWS Firewall Manager** - Firewall compliance
- **Third-party integrations** - Any integrated products

---

## Setup Instructions

### Step 1: Enable Organization Integration

In the **Management Account**, enable Security Hub organization integration:

```bash
# Enable Security Hub in management account first
aws securityhub enable-security-hub --region us-east-1

# Designate delegated administrator
aws securityhub enable-organization-admin-account \
    --admin-account-id 123456789012 \
    --region us-east-1
```

### Step 2: Configure Delegated Admin Account

In the **Delegated Admin Account**:

```bash
# Enable auto-enable for new accounts
aws securityhub update-organization-configuration \
    --auto-enable \
    --region us-east-1

# Enable cross-region aggregation
aws securityhub create-finding-aggregator \
    --region-linking-mode ALL_REGIONS \
    --region us-east-1
```

### Step 3: Create IAM Role for WAF Scanner

Create a read-only role in the Delegated Admin account:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "SecurityHubReadOnly",
            "Effect": "Allow",
            "Action": [
                "securityhub:DescribeHub",
                "securityhub:GetFindings",
                "securityhub:ListMembers",
                "securityhub:GetAdministratorAccount",
                "securityhub:GetEnabledStandards",
                "securityhub:DescribeStandardsControls",
                "securityhub:GetInsights",
                "securityhub:GetInsightResults"
            ],
            "Resource": "*"
        }
    ]
}
```

### Step 4: Connect WAF Scanner

```python
from security_hub_enterprise import EnterpriseSecurityHubManager

# Option 1: AssumeRole to Delegated Admin (Recommended)
manager = EnterpriseSecurityHubManager()
result = manager.connect(
    role_arn="arn:aws:iam::SECURITY_ACCOUNT_ID:role/SecurityHubReadOnly",
    region="us-east-1"
)

# Option 2: Direct credentials in Delegated Admin
manager = EnterpriseSecurityHubManager()
result = manager.connect(
    access_key="AKIA...",
    secret_key="...",
    region="us-east-1"
)
```

---

## API Usage Examples

### Get All Member Accounts (500+)

```python
# Generator pattern - memory efficient for 500+ accounts
for account in manager.get_all_member_accounts():
    print(f"Account: {account['account_id']} - Status: {account['status']}")

# Or get summary
summary = manager.get_member_accounts_summary()
print(f"Total accounts: {summary['total_accounts']}")
print(f"Enabled: {summary['enabled_accounts']}")
```

### Get Aggregated Findings

```python
# Get critical findings from ALL 500 accounts in one call
for finding in manager.get_aggregated_findings(
    severity_filter=["CRITICAL", "HIGH"],
    max_results=1000
):
    print(f"[{finding['account_id']}] {finding['title']}")

# Get summary statistics
summary = manager.get_findings_summary()
print(f"Total findings across all accounts: {summary['total_findings']}")
print(f"Critical: {summary['by_severity']['CRITICAL']}")
```

### Filter by Specific Accounts

```python
# If you only want findings from specific accounts
target_accounts = ["111111111111", "222222222222"]

for finding in manager.get_aggregated_findings(
    account_ids=target_accounts,
    severity_filter=["CRITICAL"]
):
    print(finding)
```

---

## Performance Optimization

### Caching

The module implements caching to reduce API calls:

```python
from security_hub_enterprise import SecurityHubConfig, EnterpriseSecurityHubManager

config = SecurityHubConfig(
    cache_ttl_seconds=600,  # 10 minute cache
    pagination_batch_size=100
)

manager = EnterpriseSecurityHubManager(config=config)
```

### Pagination

For 500+ accounts with potentially millions of findings:

```python
# Generator pattern prevents loading everything into memory
for finding in manager.get_aggregated_findings():
    # Process one finding at a time
    process_finding(finding)
    
# Or batch process
batch = []
for finding in manager.get_aggregated_findings(max_results=10000):
    batch.append(finding)
    if len(batch) >= 100:
        process_batch(batch)
        batch = []
```

---

## Integration with WAF Assessment

### Automatic Pillar Scoring

Security Hub findings can automatically influence WAF pillar scores:

```python
def calculate_security_pillar_score(manager):
    """Use Security Hub findings to calculate Security pillar score"""
    summary = manager.get_findings_summary()
    
    # Base score
    score = 100
    
    # Deduct for critical findings
    score -= summary['by_severity']['CRITICAL'] * 5
    score -= summary['by_severity']['HIGH'] * 2
    score -= summary['by_severity']['MEDIUM'] * 0.5
    
    # Compliance bonus
    compliance_rate = summary.get('compliance_rate', 0)
    score = (score + compliance_rate) / 2
    
    return max(0, min(100, score))
```

### Cross-Reference with WAF Questions

```python
# Map Security Hub standards to WAF pillars
STANDARD_TO_PILLAR = {
    "aws-foundational-security-best-practices": "Security",
    "cis-aws-foundations-benchmark": "Security",
    "pci-dss": "Security",
    "nist-800-53": ["Security", "Operational Excellence"]
}
```

---

## Troubleshooting

### "Access Denied" Errors

1. Verify you're connecting to the **Delegated Admin** account, not a member
2. Check IAM permissions include `securityhub:ListMembers`
3. Ensure the role has cross-account trust if using AssumeRole

### "Security Hub Not Enabled"

```bash
# Check if Security Hub is enabled
aws securityhub describe-hub --region us-east-1

# If not enabled, enable it:
aws securityhub enable-security-hub --region us-east-1
```

### Missing Member Accounts

1. Check organization integration is enabled
2. Verify auto-enable is configured
3. Some accounts may need manual invitation

```bash
# List all members
aws securityhub list-members --region us-east-1

# Invite specific account
aws securityhub create-members \
    --account-details AccountId=123456789012,Email=account@company.com \
    --region us-east-1
```

---

## Cost Considerations

Security Hub pricing (as of 2024):
- **Finding ingestion**: ~$0.0001 per finding
- **Security checks**: First 10,000 free, then ~$0.0003 per check

For 500 accounts, typical monthly cost:
- ~$500-2,000/month depending on finding volume
- Much cheaper than individual account scanning tools

---

## Summary

| Feature | Individual Scanning | Delegated Admin |
|---------|-------------------|-----------------|
| API Connections | 500+ | 1 |
| Setup Complexity | High | Low (one-time) |
| Maintenance | Per-account | Centralized |
| Finding Coverage | Manual selection | Automatic |
| Cross-Region | Manual aggregation | Automatic |
| New Accounts | Manual setup | Auto-enabled |
| **Recommendation** | ❌ | ✅ **Use This** |

---

## Files Created

1. `security_hub_enterprise.py` - Enterprise Security Hub manager
2. `docs/SECURITY_HUB_500_ACCOUNTS_GUIDE.md` - This documentation

---

## Next Steps

1. Set up Delegated Administrator in your AWS Organization
2. Enable cross-region aggregation
3. Create read-only IAM role for WAF Scanner
4. Configure secrets in Streamlit:

```toml
# .streamlit/secrets.toml
[security_hub]
delegated_admin_role_arn = "arn:aws:iam::ACCOUNT:role/SecurityHubReadOnly"
aggregation_region = "us-east-1"
```
