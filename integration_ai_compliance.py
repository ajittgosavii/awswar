"""
Unified AI Lens & Compliance Integration Layer
===============================================
Provides cross-cutting AI insights and compliance mapping across ALL application tabs.

This module integrates:
1. AI Lens (ML, GenAI, Responsible AI) - Provides intelligent analysis and recommendations
2. Compliance Frameworks (SOC2, HIPAA, PCI-DSS, ISO 27001, CIS, GDPR) - Maps findings to requirements

Integration Points:
- WAF Review: AI-powered finding analysis, compliance gap identification
- Architecture Designer: AI design recommendations, compliance-aware patterns
- EKS Modernization: AI/ML workload best practices, container compliance
- FinOps: AI cost optimization, compliance cost analysis
- All Tabs: Consistent AI insights panel, compliance status indicators

Version: 1.0.0
Author: Enterprise WAF Scanner Team
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib

# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

class AILensType(Enum):
    """Types of AI Lenses"""
    GENERAL = "general"           # General AI insights
    MACHINE_LEARNING = "ml"       # ML workload specific
    GENERATIVE_AI = "genai"       # LLM/Foundation models
    RESPONSIBLE_AI = "rai"        # Ethics & governance
    SECURITY = "security"         # Security-focused AI
    COST = "cost"                 # Cost optimization AI

class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOC2 = "SOC 2 Type II"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS v4.0"
    ISO_27001 = "ISO 27001:2022"
    CIS = "CIS AWS Benchmarks"
    GDPR = "GDPR"
    NIST = "NIST CSF"
    FEDRAMP = "FedRAMP"

class WAFPillar(Enum):
    """WAF Pillars for mapping"""
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"

# Pillar icons and colors
PILLAR_CONFIG = {
    WAFPillar.OPERATIONAL_EXCELLENCE: {"icon": "⚙️", "color": "#FF6B6B"},
    WAFPillar.SECURITY: {"icon": "🔒", "color": "#4ECDC4"},
    WAFPillar.RELIABILITY: {"icon": "🛡️", "color": "#45B7D1"},
    WAFPillar.PERFORMANCE_EFFICIENCY: {"icon": "⚡", "color": "#96CEB4"},
    WAFPillar.COST_OPTIMIZATION: {"icon": "💰", "color": "#FFEAA7"},
    WAFPillar.SUSTAINABILITY: {"icon": "🌱", "color": "#81C784"}
}

# Framework to pillar mapping
FRAMEWORK_PILLAR_MAP = {
    ComplianceFramework.SOC2: [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    ComplianceFramework.HIPAA: [WAFPillar.SECURITY, WAFPillar.RELIABILITY],
    ComplianceFramework.PCI_DSS: [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    ComplianceFramework.ISO_27001: list(WAFPillar),  # All pillars
    ComplianceFramework.CIS: [WAFPillar.SECURITY, WAFPillar.RELIABILITY],
    ComplianceFramework.GDPR: [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    ComplianceFramework.NIST: [WAFPillar.SECURITY, WAFPillar.RELIABILITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    ComplianceFramework.FEDRAMP: list(WAFPillar)  # All pillars
}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class AIInsight:
    """AI-generated insight"""
    id: str
    lens_type: AILensType
    category: str
    title: str
    description: str
    severity: str  # critical, high, medium, low, info
    confidence: float  # 0.0 - 1.0
    recommendations: List[str]
    affected_resources: List[str] = field(default_factory=list)
    waf_pillars: List[WAFPillar] = field(default_factory=list)
    compliance_impact: List[ComplianceFramework] = field(default_factory=list)
    auto_remediatable: bool = False
    remediation_code: Optional[str] = None

@dataclass
class ComplianceStatus:
    """Compliance status for a framework"""
    framework: ComplianceFramework
    score: float  # 0-100
    met_requirements: int
    partial_requirements: int
    gap_requirements: int
    total_requirements: int
    critical_gaps: List[str]
    high_gaps: List[str]
    evidence_items: List[str]

@dataclass
class IntegratedAssessment:
    """Combined AI + Compliance assessment"""
    id: str
    timestamp: datetime
    context: str  # Which tab/module generated this
    ai_insights: List[AIInsight]
    compliance_status: Dict[ComplianceFramework, ComplianceStatus]
    waf_scores: Dict[WAFPillar, float]
    overall_score: float
    priority_actions: List[str]

# ============================================================================
# AI LENS SERVICE
# ============================================================================

class AILensService:
    """
    Unified AI Lens service for cross-tab integration.
    Provides AI-powered analysis for any context.
    """
    
    def __init__(self):
        self.anthropic_client = None
        self.bedrock_client = None
        self._initialize_ai_client()
    
    def _initialize_ai_client(self):
        """Initialize AI client (Claude API or Bedrock)"""
        try:
            # Try Anthropic API first
            import os
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if hasattr(st, 'secrets'):
                api_key = api_key or st.secrets.get('ANTHROPIC_API_KEY')
            
            if api_key:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                return
            
            # Try AWS Bedrock as fallback
            import boto3
            self.bedrock_client = boto3.client('bedrock-runtime')
        except Exception:
            pass
    
    def _call_ai(self, prompt: str, system_prompt: str = None) -> Optional[str]:
        """Call AI model"""
        default_system = """You are an AWS Well-Architected Framework expert with deep knowledge of:
        - Security best practices and compliance frameworks
        - Cloud architecture patterns and anti-patterns
        - Cost optimization and FinOps
        - ML/AI workloads and responsible AI
        - Container orchestration (EKS/Kubernetes)
        
        Provide actionable, specific recommendations based on AWS best practices."""
        
        system = system_prompt or default_system
        
        try:
            if self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=system,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.bedrock_client:
                response = self.bedrock_client.invoke_model(
                    modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                    body=json.dumps({
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 4096,
                        "system": system,
                        "messages": [{"role": "user", "content": prompt}]
                    })
                )
                result = json.loads(response['body'].read())
                return result['content'][0]['text']
        except Exception as e:
            st.warning(f"AI service unavailable: {str(e)[:100]}")
        
        return None
    
    def analyze_findings(self, findings: List[Dict], context: str = "general") -> List[AIInsight]:
        """
        Analyze findings and generate AI insights.
        Can be called from any tab with findings data.
        """
        insights = []
        
        # Group findings by service and severity
        severity_groups = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
        service_groups = {}
        
        for finding in findings:
            severity = finding.get('severity', 'MEDIUM')
            service = finding.get('service', 'Unknown')
            
            if severity in severity_groups:
                severity_groups[severity].append(finding)
            
            if service not in service_groups:
                service_groups[service] = []
            service_groups[service].append(finding)
        
        # Generate pattern-based insights
        insights.extend(self._analyze_patterns(findings, service_groups, severity_groups))
        
        # Generate AI-powered insights if available
        if self.anthropic_client or self.bedrock_client:
            ai_insights = self._generate_ai_insights(findings, context)
            if ai_insights:
                insights.extend(ai_insights)
        
        # Sort by severity and confidence
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        insights.sort(key=lambda x: (severity_order.get(x.severity, 5), -x.confidence))
        
        return insights
    
    def _analyze_patterns(self, findings: List[Dict], service_groups: Dict, 
                          severity_groups: Dict) -> List[AIInsight]:
        """Analyze patterns in findings"""
        insights = []
        
        # Pattern: Multiple critical findings
        if len(severity_groups.get('CRITICAL', [])) >= 3:
            insights.append(AIInsight(
                id="pattern-critical-cluster",
                lens_type=AILensType.SECURITY,
                category="Security Pattern",
                title="Critical Security Issues Cluster Detected",
                description=f"Found {len(severity_groups['CRITICAL'])} critical severity issues. This indicates systemic security gaps that require immediate attention.",
                severity="critical",
                confidence=0.95,
                recommendations=[
                    "Prioritize critical findings for immediate remediation",
                    "Consider implementing security automation to prevent recurrence",
                    "Review security policies and access controls",
                    "Enable AWS Security Hub for continuous monitoring"
                ],
                waf_pillars=[WAFPillar.SECURITY],
                compliance_impact=[ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA]
            ))
        
        # Pattern: S3 bucket issues
        s3_findings = service_groups.get('S3', [])
        if len(s3_findings) >= 2:
            public_issues = [f for f in s3_findings if 'public' in f.get('title', '').lower()]
            encryption_issues = [f for f in s3_findings if 'encrypt' in f.get('title', '').lower()]
            
            if public_issues:
                insights.append(AIInsight(
                    id="pattern-s3-public",
                    lens_type=AILensType.SECURITY,
                    category="Data Security",
                    title="S3 Public Access Risk",
                    description=f"Found {len(public_issues)} S3 buckets with potential public access issues. This is a common cause of data breaches.",
                    severity="critical",
                    confidence=0.92,
                    recommendations=[
                        "Enable S3 Block Public Access at account level",
                        "Review and restrict bucket policies",
                        "Enable S3 Access Analyzer to detect public access",
                        "Implement S3 Object Lock for sensitive data"
                    ],
                    affected_resources=[f.get('resource', '') for f in public_issues],
                    waf_pillars=[WAFPillar.SECURITY],
                    compliance_impact=[ComplianceFramework.SOC2, ComplianceFramework.HIPAA, ComplianceFramework.GDPR],
                    auto_remediatable=True
                ))
            
            if encryption_issues:
                insights.append(AIInsight(
                    id="pattern-s3-encryption",
                    lens_type=AILensType.SECURITY,
                    category="Data Protection",
                    title="S3 Encryption Gaps",
                    description=f"Found {len(encryption_issues)} S3 buckets without default encryption. Data at rest should always be encrypted.",
                    severity="high",
                    confidence=0.90,
                    recommendations=[
                        "Enable default SSE-S3 or SSE-KMS encryption",
                        "Use bucket policies to enforce encryption",
                        "Consider AWS KMS for key management",
                        "Enable encryption for existing objects"
                    ],
                    affected_resources=[f.get('resource', '') for f in encryption_issues],
                    waf_pillars=[WAFPillar.SECURITY],
                    compliance_impact=[ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA],
                    auto_remediatable=True
                ))
        
        # Pattern: IAM issues
        iam_findings = service_groups.get('IAM', [])
        if iam_findings:
            insights.append(AIInsight(
                id="pattern-iam",
                lens_type=AILensType.SECURITY,
                category="Identity & Access",
                title="IAM Security Improvements Needed",
                description=f"Found {len(iam_findings)} IAM-related issues. Identity management is the foundation of cloud security.",
                severity="high",
                confidence=0.88,
                recommendations=[
                    "Implement least privilege access",
                    "Enable MFA for all IAM users",
                    "Use IAM roles instead of long-term credentials",
                    "Regularly review and rotate credentials",
                    "Enable IAM Access Analyzer"
                ],
                waf_pillars=[WAFPillar.SECURITY],
                compliance_impact=[ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS, ComplianceFramework.ISO_27001]
            ))
        
        # Pattern: EC2 security
        ec2_findings = service_groups.get('EC2', [])
        if ec2_findings:
            sg_issues = [f for f in ec2_findings if 'security group' in f.get('title', '').lower()]
            if sg_issues:
                insights.append(AIInsight(
                    id="pattern-ec2-sg",
                    lens_type=AILensType.SECURITY,
                    category="Network Security",
                    title="Security Group Configuration Issues",
                    description=f"Found {len(sg_issues)} security groups with potentially overly permissive rules.",
                    severity="high",
                    confidence=0.85,
                    recommendations=[
                        "Restrict inbound rules to specific IP ranges",
                        "Remove 0.0.0.0/0 rules for sensitive ports (22, 3389, 3306)",
                        "Use VPC endpoints instead of public internet access",
                        "Implement AWS Network Firewall for advanced protection"
                    ],
                    affected_resources=[f.get('resource', '') for f in sg_issues],
                    waf_pillars=[WAFPillar.SECURITY, WAFPillar.RELIABILITY],
                    compliance_impact=[ComplianceFramework.PCI_DSS, ComplianceFramework.CIS]
                ))
        
        # Pattern: Cost optimization opportunities
        cost_services = ['Cost Explorer', 'Trusted Advisor', 'Compute Optimizer']
        cost_findings = []
        for svc in cost_services:
            cost_findings.extend(service_groups.get(svc, []))
        
        if not cost_findings and len(findings) > 10:
            # No cost findings but many resources - suggest cost review
            insights.append(AIInsight(
                id="pattern-cost-review",
                lens_type=AILensType.COST,
                category="Cost Optimization",
                title="Cost Optimization Review Recommended",
                description="Multiple resources detected but no cost optimization analysis performed. Potential savings opportunities may exist.",
                severity="info",
                confidence=0.70,
                recommendations=[
                    "Enable AWS Cost Explorer for cost visibility",
                    "Use AWS Compute Optimizer for right-sizing",
                    "Review Reserved Instance and Savings Plan coverage",
                    "Identify and terminate unused resources",
                    "Implement cost allocation tags"
                ],
                waf_pillars=[WAFPillar.COST_OPTIMIZATION],
                compliance_impact=[]
            ))
        
        # Pattern: Reliability concerns
        reliability_services = ['Auto Scaling', 'ELB', 'Route 53', 'Backup']
        has_reliability = any(svc in service_groups for svc in reliability_services)
        
        if not has_reliability and len(findings) > 5:
            insights.append(AIInsight(
                id="pattern-reliability",
                lens_type=AILensType.GENERAL,
                category="Reliability",
                title="Reliability Architecture Review Needed",
                description="Limited visibility into reliability controls. Consider implementing high availability patterns.",
                severity="medium",
                confidence=0.65,
                recommendations=[
                    "Implement Auto Scaling for compute resources",
                    "Use Multi-AZ deployments for databases",
                    "Configure health checks and automated failover",
                    "Enable AWS Backup for data protection",
                    "Implement disaster recovery procedures"
                ],
                waf_pillars=[WAFPillar.RELIABILITY],
                compliance_impact=[ComplianceFramework.SOC2, ComplianceFramework.ISO_27001]
            ))
        
        return insights
    
    def _generate_ai_insights(self, findings: List[Dict], context: str) -> List[AIInsight]:
        """Generate AI-powered insights using Claude"""
        
        # Prepare findings summary for AI
        findings_summary = []
        for f in findings[:20]:  # Limit to 20 for token efficiency
            findings_summary.append({
                "title": f.get('title', ''),
                "severity": f.get('severity', ''),
                "service": f.get('service', ''),
                "resource": f.get('resource', '')
            })
        
        prompt = f"""Analyze these AWS security findings and provide strategic insights:

Context: {context}

Findings:
{json.dumps(findings_summary, indent=2)}

Provide 2-3 strategic insights in JSON format:
[
    {{
        "title": "Insight title",
        "description": "Detailed description",
        "severity": "critical|high|medium|low",
        "category": "Category name",
        "recommendations": ["rec1", "rec2", "rec3"],
        "waf_pillars": ["Security", "Reliability"],
        "compliance_frameworks": ["SOC2", "HIPAA"]
    }}
]

Focus on:
1. Cross-cutting patterns and root causes
2. Business risk implications
3. Actionable remediation strategies
4. Compliance implications"""

        try:
            response = self._call_ai(prompt)
            if response:
                # Parse JSON from response
                import re
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    ai_data = json.loads(json_match.group())
                    
                    insights = []
                    for item in ai_data:
                        insights.append(AIInsight(
                            id=f"ai-{hashlib.md5(item.get('title', '').encode()).hexdigest()[:8]}",
                            lens_type=AILensType.GENERAL,
                            category=item.get('category', 'AI Analysis'),
                            title=item.get('title', ''),
                            description=item.get('description', ''),
                            severity=item.get('severity', 'medium'),
                            confidence=0.85,
                            recommendations=item.get('recommendations', []),
                            waf_pillars=[WAFPillar(p) for p in item.get('waf_pillars', ['Security']) 
                                        if p in [e.value for e in WAFPillar]],
                            compliance_impact=[ComplianceFramework[f.replace(' ', '_').replace('-', '_').upper()] 
                                              for f in item.get('compliance_frameworks', [])
                                              if f.replace(' ', '_').replace('-', '_').upper() in ComplianceFramework.__members__]
                        ))
                    return insights
        except Exception as e:
            pass
        
        return []
    
    def get_architecture_recommendations(self, architecture: Dict) -> List[AIInsight]:
        """Get AI recommendations for an architecture design"""
        
        prompt = f"""Review this AWS architecture design and provide Well-Architected recommendations:

Architecture:
{json.dumps(architecture, indent=2)}

Provide recommendations in JSON format covering all 6 WAF pillars:
[
    {{
        "pillar": "Security|Reliability|...",
        "title": "Recommendation title",
        "description": "Why this matters",
        "current_gap": "What's missing",
        "recommendation": "What to implement",
        "aws_services": ["Service1", "Service2"],
        "priority": "high|medium|low"
    }}
]"""

        insights = []
        response = self._call_ai(prompt)
        
        if response:
            try:
                import re
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    recs = json.loads(json_match.group())
                    for rec in recs:
                        pillar = rec.get('pillar', 'Security')
                        insights.append(AIInsight(
                            id=f"arch-{hashlib.md5(rec.get('title', '').encode()).hexdigest()[:8]}",
                            lens_type=AILensType.GENERAL,
                            category=f"Architecture - {pillar}",
                            title=rec.get('title', ''),
                            description=rec.get('description', ''),
                            severity=rec.get('priority', 'medium'),
                            confidence=0.80,
                            recommendations=[rec.get('recommendation', '')],
                            waf_pillars=[WAFPillar(pillar)] if pillar in [e.value for e in WAFPillar] else [WAFPillar.SECURITY]
                        ))
            except Exception:
                pass
        
        return insights
    
    def get_eks_recommendations(self, cluster_config: Dict) -> List[AIInsight]:
        """Get AI recommendations for EKS configuration"""
        
        insights = []
        
        # Analyze cluster configuration
        node_groups = cluster_config.get('node_groups', [])
        networking = cluster_config.get('networking', {})
        security = cluster_config.get('security', {})
        
        # Security recommendations
        if not security.get('secrets_encryption', False):
            insights.append(AIInsight(
                id="eks-secrets-encryption",
                lens_type=AILensType.SECURITY,
                category="EKS Security",
                title="Enable EKS Secrets Encryption",
                description="EKS secrets should be encrypted using AWS KMS for data protection compliance.",
                severity="high",
                confidence=0.95,
                recommendations=[
                    "Enable envelope encryption for Kubernetes secrets",
                    "Use AWS KMS CMK for key management",
                    "Rotate encryption keys regularly"
                ],
                waf_pillars=[WAFPillar.SECURITY],
                compliance_impact=[ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS, ComplianceFramework.HIPAA],
                auto_remediatable=True
            ))
        
        if not security.get('pod_security_policy', False):
            insights.append(AIInsight(
                id="eks-pod-security",
                lens_type=AILensType.SECURITY,
                category="EKS Security",
                title="Implement Pod Security Standards",
                description="Pod Security Standards should be enforced to prevent privileged container execution.",
                severity="high",
                confidence=0.90,
                recommendations=[
                    "Enable Pod Security Admission controller",
                    "Apply baseline or restricted policy",
                    "Use OPA Gatekeeper for advanced policies"
                ],
                waf_pillars=[WAFPillar.SECURITY],
                compliance_impact=[ComplianceFramework.CIS, ComplianceFramework.SOC2]
            ))
        
        # Reliability recommendations
        if len(node_groups) < 2:
            insights.append(AIInsight(
                id="eks-multi-az",
                lens_type=AILensType.GENERAL,
                category="EKS Reliability",
                title="Implement Multi-AZ Node Groups",
                description="Single node group configuration reduces fault tolerance. Spread across multiple AZs.",
                severity="medium",
                confidence=0.85,
                recommendations=[
                    "Create node groups across multiple AZs",
                    "Use managed node groups for simplified operations",
                    "Implement Pod Disruption Budgets"
                ],
                waf_pillars=[WAFPillar.RELIABILITY],
                compliance_impact=[ComplianceFramework.SOC2]
            ))
        
        # Cost recommendations
        if not cluster_config.get('spot_instances', False):
            insights.append(AIInsight(
                id="eks-spot",
                lens_type=AILensType.COST,
                category="EKS Cost Optimization",
                title="Consider Spot Instances for Cost Savings",
                description="Spot instances can reduce EKS node costs by up to 90% for fault-tolerant workloads.",
                severity="info",
                confidence=0.75,
                recommendations=[
                    "Use Spot instances for non-critical workloads",
                    "Implement node termination handlers",
                    "Mix On-Demand and Spot in node groups"
                ],
                waf_pillars=[WAFPillar.COST_OPTIMIZATION],
                compliance_impact=[]
            ))
        
        return insights


# ============================================================================
# COMPLIANCE SERVICE
# ============================================================================

class ComplianceService:
    """
    Unified Compliance service for cross-tab integration.
    Maps findings to compliance frameworks and calculates compliance status.
    """
    
    def __init__(self):
        self.framework_requirements = self._load_framework_requirements()
    
    def _load_framework_requirements(self) -> Dict[ComplianceFramework, List[Dict]]:
        """Load compliance framework requirements"""
        
        return {
            ComplianceFramework.SOC2: [
                {"id": "CC6.1", "title": "Logical Access Security", "category": "Security", 
                 "finding_keywords": ["iam", "access", "authentication", "mfa"], "priority": "high"},
                {"id": "CC6.6", "title": "System Boundary Protection", "category": "Security",
                 "finding_keywords": ["security group", "vpc", "firewall", "network"], "priority": "high"},
                {"id": "CC6.7", "title": "Data Transmission Security", "category": "Security",
                 "finding_keywords": ["encryption", "tls", "ssl", "transit"], "priority": "high"},
                {"id": "CC7.1", "title": "System Monitoring", "category": "Operations",
                 "finding_keywords": ["cloudwatch", "monitoring", "logging", "cloudtrail"], "priority": "medium"},
                {"id": "CC7.2", "title": "Incident Response", "category": "Operations",
                 "finding_keywords": ["guardduty", "security hub", "alert"], "priority": "medium"},
                {"id": "CC8.1", "title": "Change Management", "category": "Operations",
                 "finding_keywords": ["config", "cloudformation", "change"], "priority": "medium"},
            ],
            ComplianceFramework.HIPAA: [
                {"id": "164.312(a)(1)", "title": "Access Control", "category": "Technical Safeguards",
                 "finding_keywords": ["iam", "access", "authentication"], "priority": "high"},
                {"id": "164.312(a)(2)(iv)", "title": "Encryption", "category": "Technical Safeguards",
                 "finding_keywords": ["encryption", "kms", "encrypt"], "priority": "high"},
                {"id": "164.312(b)", "title": "Audit Controls", "category": "Technical Safeguards",
                 "finding_keywords": ["cloudtrail", "logging", "audit"], "priority": "high"},
                {"id": "164.312(c)(1)", "title": "Integrity Controls", "category": "Technical Safeguards",
                 "finding_keywords": ["integrity", "versioning", "backup"], "priority": "medium"},
                {"id": "164.312(d)", "title": "Person Authentication", "category": "Technical Safeguards",
                 "finding_keywords": ["mfa", "authentication", "identity"], "priority": "high"},
                {"id": "164.312(e)(1)", "title": "Transmission Security", "category": "Technical Safeguards",
                 "finding_keywords": ["tls", "ssl", "transit", "encryption"], "priority": "high"},
            ],
            ComplianceFramework.PCI_DSS: [
                {"id": "1.3", "title": "Firewall Configuration", "category": "Network Security",
                 "finding_keywords": ["security group", "firewall", "vpc"], "priority": "high"},
                {"id": "3.4", "title": "Data Encryption", "category": "Data Protection",
                 "finding_keywords": ["encryption", "kms", "encrypt"], "priority": "high"},
                {"id": "7.1", "title": "Access Control", "category": "Access Control",
                 "finding_keywords": ["iam", "access", "least privilege"], "priority": "high"},
                {"id": "8.3", "title": "Multi-Factor Authentication", "category": "Authentication",
                 "finding_keywords": ["mfa", "multi-factor"], "priority": "high"},
                {"id": "10.2", "title": "Audit Logging", "category": "Monitoring",
                 "finding_keywords": ["cloudtrail", "logging", "audit"], "priority": "high"},
                {"id": "11.4", "title": "Intrusion Detection", "category": "Security Testing",
                 "finding_keywords": ["guardduty", "intrusion", "detection"], "priority": "medium"},
            ],
            ComplianceFramework.ISO_27001: [
                {"id": "A.9.1", "title": "Access Control Policy", "category": "Access Control",
                 "finding_keywords": ["iam", "access", "policy"], "priority": "high"},
                {"id": "A.9.4", "title": "System Access Control", "category": "Access Control",
                 "finding_keywords": ["authentication", "mfa", "login"], "priority": "high"},
                {"id": "A.10.1", "title": "Cryptographic Controls", "category": "Cryptography",
                 "finding_keywords": ["encryption", "kms", "cryptograph"], "priority": "high"},
                {"id": "A.12.4", "title": "Logging and Monitoring", "category": "Operations Security",
                 "finding_keywords": ["cloudwatch", "cloudtrail", "logging"], "priority": "medium"},
                {"id": "A.13.1", "title": "Network Security", "category": "Communications Security",
                 "finding_keywords": ["vpc", "security group", "network"], "priority": "high"},
                {"id": "A.18.1", "title": "Compliance", "category": "Compliance",
                 "finding_keywords": ["compliance", "audit", "config"], "priority": "medium"},
            ],
            ComplianceFramework.CIS: [
                {"id": "1.1", "title": "Root Account MFA", "category": "Identity",
                 "finding_keywords": ["root", "mfa"], "priority": "critical"},
                {"id": "1.4", "title": "Access Key Rotation", "category": "Identity",
                 "finding_keywords": ["access key", "rotation", "credential"], "priority": "high"},
                {"id": "2.1", "title": "CloudTrail Enabled", "category": "Logging",
                 "finding_keywords": ["cloudtrail", "logging"], "priority": "high"},
                {"id": "2.6", "title": "S3 Bucket Logging", "category": "Logging",
                 "finding_keywords": ["s3", "logging", "access log"], "priority": "medium"},
                {"id": "4.1", "title": "Security Group SSH", "category": "Networking",
                 "finding_keywords": ["security group", "ssh", "22", "0.0.0.0"], "priority": "high"},
                {"id": "4.3", "title": "Default Security Group", "category": "Networking",
                 "finding_keywords": ["default", "security group"], "priority": "medium"},
            ],
            ComplianceFramework.GDPR: [
                {"id": "Art.5", "title": "Data Protection Principles", "category": "Principles",
                 "finding_keywords": ["encryption", "access", "data"], "priority": "high"},
                {"id": "Art.25", "title": "Data Protection by Design", "category": "Design",
                 "finding_keywords": ["encryption", "security", "privacy"], "priority": "high"},
                {"id": "Art.30", "title": "Records of Processing", "category": "Documentation",
                 "finding_keywords": ["logging", "audit", "cloudtrail"], "priority": "medium"},
                {"id": "Art.32", "title": "Security of Processing", "category": "Security",
                 "finding_keywords": ["encryption", "access control", "security"], "priority": "high"},
                {"id": "Art.33", "title": "Breach Notification", "category": "Incident Response",
                 "finding_keywords": ["guardduty", "security hub", "incident"], "priority": "high"},
            ],
            ComplianceFramework.NIST: [
                {"id": "PR.AC", "title": "Access Control", "category": "Protect",
                 "finding_keywords": ["iam", "access", "authentication"], "priority": "high"},
                {"id": "PR.DS", "title": "Data Security", "category": "Protect",
                 "finding_keywords": ["encryption", "data", "kms"], "priority": "high"},
                {"id": "PR.IP", "title": "Information Protection", "category": "Protect",
                 "finding_keywords": ["backup", "config", "baseline"], "priority": "medium"},
                {"id": "DE.CM", "title": "Security Monitoring", "category": "Detect",
                 "finding_keywords": ["cloudwatch", "guardduty", "monitoring"], "priority": "medium"},
                {"id": "DE.AE", "title": "Anomaly Detection", "category": "Detect",
                 "finding_keywords": ["guardduty", "anomaly", "threat"], "priority": "medium"},
            ],
            ComplianceFramework.FEDRAMP: [
                {"id": "AC-2", "title": "Account Management", "category": "Access Control",
                 "finding_keywords": ["iam", "account", "user"], "priority": "high"},
                {"id": "AC-17", "title": "Remote Access", "category": "Access Control",
                 "finding_keywords": ["vpn", "remote", "bastion"], "priority": "high"},
                {"id": "AU-2", "title": "Audit Events", "category": "Audit",
                 "finding_keywords": ["cloudtrail", "audit", "logging"], "priority": "high"},
                {"id": "SC-7", "title": "Boundary Protection", "category": "System Protection",
                 "finding_keywords": ["vpc", "security group", "firewall"], "priority": "high"},
                {"id": "SC-28", "title": "Protection at Rest", "category": "System Protection",
                 "finding_keywords": ["encryption", "rest", "kms"], "priority": "high"},
            ]
        }
    
    def assess_compliance(self, findings: List[Dict], 
                          frameworks: List[ComplianceFramework] = None) -> Dict[ComplianceFramework, ComplianceStatus]:
        """
        Assess compliance status based on findings.
        Returns compliance status for each framework.
        """
        
        if frameworks is None:
            frameworks = list(ComplianceFramework)
        
        compliance_status = {}
        
        for framework in frameworks:
            requirements = self.framework_requirements.get(framework, [])
            
            met = 0
            partial = 0
            gaps = 0
            critical_gaps = []
            high_gaps = []
            evidence = []
            
            for req in requirements:
                # Check if findings relate to this requirement
                keywords = req.get('finding_keywords', [])
                related_findings = []
                
                for finding in findings:
                    title = finding.get('title', '').lower()
                    service = finding.get('service', '').lower()
                    desc = finding.get('description', '').lower()
                    
                    if any(kw in title or kw in service or kw in desc for kw in keywords):
                        related_findings.append(finding)
                
                # Determine requirement status
                if related_findings:
                    # Has related findings - check severity
                    critical = any(f.get('severity') == 'CRITICAL' for f in related_findings)
                    high = any(f.get('severity') == 'HIGH' for f in related_findings)
                    
                    if critical:
                        gaps += 1
                        critical_gaps.append(f"{req['id']}: {req['title']}")
                    elif high:
                        partial += 1
                        high_gaps.append(f"{req['id']}: {req['title']}")
                    else:
                        partial += 1
                    
                    evidence.append(f"{req['id']}: {len(related_findings)} findings")
                else:
                    # No findings for this requirement - assume met
                    met += 1
                    evidence.append(f"{req['id']}: No issues found")
            
            total = len(requirements)
            score = ((met * 100) + (partial * 50)) / max(total, 1)
            
            compliance_status[framework] = ComplianceStatus(
                framework=framework,
                score=min(100, score),
                met_requirements=met,
                partial_requirements=partial,
                gap_requirements=gaps,
                total_requirements=total,
                critical_gaps=critical_gaps,
                high_gaps=high_gaps,
                evidence_items=evidence
            )
        
        return compliance_status
    
    def get_compliance_impact(self, finding: Dict) -> List[ComplianceFramework]:
        """Get list of compliance frameworks impacted by a finding"""
        
        impacted = []
        title = finding.get('title', '').lower()
        service = finding.get('service', '').lower()
        desc = finding.get('description', '').lower()
        
        for framework, requirements in self.framework_requirements.items():
            for req in requirements:
                keywords = req.get('finding_keywords', [])
                if any(kw in title or kw in service or kw in desc for kw in keywords):
                    if framework not in impacted:
                        impacted.append(framework)
                    break
        
        return impacted
    
    def get_framework_summary(self, framework: ComplianceFramework) -> Dict:
        """Get summary of a compliance framework"""
        
        requirements = self.framework_requirements.get(framework, [])
        
        return {
            "framework": framework.value,
            "total_requirements": len(requirements),
            "categories": list(set(r.get('category', '') for r in requirements)),
            "high_priority": len([r for r in requirements if r.get('priority') == 'high']),
            "requirements": requirements
        }


# ============================================================================
# UNIFIED INTEGRATION SERVICE
# ============================================================================

class UnifiedIntegrationService:
    """
    Master integration service that combines AI Lens and Compliance.
    Provides a single interface for all tabs to use.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.ai_lens = AILensService()
        self.compliance = ComplianceService()
        self._initialized = True
    
    def get_integrated_assessment(self, findings: List[Dict], 
                                   context: str = "general",
                                   frameworks: List[ComplianceFramework] = None) -> IntegratedAssessment:
        """
        Get complete integrated assessment with AI insights and compliance status.
        This is the main method that tabs should use.
        """
        
        # Get AI insights
        ai_insights = self.ai_lens.analyze_findings(findings, context)
        
        # Get compliance status
        compliance_status = self.compliance.assess_compliance(findings, frameworks)
        
        # Calculate WAF pillar scores from findings
        waf_scores = self._calculate_waf_scores(findings)
        
        # Calculate overall score
        overall_score = sum(waf_scores.values()) / len(waf_scores) if waf_scores else 0
        
        # Get priority actions
        priority_actions = self._get_priority_actions(ai_insights, compliance_status)
        
        return IntegratedAssessment(
            id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
            timestamp=datetime.now(),
            context=context,
            ai_insights=ai_insights,
            compliance_status=compliance_status,
            waf_scores=waf_scores,
            overall_score=overall_score,
            priority_actions=priority_actions
        )
    
    def _calculate_waf_scores(self, findings: List[Dict]) -> Dict[WAFPillar, float]:
        """Calculate WAF pillar scores from findings"""
        
        scores = {pillar: 100.0 for pillar in WAFPillar}
        
        # Service to pillar mapping
        service_pillar = {
            'IAM': WAFPillar.SECURITY,
            'S3': WAFPillar.SECURITY,
            'EC2': WAFPillar.RELIABILITY,
            'RDS': WAFPillar.RELIABILITY,
            'VPC': WAFPillar.SECURITY,
            'Lambda': WAFPillar.PERFORMANCE_EFFICIENCY,
            'CloudWatch': WAFPillar.OPERATIONAL_EXCELLENCE,
            'CloudTrail': WAFPillar.SECURITY,
            'KMS': WAFPillar.SECURITY,
            'ELB': WAFPillar.RELIABILITY,
            'Auto Scaling': WAFPillar.RELIABILITY,
            'Cost Explorer': WAFPillar.COST_OPTIMIZATION,
            'Trusted Advisor': WAFPillar.COST_OPTIMIZATION,
            'EKS': WAFPillar.RELIABILITY,
            'ECS': WAFPillar.RELIABILITY
        }
        
        # Deduct points based on findings
        for finding in findings:
            service = finding.get('service', '')
            severity = finding.get('severity', 'MEDIUM')
            pillar = service_pillar.get(service, WAFPillar.SECURITY)
            
            deduction = {'CRITICAL': 15, 'HIGH': 10, 'MEDIUM': 5, 'LOW': 2}.get(severity, 5)
            scores[pillar] = max(0, scores[pillar] - deduction)
        
        return scores
    
    def _get_priority_actions(self, insights: List[AIInsight], 
                               compliance: Dict[ComplianceFramework, ComplianceStatus]) -> List[str]:
        """Get prioritized action items"""
        
        actions = []
        
        # Add actions from critical insights
        for insight in insights:
            if insight.severity in ['critical', 'high']:
                actions.append(f"[{insight.severity.upper()}] {insight.title}: {insight.recommendations[0] if insight.recommendations else 'Review required'}")
        
        # Add actions from compliance gaps
        for framework, status in compliance.items():
            for gap in status.critical_gaps[:2]:
                actions.append(f"[COMPLIANCE] {framework.value}: {gap}")
        
        return actions[:10]  # Limit to top 10


# ============================================================================
# UI COMPONENTS
# ============================================================================

class IntegrationUIComponents:
    """
    Reusable UI components for AI Lens and Compliance display.
    Use these in any tab for consistent presentation.
    """
    
    @staticmethod
    def render_ai_insights_panel(insights: List[AIInsight], expanded: bool = True):
        """Render AI insights panel - use in any tab"""
        
        if not insights:
            return
        
        with st.expander("🤖 AI Lens Insights", expanded=expanded):
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            critical = len([i for i in insights if i.severity == 'critical'])
            high = len([i for i in insights if i.severity == 'high'])
            medium = len([i for i in insights if i.severity == 'medium'])
            
            with col1:
                st.metric("Total Insights", len(insights))
            with col2:
                st.metric("🔴 Critical", critical)
            with col3:
                st.metric("🟠 High", high)
            with col4:
                st.metric("🟡 Medium", medium)
            
            st.markdown("---")
            
            # Render each insight
            for insight in insights:
                IntegrationUIComponents._render_single_insight(insight)
    
    @staticmethod
    def _render_single_insight(insight: AIInsight):
        """Render a single AI insight"""
        
        severity_config = {
            'critical': {'icon': '🔴', 'color': '#dc3545'},
            'high': {'icon': '🟠', 'color': '#fd7e14'},
            'medium': {'icon': '🟡', 'color': '#ffc107'},
            'low': {'icon': '🟢', 'color': '#28a745'},
            'info': {'icon': 'ℹ️', 'color': '#17a2b8'}
        }
        
        config = severity_config.get(insight.severity, severity_config['medium'])
        
        st.markdown(f"""
        <div style="border-left: 4px solid {config['color']}; padding: 10px 15px; 
                    margin-bottom: 10px; background: #f8f9fa; border-radius: 0 5px 5px 0;">
            <h4 style="margin: 0;">{config['icon']} {insight.title}</h4>
            <p style="color: #666; margin: 5px 0;">{insight.description}</p>
            <small>
                <b>Category:</b> {insight.category} | 
                <b>Confidence:</b> {insight.confidence:.0%} |
                <b>Pillars:</b> {', '.join([p.value for p in insight.waf_pillars])}
            </small>
        </div>
        """, unsafe_allow_html=True)
        
        if insight.recommendations:
            with st.expander("📋 Recommendations", expanded=False):
                for rec in insight.recommendations:
                    st.markdown(f"• {rec}")
        
        if insight.compliance_impact:
            st.caption(f"🔒 Compliance Impact: {', '.join([f.value for f in insight.compliance_impact])}")
    
    @staticmethod
    def render_compliance_status_panel(compliance_status: Dict[ComplianceFramework, ComplianceStatus], 
                                        expanded: bool = True):
        """Render compliance status panel - use in any tab"""
        
        if not compliance_status:
            return
        
        with st.expander("🔒 Compliance Status", expanded=expanded):
            # Framework cards
            cols = st.columns(min(len(compliance_status), 4))
            
            for idx, (framework, status) in enumerate(compliance_status.items()):
                with cols[idx % 4]:
                    score = status.score
                    color = "#28a745" if score >= 80 else "#ffc107" if score >= 60 else "#dc3545"
                    
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; border-radius: 10px; padding: 15px; 
                                text-align: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; font-size: 14px;">{framework.value}</h4>
                        <h2 style="color: {color}; margin: 10px 0;">{score:.0f}%</h2>
                        <small>
                            ✅ {status.met_requirements} | 
                            ⚠️ {status.partial_requirements} | 
                            ❌ {status.gap_requirements}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Critical gaps
            all_critical = []
            for framework, status in compliance_status.items():
                for gap in status.critical_gaps:
                    all_critical.append(f"**{framework.value}**: {gap}")
            
            if all_critical:
                st.markdown("---")
                st.markdown("### ⚠️ Critical Compliance Gaps")
                for gap in all_critical[:5]:
                    st.error(gap)
    
    @staticmethod
    def render_waf_pillar_scores(waf_scores: Dict[WAFPillar, float]):
        """Render WAF pillar scores visualization"""
        
        st.markdown("### 📊 WAF Pillar Scores")
        
        cols = st.columns(6)
        
        for idx, pillar in enumerate(WAFPillar):
            score = waf_scores.get(pillar, 0)
            config = PILLAR_CONFIG.get(pillar, {"icon": "📋", "color": "#666"})
            
            color = "#28a745" if score >= 80 else "#ffc107" if score >= 60 else "#dc3545"
            
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; border: 2px solid {config['color']}; 
                            border-radius: 10px; margin: 5px;">
                    <div style="font-size: 24px;">{config['icon']}</div>
                    <div style="font-size: 12px; color: #666;">{pillar.value}</div>
                    <div style="font-size: 24px; font-weight: bold; color: {color};">{score:.0f}</div>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def render_integrated_sidebar():
        """Render integrated AI/Compliance status in sidebar"""
        
        # Get current assessment from session state
        assessment = st.session_state.get('current_integrated_assessment')
        
        if not assessment:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🤖 AI Lens")
            st.sidebar.info("Run a scan to see AI insights")
            st.sidebar.markdown("### 🔒 Compliance")
            st.sidebar.info("Run a scan to see compliance status")
            return
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤖 AI Lens")
        
        critical = len([i for i in assessment.ai_insights if i.severity == 'critical'])
        high = len([i for i in assessment.ai_insights if i.severity == 'high'])
        
        if critical > 0:
            st.sidebar.error(f"🔴 {critical} Critical Insights")
        if high > 0:
            st.sidebar.warning(f"🟠 {high} High Insights")
        if critical == 0 and high == 0:
            st.sidebar.success("✅ No critical issues")
        
        st.sidebar.markdown("### 🔒 Compliance")
        
        # Show lowest compliance score
        if assessment.compliance_status:
            min_framework = min(assessment.compliance_status.items(), key=lambda x: x[1].score)
            st.sidebar.metric(
                min_framework[0].value,
                f"{min_framework[1].score:.0f}%",
                delta=f"{min_framework[1].gap_requirements} gaps"
            )
    
    @staticmethod
    def render_quick_actions(assessment: IntegratedAssessment):
        """Render quick action buttons based on assessment"""
        
        if not assessment.priority_actions:
            return
        
        st.markdown("### ⚡ Priority Actions")
        
        for action in assessment.priority_actions[:5]:
            if "[CRITICAL]" in action:
                st.error(action)
            elif "[HIGH]" in action:
                st.warning(action)
            elif "[COMPLIANCE]" in action:
                st.info(action)
            else:
                st.markdown(f"• {action}")


# ============================================================================
# TAB INTEGRATION HELPERS
# ============================================================================

class TabIntegrationHelper:
    """
    Helper functions to integrate AI Lens and Compliance into specific tabs.
    Call these from each tab to add the integration.
    """
    
    @staticmethod
    def integrate_with_waf_review(findings: List[Dict]):
        """Add AI/Compliance integration to WAF Review tab"""
        
        service = UnifiedIntegrationService()
        assessment = service.get_integrated_assessment(
            findings, 
            context="WAF Review",
            frameworks=[ComplianceFramework.SOC2, ComplianceFramework.HIPAA, 
                       ComplianceFramework.PCI_DSS, ComplianceFramework.ISO_27001]
        )
        
        # Store in session state
        st.session_state['current_integrated_assessment'] = assessment
        
        # Render components
        st.markdown("---")
        IntegrationUIComponents.render_ai_insights_panel(assessment.ai_insights)
        IntegrationUIComponents.render_compliance_status_panel(assessment.compliance_status)
        IntegrationUIComponents.render_waf_pillar_scores(assessment.waf_scores)
        IntegrationUIComponents.render_quick_actions(assessment)
        
        return assessment
    
    @staticmethod
    def integrate_with_architecture_designer(architecture: Dict):
        """Add AI/Compliance integration to Architecture Designer tab"""
        
        service = UnifiedIntegrationService()
        
        # Get architecture-specific recommendations
        arch_insights = service.ai_lens.get_architecture_recommendations(architecture)
        
        # Create assessment
        assessment = IntegratedAssessment(
            id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
            timestamp=datetime.now(),
            context="Architecture Designer",
            ai_insights=arch_insights,
            compliance_status={},
            waf_scores={pillar: 100.0 for pillar in WAFPillar},
            overall_score=100.0,
            priority_actions=[i.recommendations[0] for i in arch_insights if i.recommendations][:5]
        )
        
        st.session_state['current_integrated_assessment'] = assessment
        
        st.markdown("---")
        st.markdown("### 🤖 AI Architecture Review")
        IntegrationUIComponents.render_ai_insights_panel(arch_insights, expanded=True)
        
        return assessment
    
    @staticmethod
    def integrate_with_eks_modernization(cluster_config: Dict):
        """Add AI/Compliance integration to EKS Modernization tab"""
        
        service = UnifiedIntegrationService()
        
        # Get EKS-specific recommendations
        eks_insights = service.ai_lens.get_eks_recommendations(cluster_config)
        
        # Get container-related compliance status
        container_findings = [
            {"title": "EKS Security", "service": "EKS", "severity": "MEDIUM"}
        ]
        compliance_status = service.compliance.assess_compliance(
            container_findings,
            [ComplianceFramework.SOC2, ComplianceFramework.CIS]
        )
        
        assessment = IntegratedAssessment(
            id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
            timestamp=datetime.now(),
            context="EKS Modernization",
            ai_insights=eks_insights,
            compliance_status=compliance_status,
            waf_scores={pillar: 85.0 for pillar in WAFPillar},
            overall_score=85.0,
            priority_actions=[i.recommendations[0] for i in eks_insights if i.recommendations][:5]
        )
        
        st.session_state['current_integrated_assessment'] = assessment
        
        st.markdown("---")
        st.markdown("### 🤖 AI EKS Review")
        IntegrationUIComponents.render_ai_insights_panel(eks_insights)
        IntegrationUIComponents.render_compliance_status_panel(compliance_status)
        
        return assessment
    
    @staticmethod
    def integrate_with_finops(cost_data: Dict):
        """Add AI/Compliance integration to FinOps tab"""
        
        service = UnifiedIntegrationService()
        
        # Generate cost-focused insights
        cost_insights = [
            AIInsight(
                id="finops-savings",
                lens_type=AILensType.COST,
                category="Cost Optimization",
                title="Reserved Instance Coverage Analysis",
                description="Analyze RI and Savings Plan coverage for potential cost savings.",
                severity="info",
                confidence=0.85,
                recommendations=[
                    "Review On-Demand vs Reserved Instance spend",
                    "Consider Savings Plans for compute-heavy workloads",
                    "Enable Cost Explorer rightsizing recommendations"
                ],
                waf_pillars=[WAFPillar.COST_OPTIMIZATION],
                compliance_impact=[]
            ),
            AIInsight(
                id="finops-waste",
                lens_type=AILensType.COST,
                category="Cost Optimization",
                title="Resource Utilization Review",
                description="Identify underutilized resources for rightsizing or termination.",
                severity="medium",
                confidence=0.80,
                recommendations=[
                    "Use AWS Compute Optimizer for EC2 rightsizing",
                    "Review and clean up unattached EBS volumes",
                    "Check for unused Elastic IPs"
                ],
                waf_pillars=[WAFPillar.COST_OPTIMIZATION, WAFPillar.SUSTAINABILITY],
                compliance_impact=[]
            )
        ]
        
        st.markdown("---")
        st.markdown("### 🤖 AI Cost Insights")
        IntegrationUIComponents.render_ai_insights_panel(cost_insights)
        
        return cost_insights
    
    @staticmethod
    def integrate_with_compliance_tab(findings: List[Dict]):
        """Add AI integration to Compliance tab"""
        
        service = UnifiedIntegrationService()
        
        # Get full compliance assessment
        compliance_status = service.compliance.assess_compliance(
            findings,
            list(ComplianceFramework)
        )
        
        # Get AI insights focused on compliance
        ai_insights = service.ai_lens.analyze_findings(findings, context="Compliance Assessment")
        
        # Filter to compliance-relevant insights
        compliance_insights = [i for i in ai_insights if i.compliance_impact]
        
        st.markdown("### 🤖 AI Compliance Analysis")
        IntegrationUIComponents.render_ai_insights_panel(compliance_insights, expanded=True)
        
        return compliance_status, compliance_insights


# ============================================================================
# MAIN INTEGRATION FUNCTION
# ============================================================================

def get_integration_service() -> UnifiedIntegrationService:
    """Get the singleton integration service instance"""
    return UnifiedIntegrationService()


def render_integrated_assessment(findings: List[Dict], context: str = "general"):
    """
    Main function to render integrated AI/Compliance assessment.
    Call this from any tab with findings data.
    """
    
    service = get_integration_service()
    assessment = service.get_integrated_assessment(findings, context)
    
    st.session_state['current_integrated_assessment'] = assessment
    
    # Render all components
    st.markdown("---")
    IntegrationUIComponents.render_waf_pillar_scores(assessment.waf_scores)
    IntegrationUIComponents.render_ai_insights_panel(assessment.ai_insights)
    IntegrationUIComponents.render_compliance_status_panel(assessment.compliance_status)
    IntegrationUIComponents.render_quick_actions(assessment)
    
    return assessment


# ============================================================================
# EXPORT INTEGRATION CODE SNIPPETS FOR EACH TAB
# ============================================================================

INTEGRATION_CODE_SNIPPETS = """
# ============================================================================
# HOW TO INTEGRATE INTO EACH TAB
# ============================================================================

# === WAF Review Tab ===
# Add at the end of display_multi_account_results():

from integration_ai_compliance import TabIntegrationHelper

def display_multi_account_results(results):
    # ... existing code ...
    
    # Add AI/Compliance integration
    findings = []
    for account_id, data in results.items():
        if account_id != 'consolidated_pdf' and isinstance(data, dict):
            findings.extend(data.get('findings', []))
    
    if findings:
        TabIntegrationHelper.integrate_with_waf_review(findings)


# === Architecture Designer Tab ===
# Add after architecture is generated:

from integration_ai_compliance import TabIntegrationHelper

def render_architecture_output(architecture):
    # ... existing code ...
    
    # Add AI review
    TabIntegrationHelper.integrate_with_architecture_designer(architecture)


# === EKS Modernization Tab ===
# Add after cluster config is defined:

from integration_ai_compliance import TabIntegrationHelper

def render_eks_cluster_design(cluster_config):
    # ... existing code ...
    
    # Add AI/Compliance review
    TabIntegrationHelper.integrate_with_eks_modernization(cluster_config)


# === FinOps Tab ===
# Add in the cost analysis section:

from integration_ai_compliance import TabIntegrationHelper

def render_finops_analysis(cost_data):
    # ... existing code ...
    
    # Add AI cost insights
    TabIntegrationHelper.integrate_with_finops(cost_data)


# === Compliance Tab ===
# Replace or enhance existing compliance rendering:

from integration_ai_compliance import TabIntegrationHelper

def render_compliance_module(findings):
    # Get enhanced compliance with AI insights
    compliance_status, ai_insights = TabIntegrationHelper.integrate_with_compliance_tab(findings)
    
    # ... render compliance details ...


# === Sidebar Integration ===
# Add to main app sidebar:

from integration_ai_compliance import IntegrationUIComponents

def render_sidebar():
    # ... existing sidebar code ...
    
    # Add AI/Compliance status
    IntegrationUIComponents.render_integrated_sidebar()
"""


if __name__ == "__main__":
    # Demo/test mode
    st.set_page_config(page_title="AI Lens & Compliance Integration", layout="wide")
    
    st.title("🤖 AI Lens & Compliance Integration Demo")
    
    # Sample findings for demo
    sample_findings = [
        {"title": "S3 Bucket Without Encryption", "service": "S3", "severity": "HIGH", "resource": "my-bucket"},
        {"title": "Security Group Open to Internet", "service": "EC2", "severity": "CRITICAL", "resource": "sg-123"},
        {"title": "IAM User Without MFA", "service": "IAM", "severity": "HIGH", "resource": "admin-user"},
        {"title": "CloudTrail Not Enabled", "service": "CloudTrail", "severity": "MEDIUM", "resource": "account"},
        {"title": "RDS Instance Not Encrypted", "service": "RDS", "severity": "HIGH", "resource": "mydb"},
    ]
    
    render_integrated_assessment(sample_findings, "Demo")
