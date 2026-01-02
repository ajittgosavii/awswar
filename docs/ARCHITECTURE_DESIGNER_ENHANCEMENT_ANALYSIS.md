# Architecture Designer Enhancement Analysis

## Executive Summary

This document analyzes three key areas:
1. **Upload Analyzer** - Current file format support and gaps (Visio, Draw.io)
2. **Diagram Generator** - Architecture visualization capabilities
3. **WAF Question Alignment** - Question mapping to Architecture Designer and EKS Modernization

---

## 1. Architecture Upload Analyzer

### Current Supported Formats

| Format | Extension | Status | Parser Type |
|--------|-----------|--------|-------------|
| Terraform | `.tf`, `.tfvars` | ✅ Supported | Pattern matching |
| CloudFormation | `.yaml`, `.yml`, `.json` | ✅ Supported | YAML/JSON parsing |
| AWS CDK | `.py`, `.ts` | ✅ Supported | Pattern matching |
| PDF | `.pdf` | ✅ Supported | Text extraction |
| Word | `.docx` | ✅ Supported | Document parsing |
| PowerPoint | `.pptx` | ✅ Supported | Slide parsing |
| Text/Markdown | `.txt`, `.md` | ✅ Supported | Direct text |

### Missing Formats (Gap)

| Format | Extension | Priority | Complexity |
|--------|-----------|----------|------------|
| **Visio** | `.vsdx`, `.vsd` | 🔴 High | Medium |
| **Draw.io** | `.drawio`, `.xml` | 🔴 High | Low |
| **Lucidchart** | `.lucidchart`, `.csv` | 🟡 Medium | Low |
| **Mermaid** | `.mmd` | 🟢 Low | Low |
| **PlantUML** | `.puml` | 🟢 Low | Low |

### Why Visio & Draw.io Matter

1. **Industry Standard**: Visio is the enterprise standard for architecture diagrams
2. **AWS Official**: AWS Architecture Icons are distributed for Visio
3. **Draw.io Popularity**: Free tool widely used in AWS community
4. **Existing Assets**: Many organizations have architecture documented in these formats

---

## 2. Architecture Diagram Generator

### Current Capabilities

The `svg_diagram_generator.py` provides:

| Feature | Status | Description |
|---------|--------|-------------|
| AWS Service Icons | ✅ | 45+ services with category colors |
| Connection Lines | ✅ | Arrows and flow indicators |
| Grouping | ✅ | VPC, Subnet, AZ groupings |
| Labels | ✅ | Service names and annotations |
| Export to SVG | ✅ | Vector format |
| Multi-tier layouts | ✅ | Web, App, Data tiers |

### Missing Diagram Features (Gap)

| Feature | Priority | Description |
|---------|----------|-------------|
| Export to PNG/PDF | 🔴 High | Beyond SVG format |
| Interactive diagrams | 🟡 Medium | Clickable components |
| Real AWS icons | 🔴 High | Official AWS icon set |
| Auto-layout algorithms | 🟡 Medium | Automatic positioning |
| Animation support | 🟢 Low | Data flow visualization |

---

## 3. WAF Question Alignment

### Total Questions: 205

The complete WAF question set contains 205 questions across 6 pillars:

| Pillar | Questions | % |
|--------|-----------|---|
| Operational Excellence | 34 | 17% |
| Security | 42 | 20% |
| Reliability | 38 | 19% |
| Performance Efficiency | 32 | 16% |
| Cost Optimization | 35 | 17% |
| Sustainability | 24 | 12% |

### Architecture Designer WAF Integration

The Architecture Designer uses **service-based detection** to auto-answer questions:

| Service Category | Detected Services | Auto-Mapped Questions |
|-----------------|-------------------|----------------------|
| Compute | EC2, Lambda, ECS, EKS, Fargate | 25-30 questions |
| Networking | VPC, ALB, CloudFront, Route53 | 20-25 questions |
| Database | RDS, Aurora, DynamoDB, ElastiCache | 18-22 questions |
| Security | IAM, KMS, WAF, Shield, GuardDuty | 30-35 questions |
| Monitoring | CloudWatch, CloudTrail, Config | 15-20 questions |
| Storage | S3, EFS, EBS | 12-15 questions |

**Total Auto-Detected**: ~130-150 questions (65-75% of 205)

**Remaining Manual**: ~55-75 questions (25-35%)

### EKS Modernization WAF Integration

The EKS Modernization module has **35 EKS-specific requirements** mapped to WAF pillars:

| Pillar | EKS Requirements | Key Checks |
|--------|-----------------|------------|
| **Security** | 7 | Secrets encryption, Pod Security, Network Policies, IRSA, Audit Logging |
| **Reliability** | 6 | Multi-AZ, Cluster Autoscaler, PDBs, HPA, Health Checks |
| **Operational Excellence** | 5 | Container Insights, GitOps, Prometheus, FluentBit |
| **Performance Efficiency** | 4 | HPA, VPA, Resource Quotas, Limit Ranges |
| **Cost Optimization** | 5 | Spot Instances, Karpenter, VPA, Graviton |
| **Sustainability** | 4 | Graviton, Efficient Scaling, Right-sizing |

**Total EKS-Specific**: 35 requirements + maps to ~40-50 WAF questions

### Question Overlap Matrix

```
                    Architecture    EKS             
                    Designer       Modernization    Coverage
┌────────────────────────────────────────────────────────────┐
│ Compute              ██████████     ████████████  High     │
│ Container/K8s        ████           ████████████  High     │
│ Networking           ██████████     ██████████    Medium   │
│ Security             ██████████     ████████████  High     │
│ Monitoring           ██████████     ████████████  High     │
│ Database             ██████████     ████          Low      │
│ Storage              ██████████     ██████        Medium   │
│ Cost                 ██████████     ████████████  High     │
│ Sustainability       ████████       ████████████  Medium   │
└────────────────────────────────────────────────────────────┘
```

---

## Enhancement Recommendations

### Priority 1: Add Visio & Draw.io Support (Week 1)

```python
# New file parsers needed:
SUPPORTED_FORMATS = {
    'vsdx': VisioParser,    # Microsoft Visio
    'drawio': DrawIOParser, # Draw.io/Diagrams.net
    'xml': DrawIOParser,    # Draw.io XML export
}
```

**Implementation approach:**
1. **Visio (.vsdx)**: Use `python-pptx` similar library or `vsdx` package
2. **Draw.io (.drawio)**: Parse XML, extract mxCell elements with AWS service names

### Priority 2: Enhanced Diagram Generation (Week 2)

1. Add AWS Architecture Icons (official SVG set)
2. Implement PNG/PDF export via cairo/PIL
3. Add auto-layout algorithms
4. Interactive diagrams with Streamlit components

### Priority 3: WAF Question Auto-Mapping (Week 3)

Increase auto-detection from 65-75% to 85-90%:

1. Parse uploaded diagrams for service detection
2. Extract configuration patterns (Multi-AZ, encryption hints)
3. Map diagram annotations to WAF responses

---

## Implementation Details

### Visio Parser

```python
class VisioParser:
    """Parse Microsoft Visio files for AWS services"""
    
    VISIO_AWS_SHAPES = {
        'AWS::EC2::Instance': 'ec2',
        'AWS::Lambda::Function': 'lambda',
        'AWS::S3::Bucket': 's3',
        'Amazon EC2': 'ec2',
        'Amazon S3': 's3',
        'Amazon RDS': 'rds',
        # ... 100+ mappings
    }
    
    def parse(self, content: bytes) -> Tuple[List[str], Dict]:
        """Extract AWS services from Visio file"""
        import zipfile
        from xml.etree import ElementTree
        
        services = []
        service_counts = {}
        
        with zipfile.ZipFile(io.BytesIO(content)) as vsdx:
            # Parse pages
            for name in vsdx.namelist():
                if 'page' in name and name.endswith('.xml'):
                    xml_content = vsdx.read(name)
                    root = ElementTree.fromstring(xml_content)
                    
                    # Find shape names
                    for shape in root.iter():
                        text = shape.text or ''
                        for pattern, service in self.VISIO_AWS_SHAPES.items():
                            if pattern.lower() in text.lower():
                                services.append(service)
                                service_counts[service] = service_counts.get(service, 0) + 1
        
        return list(set(services)), service_counts
```

### Draw.io Parser

```python
class DrawIOParser:
    """Parse Draw.io/Diagrams.net files"""
    
    DRAWIO_AWS_PATTERNS = {
        r'mxgraph\.aws4\.(ec2|instance)': 'ec2',
        r'mxgraph\.aws4\.(lambda|function)': 'lambda',
        r'mxgraph\.aws4\.(s3|bucket)': 's3',
        r'mxgraph\.aws4\.(rds|database)': 'rds',
        r'mxgraph\.aws4\.(dynamodb)': 'dynamodb',
        r'mxgraph\.aws4\.(vpc|subnet)': 'vpc',
        r'mxgraph\.aws4\.(alb|elb|loadbalancer)': 'alb',
        r'mxgraph\.aws4\.(cloudfront)': 'cloudfront',
        r'mxgraph\.aws4\.(eks|kubernetes)': 'eks',
        r'mxgraph\.aws4\.(ecs|container)': 'ecs',
        # ... pattern for all AWS services
    }
    
    def parse(self, content: str) -> Tuple[List[str], Dict]:
        """Extract AWS services from Draw.io XML"""
        import base64
        from xml.etree import ElementTree
        
        services = []
        service_counts = {}
        
        # Handle compressed or plain XML
        if '<mxfile' not in content:
            # Try base64 decode
            try:
                content = base64.b64decode(content).decode('utf-8')
            except:
                pass
        
        root = ElementTree.fromstring(content)
        
        # Find all mxCell elements with style containing AWS shapes
        for cell in root.iter('mxCell'):
            style = cell.get('style', '')
            value = cell.get('value', '')
            
            # Check style for AWS shapes
            for pattern, service in self.DRAWIO_AWS_PATTERNS.items():
                if re.search(pattern, style, re.IGNORECASE):
                    services.append(service)
                    service_counts[service] = service_counts.get(service, 0) + 1
            
            # Also check value text for service names
            for pattern, service in TEXT_SERVICE_PATTERNS.items():
                if re.search(pattern, value, re.IGNORECASE):
                    if service not in services:
                        services.append(service)
        
        return list(set(services)), service_counts
```

---

## Summary Table

| Area | Current | Enhanced | Value Add |
|------|---------|----------|-----------|
| **File Formats** | 7 formats | 10+ formats | +40% coverage |
| **Visio Support** | ❌ None | ✅ Full | Enterprise standard |
| **Draw.io Support** | ❌ None | ✅ Full | Community standard |
| **Diagram Export** | SVG only | SVG/PNG/PDF | Professional output |
| **WAF Auto-Detect** | 65-75% | 85-90% | Faster assessments |
| **EKS Questions** | 35 specific | 35 + WAF mapping | Complete coverage |

---

## Next Steps

1. **Implement VisioParser and DrawIOParser** (Attached)
2. **Update file_uploader to accept new formats**
3. **Add PNG/PDF export to diagram generator**
4. **Create WAF question mapping for uploaded diagrams**

Would you like me to implement these enhancements now?
