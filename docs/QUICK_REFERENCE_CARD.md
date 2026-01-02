# Multi-Level Reporting - Quick Reference Card

## 🚀 Quick Start (5 Minutes)

### Step 1: Import Account Profiles (1 min)
```
1. Download account_profiles_template.csv
2. Fill in your account details
3. Go to "Account Profile Manager" → Import/Export
4. Upload CSV file
5. Click "Import Accounts"
```

### Step 2: Enable Security Hub (2 min)
```bash
# Enable Security Hub
aws securityhub enable-security-hub --region us-east-1

# Enable cross-account aggregation
aws securityhub create-finding-aggregator \
    --region us-east-1 \
    --region-linking-mode ALL_REGIONS
```

### Step 3: Generate Your First Report (2 min)
```
1. Go to "Multi-Level Reporting" → "Account Reports"
2. Select an account
3. Choose format (PDF recommended)
4. Click "Generate Account Report"
5. Download!
```

---

## 📊 Report Types Cheat Sheet

| Report Type | Audience | Use Case | Best Format |
|------------|----------|----------|-------------|
| **Account** | Dev Teams | Specific findings & remediation | PDF or JSON |
| **OU** | Managers | Team trends & resource planning | Excel or PDF |
| **Executive** | CTO/CISO | Strategic overview & top risks | PDF (1-2 pages) |
| **Compliance** | Auditors | Control evidence & gap analysis | Excel or PDF |

---

## 🎯 When to Use Each Report

### Use ACCOUNT Report When:
✅ Development team needs specific fixes  
✅ Account owner wants their scorecard  
✅ Detailed technical remediation needed  
✅ Compliance evidence for one account  

**Frequency:** Monthly for Tier 1, Quarterly for Tier 2-3

### Use OU Report When:
✅ Manager needs team performance view  
✅ Resource allocation decisions needed  
✅ Comparing accounts within OU  
✅ Budget planning for OU  

**Frequency:** Quarterly

### Use EXECUTIVE Report When:
✅ Board meeting presentation  
✅ Strategic planning session  
✅ C-level risk briefing  
✅ Investment prioritization  

**Frequency:** Quarterly or on-demand

### Use COMPLIANCE Report When:
✅ Audit is approaching  
✅ Framework certification needed  
✅ Gap analysis required  
✅ Evidence collection for auditors  

**Frequency:** Per audit cycle (semi-annual typically)

---

## 💡 Pro Tips

### Tip 1: Tier Your Accounts Properly
```
Tier 1 - Critical Production
├── Customer-facing apps
├── Payment processing
├── Compliance-scoped accounts
└── Revenue-generating systems

Tier 2 - Supporting Production
├── Internal tools
├── Analytics platforms
└── Reporting systems

Tier 3 - Non-Production
├── Staging environments
└── Test systems

Tier 4 - Infrastructure
├── Security logging
├── Monitoring tools
└── CI/CD pipelines

Tier 5 - Sandbox
├── Development
└── Experimental
```

### Tip 2: Use Tags Effectively
```csv
# Good tagging in CSV
compliance_frameworks: "PCI-DSS,SOC2,HIPAA"
business_unit: "Finance"
owner_email: "team@company.com"
```

### Tip 3: Report Naming Convention
```
account_report_<account-name>_<YYYYMMDD>.pdf
ou_report_<ou-name>_<YYYYMMDD>.pdf
executive_report_<YYYYMMDD>.pdf
compliance_<framework>_<YYYYMMDD>.pdf
```

### Tip 4: Scheduling Reports
```
Monthly:
- Generate all Tier 1 account reports
- Send to development teams

Quarterly:
- Generate all OU reports
- Generate executive report
- Send to management

Semi-Annual:
- Generate compliance reports
- Prepare for audits
```

---

## 🔧 Common Tasks

### Add Single Account
```
Multi-Level Reporting → Account Profile Manager → Add Account
Fill in: ID, Name, Environment, Tier, Owner
Click: Add Account Profile
```

### Bulk Import Accounts
```
Prepare CSV with columns:
- account_id
- account_name
- environment
- tier
- owner_email
- compliance_frameworks

Import: Account Profile Manager → Import/Export → Choose CSV → Import
```

### Generate Account Report
```
Multi-Level Reporting → Account Reports
Select: Account, Format
Generate: Click "Generate Account Report"
Download: Save PDF/Word/JSON
```

### Generate OU Report
```
Multi-Level Reporting → OU Reports
Enter: OU Name, Accounts
Select: Format (Excel recommended)
Generate: Click "Generate OU Report"
Analyze: View team comparisons
```

### Generate Executive Summary
```
Multi-Level Reporting → Executive Reports
Enter: Org Name, Account Count
Select: PDF
Generate: Click "Generate Executive Report"
Result: 1-2 page summary for C-level
```

### Generate Compliance Report
```
Multi-Level Reporting → Compliance Reports
Select: Framework (PCI/HIPAA/SOC2)
Enter: Accounts in scope
Format: Excel (for data analysis) or PDF (for auditors)
Generate: Click "Generate Compliance Report"
Deliver: Send to audit team
```

---

## 📋 Pre-Flight Checklist

### Before Generating Reports:

#### ✅ Security Hub Ready?
```bash
# Check Security Hub status
aws securityhub describe-hub

# Verify findings exist
aws securityhub get-findings --max-results 10

# Check member accounts
aws securityhub list-members
```

#### ✅ Account Profiles Complete?
```
□ All accounts have IDs and names
□ Environments set correctly
□ Tiers assigned appropriately
□ Owner emails provided
□ Compliance frameworks tagged
```

#### ✅ Dependencies Installed?
```bash
pip install streamlit pandas reportlab python-docx openpyxl boto3
```

---

## 🐛 Quick Troubleshooting

### Problem: "No findings returned"
**Fix:**
```bash
# 1. Check Security Hub enabled
aws securityhub describe-hub

# 2. Wait for findings to populate (can take 24hrs)

# 3. Enable security standards
aws securityhub batch-enable-standards \
    --standards-subscription-requests \
    StandardsArn=arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0
```

### Problem: "Permission denied"
**Fix:**
```json
{
  "Effect": "Allow",
  "Action": [
    "securityhub:GetFindings",
    "securityhub:DescribeHub",
    "securityhub:ListMembers"
  ],
  "Resource": "*"
}
```

### Problem: "Report generation fails"
**Fix:**
```bash
# 1. Check dependencies
pip list | grep -E "reportlab|docx|openpyxl"

# 2. Reinstall if needed
pip install --upgrade reportlab python-docx openpyxl

# 3. Check account profile is complete
```

### Problem: "Empty compliance report"
**Fix:**
```
1. Verify accounts have compliance_frameworks set in profile
2. Check Security Hub has compliance findings
3. Ensure correct framework selected
```

---

## 📊 Sample Report Contents

### Account Report Contains:
```
✓ Account metadata (ID, name, tier, owner)
✓ Security Hub findings count
✓ Severity breakdown (Critical/High/Medium/Low)
✓ WAF pillar scores
✓ Immediate actions (Critical/High)
✓ Short-term actions (Medium)
✓ Long-term improvements (Low)
✓ Remediation instructions
```

### OU Report Contains:
```
✓ OU summary (accounts, findings)
✓ Account comparison table
✓ Common issues across OU
✓ Team performance rankings
✓ Pillar analysis
✓ Resource needs estimation
✓ Cost estimates for remediation
```

### Executive Report Contains:
```
✓ Executive summary (1 page)
✓ Overall risk level
✓ Compliance status
✓ Top 10 organizational risks
✓ Strategic recommendations
✓ Investment priorities
✓ Budget requirements
✓ Industry benchmarking
```

### Compliance Report Contains:
```
✓ Framework scope (PCI/HIPAA/etc)
✓ Accounts in scope
✓ Control coverage matrix
✓ Evidence by control
✓ Gap analysis
✓ Remediation timeline
✓ Account-by-account compliance
✓ Audit trail
```

---

## 🎯 Success Metrics

### After 1 Month:
```
✓ All Tier 1 accounts have profiles
✓ Generated 10+ account reports
✓ Development teams have remediation plans
✓ Security Hub findings trending down
```

### After 3 Months:
```
✓ All accounts have profiles
✓ Generated first OU reports
✓ Managers have resource plans
✓ 20%+ reduction in High/Critical findings
```

### After 6 Months:
```
✓ Quarterly executive reports established
✓ Compliance reports for all frameworks
✓ Industry-standard reporting cadence
✓ 50%+ reduction in High/Critical findings
```

---

## 📞 Support Resources

### Documentation
```
├── INTEGRATION_GUIDE_SECURITY_HUB.md (Full integration guide)
├── AWS_WAF_MULTI_ACCOUNT_INDUSTRY_STANDARDS.md (Industry practices)
└── This Quick Reference Card
```

### AWS Security Hub Documentation
```
https://docs.aws.amazon.com/securityhub/
```

### AWS Well-Architected Framework
```
https://aws.amazon.com/architecture/well-architected/
```

---

## 🎓 Remember

1. **Start Small:** Begin with Tier 1 accounts
2. **Iterate:** Improve profiles over time
3. **Automate:** Schedule regular report generation
4. **Act:** Reports are useless without remediation
5. **Track:** Monitor trends over time

**Goal:** Not just reporting, but continuous improvement!

---

## ⚡ Emergency Commands

### Quick Security Hub Check
```bash
aws securityhub get-findings \
    --filters RecordState[0].Comparison=EQUALS,RecordState[0].Value=ACTIVE,SeverityLabel[0].Comparison=EQUALS,SeverityLabel[0].Value=CRITICAL \
    --max-results 10
```

### Quick Account Status
```python
# In Python/Streamlit
from multi_level_reporting_securityhub import SecurityHubAggregator

aggregator = SecurityHubAggregator(session)
findings = aggregator.aggregate_findings(account_profiles)
print(f"Critical: {findings.critical_count}")
print(f"High: {findings.high_count}")
```

### Quick Report Generation
```python
from multi_level_reporting_securityhub import MultiLevelReportGenerator

generator = MultiLevelReportGenerator()
pdf = generator.generate_account_report(profile, findings, scorecard)
```

---

**Version:** 1.0  
**Last Updated:** December 2024  
**Platform:** AWS Security Hub + Manual Scan Approach
