# Quick Setup Guide - EKS Modernization Module

## 🚀 Step-by-Step Installation

### Step 1: Extract the Updated Application
```bash
unzip aws-waf-advisor-SECURITY-HUB-updated.zip
cd aws-waf-advisor-FINAL
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages including:
- streamlit
- pandas, numpy
- plotly (for visualizations)
- boto3 (for AWS integration)
- anthropic (for AI features)
- **python-docx (NEW - for Word export)**
- reportlab (for PDF)
- And all other dependencies

### Step 3: Run the Application
```bash
streamlit run streamlit_app.py
```

### Step 4: Access EKS Modernization
1. Open your browser (should auto-open to http://localhost:8501)
2. Click on the "🚀 EKS Modernization" tab
3. You should now see the comprehensive design wizard!

---

## ✅ Verification

The module is working if you see:
- ✅ No error messages in yellow/red boxes
- ✅ Design Wizard with 6 steps displayed
- ✅ Progress bar at the top
- ✅ Step navigation: 1️⃣ Project Setup, 2️⃣ Compute & Scaling, etc.

---

## 🎯 Quick Test

### Test the Basic Functionality:
1. **Go to Step 1 - Project Setup:**
   - Enter project name: "test-cluster"
   - Select environment: "production"
   - Select region: "us-east-1"

2. **Click "Next ➡️"** to go through the wizard

3. **At Step 6 - Review & Validate:**
   - You'll see your configuration summary
   - Cost estimation
   - Option to export

4. **Test Export:**
   - Click "📖 Documentation" mode in sidebar
   - Try "📋 Export to JSON" - should work immediately
   - Try "📄 Export to Word" - should work if python-docx is installed

---

## 🔧 Troubleshooting

### Issue: "EKS Modernization module not available"
**Solution:** Make sure you installed all dependencies:
```bash
pip install -r requirements.txt
```

### Issue: Word export shows error
**Solution:** Install python-docx specifically:
```bash
pip install python-docx>=0.8.11
```

### Issue: Import errors for other packages
**Solution:** Install missing package:
```bash
# For plotly
pip install plotly>=5.18.0

# For pandas
pip install pandas>=2.0.0

# For anthropic
pip install anthropic>=0.18.0
```

### Issue: AWS-related errors
**Solution:** Make sure boto3 is installed:
```bash
pip install boto3>=1.28.0 botocore>=1.31.0
```

---

## 📦 What's Included

### Core Features (Always Available):
- ✅ 6-step Design Wizard
- ✅ Comprehensive configuration options
- ✅ Cost calculator
- ✅ Best practices validation
- ✅ JSON export
- ✅ Architecture diagram generation

### Optional Features (Require Dependencies):
- 🤖 AI-powered validation (requires: `anthropic` package + API key)
- 💰 Real-time AWS pricing (requires: `boto3` + AWS credentials)
- 📄 Word export (requires: `python-docx`)
- 📄 PDF export (framework ready, requires implementation)

---

## 🎨 Features to Try

### 1. Design Wizard
Navigate through all 6 steps:
1. **Project Setup** - Define cluster basics
2. **Compute & Scaling** - Configure node groups, Karpenter, Fargate
3. **Storage & Data** - Set up EBS, EFS, FSx
4. **Networking & Security** - Configure VPC, load balancers, security
5. **Observability & Tools** - Set up logging, metrics, add-ons
6. **Review & Validate** - See summary, costs, export options

### 2. Quick Calculator
- Go to sidebar → Select "📊 Quick Calculator"
- Enter your workload requirements
- Get instant sizing recommendations

### 3. Best Practices
- Go to sidebar → Select "📚 Best Practices"
- View comprehensive EKS best practices
- Categories: Security, Cost Optimization, Performance, Reliability

### 4. Documentation Export
- Complete the wizard first
- Go to sidebar → Select "📖 Documentation"
- Export your design in multiple formats:
  - **JSON** - For version control and IaC
  - **Word** - For presentations and documentation
  - **PDF** - Coming soon

---

## 💡 Pro Tips

### Tip 1: Save Your Designs
Export your design as JSON and save it:
```bash
# Your design is saved as: project_name_design.json
# You can import it later or use it for IaC generation
```

### Tip 2: Cost Optimization
- Enable Karpenter for 20-60% cost savings
- Use Spot instances for non-critical workloads
- Right-size your node groups based on actual workload

### Tip 3: Security Best Practices
- Always enable IRSA (IAM Roles for Service Accounts)
- Use Pod Security Standards in "restricted" mode
- Enable encryption at rest for all storage
- Implement network policies

### Tip 4: Multi-AZ Deployment
- Select at least 3 availability zones
- This ensures high availability
- Required for production workloads

---

## 📊 Expected Outputs

### After Completing the Wizard:

**1. Configuration Summary**
- Complete cluster specification
- All components listed
- Security settings
- Networking configuration

**2. Cost Analysis**
- Monthly cost estimate
- Breakdown by component
- Optimization recommendations
- Reserved instance suggestions

**3. Architecture Diagram**
- Professional SVG diagram
- AWS-style visualization
- Multi-AZ layout
- Component relationships

**4. Documentation**
- Word document with:
  - Executive summary
  - Technical specifications
  - Architecture diagrams
  - Implementation guide
  - Cost analysis

---

## 🆘 Support

### If You Encounter Issues:

1. **Check the error message** - Usually very specific
2. **Verify dependencies** - Run `pip list` to see installed packages
3. **Check requirements** - Compare with `requirements.txt`
4. **Reinstall if needed** - `pip install -r requirements.txt --force-reinstall`

### Common Solutions:

**Module import errors:**
```bash
pip install -r requirements.txt
```

**Streamlit errors:**
```bash
pip install --upgrade streamlit
```

**Package conflicts:**
```bash
pip install -r requirements.txt --force-reinstall
```

---

## 🎯 Success Criteria

You're all set when:
- ✅ No error messages on EKS Modernization tab
- ✅ Can navigate through all 6 wizard steps
- ✅ Can see cost estimates
- ✅ Can export to JSON
- ✅ Can see architecture diagrams
- ✅ (Optional) Can export to Word

---

## 📞 Next Steps

Once everything is working:

1. **Create your first design:**
   - Use the wizard to design a cluster
   - Export the configuration
   - Review the cost estimates

2. **Explore advanced features:**
   - Enable Karpenter for auto-scaling
   - Configure service mesh
   - Set up observability stack
   - Add CI/CD tools (ArgoCD, Flux)

3. **Generate documentation:**
   - Export Word documents for stakeholders
   - Save JSON for version control
   - Generate diagrams for presentations

4. **Implement your design:**
   - Use the configuration as reference
   - Generate IaC templates (coming soon)
   - Follow the implementation guide

---

## 🎉 You're Ready!

The comprehensive EKS Modernization module is now fully functional. Start designing enterprise-grade Kubernetes clusters with confidence!

**Happy Architecting! 🚀**
