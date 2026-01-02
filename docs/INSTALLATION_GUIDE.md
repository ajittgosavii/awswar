# 📦 Installation Guide - AWS WAF Scanner Enterprise Edition
## Updated Dependencies for All 10 Enhancements

---

## 📊 **What Changed in requirements.txt**

### **NEW Packages Added:**

| Package | Version | Purpose | Required? |
|---------|---------|---------|-----------|
| **click** | >=8.1.0 | CLI tool for CI/CD integration | ✅ **Yes** |
| **numpy** | >=1.24.0 | Pandas dependency (explicit) | ✅ **Yes** |
| **kaleido** | >=0.2.1 | Export Plotly charts to PNG/SVG | ⚠️ Optional |
| **pyrebase4** | >=4.7.0 | Firebase client library | ⚠️ Optional |
| **python-dotenv** | >=1.0.0 | Environment variables (.env files) | ⚠️ Optional |
| **networkx** | >=3.1 | Resource dependency graphs | ⚠️ Optional |
| **pyvis** | >=0.3.2 | Interactive graph visualization | ⚠️ Optional |
| **pytest** | >=7.4.0 | Testing framework | ⚠️ Dev only |
| **pytest-cov** | >=4.1.0 | Code coverage | ⚠️ Dev only |
| **black** | >=23.0.0 | Code formatter | ⚠️ Dev only |
| **flake8** | >=6.0.0 | Linter | ⚠️ Dev only |

### **Existing Packages (No Change):**

| Package | Version | Purpose |
|---------|---------|---------|
| streamlit | >=1.28.0 | Web interface |
| anthropic | >=0.18.0 | AI analysis |
| boto3 | >=1.34.0 | AWS SDK |
| botocore | >=1.34.0 | AWS core |
| pyyaml | >=6.0 | Config files |
| pandas | >=2.0.0 | Data processing |
| plotly | >=5.17.0 | Interactive charts |
| python-docx | >=0.8.11 | Word docs |
| reportlab | >=4.0.0 | PDFs |
| Pillow | >=10.0.0 | Images |
| firebase-admin | >=6.2.0 | Firebase auth |
| google-cloud-firestore | >=2.11.0 | Firestore |
| python-dateutil | >=2.8.2 | Date utilities |
| requests | >=2.31.0 | HTTP |

---

## 🚀 **Installation Methods**

### **Method 1: Full Installation (Recommended)**

Install everything including optional features:

```bash
# Clone/download your project
cd waf-scanner

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import streamlit; import click; import plotly; print('✅ All packages installed!')"

# Initialize database
python -c "from waf_database import WAFDatabase; WAFDatabase(); print('✅ Database initialized!')"
```

**This includes:**
- ✅ Core scanner
- ✅ Interactive dashboards
- ✅ Historical tracking
- ✅ CI/CD CLI tool
- ✅ Compliance mapping
- ✅ Cost calculator
- ✅ Remediation engine
- ✅ Firebase auth (optional)
- ✅ Dependency mapping (optional)

---

### **Method 2: Minimal Installation (Core Features Only)**

Install only essential packages:

```bash
# Minimal install
pip install streamlit>=1.28.0 \
            boto3>=1.34.0 \
            pandas>=2.0.0 \
            plotly>=5.17.0 \
            click>=8.1.0 \
            anthropic>=0.18.0 \
            python-docx>=0.8.11 \
            reportlab>=4.0.0

# Initialize database
python -c "from waf_database import WAFDatabase; WAFDatabase()"
```

**This includes:**
- ✅ Core scanner
- ✅ Interactive dashboards
- ✅ Historical tracking
- ✅ CI/CD CLI tool
- ✅ Compliance mapping
- ✅ Cost calculator
- ✅ Remediation engine
- ❌ Firebase auth
- ❌ Dependency mapping
- ❌ Development tools

---

### **Method 3: Development Installation**

For developers who want testing/linting tools:

```bash
# Full install plus dev tools
pip install -r requirements.txt
pip install pytest>=7.4.0 pytest-cov>=4.1.0 black>=23.0.0 flake8>=6.0.0

# Run tests
pytest tests/

# Format code
black *.py

# Lint code
flake8 *.py
```

---

### **Method 4: Docker Installation**

Use Docker for isolated environment:

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY .streamlit/ .streamlit/

# Initialize database
RUN python -c "from waf_database import WAFDatabase; WAFDatabase()"

EXPOSE 8501

CMD ["streamlit", "run", "waf_scanner_integrated.py", "--server.port=8501"]
EOF

# Build image
docker build -t waf-scanner-enterprise .

# Run container
docker run -p 8501:8501 \
  -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
  -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
  -v $(pwd)/waf_scanner.db:/app/waf_scanner.db \
  waf-scanner-enterprise
```

---

## 🔍 **Package Purpose Breakdown**

### **1. CLI Tool (CI/CD Integration)**

**Package:** `click>=8.1.0`

**Why needed:**
- Powers `waf_cli.py` for command-line interface
- Essential for CI/CD pipelines (GitHub Actions, GitLab CI)
- Provides quality gates, multiple output formats

**Usage:**
```bash
python waf_cli.py scan \
  --account-id 123456789012 \
  --max-critical 0 \
  --format sarif
```

**Without it:** CI/CD integration won't work

---

### **2. Interactive Visualizations**

**Packages:** 
- `plotly>=5.17.0` (already had)
- `kaleido>=0.2.1` (NEW - optional)

**Why needed:**
- Plotly creates 7 interactive chart types
- Kaleido exports charts to PNG/SVG for static reports

**Usage:**
```python
from interactive_dashboard import InteractiveDashboard

dashboard = InteractiveDashboard()
fig = dashboard.create_severity_distribution_pie(findings)
fig.write_image("severity.png")  # Requires kaleido
```

**Without kaleido:** Can't export charts to images (but interactive viewing still works)

---

### **3. Historical Tracking**

**Packages:**
- `pandas>=2.0.0` (already had)
- `sqlite3` (built into Python)
- `numpy>=1.24.0` (NEW - pandas dependency)

**Why needed:**
- Database with 11 tables for historical tracking
- Trend analysis with pandas
- NumPy for numerical operations

**Usage:**
```python
from waf_database import WAFDatabase

db = WAFDatabase()
trends = db.get_trend_data(account_id, days=30)
```

**Without it:** No historical tracking, trends, or collaboration features

---

### **4. Resource Dependency Mapping (Optional)**

**Packages:**
- `networkx>=3.1` (NEW - optional)
- `pyvis>=0.3.2` (NEW - optional)

**Why needed:**
- Build resource dependency graphs
- Visualize "blast radius" of changes
- Interactive network diagrams

**Usage:**
```python
from resource_dependency_mapper import DependencyMapper

mapper = DependencyMapper(session)
impact = mapper.get_blast_radius('sg-12345')
```

**Without it:** No dependency mapping (other features still work)

---

### **5. Firebase Authentication (Optional)**

**Packages:**
- `firebase-admin>=6.2.0` (already had)
- `pyrebase4>=4.7.0` (NEW - optional)
- `google-cloud-firestore>=2.11.0` (already had)
- `python-dotenv>=1.0.0` (NEW - optional)

**Why needed:**
- SSO authentication
- User management
- .env file support for credentials

**Usage:**
```python
from firebase_auth import FirebaseAuth

auth = FirebaseAuth()
user = auth.sign_in_with_email(email, password)
```

**Without it:** No SSO (can still use app without authentication)

---

## ✅ **Verification Steps**

After installation, verify everything works:

### **Step 1: Check Package Installation**

```python
# verify_installation.py
import sys

packages = {
    'streamlit': 'Web interface',
    'click': 'CLI tool',
    'plotly': 'Interactive charts',
    'pandas': 'Data processing',
    'boto3': 'AWS SDK',
    'anthropic': 'AI analysis',
}

print("Checking required packages...\n")

for package, purpose in packages.items():
    try:
        __import__(package)
        print(f"✅ {package:20} - {purpose}")
    except ImportError:
        print(f"❌ {package:20} - {purpose} (MISSING!)")

print("\n✅ All core packages installed successfully!")
```

```bash
python verify_installation.py
```

---

### **Step 2: Initialize Database**

```python
from waf_database import WAFDatabase

db = WAFDatabase('waf_scanner.db')
print("✅ Database initialized with 11 tables")

# Test database
stats = db.get_summary_stats()
print(f"✅ Database query successful: {stats}")
```

---

### **Step 3: Test Modules**

```python
# Test all modules
from waf_database import WAFDatabase
from compliance_mapper import ComplianceMapper
from cost_calculator import CostImpactCalculator
from interactive_dashboard import InteractiveDashboard
from remediation_engine import RemediationEngine

print("✅ Database Module")
print("✅ Compliance Mapper")
print("✅ Cost Calculator")
print("✅ Interactive Dashboard")
print("✅ Remediation Engine")
```

---

### **Step 4: Run CLI Tool**

```bash
# Test CLI
python waf_cli.py --help

# Expected output:
# Usage: waf_cli.py [OPTIONS] COMMAND [ARGS]...
#   AWS WAF Scanner CLI
# Commands:
#   scan          Run WAF security scan
#   check_gates   Check quality gates from configuration file
```

---

### **Step 5: Launch Streamlit App**

```bash
streamlit run waf_scanner_integrated.py

# Expected output:
#   You can now view your Streamlit app in your browser.
#   Local URL: http://localhost:8501
```

---

## 🐛 **Troubleshooting**

### **Issue: Click not installed**

```bash
# Error: ModuleNotFoundError: No module named 'click'

# Solution:
pip install click>=8.1.0
```

### **Issue: Kaleido installation fails**

```bash
# Kaleido is optional, you can skip it
pip install -r requirements.txt --ignore-installed kaleido

# Or install without Kaleido:
grep -v kaleido requirements.txt > requirements_no_kaleido.txt
pip install -r requirements_no_kaleido.txt
```

### **Issue: Firebase packages fail**

```bash
# Firebase is optional, skip if not using SSO
pip install -r requirements.txt --no-deps firebase-admin pyrebase4

# Or install without Firebase:
grep -v -E "(firebase|google-cloud)" requirements.txt > requirements_no_firebase.txt
pip install -r requirements_no_firebase.txt
```

### **Issue: NetworkX/PyVis not needed**

```bash
# These are optional for dependency mapping
grep -v -E "(networkx|pyvis)" requirements.txt > requirements_no_graphs.txt
pip install -r requirements_no_graphs.txt
```

---

## 📋 **Dependency Matrix**

| Feature | Required Packages | Optional Packages |
|---------|------------------|-------------------|
| **Core Scanner** | streamlit, boto3, pandas | - |
| **AI Analysis** | anthropic | - |
| **PDF Reports** | reportlab, python-docx | Pillow |
| **Interactive Dashboards** | plotly | kaleido |
| **Historical Tracking** | pandas, numpy | - |
| **CLI Tool** | click | - |
| **Compliance Mapping** | - | - |
| **Cost Calculator** | - | - |
| **Remediation Engine** | - | - |
| **Firebase Auth** | - | firebase-admin, pyrebase4 |
| **Dependency Mapping** | - | networkx, pyvis |
| **CI/CD** | click | - |

---

## 🎯 **Recommended Installation Path**

### **For Production Use:**

```bash
# 1. Install core + essential packages
pip install streamlit boto3 pandas plotly click anthropic \
            python-docx reportlab pyyaml requests python-dateutil

# 2. Initialize database
python -c "from waf_database import WAFDatabase; WAFDatabase()"

# 3. Test
streamlit run waf_scanner_integrated.py
```

### **For Full Enterprise Features:**

```bash
# 1. Install everything
pip install -r requirements.txt

# 2. Initialize database
python -c "from waf_database import WAFDatabase; WAFDatabase()"

# 3. Test
streamlit run waf_scanner_integrated.py
python waf_cli.py --help
```

---

## 🚀 **Next Steps After Installation**

1. ✅ Review `QUICK_REFERENCE.md` for commands
2. ✅ Follow `IMPLEMENTATION_GUIDE.md` for setup
3. ✅ Run test scan with demo mode
4. ✅ Integrate modules into your scanner
5. ✅ Set up CI/CD pipeline

---

## 📞 **Support**

**Installation Issues?**
1. Check Python version: `python --version` (need 3.10+)
2. Upgrade pip: `pip install --upgrade pip`
3. Try virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

**Still having issues?**
- Review error messages carefully
- Check if packages are compatible with your OS
- Try installing packages one by one
- Use `pip install -v` for verbose output

---

**✅ You're ready to install! Use the updated `requirements.txt` file.**
