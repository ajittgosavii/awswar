"""
EKS Modernization Hub - INTEGRATED with WAF, Compliance & AI Lens
=================================================================
Complete platform for EKS transformation fully integrated with:
- All 6 AWS Well-Architected Framework Pillars  
- 8 Compliance Frameworks (SOC2, HIPAA, PCI-DSS, ISO 27001, CIS, GDPR, NIST, FedRAMP)
- AI Lens for intelligent Kubernetes recommendations

Version: 4.0.0 (WAF-Compliance-AI Integrated)
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# ============================================================================
# ENUMS & CONSTANTS  
# ============================================================================

class WAFPillar(Enum):
    """AWS Well-Architected Framework Pillars"""
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"

class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    SOC2 = "SOC 2 Type II"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS v4.0"
    ISO_27001 = "ISO 27001:2022"
    CIS = "CIS EKS Benchmarks"
    GDPR = "GDPR"
    NIST = "NIST CSF"
    FEDRAMP = "FedRAMP"

class EKSSecurityLevel(Enum):
    """EKS Security posture levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SECURE = "secure"

# Pillar configuration
PILLAR_CONFIG = {
    WAFPillar.OPERATIONAL_EXCELLENCE: {"icon": "⚙️", "color": "#FF6B6B", "weight": 0.15},
    WAFPillar.SECURITY: {"icon": "🔒", "color": "#4ECDC4", "weight": 0.25},
    WAFPillar.RELIABILITY: {"icon": "🛡️", "color": "#45B7D1", "weight": 0.20},
    WAFPillar.PERFORMANCE_EFFICIENCY: {"icon": "⚡", "color": "#96CEB4", "weight": 0.15},
    WAFPillar.COST_OPTIMIZATION: {"icon": "💰", "color": "#FFEAA7", "weight": 0.15},
    WAFPillar.SUSTAINABILITY: {"icon": "🌱", "color": "#81C784", "weight": 0.10}
}

# EKS Feature to WAF Pillar mapping
EKS_FEATURE_PILLAR_MAP = {
    # Security Features
    'secrets_encryption': [WAFPillar.SECURITY],
    'pod_security_standards': [WAFPillar.SECURITY],
    'network_policies': [WAFPillar.SECURITY],
    'private_endpoint': [WAFPillar.SECURITY],
    'irsa': [WAFPillar.SECURITY],
    'oidc_provider': [WAFPillar.SECURITY],
    'audit_logging': [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    'image_scanning': [WAFPillar.SECURITY],
    'runtime_security': [WAFPillar.SECURITY],
    'service_mesh': [WAFPillar.SECURITY, WAFPillar.RELIABILITY],
    
    # Reliability Features
    'multi_az': [WAFPillar.RELIABILITY],
    'cluster_autoscaler': [WAFPillar.RELIABILITY, WAFPillar.COST_OPTIMIZATION],
    'karpenter': [WAFPillar.RELIABILITY, WAFPillar.COST_OPTIMIZATION],
    'pod_disruption_budgets': [WAFPillar.RELIABILITY],
    'health_checks': [WAFPillar.RELIABILITY],
    'managed_node_groups': [WAFPillar.RELIABILITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    'fargate': [WAFPillar.RELIABILITY, WAFPillar.COST_OPTIMIZATION],
    'horizontal_pod_autoscaler': [WAFPillar.RELIABILITY, WAFPillar.PERFORMANCE_EFFICIENCY],
    'vertical_pod_autoscaler': [WAFPillar.RELIABILITY, WAFPillar.COST_OPTIMIZATION],
    
    # Operational Excellence Features
    'cloudwatch_container_insights': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'prometheus': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'grafana': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'fluentbit': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'gitops': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'argocd': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'flux': [WAFPillar.OPERATIONAL_EXCELLENCE],
    
    # Performance Features
    'cluster_proportional_autoscaler': [WAFPillar.PERFORMANCE_EFFICIENCY],
    'node_local_dns': [WAFPillar.PERFORMANCE_EFFICIENCY],
    'cni_optimization': [WAFPillar.PERFORMANCE_EFFICIENCY],
    
    # Cost Features
    'spot_instances': [WAFPillar.COST_OPTIMIZATION],
    'savings_plans': [WAFPillar.COST_OPTIMIZATION],
    'resource_quotas': [WAFPillar.COST_OPTIMIZATION],
    'limit_ranges': [WAFPillar.COST_OPTIMIZATION],
    
    # Sustainability Features
    'graviton_nodes': [WAFPillar.SUSTAINABILITY, WAFPillar.COST_OPTIMIZATION],
    'right_sizing': [WAFPillar.SUSTAINABILITY, WAFPillar.COST_OPTIMIZATION],
}

# EKS Feature to Compliance mapping
EKS_FEATURE_COMPLIANCE_MAP = {
    'secrets_encryption': [ComplianceFramework.SOC2, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS, ComplianceFramework.ISO_27001],
    'audit_logging': [ComplianceFramework.SOC2, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS, ComplianceFramework.CIS, ComplianceFramework.NIST],
    'network_policies': [ComplianceFramework.PCI_DSS, ComplianceFramework.CIS, ComplianceFramework.NIST],
    'private_endpoint': [ComplianceFramework.PCI_DSS, ComplianceFramework.CIS, ComplianceFramework.HIPAA],
    'irsa': [ComplianceFramework.SOC2, ComplianceFramework.CIS, ComplianceFramework.NIST],
    'pod_security_standards': [ComplianceFramework.CIS, ComplianceFramework.NIST, ComplianceFramework.SOC2],
    'image_scanning': [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS],
    'runtime_security': [ComplianceFramework.PCI_DSS, ComplianceFramework.NIST],
    'multi_az': [ComplianceFramework.SOC2, ComplianceFramework.HIPAA],
}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class EKSClusterConfig:
    """EKS Cluster configuration"""
    name: str = "my-cluster"
    version: str = "1.29"
    region: str = "us-east-1"
    
    # Node configuration
    node_groups: List[Dict] = field(default_factory=list)
    fargate_profiles: List[Dict] = field(default_factory=list)
    use_karpenter: bool = False
    use_spot: bool = False
    use_graviton: bool = False
    
    # Security configuration
    secrets_encryption: bool = False
    pod_security_standards: bool = False
    network_policies: bool = False
    private_endpoint: bool = False
    public_endpoint: bool = True
    irsa_enabled: bool = False
    oidc_provider: bool = False
    audit_logging: bool = True
    image_scanning: bool = False
    runtime_security: bool = False
    
    # Networking
    vpc_cni_version: str = "latest"
    service_mesh: str = "none"  # none, istio, appmesh
    
    # Observability
    cloudwatch_insights: bool = False
    prometheus: bool = False
    grafana: bool = False
    fluentbit: bool = False
    
    # Operations
    gitops: str = "none"  # none, argocd, flux
    managed_node_groups: bool = True
    
    # Scaling
    cluster_autoscaler: bool = False
    horizontal_pod_autoscaler: bool = True
    vertical_pod_autoscaler: bool = False
    
    # Cost
    resource_quotas: bool = False
    limit_ranges: bool = False
    
    # Reliability
    multi_az: bool = True
    pod_disruption_budgets: bool = False

@dataclass
class EKSFinding:
    """EKS security/compliance finding"""
    id: str
    category: str
    pillar: WAFPillar
    severity: str
    title: str
    description: str
    recommendation: str
    compliance_impact: List[ComplianceFramework] = field(default_factory=list)
    cis_benchmark: str = ""
    remediation_yaml: str = ""
    auto_remediatable: bool = False

@dataclass
class EKSWAFScore:
    """WAF Pillar score for EKS"""
    pillar: WAFPillar
    score: int
    max_score: int = 100
    findings_count: int = 0
    features_enabled: List[str] = field(default_factory=list)
    features_missing: List[str] = field(default_factory=list)

@dataclass
class EKSComplianceScore:
    """Compliance score for EKS"""
    framework: ComplianceFramework
    score: int
    controls_passed: int = 0
    controls_failed: int = 0
    total_controls: int = 0
    critical_gaps: List[str] = field(default_factory=list)

@dataclass
class EKSAssessment:
    """Complete EKS assessment"""
    id: str
    timestamp: datetime
    cluster_config: EKSClusterConfig
    waf_scores: Dict[WAFPillar, EKSWAFScore]
    compliance_scores: Dict[ComplianceFramework, EKSComplianceScore]
    findings: List[EKSFinding]
    overall_waf_score: int
    overall_compliance_score: int
    security_posture: EKSSecurityLevel
    ai_recommendations: List[str]

# ============================================================================
# EKS WAF ASSESSOR
# ============================================================================

class EKSWAFAssessor:
    """Assesses EKS configurations against WAF pillars"""
    
    def __init__(self):
        self.pillar_requirements = self._load_pillar_requirements()
    
    def _load_pillar_requirements(self) -> Dict[WAFPillar, List[Dict]]:
        """Load WAF requirements for EKS"""
        return {
            WAFPillar.SECURITY: [
                {"id": "EKS-SEC-01", "feature": "secrets_encryption", "title": "Secrets Encryption", "weight": 20, "critical": True},
                {"id": "EKS-SEC-02", "feature": "pod_security_standards", "title": "Pod Security Standards", "weight": 15, "critical": True},
                {"id": "EKS-SEC-03", "feature": "network_policies", "title": "Network Policies", "weight": 15, "critical": False},
                {"id": "EKS-SEC-04", "feature": "private_endpoint", "title": "Private API Endpoint", "weight": 15, "critical": False},
                {"id": "EKS-SEC-05", "feature": "irsa_enabled", "title": "IAM Roles for Service Accounts", "weight": 15, "critical": True},
                {"id": "EKS-SEC-06", "feature": "audit_logging", "title": "Control Plane Audit Logging", "weight": 10, "critical": True},
                {"id": "EKS-SEC-07", "feature": "image_scanning", "title": "Container Image Scanning", "weight": 10, "critical": False},
            ],
            WAFPillar.RELIABILITY: [
                {"id": "EKS-REL-01", "feature": "multi_az", "title": "Multi-AZ Deployment", "weight": 25, "critical": True},
                {"id": "EKS-REL-02", "feature": "cluster_autoscaler", "title": "Cluster Auto Scaling", "weight": 20, "critical": False},
                {"id": "EKS-REL-03", "feature": "pod_disruption_budgets", "title": "Pod Disruption Budgets", "weight": 15, "critical": False},
                {"id": "EKS-REL-04", "feature": "managed_node_groups", "title": "Managed Node Groups", "weight": 15, "critical": False},
                {"id": "EKS-REL-05", "feature": "horizontal_pod_autoscaler", "title": "Horizontal Pod Autoscaler", "weight": 15, "critical": False},
                {"id": "EKS-REL-06", "feature": "multi_az", "title": "Health Checks", "weight": 10, "critical": False},
            ],
            WAFPillar.OPERATIONAL_EXCELLENCE: [
                {"id": "EKS-OPS-01", "feature": "cloudwatch_insights", "title": "CloudWatch Container Insights", "weight": 25, "critical": False},
                {"id": "EKS-OPS-02", "feature": "audit_logging", "title": "Audit Logging Enabled", "weight": 20, "critical": True},
                {"id": "EKS-OPS-03", "feature": "gitops", "title": "GitOps Deployment", "weight": 20, "critical": False},
                {"id": "EKS-OPS-04", "feature": "prometheus", "title": "Prometheus Monitoring", "weight": 15, "critical": False},
                {"id": "EKS-OPS-05", "feature": "fluentbit", "title": "Centralized Logging", "weight": 20, "critical": False},
            ],
            WAFPillar.PERFORMANCE_EFFICIENCY: [
                {"id": "EKS-PERF-01", "feature": "horizontal_pod_autoscaler", "title": "HPA Configured", "weight": 30, "critical": False},
                {"id": "EKS-PERF-02", "feature": "vertical_pod_autoscaler", "title": "VPA for Right-sizing", "weight": 25, "critical": False},
                {"id": "EKS-PERF-03", "feature": "resource_quotas", "title": "Resource Quotas", "weight": 20, "critical": False},
                {"id": "EKS-PERF-04", "feature": "limit_ranges", "title": "Limit Ranges", "weight": 25, "critical": False},
            ],
            WAFPillar.COST_OPTIMIZATION: [
                {"id": "EKS-COST-01", "feature": "use_spot", "title": "Spot Instance Usage", "weight": 25, "critical": False},
                {"id": "EKS-COST-02", "feature": "use_karpenter", "title": "Karpenter for Scaling", "weight": 25, "critical": False},
                {"id": "EKS-COST-03", "feature": "vertical_pod_autoscaler", "title": "VPA Right-sizing", "weight": 20, "critical": False},
                {"id": "EKS-COST-04", "feature": "resource_quotas", "title": "Resource Quotas", "weight": 15, "critical": False},
                {"id": "EKS-COST-05", "feature": "use_graviton", "title": "Graviton Processors", "weight": 15, "critical": False},
            ],
            WAFPillar.SUSTAINABILITY: [
                {"id": "EKS-SUS-01", "feature": "use_graviton", "title": "Graviton Nodes", "weight": 35, "critical": False},
                {"id": "EKS-SUS-02", "feature": "use_karpenter", "title": "Efficient Scaling", "weight": 25, "critical": False},
                {"id": "EKS-SUS-03", "feature": "vertical_pod_autoscaler", "title": "Right-sizing Workloads", "weight": 25, "critical": False},
                {"id": "EKS-SUS-04", "feature": "use_spot", "title": "Spot Instance Usage", "weight": 15, "critical": False},
            ],
        }
    
    def assess(self, config: EKSClusterConfig) -> Tuple[Dict[WAFPillar, EKSWAFScore], List[EKSFinding]]:
        """Assess EKS cluster against all WAF pillars"""
        scores = {}
        findings = []
        
        for pillar in WAFPillar:
            pillar_score, pillar_findings = self._assess_pillar(pillar, config)
            scores[pillar] = pillar_score
            findings.extend(pillar_findings)
        
        return scores, findings
    
    def _assess_pillar(self, pillar: WAFPillar, config: EKSClusterConfig) -> Tuple[EKSWAFScore, List[EKSFinding]]:
        """Assess a single pillar"""
        requirements = self.pillar_requirements.get(pillar, [])
        
        total_weight = sum(r.get('weight', 0) for r in requirements)
        achieved_weight = 0
        features_enabled = []
        features_missing = []
        findings = []
        
        for req in requirements:
            feature = req.get('feature', '')
            feature_enabled = getattr(config, feature, False)
            
            # Special handling for non-boolean features
            if feature == 'gitops':
                feature_enabled = config.gitops != 'none'
            elif feature == 'service_mesh':
                feature_enabled = config.service_mesh != 'none'
            
            if feature_enabled:
                achieved_weight += req.get('weight', 0)
                features_enabled.append(req['title'])
            else:
                features_missing.append(req['title'])
                
                # Generate finding
                severity = "CRITICAL" if req.get('critical', False) else "HIGH" if req.get('weight', 0) >= 20 else "MEDIUM"
                
                findings.append(EKSFinding(
                    id=req['id'],
                    category="EKS Configuration",
                    pillar=pillar,
                    severity=severity,
                    title=f"Missing: {req['title']}",
                    description=f"EKS cluster is missing {req['title']} capability",
                    recommendation=f"Enable {feature} for improved {pillar.value}",
                    compliance_impact=EKS_FEATURE_COMPLIANCE_MAP.get(feature, []),
                    auto_remediatable=True
                ))
        
        score = int((achieved_weight / total_weight * 100)) if total_weight > 0 else 0
        
        return EKSWAFScore(
            pillar=pillar,
            score=score,
            findings_count=len(findings),
            features_enabled=features_enabled,
            features_missing=features_missing
        ), findings


# ============================================================================
# EKS COMPLIANCE ASSESSOR
# ============================================================================

class EKSComplianceAssessor:
    """Assesses EKS configurations against compliance frameworks"""
    
    def __init__(self):
        self.framework_controls = self._load_framework_controls()
    
    def _load_framework_controls(self) -> Dict[ComplianceFramework, List[Dict]]:
        """Load compliance controls for EKS"""
        return {
            ComplianceFramework.CIS: [
                {"id": "CIS-EKS-1.1", "title": "Ensure audit logging is enabled", "feature": "audit_logging", "critical": True},
                {"id": "CIS-EKS-1.2", "title": "Ensure secrets encryption is enabled", "feature": "secrets_encryption", "critical": True},
                {"id": "CIS-EKS-2.1", "title": "Ensure private endpoint is enabled", "feature": "private_endpoint", "critical": False},
                {"id": "CIS-EKS-3.1", "title": "Ensure network policies are configured", "feature": "network_policies", "critical": True},
                {"id": "CIS-EKS-4.1", "title": "Ensure IRSA is used", "feature": "irsa_enabled", "critical": True},
                {"id": "CIS-EKS-5.1", "title": "Ensure Pod Security Standards enforced", "feature": "pod_security_standards", "critical": True},
            ],
            ComplianceFramework.SOC2: [
                {"id": "SOC2-CC6.1", "title": "Access Control - IRSA", "feature": "irsa_enabled", "critical": True},
                {"id": "SOC2-CC6.7", "title": "Encryption - Secrets", "feature": "secrets_encryption", "critical": True},
                {"id": "SOC2-CC7.1", "title": "Monitoring - Logging", "feature": "audit_logging", "critical": True},
                {"id": "SOC2-CC7.2", "title": "Monitoring - Container Insights", "feature": "cloudwatch_insights", "critical": False},
                {"id": "SOC2-A1.2", "title": "Availability - Multi-AZ", "feature": "multi_az", "critical": True},
            ],
            ComplianceFramework.HIPAA: [
                {"id": "HIPAA-164.312(a)", "title": "Access Control - IRSA", "feature": "irsa_enabled", "critical": True},
                {"id": "HIPAA-164.312(a)(2)(iv)", "title": "Encryption - Secrets", "feature": "secrets_encryption", "critical": True},
                {"id": "HIPAA-164.312(b)", "title": "Audit Logging", "feature": "audit_logging", "critical": True},
                {"id": "HIPAA-164.312(e)", "title": "Network Security", "feature": "network_policies", "critical": True},
                {"id": "HIPAA-164.308(a)(7)", "title": "Availability - Multi-AZ", "feature": "multi_az", "critical": True},
            ],
            ComplianceFramework.PCI_DSS: [
                {"id": "PCI-1.3", "title": "Network Segmentation", "feature": "network_policies", "critical": True},
                {"id": "PCI-3.4", "title": "Secrets Encryption", "feature": "secrets_encryption", "critical": True},
                {"id": "PCI-7.1", "title": "Access Control - IRSA", "feature": "irsa_enabled", "critical": True},
                {"id": "PCI-10.2", "title": "Audit Logging", "feature": "audit_logging", "critical": True},
                {"id": "PCI-11.4", "title": "Runtime Security", "feature": "runtime_security", "critical": False},
            ],
            ComplianceFramework.ISO_27001: [
                {"id": "ISO-A.9.1", "title": "Access Control", "feature": "irsa_enabled", "critical": True},
                {"id": "ISO-A.10.1", "title": "Cryptography", "feature": "secrets_encryption", "critical": True},
                {"id": "ISO-A.12.4", "title": "Logging", "feature": "audit_logging", "critical": True},
                {"id": "ISO-A.13.1", "title": "Network Security", "feature": "network_policies", "critical": True},
                {"id": "ISO-A.17.1", "title": "Availability", "feature": "multi_az", "critical": True},
            ],
            ComplianceFramework.NIST: [
                {"id": "NIST-PR.AC", "title": "Access Control", "feature": "irsa_enabled", "critical": True},
                {"id": "NIST-PR.DS", "title": "Data Security", "feature": "secrets_encryption", "critical": True},
                {"id": "NIST-DE.CM", "title": "Monitoring", "feature": "cloudwatch_insights", "critical": False},
                {"id": "NIST-PR.IP", "title": "Network Protection", "feature": "network_policies", "critical": True},
            ],
            ComplianceFramework.GDPR: [
                {"id": "GDPR-Art.32", "title": "Security - Encryption", "feature": "secrets_encryption", "critical": True},
                {"id": "GDPR-Art.30", "title": "Records - Logging", "feature": "audit_logging", "critical": True},
                {"id": "GDPR-Art.25", "title": "Privacy by Design", "feature": "network_policies", "critical": False},
            ],
            ComplianceFramework.FEDRAMP: [
                {"id": "FEDRAMP-AC-2", "title": "Account Management", "feature": "irsa_enabled", "critical": True},
                {"id": "FEDRAMP-AU-2", "title": "Audit Events", "feature": "audit_logging", "critical": True},
                {"id": "FEDRAMP-SC-7", "title": "Boundary Protection", "feature": "network_policies", "critical": True},
                {"id": "FEDRAMP-SC-28", "title": "Protection at Rest", "feature": "secrets_encryption", "critical": True},
            ],
        }
    
    def assess(self, config: EKSClusterConfig, 
               frameworks: List[ComplianceFramework] = None) -> Dict[ComplianceFramework, EKSComplianceScore]:
        """Assess EKS against compliance frameworks"""
        
        if frameworks is None:
            frameworks = list(ComplianceFramework)
        
        scores = {}
        
        for framework in frameworks:
            controls = self.framework_controls.get(framework, [])
            
            passed = 0
            failed = 0
            critical_gaps = []
            
            for control in controls:
                feature = control.get('feature', '')
                feature_enabled = getattr(config, feature, False)
                
                if feature_enabled:
                    passed += 1
                else:
                    failed += 1
                    if control.get('critical', False):
                        critical_gaps.append(f"{control['id']}: {control['title']}")
            
            total = len(controls)
            score = int((passed / total * 100)) if total > 0 else 0
            
            scores[framework] = EKSComplianceScore(
                framework=framework,
                score=score,
                controls_passed=passed,
                controls_failed=failed,
                total_controls=total,
                critical_gaps=critical_gaps
            )
        
        return scores


# ============================================================================
# EKS AI LENS
# ============================================================================

class EKSAILens:
    """AI-powered EKS analysis and recommendations"""
    
    def __init__(self):
        self.ai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize AI client"""
        try:
            import os
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if hasattr(st, 'secrets'):
                api_key = api_key or st.secrets.get('ANTHROPIC_API_KEY')
            
            if api_key:
                from anthropic import Anthropic
                self.ai_client = Anthropic(api_key=api_key)
        except Exception:
            pass
    
    def analyze(self, config: EKSClusterConfig, 
                waf_scores: Dict[WAFPillar, EKSWAFScore],
                compliance_scores: Dict[ComplianceFramework, EKSComplianceScore]) -> List[str]:
        """Generate AI recommendations for EKS"""
        
        recommendations = []
        
        # Pattern-based recommendations
        recommendations.extend(self._pattern_recommendations(config, waf_scores))
        
        # AI-powered recommendations
        if self.ai_client:
            ai_recs = self._ai_recommendations(config, waf_scores, compliance_scores)
            if ai_recs:
                recommendations.extend(ai_recs)
        
        return recommendations
    
    def _pattern_recommendations(self, config: EKSClusterConfig,
                                 waf_scores: Dict[WAFPillar, EKSWAFScore]) -> List[str]:
        """Generate pattern-based EKS recommendations"""
        recs = []
        
        # Security recommendations
        security_score = waf_scores.get(WAFPillar.SECURITY, EKSWAFScore(pillar=WAFPillar.SECURITY, score=0))
        if security_score.score < 70:
            if not config.secrets_encryption:
                recs.append("🔐 **Critical**: Enable secrets encryption with AWS KMS. Required for SOC2, HIPAA, PCI-DSS compliance.")
            if not config.pod_security_standards:
                recs.append("🛡️ **Critical**: Enable Pod Security Standards (PSS). Prevents privileged container execution.")
            if not config.network_policies:
                recs.append("🌐 **High**: Implement Network Policies for pod-to-pod traffic control. Required for PCI-DSS.")
            if not config.irsa_enabled:
                recs.append("🔑 **Critical**: Enable IRSA (IAM Roles for Service Accounts). Eliminates need for static credentials.")
        
        # Reliability recommendations
        reliability_score = waf_scores.get(WAFPillar.RELIABILITY, EKSWAFScore(pillar=WAFPillar.RELIABILITY, score=0))
        if reliability_score.score < 70:
            if not config.multi_az:
                recs.append("🌍 **Critical**: Enable Multi-AZ deployment for high availability.")
            if not config.cluster_autoscaler and not config.use_karpenter:
                recs.append("📈 **High**: Implement Karpenter or Cluster Autoscaler for automatic scaling.")
            if not config.pod_disruption_budgets:
                recs.append("⚡ **Medium**: Configure Pod Disruption Budgets for controlled rolling updates.")
        
        # Cost recommendations
        cost_score = waf_scores.get(WAFPillar.COST_OPTIMIZATION, EKSWAFScore(pillar=WAFPillar.COST_OPTIMIZATION, score=0))
        if cost_score.score < 70:
            if not config.use_spot:
                recs.append("💰 **Medium**: Use Spot instances for fault-tolerant workloads. Up to 90% cost savings.")
            if not config.use_karpenter:
                recs.append("💵 **Medium**: Migrate to Karpenter for intelligent node provisioning and cost optimization.")
            if not config.use_graviton:
                recs.append("🌱 **Medium**: Use Graviton-based nodes for better price-performance.")
        
        # Operational Excellence recommendations
        ops_score = waf_scores.get(WAFPillar.OPERATIONAL_EXCELLENCE, EKSWAFScore(pillar=WAFPillar.OPERATIONAL_EXCELLENCE, score=0))
        if ops_score.score < 70:
            if not config.cloudwatch_insights:
                recs.append("📊 **High**: Enable CloudWatch Container Insights for monitoring and observability.")
            if config.gitops == 'none':
                recs.append("🔄 **Medium**: Implement GitOps with ArgoCD or Flux for declarative deployments.")
            if not config.fluentbit:
                recs.append("📝 **Medium**: Deploy Fluent Bit for centralized logging.")
        
        return recs
    
    def _ai_recommendations(self, config: EKSClusterConfig,
                           waf_scores: Dict[WAFPillar, EKSWAFScore],
                           compliance_scores: Dict[ComplianceFramework, EKSComplianceScore]) -> List[str]:
        """Generate AI-powered recommendations"""
        
        prompt = f"""Analyze this EKS cluster configuration and provide 3-5 specific recommendations:

EKS Configuration:
- Kubernetes Version: {config.version}
- Multi-AZ: {config.multi_az}
- Secrets Encryption: {config.secrets_encryption}
- Network Policies: {config.network_policies}
- IRSA: {config.irsa_enabled}
- Karpenter: {config.use_karpenter}
- Spot Instances: {config.use_spot}
- GitOps: {config.gitops}

WAF Scores:
{json.dumps({p.value: s.score for p, s in waf_scores.items()}, indent=2)}

Compliance Scores:
{json.dumps({f.value: s.score for f, s in compliance_scores.items()}, indent=2)}

Provide recommendations in this format:
- [PRIORITY] **Category**: Specific recommendation

Focus on Kubernetes best practices, security hardening, and operational efficiency."""

        try:
            response = self.ai_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = response.content[0].text
            recs = []
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    recs.append(line[2:])
            
            return recs[:5]
        except Exception:
            return []


# ============================================================================
# MAIN INTEGRATED MODULE
# ============================================================================

class EKSModernizationIntegrated:
    """Main EKS Modernization Hub with full integration"""
    
    def __init__(self):
        self.waf_assessor = EKSWAFAssessor()
        self.compliance_assessor = EKSComplianceAssessor()
        self.ai_lens = EKSAILens()
    
    @staticmethod
    def render():
        """Render the integrated EKS Modernization Hub"""
        
        st.markdown("# ☸️ EKS Modernization Hub")
        st.markdown("### Integrated with WAF, Compliance & AI Lens")
        
        # Initialize session state
        if 'eks_config' not in st.session_state:
            st.session_state.eks_config = EKSClusterConfig()
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 Cluster Config",
            "📊 WAF Assessment",
            "🔒 Compliance",
            "🤖 AI Insights",
            "🚀 Karpenter",
            "📥 Export"
        ])
        
        with tab1:
            EKSModernizationIntegrated._render_config_tab()
        
        with tab2:
            EKSModernizationIntegrated._render_waf_tab()
        
        with tab3:
            EKSModernizationIntegrated._render_compliance_tab()
        
        with tab4:
            EKSModernizationIntegrated._render_ai_tab()
        
        with tab5:
            EKSModernizationIntegrated._render_karpenter_tab()
        
        with tab6:
            EKSModernizationIntegrated._render_export_tab()
    
    @staticmethod
    def _render_config_tab():
        """Render cluster configuration tab"""
        
        st.markdown("### ⚙️ EKS Cluster Configuration")
        
        config = st.session_state.eks_config
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Basic Configuration")
            config.name = st.text_input("Cluster Name", value=config.name)
            config.version = st.selectbox(
                "Kubernetes Version",
                options=["1.29", "1.28", "1.27", "1.26"],
                index=0
            )
            config.region = st.selectbox(
                "Region",
                options=["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"],
                index=0
            )
            
            st.markdown("#### Node Configuration")
            config.managed_node_groups = st.checkbox("Use Managed Node Groups", value=config.managed_node_groups)
            config.use_karpenter = st.checkbox("Use Karpenter", value=config.use_karpenter)
            config.use_spot = st.checkbox("Use Spot Instances", value=config.use_spot)
            config.use_graviton = st.checkbox("Use Graviton (ARM64)", value=config.use_graviton)
        
        with col2:
            st.markdown("#### Security Configuration")
            config.secrets_encryption = st.checkbox("🔐 Secrets Encryption (KMS)", value=config.secrets_encryption)
            config.pod_security_standards = st.checkbox("🛡️ Pod Security Standards", value=config.pod_security_standards)
            config.network_policies = st.checkbox("🌐 Network Policies", value=config.network_policies)
            config.private_endpoint = st.checkbox("🔒 Private API Endpoint", value=config.private_endpoint)
            config.irsa_enabled = st.checkbox("🔑 IAM Roles for Service Accounts", value=config.irsa_enabled)
            config.audit_logging = st.checkbox("📝 Control Plane Audit Logging", value=config.audit_logging)
            config.image_scanning = st.checkbox("🔍 Container Image Scanning", value=config.image_scanning)
            config.runtime_security = st.checkbox("⚠️ Runtime Security (Falco)", value=config.runtime_security)
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Observability")
            config.cloudwatch_insights = st.checkbox("📊 CloudWatch Container Insights", value=config.cloudwatch_insights)
            config.prometheus = st.checkbox("📈 Prometheus", value=config.prometheus)
            config.grafana = st.checkbox("📉 Grafana", value=config.grafana)
            config.fluentbit = st.checkbox("📝 Fluent Bit Logging", value=config.fluentbit)
        
        with col4:
            st.markdown("#### Operations & Scaling")
            config.gitops = st.selectbox("GitOps Tool", options=["none", "argocd", "flux"], index=0)
            config.cluster_autoscaler = st.checkbox("Cluster Autoscaler", value=config.cluster_autoscaler)
            config.horizontal_pod_autoscaler = st.checkbox("Horizontal Pod Autoscaler", value=config.horizontal_pod_autoscaler)
            config.vertical_pod_autoscaler = st.checkbox("Vertical Pod Autoscaler", value=config.vertical_pod_autoscaler)
            config.pod_disruption_budgets = st.checkbox("Pod Disruption Budgets", value=config.pod_disruption_budgets)
        
        st.markdown("---")
        st.markdown("#### Reliability & Cost")
        
        col5, col6 = st.columns(2)
        with col5:
            config.multi_az = st.checkbox("🌍 Multi-AZ Deployment", value=config.multi_az)
            config.service_mesh = st.selectbox("Service Mesh", options=["none", "istio", "appmesh"], index=0)
        
        with col6:
            config.resource_quotas = st.checkbox("💰 Resource Quotas", value=config.resource_quotas)
            config.limit_ranges = st.checkbox("📏 Limit Ranges", value=config.limit_ranges)
        
        st.session_state.eks_config = config
        
        # Quick score preview
        if st.button("🔄 Calculate Assessment", use_container_width=True, key="eks_calc_assessment_btn"):
            hub = EKSModernizationIntegrated()
            waf_scores, findings = hub.waf_assessor.assess(config)
            st.session_state.eks_waf_scores = waf_scores
            st.session_state.eks_findings = findings
            
            st.markdown("#### Quick WAF Score Preview")
            cols = st.columns(6)
            for idx, pillar in enumerate(WAFPillar):
                score = waf_scores.get(pillar, EKSWAFScore(pillar=pillar, score=0))
                pillar_config = PILLAR_CONFIG[pillar]
                color = "#4CAF50" if score.score >= 80 else "#FF9800" if score.score >= 60 else "#F44336"
                
                with cols[idx]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px; 
                                border-left: 4px solid {pillar_config['color']};">
                        <div style="font-size: 20px;">{pillar_config['icon']}</div>
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{score.score}</div>
                        <div style="font-size: 9px; color: #666;">{pillar.value[:12]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    @staticmethod
    def _render_waf_tab():
        """Render WAF assessment tab"""
        
        st.markdown("### 📊 Well-Architected Framework Assessment")
        
        config = st.session_state.eks_config
        hub = EKSModernizationIntegrated()
        waf_scores, findings = hub.waf_assessor.assess(config)
        
        st.session_state.eks_waf_scores = waf_scores
        st.session_state.eks_findings = findings
        
        # Overall score
        overall = sum(s.score * PILLAR_CONFIG[p]['weight'] for p, s in waf_scores.items())
        
        # Security posture
        if overall >= 80:
            posture = "SECURE"
            posture_color = "#4CAF50"
        elif overall >= 60:
            posture = "MEDIUM"
            posture_color = "#FF9800"
        else:
            posture = "HIGH RISK"
            posture_color = "#F44336"
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #1a237e 0%, #4a148c 100%); 
                        border-radius: 15px; color: white;">
                <h2 style="margin: 0;">EKS WAF Score</h2>
                <h1 style="font-size: 72px; margin: 10px 0;">{overall:.0f}</h1>
                <span style="background: {posture_color}; padding: 5px 15px; border-radius: 20px;">
                    {posture}
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📈 Pillar Scores")
        
        cols = st.columns(6)
        for idx, pillar in enumerate(WAFPillar):
            score = waf_scores.get(pillar, EKSWAFScore(pillar=pillar, score=0))
            pillar_config = PILLAR_CONFIG[pillar]
            color = "#4CAF50" if score.score >= 80 else "#FF9800" if score.score >= 60 else "#F44336"
            
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: white; border-radius: 10px; 
                            border: 2px solid {pillar_config['color']}; margin-bottom: 10px;">
                    <div style="font-size: 28px;">{pillar_config['icon']}</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{score.score}</div>
                    <div style="font-size: 11px; color: #666; font-weight: bold;">{pillar.value}</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Details"):
                    st.markdown("**Enabled:**")
                    for f in score.features_enabled:
                        st.markdown(f"✅ {f}")
                    st.markdown("**Missing:**")
                    for f in score.features_missing:
                        st.markdown(f"❌ {f}")
        
        # Findings
        st.markdown("---")
        st.markdown("### 🔍 Security Findings")
        
        critical = [f for f in findings if f.severity == "CRITICAL"]
        high = [f for f in findings if f.severity == "HIGH"]
        medium = [f for f in findings if f.severity == "MEDIUM"]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Findings", len(findings))
        col2.metric("🔴 Critical", len(critical))
        col3.metric("🟠 High", len(high))
        col4.metric("🟡 Medium", len(medium))
        
        for finding in findings:
            severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(finding.severity, "⚪")
            
            with st.expander(f"{severity_icon} [{finding.pillar.value}] {finding.title}"):
                st.markdown(f"**Description:** {finding.description}")
                st.markdown(f"**Recommendation:** {finding.recommendation}")
                if finding.compliance_impact:
                    st.warning(f"⚠️ Compliance Impact: {', '.join([f.value for f in finding.compliance_impact])}")
    
    @staticmethod
    def _render_compliance_tab():
        """Render compliance assessment tab"""
        
        st.markdown("### 🔒 Compliance Framework Assessment")
        
        config = st.session_state.eks_config
        hub = EKSModernizationIntegrated()
        compliance_scores = hub.compliance_assessor.assess(config)
        
        st.session_state.eks_compliance_scores = compliance_scores
        
        # Framework cards
        st.markdown("### 📋 Compliance Status by Framework")
        
        cols = st.columns(4)
        for idx, (framework, score) in enumerate(compliance_scores.items()):
            color = "#4CAF50" if score.score >= 80 else "#FF9800" if score.score >= 60 else "#F44336"
            status = "✅" if score.score >= 80 else "⚠️" if score.score >= 60 else "❌"
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div style="padding: 15px; background: white; border-radius: 10px; 
                            border-left: 4px solid {color}; margin-bottom: 15px; min-height: 140px;">
                    <h4 style="margin: 0;">{status} {framework.value}</h4>
                    <h2 style="color: {color}; margin: 10px 0;">{score.score}%</h2>
                    <small>
                        ✅ {score.controls_passed} passed<br>
                        ❌ {score.controls_failed} failed
                    </small>
                </div>
                """, unsafe_allow_html=True)
        
        # Critical gaps
        st.markdown("---")
        st.markdown("### 🚨 Critical Compliance Gaps")
        
        all_gaps = []
        for framework, score in compliance_scores.items():
            for gap in score.critical_gaps:
                all_gaps.append({"framework": framework.value, "gap": gap})
        
        if all_gaps:
            for gap in all_gaps:
                st.error(f"**{gap['framework']}**: {gap['gap']}")
        else:
            st.success("✅ No critical compliance gaps!")
    
    @staticmethod
    def _render_ai_tab():
        """Render AI insights tab"""
        
        st.markdown("### 🤖 AI-Powered EKS Insights")
        
        config = st.session_state.eks_config
        waf_scores = st.session_state.get('eks_waf_scores', {})
        compliance_scores = st.session_state.get('eks_compliance_scores', {})
        
        if not waf_scores:
            hub = EKSModernizationIntegrated()
            waf_scores, _ = hub.waf_assessor.assess(config)
            compliance_scores = hub.compliance_assessor.assess(config)
        
        hub = EKSModernizationIntegrated()
        
        with st.spinner("🤖 Analyzing EKS configuration with AI..."):
            recommendations = hub.ai_lens.analyze(config, waf_scores, compliance_scores)
        
        if recommendations:
            st.markdown("### 💡 AI Recommendations")
            
            for idx, rec in enumerate(recommendations, 1):
                if "Critical" in rec or "CRITICAL" in rec:
                    st.error(f"**{idx}.** {rec}")
                elif "High" in rec or "HIGH" in rec:
                    st.warning(f"**{idx}.** {rec}")
                else:
                    st.info(f"**{idx}.** {rec}")
        
        # Quick improvements
        st.markdown("---")
        st.markdown("### 🎯 Quick Security Hardening")
        
        hardening_items = [
            ("Secrets Encryption", config.secrets_encryption, "secrets_encryption"),
            ("Pod Security Standards", config.pod_security_standards, "pod_security_standards"),
            ("Network Policies", config.network_policies, "network_policies"),
            ("IRSA", config.irsa_enabled, "irsa_enabled"),
            ("Private Endpoint", config.private_endpoint, "private_endpoint"),
        ]
        
        for name, enabled, feature in hardening_items:
            if not enabled:
                st.markdown(f"""
                <div style="padding: 10px; background: #fff3cd; border-radius: 5px; margin-bottom: 10px;">
                    ⚠️ <b>{name}</b> is not enabled. Enable for better security posture.
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def _render_karpenter_tab():
        """Render Karpenter configuration tab"""
        
        st.markdown("### 🚀 Karpenter Configuration")
        
        config = st.session_state.eks_config
        
        if not config.use_karpenter:
            st.warning("⚠️ Karpenter is not enabled. Enable it in the Cluster Config tab for intelligent node provisioning.")
            
            st.markdown("### Why Karpenter?")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                #### 💰 Cost Savings
                - Up to 60% cost reduction
                - Intelligent Spot usage
                - Automatic consolidation
                """)
            
            with col2:
                st.markdown("""
                #### ⚡ Performance
                - Fast node provisioning
                - Right-sized instances
                - Bin-packing optimization
                """)
            
            with col3:
                st.markdown("""
                #### 🔄 Simplicity
                - No node groups to manage
                - Declarative configuration
                - Kubernetes-native
                """)
            
            return
        
        st.success("✅ Karpenter is enabled!")
        
        # Generate Karpenter configs
        st.markdown("### 📄 NodePool Configuration")
        
        nodepool_yaml = f"""apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"{', "arm64"' if config.use_graviton else ''}]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"{', "spot"' if config.use_spot else ''}]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-generation
          operator: Gt
          values: ["5"]
      nodeClassRef:
        name: default
  limits:
    cpu: 1000
    memory: 1000Gi
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s
"""
        
        st.code(nodepool_yaml, language="yaml")
        
        st.download_button(
            "📥 Download NodePool YAML",
            data=nodepool_yaml,
            file_name="nodepool.yaml",
            mime="text/yaml",
            key="eks_karpenter_nodepool_yaml_btn"
        )
        
        st.markdown("### 📄 EC2NodeClass Configuration")
        
        ec2nodeclass_yaml = f"""apiVersion: karpenter.k8s.aws/v1beta1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiFamily: AL2
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "{config.name}"
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "{config.name}"
  role: "KarpenterNodeRole-{config.name}"
  blockDeviceMappings:
    - deviceName: /dev/xvda
      ebs:
        volumeSize: 100Gi
        volumeType: gp3
        encrypted: true
        deleteOnTermination: true
  metadataOptions:
    httpEndpoint: enabled
    httpProtocolIPv6: disabled
    httpPutResponseHopLimit: 2
    httpTokens: required  # IMDSv2
"""
        
        st.code(ec2nodeclass_yaml, language="yaml")
        
        st.download_button(
            "📥 Download EC2NodeClass YAML",
            data=ec2nodeclass_yaml,
            file_name="ec2nodeclass.yaml",
            mime="text/yaml",
            key="eks_karpenter_ec2nodeclass_yaml_btn"
        )
    
    @staticmethod
    def _render_export_tab():
        """Render export tab"""
        
        st.markdown("### 📥 Export EKS Assessment")
        
        config = st.session_state.eks_config
        waf_scores = st.session_state.get('eks_waf_scores', {})
        compliance_scores = st.session_state.get('eks_compliance_scores', {})
        findings = st.session_state.get('eks_findings', [])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 📋 JSON Export")
            
            export_data = {
                "cluster": {
                    "name": config.name,
                    "version": config.version,
                    "region": config.region,
                },
                "features": {
                    "security": {
                        "secrets_encryption": config.secrets_encryption,
                        "pod_security_standards": config.pod_security_standards,
                        "network_policies": config.network_policies,
                        "irsa_enabled": config.irsa_enabled,
                    },
                    "operations": {
                        "karpenter": config.use_karpenter,
                        "gitops": config.gitops,
                        "monitoring": config.cloudwatch_insights,
                    }
                },
                "waf_assessment": {
                    "overall_score": sum(s.score * PILLAR_CONFIG[p]['weight'] for p, s in waf_scores.items()) if waf_scores else 0,
                    "pillar_scores": {p.value: s.score for p, s in waf_scores.items()} if waf_scores else {},
                },
                "compliance_assessment": {
                    f.value: {"score": s.score, "gaps": s.critical_gaps}
                    for f, s in compliance_scores.items()
                } if compliance_scores else {},
                "generated_at": datetime.now().isoformat()
            }
            
            st.download_button(
                "📥 Download JSON",
                data=json.dumps(export_data, indent=2, default=str),
                file_name="eks_assessment.json",
                mime="application/json",
                use_container_width=True,
                key="eks_export_json_btn"
            )
        
        with col2:
            st.markdown("#### 🔍 Findings CSV")
            
            if findings:
                import pandas as pd
                findings_data = []
                for f in findings:
                    findings_data.append({
                        "ID": f.id,
                        "Pillar": f.pillar.value,
                        "Severity": f.severity,
                        "Title": f.title,
                        "Recommendation": f.recommendation,
                        "Compliance": ", ".join([c.value for c in f.compliance_impact])
                    })
                
                df = pd.DataFrame(findings_data)
                st.download_button(
                    "📥 Download Findings",
                    data=df.to_csv(index=False),
                    file_name="eks_findings.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="eks_export_findings_btn"
                )
            else:
                st.info("Run assessment first")
        
        with col3:
            st.markdown("#### 🔗 WAF Integration")
            
            if st.button("📤 Send to WAF Review", use_container_width=True, key="eks_send_waf_btn"):
                waf_findings = []
                for f in findings:
                    waf_findings.append({
                        'id': f.id,
                        'title': f.title,
                        'description': f.description,
                        'severity': f.severity,
                        'service': 'EKS',
                        'resource': config.name,
                        'account_id': 'eks-cluster',
                        'region': config.region,
                        'pillar': f.pillar.value
                    })
                
                st.session_state['eks_findings_for_waf'] = waf_findings
                st.success(f"✅ Sent {len(waf_findings)} findings to WAF Review!")


# ============================================================================
# ENTRY POINT
# ============================================================================

def render_eks_modernization_integrated():
    """Main entry point for integrated EKS Modernization Hub"""
    EKSModernizationIntegrated.render()


if __name__ == "__main__":
    st.set_page_config(page_title="EKS Modernization - Integrated", layout="wide")
    render_eks_modernization_integrated()