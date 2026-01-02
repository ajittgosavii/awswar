# AWS Connection Strategy & WAF Pillar Alignment Guide

## Overview

The AWS WAF Scanner Enterprise provides three connection strategies optimized for different scales and constraints. All findings are automatically mapped to AWS Well-Architected Framework (WAF) pillars for proper assessment scoring.

---

## Connection Modes

### Decision Matrix

| Criteria | Single Account | Multi-Account | Security Hub |
|----------|---------------|---------------|--------------|
| **Number of Accounts** | 1 | 2-500 | 500+ |
| **API Calls** | ~50 per scan | ~50 × N accounts | 1-10 total |
| **Setup Time** | 5 minutes | 30 minutes | 1-2 hours |
| **Prerequisites** | Access keys | Cross-account roles | Delegated Admin |
| **Best For** | Dev/Test, Quick scan | Production, Full control | Enterprise, API limits |
| **Rate Limit Risk** | Low | Medium-High | Very Low |

### When to Use Each Mode

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CONNECTION MODE SELECTION                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   How many AWS accounts do you need to assess?                          │
│                                                                          │
│              ┌──────────────┐                                           │
│              │   1 Account  │──────► SINGLE ACCOUNT MODE                │
│              └──────────────┘        - Direct credentials               │
│                                      - AWS profile                       │
│                                      - IAM role                          │
│                                                                          │
│              ┌──────────────┐                                           │
│              │  2-500       │──────► MULTI-ACCOUNT MODE                 │
│              │  Accounts    │        - AssumeRole per account           │
│              └──────────────┘        - Organizations discovery          │
│                                      - Parallel scanning                 │
│                                                                          │
│              ┌──────────────┐                                           │
│              │  500+        │──────► SECURITY HUB MODE                  │
│              │  Accounts    │        - Single aggregator connection     │
│              └──────────────┘        - Pre-aggregated findings          │
│                     │                - Minimal API calls                 │
│                     │                                                    │
│              ┌──────────────┐                                           │
│              │ API Rate     │──────► SECURITY HUB MODE                  │
│              │ Limit Issues │        (Even for fewer accounts)          │
│              └──────────────┘                                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Mode 1: Single Account Connection

### Use Case
- Individual AWS account assessment
- Development/testing environments
- Quick security posture check
- Learning and training

### Connection Methods

```python
from unified_aws_connector import UnifiedAWSConnector

connector = UnifiedAWSConnector()

# Method 1: Access Key + Secret Key
result = connector.connect_single_account(
    access_key="AKIA...",
    secret_key="...",
    region="us-east-1"
)

# Method 2: AWS Profile
result = connector.connect_single_account(
    profile_name="production",
    region="us-east-1"
)

# Method 3: Environment Variables / IAM Role (EC2, Lambda, ECS)
result = connector.connect_single_account(
    region="us-east-1"
)
```

### Required IAM Permissions

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "guardduty:ListDetectors",
                "guardduty:ListFindings",
                "guardduty:GetFindings",
                "inspector2:ListFindings",
                "config:DescribeComplianceByConfigRule",
                "iam:GetAccountSummary",
                "iam:ListUsers",
                "iam:GetCredentialReport",
                "securityhub:GetFindings",
                "ec2:DescribeInstances",
                "ec2:DescribeSecurityGroups",
                "s3:ListBuckets",
                "s3:GetBucketPolicy",
                "rds:DescribeDBInstances",
                "cloudtrail:DescribeTrails",
                "cloudwatch:DescribeAlarms"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## Mode 2: Multi-Account Connection

### Use Case
- AWS Organizations with 2-500 accounts
- Full control over what gets scanned
- Detailed per-account findings
- Custom scanning patterns

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MULTI-ACCOUNT SCANNING                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────┐                                               │
│   │   WAF Scanner       │                                               │
│   │   (Your Machine)    │                                               │
│   └──────────┬──────────┘                                               │
│              │                                                           │
│              │ AssumeRole                                                │
│              │                                                           │
│   ┌──────────┴──────────────────────────────────────────────────────┐   │
│   │                                                                  │   │
│   ▼                    ▼                    ▼                        │   │
│ ┌─────────────┐  ┌─────────────┐    ┌─────────────┐                 │   │
│ │  Account 1  │  │  Account 2  │    │  Account N  │                 │   │
│ │             │  │             │ .. │             │                 │   │
│ │ ┌─────────┐ │  │ ┌─────────┐ │    │ ┌─────────┐ │                 │   │
│ │ │CrossRole│ │  │ │CrossRole│ │    │ │CrossRole│ │                 │   │
│ │ └─────────┘ │  │ └─────────┘ │    │ └─────────┘ │                 │   │
│ └─────────────┘  └─────────────┘    └─────────────┘                 │   │
│                                                                          │
│   Parallel Scanning (configurable concurrency)                          │
│   Each account scanned independently                                     │
│   Findings aggregated with account_id                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Connection Methods

```python
from unified_aws_connector import UnifiedAWSConnector, AccountCredentials

connector = UnifiedAWSConnector()

# Method 1: Explicit Account List
accounts = [
    AccountCredentials(
        account_id="111111111111",
        role_arn="arn:aws:iam::111111111111:role/WAFScannerRole",
        alias="Production"
    ),
    AccountCredentials(
        account_id="222222222222",
        role_arn="arn:aws:iam::222222222222:role/WAFScannerRole",
        alias="Staging"
    ),
    AccountCredentials(
        account_id="333333333333",
        role_arn="arn:aws:iam::333333333333:role/WAFScannerRole",
        external_id="my-external-id",  # Optional
        alias="Development"
    )
]

result = connector.connect_multi_account(accounts=accounts)

# Method 2: Auto-discover from Organizations
management_session = boto3.Session(...)  # Management account credentials

result = connector.connect_multi_account(
    management_session=management_session,
    use_organizations=True,
    cross_account_role="OrganizationAccountAccessRole"
)
```

### Cross-Account Role Setup

Deploy this role in each member account:

```yaml
# CloudFormation Template: cross-account-role.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: WAF Scanner Cross-Account Role

Parameters:
  TrustedAccountId:
    Type: String
    Description: Account ID where WAF Scanner runs

Resources:
  WAFScannerRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: WAFScannerRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${TrustedAccountId}:root'
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/SecurityAudit
        - arn:aws:iam::aws:policy/ReadOnlyAccess
```

Deploy with StackSets:
```bash
aws cloudformation create-stack-set \
    --stack-set-name WAFScannerRole \
    --template-body file://cross-account-role.yaml \
    --parameters ParameterKey=TrustedAccountId,ParameterValue=YOUR_SCANNER_ACCOUNT \
    --permission-model SERVICE_MANAGED \
    --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false
```

---

## Mode 3: Security Hub Connection (500+ Accounts)

### Use Case
- Large enterprises with 500+ accounts
- API rate limit constraints
- Aggregated view requirement
- Compliance-focused assessments

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SECURITY HUB AGGREGATION                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────┐        ┌──────────────────────────────────┐   │
│   │   WAF Scanner       │        │     DELEGATED ADMINISTRATOR       │   │
│   │   (Your Machine)    │───────►│          ACCOUNT                  │   │
│   └─────────────────────┘        │                                    │   │
│         │                        │  ┌────────────────────────────┐   │   │
│         │ 1 API Call             │  │    SECURITY HUB            │   │   │
│         │                        │  │    AGGREGATOR              │   │   │
│         │                        │  │                            │   │   │
│         │                        │  │  Pre-aggregated findings   │   │   │
│         │                        │  │  from ALL 500+ accounts    │   │   │
│         │                        │  │                            │   │   │
│         └────────────────────────│  │  - GuardDuty findings      │   │   │
│                                  │  │  - Inspector findings      │   │   │
│                                  │  │  - Config compliance       │   │   │
│                                  │  │  - Macie findings          │   │   │
│                                  │  │  - Third-party products    │   │   │
│                                  │  └────────────────────────────┘   │   │
│                                  └──────────────────────────────────┘   │
│                                               ▲                          │
│                                               │                          │
│         ┌─────────────────────────────────────┴───────────────────────┐ │
│         │              AUTOMATIC AGGREGATION (by AWS)                  │ │
│         └─────────────────────────────────────────────────────────────┘ │
│                    ▲            ▲            ▲            ▲              │
│                    │            │            │            │              │
│              ┌─────┴───┐  ┌─────┴───┐  ┌─────┴───┐  ┌─────┴───┐        │
│              │ Acct 1  │  │ Acct 2  │  │  ...    │  │Acct 500+│        │
│              │ Member  │  │ Member  │  │         │  │ Member  │        │
│              └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Connection Methods

```python
from unified_aws_connector import UnifiedAWSConnector

connector = UnifiedAWSConnector()

# Method 1: AssumeRole to Delegated Admin (Recommended)
result = connector.connect_security_hub(
    role_arn="arn:aws:iam::SECURITY_ACCOUNT_ID:role/SecurityHubReadOnly",
    region="us-east-1"
)

# Method 2: Direct Credentials
result = connector.connect_security_hub(
    access_key="AKIA...",
    secret_key="...",
    region="us-east-1"
)
```

### Setup Requirements

1. **Enable Security Hub** in Management Account
2. **Designate Delegated Administrator**
3. **Enable Auto-Enable** for new accounts
4. **Enable Cross-Region Aggregation**

See `docs/SECURITY_HUB_500_ACCOUNTS_GUIDE.md` for detailed setup.

---

## WAF Pillar Alignment

### Pillar Mapping

All findings are automatically mapped to WAF pillars based on:

1. **Finding Type** (most specific)
2. **Resource Type**
3. **Source Service**
4. **Generator ID**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         WAF PILLAR MAPPING                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────┐     ┌─────────────────────────────────────────┐   │
│   │ Security Hub    │     │                                          │   │
│   │ Finding         │────►│   WAF Pillar Mapper                      │   │
│   │                 │     │                                          │   │
│   │ - Type          │     │   1. Check finding type                  │   │
│   │ - Resource      │     │   2. Check resource type                 │   │
│   │ - Product       │     │   3. Check product/service               │   │
│   │ - Generator     │     │   4. Default to Security                 │   │
│   └─────────────────┘     │                                          │   │
│                           │            ▼                              │   │
│                           │   ┌─────────────────────────────────┐    │   │
│                           │   │                                 │    │   │
│                           │   │  ⚙️  Operational Excellence     │    │   │
│                           │   │  🔒 Security                    │    │   │
│                           │   │  🛡️  Reliability                │    │   │
│                           │   │  ⚡ Performance Efficiency      │    │   │
│                           │   │  💰 Cost Optimization           │    │   │
│                           │   │  🌱 Sustainability              │    │   │
│                           │   │                                 │    │   │
│                           │   └─────────────────────────────────┘    │   │
│                           └─────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Mapping Rules

| Finding Source | WAF Pillar |
|----------------|------------|
| GuardDuty threats | Security |
| Inspector vulnerabilities | Security |
| IAM findings | Security |
| WAF/Shield findings | Security |
| KMS/Secrets Manager | Security |
| CloudWatch alarms | Operational Excellence |
| CloudTrail gaps | Operational Excellence |
| Config non-compliance | Operational Excellence |
| SSM issues | Operational Excellence |
| Backup failures | Reliability |
| RDS/DynamoDB issues | Reliability |
| S3 availability | Reliability |
| Load balancer health | Reliability |
| EC2 performance | Performance Efficiency |
| Lambda throttling | Performance Efficiency |
| CloudFront latency | Performance Efficiency |
| Cost anomalies | Cost Optimization |
| Unused resources | Cost Optimization |
| Compute Optimizer | Sustainability |

### Score Calculation

```python
# Score deduction per finding
CRITICAL: -10 points
HIGH: -5 points
MEDIUM: -2 points
LOW: -0.5 points

# Example calculation
Pillar: Security
Base Score: 100
Critical Findings: 3 → -30
High Findings: 10 → -50
Medium Findings: 5 → -10
─────────────────────
Final Score: 10/100
```

### Usage Example

```python
from unified_aws_connector import UnifiedAWSConnector, WAFPillar

connector = UnifiedAWSConnector()
connector.connect_security_hub(...)

# Get all findings with WAF pillar mapping
for finding in connector.get_findings():
    print(f"Pillar: {finding['waf_pillar']}")
    print(f"Title: {finding['title']}")
    print(f"Severity: {finding['severity']}")

# Get findings for specific pillar
for finding in connector.get_findings(pillar_filter=WAFPillar.SECURITY):
    print(finding)

# Calculate pillar scores
scores = connector.calculate_pillar_scores()
print(f"Overall Score: {scores['overall_score']}")
print(f"Security: {scores['pillar_scores']['Security']}")
print(f"Reliability: {scores['pillar_scores']['Reliability']}")
```

---

## Integration with WAF Assessment

### Automatic Score Integration

```python
# In your WAF assessment module
from unified_aws_connector import UnifiedAWSConnector

def run_waf_assessment():
    connector = UnifiedAWSConnector()
    
    # Connect based on environment
    if account_count > 500:
        connector.connect_security_hub(...)
    elif account_count > 1:
        connector.connect_multi_account(...)
    else:
        connector.connect_single_account(...)
    
    # Get pillar scores from real findings
    scores = connector.calculate_pillar_scores()
    
    # Use in WAF assessment
    st.session_state['waf_pillar_scores'] = scores['pillar_scores']
    st.session_state['waf_findings'] = list(connector.get_findings())
```

### Streamlit Session State

```python
# The connector automatically stores:
st.session_state['waf_pillar_scores'] = {
    "Operational Excellence": 72,
    "Security": 65,
    "Reliability": 78,
    "Performance Efficiency": 70,
    "Cost Optimization": 85,
    "Sustainability": 68
}

st.session_state['waf_findings'] = [
    {
        'id': '...',
        'title': 'Root account has access keys',
        'severity': 'CRITICAL',
        'waf_pillar': 'Security',
        'account_id': '123456789012',
        ...
    }
]
```

---

## Files Reference

| File | Description |
|------|-------------|
| `unified_aws_connector.py` | Main connector with 3 modes + WAF mapping |
| `security_hub_enterprise.py` | Detailed Security Hub integration |
| `docs/SECURITY_HUB_500_ACCOUNTS_GUIDE.md` | Security Hub setup guide |
| `docs/CONNECTION_MODES_WAF_ALIGNMENT.md` | This document |

---

## Troubleshooting

### Common Issues

**"Access Denied" on AssumeRole**
- Check trust policy in target account
- Verify role ARN is correct
- Check external ID if required

**"Rate Exceeded" Errors**
- Switch to Security Hub mode
- Reduce parallel workers: `config.max_concurrent_accounts = 3`
- Add delays between API calls

**"Security Hub Not Enabled"**
- Enable Security Hub in AWS Console
- Check you're connecting to correct region
- Verify delegated admin is configured

**Missing Findings for Some Pillars**
- Enable additional AWS security services (GuardDuty, Inspector, Config)
- Ensure Security Hub integrations are active
- Check finding filters aren't too restrictive
