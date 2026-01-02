# 🚀 AWS WAF Scanner - Quick Reference Card
## Essential Commands & Features at a Glance

---

## 📦 **Installation**

```bash
# Install dependencies
pip install boto3 streamlit pandas plotly click sqlite3

# Initialize database
python -c "from waf_database import WAFDatabase; WAFDatabase()"

# Run application
streamlit run waf_scanner_integrated.py
```

---

## 🎯 **Core Modules Quick Reference**

### **1. Database Module**
```python
from waf_database import WAFDatabase

db = WAFDatabase()

# Store scan
scan_id = db.store_scan(scan_results)

# Get trends (last 30 days)
trends = db.get_trend_data('123456789012', days=30)

# Assign finding
db.assign_finding('finding-001', 'john@example.com', 'manager@example.com')

# Add comment
db.add_comment('finding-001', 'john@example.com', 'Working on fix')

# Update status
db.update_finding_status('finding-001', 'in_progress', 'john@example.com')

# Get summary
stats = db.get_summary_stats('123456789012')
```

### **2. Compliance Mapper**
```python
from compliance_mapper import ComplianceMapper

mapper = ComplianceMapper()

# Get compliance mappings
mappings = mapper.get_compliance_mappings('S3 Bucket Without Encryption')

# Get by framework
cis_mappings = mapper.get_compliance_by_framework(title, 'CIS_AWS_FOUNDATIONS')

# Generate report
report = mapper.generate_compliance_report(findings_list)

# Framework coverage
coverage = mapper.get_framework_coverage(findings_list)
```

**Supported Frameworks:**
- CIS AWS Foundations
- PCI-DSS v4.0
- HIPAA
- SOC 2
- NIST CSF

### **3. Cost Calculator**
```python
from cost_calculator import CostImpactCalculator

calc = CostImpactCalculator()

# Calculate finding impact
impact = calc.calculate_finding_impact(finding, resources)

# Portfolio impact
portfolio = calc.calculate_portfolio_impact(findings_list)

# Format for display
print(calc.format_cost_display(impact))
```

**Cost Metrics:**
- `monthly_waste` - Waste costs per month
- `annual_waste` - Waste costs per year
- `risk_cost` - Potential incident cost
- `total_impact` - Combined impact

### **4. Remediation Engine**
```python
from remediation_engine import RemediationEngine

engine = RemediationEngine()

# Get remediation options
options = engine.get_remediation_options(finding)

# Access different formats
terraform = options['terraform']
cloudformation = options['cloudformation']
cli_commands = options['aws_cli']
manual_steps = options['manual_steps']

# Execute automated remediation
result = engine.execute_remediation(finding, method='aws_cli')
```

**Output Formats:**
- Terraform (HCL)
- CloudFormation (JSON)
- AWS CLI (bash)
- Manual steps (text)

### **5. Interactive Dashboard**
```python
from interactive_dashboard import InteractiveDashboard
import streamlit as st

dashboard = InteractiveDashboard()

# Create charts
fig1 = dashboard.create_severity_distribution_pie(findings)
fig2 = dashboard.create_waf_pillar_radar(pillar_scores)
fig3 = dashboard.create_trend_chart(trend_data)
fig4 = dashboard.create_service_breakdown_bar(findings)
fig5 = dashboard.create_cost_impact_waterfall(cost_data)
fig6 = dashboard.create_compliance_heatmap(compliance_report)
fig7 = dashboard.create_finding_age_histogram(age_data)

# Display in Streamlit
st.plotly_chart(fig1, use_container_width=True)

# Complete dashboard
dashboard.create_dashboard_summary(scan_results, historical_data)
```

**Chart Types:**
1. Severity Pie Chart
2. WAF Pillar Radar
3. Trend Line Charts
4. Service Bar Chart
5. Cost Waterfall
6. Compliance Heatmap
7. Finding Age Histogram

### **6. CLI Tool**
```bash
# Run scan with quality gates
python waf_cli.py scan \
  --account-id 123456789012 \
  --region us-east-1 \
  --output report.json \
  --format json \
  --fail-on critical \
  --max-critical 0 \
  --max-high 5 \
  --min-waf-score 75

# Generate SARIF for GitHub
python waf_cli.py scan \
  --account-id 123456789012 \
  --output report.sarif \
  --format sarif

# Generate Markdown report
python waf_cli.py scan \
  --account-id 123456789012 \
  --output report.md \
  --format markdown

# Check quality gates
python waf_cli.py check_gates report.json
```

**Output Formats:**
- `json` - Machine-readable
- `junit` - CI/CD XML
- `sarif` - GitHub Security
- `markdown` - Human-readable

---

## 🔄 **CI/CD Integration**

### **GitHub Actions**

**File:** `.github/workflows/waf-scan.yml`

**Triggers:**
- Pull requests
- Pushes to main
- Daily schedule (2 AM UTC)
- Manual dispatch

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`
- `SLACK_WEBHOOK_URL` (optional)

**Features:**
- Quality gates
- SARIF upload
- PR comments
- Slack notifications
- Artifact storage (90 days)

### **GitLab CI**

**File:** `.gitlab-ci.yml`

**Stages:**
1. Scan
2. Analyze
3. Report
4. Notify

**Required Variables:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_ACCOUNT_ID`
- `GITLAB_TOKEN`
- `SLACK_WEBHOOK_URL` (optional)

**Features:**
- Security dashboard
- MR comments
- Quality gates
- JUnit reports
- Weekly digests

---

## 📊 **Database Schema**

```sql
-- 11 Tables
scan_history              -- Scan metrics
finding_history           -- Finding lifecycle
pillar_scores_history     -- WAF pillar trends
assignments               -- Finding ownership
comments                  -- Collaboration
status_updates            -- Audit trail
remediation_actions       -- Fix tracking
compliance_mappings       -- Framework links
cost_impact_history       -- Financial trends
resource_dependencies     -- Resource graph
notifications             -- Alert history
```

---

## 💡 **Common Workflows**

### **Workflow 1: Run Scan & Store Results**
```python
from waf_scanner_integrated import run_multi_account_scan
from waf_database import WAFDatabase

db = WAFDatabase()

# Run scan
results = run_multi_account_scan(['123456789012'])

# Store results
for account_id, account_results in results.items():
    scan_id = db.store_scan(account_results)
    print(f"Stored scan {scan_id}")
```

### **Workflow 2: Assign & Track Finding**
```python
from waf_database import WAFDatabase

db = WAFDatabase()

# Assign finding
db.assign_finding(
    finding_id='finding-001',
    assigned_to='engineer@company.com',
    assigned_by='manager@company.com',
    priority='high',
    due_days=7
)

# Add comment
db.add_comment(
    finding_id='finding-001',
    author='engineer@company.com',
    comment='Created Terraform PR #123'
)

# Update status
db.update_finding_status(
    finding_id='finding-001',
    new_status='in_progress',
    updated_by='engineer@company.com',
    notes='Remediation in progress'
)
```

### **Workflow 3: Generate Compliance Report**
```python
from compliance_mapper import ComplianceMapper
from waf_database import WAFDatabase

db = WAFDatabase()
mapper = ComplianceMapper()

# Get open findings
findings = db.get_findings_by_status('open')

# Generate report
report = mapper.generate_compliance_report(findings)

# Print violations by framework
for framework, data in report['frameworks'].items():
    print(f"{framework}:")
    print(f"  Critical: {data['critical']}")
    print(f"  High: {data['high']}")
    print(f"  Total: {data['total_violations']}")
```

### **Workflow 4: Calculate Cost Impact**
```python
from cost_calculator import CostImpactCalculator

calc = CostImpactCalculator()

# Calculate for all findings
portfolio = calc.calculate_portfolio_impact(findings)

print(f"Monthly Waste: ${portfolio['total_monthly_waste']:,.2f}")
print(f"Annual Waste: ${portfolio['total_annual_waste']:,.2f}")
print(f"Risk Exposure: ${portfolio['total_risk_exposure']:,.0f}")
print(f"Total Impact: ${portfolio['total_impact']:,.2f}")

# Top opportunities
for opp in portfolio['top_opportunities'][:5]:
    print(f"\n{opp['title']}")
    print(f"  Impact: ${opp['total_impact']:,.2f}")
```

### **Workflow 5: Generate Remediation Code**
```python
from remediation_engine import RemediationEngine

engine = RemediationEngine()

finding = {
    'service': 'S3',
    'title': 'S3 Bucket Without Encryption Enabled',
    'resource': 'my-bucket-name'
}

options = engine.get_remediation_options(finding)

# Save Terraform code
with open('fix.tf', 'w') as f:
    f.write(options['terraform'])

# Save CLI script
with open('fix.sh', 'w') as f:
    f.write('\n'.join(options['aws_cli']))

print("Remediation code generated!")
```

---

## 🎨 **Streamlit Dashboard**

### **Main Dashboard**
```python
import streamlit as st
from interactive_dashboard import InteractiveDashboard

st.set_page_config(layout="wide")
dashboard = InteractiveDashboard()

# Metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Findings", 45)
col2.metric("WAF Score", "72.5/100")
col3.metric("Critical", 3)
col4.metric("Monthly Waste", "$5,420")

# Charts
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(dashboard.create_severity_distribution_pie(findings))
with col2:
    st.plotly_chart(dashboard.create_waf_pillar_radar(pillars))
```

### **Tabs for Different Views**
```python
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "📋 Compliance", 
    "💰 Cost Impact",
    "🔧 Remediation"
])

with tab1:
    # Main dashboard
    dashboard.create_dashboard_summary(results, historical)

with tab2:
    # Compliance heatmap
    st.plotly_chart(dashboard.create_compliance_heatmap(compliance_report))

with tab3:
    # Cost waterfall
    st.plotly_chart(dashboard.create_cost_impact_waterfall(cost_impact))

with tab4:
    # Remediation for each finding
    for finding in findings:
        with st.expander(finding['title']):
            st.code(finding['remediation']['terraform'], language='hcl')
```

---

## 🔑 **Key Metrics**

### **Severity Levels**
- **CRITICAL** - Immediate action required
- **HIGH** - Fix within 7 days
- **MEDIUM** - Fix within 30 days
- **LOW** - Fix when convenient

### **WAF Pillars (Score 0-100)**
1. **Security** - Protect data and systems
2. **Reliability** - Recover from failures
3. **Performance** - Use resources efficiently
4. **Cost Optimization** - Avoid unnecessary costs
5. **Operational Excellence** - Operations best practices
6. **Sustainability** - Minimize environmental impact

### **Quality Gate Thresholds**
- **Max Critical:** 0
- **Max High:** 5
- **Min WAF Score:** 75/100

### **Cost Categories**
- **Monthly Waste:** Ongoing inefficiency costs
- **Annual Waste:** Yearly projection
- **Risk Cost:** Potential incident cost
- **Total Impact:** Combined financial impact

---

## 🛠️ **Configuration**

### **Database**
```python
DATABASE_CONFIG = {
    'db_path': 'waf_scanner.db',
    'backup_enabled': True,
    'retention_days': 90
}
```

### **Cost Calculator**
```python
COST_CONFIG = {
    'region': 'us-east-1',
    'custom_pricing': {
        'ec2': {'custom_instance': 100.00}
    }
}
```

### **Compliance**
```python
COMPLIANCE_CONFIG = {
    'custom_frameworks': {
        'ISO_27001': {...}
    }
}
```

### **Quality Gates**
```python
QUALITY_GATES = {
    'max_critical': 0,
    'max_high': 5,
    'min_waf_score': 75
}
```

---

## 🐛 **Troubleshooting**

### **Issue:** Database locked
```python
# Use WAL mode
import sqlite3
conn = sqlite3.connect('waf_scanner.db')
conn.execute('PRAGMA journal_mode=WAL')
```

### **Issue:** Charts not displaying
```bash
pip install plotly>=5.0.0
streamlit cache clear
```

### **Issue:** AWS credentials not found
```bash
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
# OR
aws configure
```

### **Issue:** CI/CD pipeline failing
- Check quality gate thresholds
- Verify AWS credentials
- Review scan logs
- Adjust `--fail-on` threshold

---

## 📚 **File Structure**

```
project/
├── Core Modules
│   ├── waf_database.py              # Historical tracking
│   ├── compliance_mapper.py         # Framework mapping
│   ├── cost_calculator.py           # Cost analysis
│   ├── remediation_engine.py        # Auto-fix generation
│   ├── interactive_dashboard.py     # Plotly charts
│   └── waf_cli.py                   # CLI tool
│
├── Integration
│   ├── waf_scanner_integrated.py    # Main scanner
│   └── waf_scanner_ai_enhanced.py   # AI module
│
├── CI/CD
│   ├── .github/workflows/waf-scan.yml  # GitHub Actions
│   └── .gitlab-ci.yml                  # GitLab CI
│
├── Documentation
│   ├── IMPLEMENTATION_GUIDE.md      # Setup guide
│   ├── ENHANCEMENT_PROPOSAL.md      # Feature details
│   ├── FINAL_SUMMARY.md             # Overview
│   └── QUICK_REFERENCE.md           # This file
│
└── Data
    └── waf_scanner.db               # SQLite database
```

---

## ⚡ **Quick Commands**

```bash
# Install
pip install -r requirements.txt

# Initialize
python -c "from waf_database import WAFDatabase; WAFDatabase()"

# Run Web App
streamlit run waf_scanner_integrated.py

# Run CLI Scan
python waf_cli.py scan --account-id 123456789012 --output report.json

# Run with Quality Gates
python waf_cli.py scan --account-id 123456789012 --max-critical 0 --min-waf-score 75

# Generate SARIF
python waf_cli.py scan --account-id 123456789012 --format sarif --output report.sarif

# Generate Markdown
python waf_cli.py scan --account-id 123456789012 --format markdown --output report.md
```

---

## 🎯 **Success Metrics**

| Metric | Target |
|--------|--------|
| Critical Findings | 0 |
| High Findings | ≤ 5 |
| WAF Score | ≥ 75/100 |
| Scan Frequency | Daily |
| Finding Age | < 30 days |
| Remediation Time | < 7 days |
| Cost Identified | Track monthly |

---

## 🚀 **Launch Checklist**

- [ ] Install dependencies
- [ ] Initialize database
- [ ] Run test scan
- [ ] View dashboard
- [ ] Test compliance mapping
- [ ] Test cost calculator
- [ ] Test remediation engine
- [ ] Set up CI/CD pipeline
- [ ] Configure quality gates
- [ ] Train team
- [ ] Document custom config
- [ ] Go live! 🎉

---

**📖 For detailed information, see `IMPLEMENTATION_GUIDE.md`**
