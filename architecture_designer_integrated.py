"""
Architecture Designer - INTEGRATED with WAF, Compliance & AI Lens
=================================================================
Problem-driven architecture design tool fully integrated with:
- All 6 AWS Well-Architected Framework Pillars
- 8 Compliance Frameworks (SOC2, HIPAA, PCI-DSS, ISO 27001, CIS, GDPR, NIST, FedRAMP)
- AI Lens for intelligent recommendations and analysis

Version: 6.0.0 (WAF-Compliance-AI Integrated)
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib

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
    CIS = "CIS AWS Benchmarks"
    GDPR = "GDPR"
    NIST = "NIST CSF"
    FEDRAMP = "FedRAMP"

class ArchitectureUseCase(Enum):
    """Architecture design use cases"""
    GREENFIELD = "greenfield"
    MIGRATION = "migration"
    COST_OPTIMIZATION = "cost_optimization"
    SECURITY_HARDENING = "security_hardening"
    MULTI_REGION = "multi_region"
    PERFORMANCE = "performance"

# Pillar configuration
PILLAR_CONFIG = {
    WAFPillar.OPERATIONAL_EXCELLENCE: {"icon": "⚙️", "color": "#FF6B6B", "weight": 0.15},
    WAFPillar.SECURITY: {"icon": "🔒", "color": "#4ECDC4", "weight": 0.25},
    WAFPillar.RELIABILITY: {"icon": "🛡️", "color": "#45B7D1", "weight": 0.20},
    WAFPillar.PERFORMANCE_EFFICIENCY: {"icon": "⚡", "color": "#96CEB4", "weight": 0.15},
    WAFPillar.COST_OPTIMIZATION: {"icon": "💰", "color": "#FFEAA7", "weight": 0.15},
    WAFPillar.SUSTAINABILITY: {"icon": "🌱", "color": "#81C784", "weight": 0.10}
}

# Service to WAF Pillar mapping
SERVICE_PILLAR_MAP = {
    # Security
    'waf': [WAFPillar.SECURITY],
    'shield': [WAFPillar.SECURITY],
    'guardduty': [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    'kms': [WAFPillar.SECURITY],
    'secrets_manager': [WAFPillar.SECURITY],
    'cognito': [WAFPillar.SECURITY],
    'iam': [WAFPillar.SECURITY],
    'macie': [WAFPillar.SECURITY],
    'inspector': [WAFPillar.SECURITY],
    'security_hub': [WAFPillar.SECURITY, WAFPillar.OPERATIONAL_EXCELLENCE],
    
    # Reliability
    'rds': [WAFPillar.RELIABILITY],
    'aurora': [WAFPillar.RELIABILITY],
    'dynamodb': [WAFPillar.RELIABILITY, WAFPillar.PERFORMANCE_EFFICIENCY],
    'elasticache': [WAFPillar.RELIABILITY, WAFPillar.PERFORMANCE_EFFICIENCY],
    'elb': [WAFPillar.RELIABILITY],
    'alb': [WAFPillar.RELIABILITY],
    'route53': [WAFPillar.RELIABILITY],
    'backup': [WAFPillar.RELIABILITY],
    'auto_scaling': [WAFPillar.RELIABILITY, WAFPillar.COST_OPTIMIZATION],
    
    # Performance
    'cloudfront': [WAFPillar.PERFORMANCE_EFFICIENCY],
    'global_accelerator': [WAFPillar.PERFORMANCE_EFFICIENCY],
    'api_gateway': [WAFPillar.PERFORMANCE_EFFICIENCY],
    
    # Operational Excellence
    'cloudwatch': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'cloudtrail': [WAFPillar.OPERATIONAL_EXCELLENCE, WAFPillar.SECURITY],
    'config': [WAFPillar.OPERATIONAL_EXCELLENCE, WAFPillar.SECURITY],
    'systems_manager': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'codepipeline': [WAFPillar.OPERATIONAL_EXCELLENCE],
    'codecommit': [WAFPillar.OPERATIONAL_EXCELLENCE],
    
    # Cost Optimization
    'lambda': [WAFPillar.COST_OPTIMIZATION, WAFPillar.SUSTAINABILITY],
    'fargate': [WAFPillar.COST_OPTIMIZATION],
    'spot_instances': [WAFPillar.COST_OPTIMIZATION],
    's3_intelligent_tiering': [WAFPillar.COST_OPTIMIZATION],
    
    # Sustainability
    'graviton': [WAFPillar.SUSTAINABILITY, WAFPillar.COST_OPTIMIZATION],
    'serverless': [WAFPillar.SUSTAINABILITY],
}

# Service to Compliance mapping
SERVICE_COMPLIANCE_MAP = {
    'kms': [ComplianceFramework.SOC2, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS, ComplianceFramework.ISO_27001],
    'cloudtrail': [ComplianceFramework.SOC2, ComplianceFramework.HIPAA, ComplianceFramework.PCI_DSS, ComplianceFramework.ISO_27001, ComplianceFramework.CIS],
    'guardduty': [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS, ComplianceFramework.NIST],
    'config': [ComplianceFramework.SOC2, ComplianceFramework.ISO_27001, ComplianceFramework.CIS],
    'waf': [ComplianceFramework.PCI_DSS, ComplianceFramework.NIST],
    'cognito': [ComplianceFramework.SOC2, ComplianceFramework.HIPAA],
    'secrets_manager': [ComplianceFramework.SOC2, ComplianceFramework.PCI_DSS],
    'macie': [ComplianceFramework.GDPR, ComplianceFramework.HIPAA],
    'security_hub': [ComplianceFramework.SOC2, ComplianceFramework.CIS, ComplianceFramework.NIST],
    'backup': [ComplianceFramework.HIPAA, ComplianceFramework.SOC2],
    'vpc': [ComplianceFramework.PCI_DSS, ComplianceFramework.CIS],
}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ArchitectureFinding:
    """Architecture design finding/gap"""
    id: str
    pillar: WAFPillar
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    description: str
    recommendation: str
    compliance_impact: List[ComplianceFramework] = field(default_factory=list)
    auto_remediatable: bool = False
    services_to_add: List[str] = field(default_factory=list)

@dataclass 
class WAFScore:
    """WAF Pillar score"""
    pillar: WAFPillar
    score: int  # 0-100
    max_score: int = 100
    findings_count: int = 0
    services_contributing: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

@dataclass
class ComplianceScore:
    """Compliance framework score"""
    framework: ComplianceFramework
    score: int  # 0-100
    requirements_met: int = 0
    requirements_partial: int = 0
    requirements_gap: int = 0
    total_requirements: int = 0
    gaps: List[str] = field(default_factory=list)

@dataclass
class ArchitectureAssessment:
    """Complete architecture assessment"""
    id: str
    timestamp: datetime
    architecture_name: str
    use_case: ArchitectureUseCase
    services: List[str]
    config: Dict
    waf_scores: Dict[WAFPillar, WAFScore]
    compliance_scores: Dict[ComplianceFramework, ComplianceScore]
    findings: List[ArchitectureFinding]
    overall_waf_score: int
    overall_compliance_score: int
    ai_recommendations: List[str]

# ============================================================================
# WAF ASSESSMENT ENGINE
# ============================================================================

class ArchitectureWAFAssessor:
    """Assesses architecture designs against WAF pillars"""
    
    def __init__(self):
        self.pillar_requirements = self._load_pillar_requirements()
    
    def _load_pillar_requirements(self) -> Dict[WAFPillar, List[Dict]]:
        """Load WAF pillar requirements for architecture assessment"""
        return {
            WAFPillar.OPERATIONAL_EXCELLENCE: [
                {"id": "OPS-01", "title": "Monitoring & Observability", "required_services": ["cloudwatch"], "weight": 20},
                {"id": "OPS-02", "title": "Audit Logging", "required_services": ["cloudtrail"], "weight": 20},
                {"id": "OPS-03", "title": "Configuration Management", "required_services": ["config", "systems_manager"], "weight": 15},
                {"id": "OPS-04", "title": "CI/CD Pipeline", "required_services": ["codepipeline", "codecommit"], "weight": 15},
                {"id": "OPS-05", "title": "Infrastructure as Code", "required_services": ["cloudformation"], "weight": 15},
                {"id": "OPS-06", "title": "Incident Response", "required_services": ["sns", "lambda"], "weight": 15},
            ],
            WAFPillar.SECURITY: [
                {"id": "SEC-01", "title": "Encryption at Rest", "required_services": ["kms"], "weight": 20},
                {"id": "SEC-02", "title": "Identity Management", "required_services": ["cognito", "iam"], "weight": 20},
                {"id": "SEC-03", "title": "Network Security", "required_services": ["waf", "shield"], "weight": 15},
                {"id": "SEC-04", "title": "Threat Detection", "required_services": ["guardduty"], "weight": 15},
                {"id": "SEC-05", "title": "Secrets Management", "required_services": ["secrets_manager"], "weight": 15},
                {"id": "SEC-06", "title": "Security Monitoring", "required_services": ["security_hub", "inspector"], "weight": 15},
            ],
            WAFPillar.RELIABILITY: [
                {"id": "REL-01", "title": "Multi-AZ Deployment", "required_config": ["multi_az"], "weight": 25},
                {"id": "REL-02", "title": "Auto Scaling", "required_services": ["auto_scaling"], "weight": 20},
                {"id": "REL-03", "title": "Load Balancing", "required_services": ["alb", "elb"], "weight": 20},
                {"id": "REL-04", "title": "Backup & Recovery", "required_services": ["backup"], "weight": 20},
                {"id": "REL-05", "title": "Health Checks", "required_services": ["route53"], "weight": 15},
            ],
            WAFPillar.PERFORMANCE_EFFICIENCY: [
                {"id": "PERF-01", "title": "Caching Strategy", "required_services": ["elasticache", "cloudfront"], "weight": 25},
                {"id": "PERF-02", "title": "CDN Distribution", "required_services": ["cloudfront"], "weight": 20},
                {"id": "PERF-03", "title": "Database Optimization", "required_services": ["aurora", "dynamodb"], "weight": 20},
                {"id": "PERF-04", "title": "API Optimization", "required_services": ["api_gateway"], "weight": 15},
                {"id": "PERF-05", "title": "Global Acceleration", "required_services": ["global_accelerator"], "weight": 20},
            ],
            WAFPillar.COST_OPTIMIZATION: [
                {"id": "COST-01", "title": "Right Sizing", "required_config": ["right_sizing"], "weight": 20},
                {"id": "COST-02", "title": "Serverless Adoption", "required_services": ["lambda", "fargate"], "weight": 20},
                {"id": "COST-03", "title": "Reserved Capacity", "required_config": ["reserved_instances"], "weight": 20},
                {"id": "COST-04", "title": "Spot Usage", "required_services": ["spot_instances"], "weight": 15},
                {"id": "COST-05", "title": "Storage Tiering", "required_services": ["s3_intelligent_tiering"], "weight": 15},
                {"id": "COST-06", "title": "Auto Scaling", "required_services": ["auto_scaling"], "weight": 10},
            ],
            WAFPillar.SUSTAINABILITY: [
                {"id": "SUS-01", "title": "Serverless Architecture", "required_services": ["lambda", "fargate"], "weight": 30},
                {"id": "SUS-02", "title": "Graviton Processors", "required_services": ["graviton"], "weight": 25},
                {"id": "SUS-03", "title": "Right Sizing", "required_config": ["right_sizing"], "weight": 20},
                {"id": "SUS-04", "title": "Auto Scaling", "required_services": ["auto_scaling"], "weight": 15},
                {"id": "SUS-05", "title": "Regional Efficiency", "required_config": ["efficient_region"], "weight": 10},
            ],
        }
    
    def assess(self, services: List[str], config: Dict) -> Tuple[Dict[WAFPillar, WAFScore], List[ArchitectureFinding]]:
        """Assess architecture against all WAF pillars"""
        scores = {}
        findings = []
        
        for pillar in WAFPillar:
            pillar_score, pillar_findings = self._assess_pillar(pillar, services, config)
            scores[pillar] = pillar_score
            findings.extend(pillar_findings)
        
        return scores, findings
    
    def _assess_pillar(self, pillar: WAFPillar, services: List[str], config: Dict) -> Tuple[WAFScore, List[ArchitectureFinding]]:
        """Assess a single pillar"""
        requirements = self.pillar_requirements.get(pillar, [])
        
        total_weight = sum(r.get('weight', 0) for r in requirements)
        achieved_weight = 0
        contributing_services = []
        findings = []
        suggestions = []
        
        for req in requirements:
            req_met = False
            
            # Check required services
            required_services = req.get('required_services', [])
            if required_services:
                services_lower = [s.lower().replace(' ', '_') for s in services]
                if any(rs in services_lower for rs in required_services):
                    req_met = True
                    contributing_services.extend([s for s in services if s.lower().replace(' ', '_') in required_services])
            
            # Check required config
            required_config = req.get('required_config', [])
            if required_config:
                if any(config.get(rc, False) for rc in required_config):
                    req_met = True
            
            if req_met:
                achieved_weight += req.get('weight', 0)
            else:
                # Generate finding
                severity = "HIGH" if req.get('weight', 0) >= 20 else "MEDIUM"
                findings.append(ArchitectureFinding(
                    id=f"ARCH-{req['id']}",
                    pillar=pillar,
                    severity=severity,
                    title=f"Missing: {req['title']}",
                    description=f"Architecture is missing {req['title']} capability",
                    recommendation=f"Add {', '.join(required_services or required_config)} to improve {pillar.value}",
                    services_to_add=required_services or [],
                    compliance_impact=self._get_compliance_impact(required_services)
                ))
                suggestions.append(f"Add {req['title']} using {', '.join(required_services or required_config)}")
        
        score = int((achieved_weight / total_weight * 100)) if total_weight > 0 else 0
        
        return WAFScore(
            pillar=pillar,
            score=score,
            findings_count=len(findings),
            services_contributing=list(set(contributing_services)),
            improvement_suggestions=suggestions
        ), findings
    
    def _get_compliance_impact(self, services: List[str]) -> List[ComplianceFramework]:
        """Get compliance frameworks impacted by missing services"""
        impacted = []
        for service in services:
            frameworks = SERVICE_COMPLIANCE_MAP.get(service, [])
            for f in frameworks:
                if f not in impacted:
                    impacted.append(f)
        return impacted


# ============================================================================
# COMPLIANCE ASSESSMENT ENGINE
# ============================================================================

class ArchitectureComplianceAssessor:
    """Assesses architecture designs against compliance frameworks"""
    
    def __init__(self):
        self.framework_requirements = self._load_framework_requirements()
    
    def _load_framework_requirements(self) -> Dict[ComplianceFramework, List[Dict]]:
        """Load compliance framework requirements"""
        return {
            ComplianceFramework.SOC2: [
                {"id": "CC6.1", "title": "Access Control", "required_services": ["cognito", "iam"], "category": "Security"},
                {"id": "CC6.6", "title": "Network Protection", "required_services": ["waf", "vpc"], "category": "Security"},
                {"id": "CC6.7", "title": "Encryption", "required_services": ["kms"], "category": "Security"},
                {"id": "CC7.1", "title": "Monitoring", "required_services": ["cloudwatch", "cloudtrail"], "category": "Operations"},
                {"id": "CC7.2", "title": "Incident Response", "required_services": ["guardduty", "security_hub"], "category": "Operations"},
                {"id": "CC8.1", "title": "Change Management", "required_services": ["config", "codepipeline"], "category": "Operations"},
            ],
            ComplianceFramework.HIPAA: [
                {"id": "164.312(a)", "title": "Access Control", "required_services": ["cognito", "iam"], "category": "Technical"},
                {"id": "164.312(a)(2)(iv)", "title": "Encryption", "required_services": ["kms"], "category": "Technical"},
                {"id": "164.312(b)", "title": "Audit Controls", "required_services": ["cloudtrail"], "category": "Technical"},
                {"id": "164.312(c)", "title": "Integrity", "required_services": ["backup"], "category": "Technical"},
                {"id": "164.312(d)", "title": "Authentication", "required_services": ["cognito"], "category": "Technical"},
                {"id": "164.312(e)", "title": "Transmission Security", "required_services": ["kms", "alb"], "category": "Technical"},
            ],
            ComplianceFramework.PCI_DSS: [
                {"id": "1.3", "title": "Firewall Config", "required_services": ["waf", "vpc"], "category": "Network"},
                {"id": "3.4", "title": "Data Encryption", "required_services": ["kms"], "category": "Data Protection"},
                {"id": "7.1", "title": "Access Control", "required_services": ["iam"], "category": "Access Control"},
                {"id": "8.3", "title": "MFA", "required_services": ["cognito"], "category": "Authentication"},
                {"id": "10.2", "title": "Audit Logging", "required_services": ["cloudtrail"], "category": "Monitoring"},
                {"id": "11.4", "title": "IDS/IPS", "required_services": ["guardduty"], "category": "Security Testing"},
            ],
            ComplianceFramework.ISO_27001: [
                {"id": "A.9.1", "title": "Access Control Policy", "required_services": ["iam"], "category": "Access Control"},
                {"id": "A.10.1", "title": "Cryptography", "required_services": ["kms"], "category": "Cryptography"},
                {"id": "A.12.4", "title": "Logging", "required_services": ["cloudwatch", "cloudtrail"], "category": "Operations"},
                {"id": "A.13.1", "title": "Network Security", "required_services": ["vpc", "waf"], "category": "Communications"},
                {"id": "A.14.2", "title": "Secure Development", "required_services": ["codepipeline"], "category": "Development"},
                {"id": "A.18.1", "title": "Compliance", "required_services": ["config", "security_hub"], "category": "Compliance"},
            ],
            ComplianceFramework.CIS: [
                {"id": "1.1", "title": "Root MFA", "required_services": ["iam"], "category": "Identity"},
                {"id": "2.1", "title": "CloudTrail", "required_services": ["cloudtrail"], "category": "Logging"},
                {"id": "3.1", "title": "S3 Encryption", "required_services": ["kms"], "category": "Data"},
                {"id": "4.1", "title": "Security Groups", "required_services": ["vpc"], "category": "Networking"},
                {"id": "5.1", "title": "Config Enabled", "required_services": ["config"], "category": "Monitoring"},
            ],
            ComplianceFramework.GDPR: [
                {"id": "Art.5", "title": "Data Protection", "required_services": ["kms", "macie"], "category": "Principles"},
                {"id": "Art.25", "title": "Privacy by Design", "required_services": ["kms", "vpc"], "category": "Design"},
                {"id": "Art.30", "title": "Records", "required_services": ["cloudtrail"], "category": "Documentation"},
                {"id": "Art.32", "title": "Security", "required_services": ["kms", "guardduty"], "category": "Security"},
                {"id": "Art.33", "title": "Breach Notification", "required_services": ["security_hub", "sns"], "category": "Incident"},
            ],
            ComplianceFramework.NIST: [
                {"id": "PR.AC", "title": "Access Control", "required_services": ["iam", "cognito"], "category": "Protect"},
                {"id": "PR.DS", "title": "Data Security", "required_services": ["kms"], "category": "Protect"},
                {"id": "DE.CM", "title": "Monitoring", "required_services": ["cloudwatch", "guardduty"], "category": "Detect"},
                {"id": "DE.AE", "title": "Anomaly Detection", "required_services": ["guardduty"], "category": "Detect"},
                {"id": "RS.RP", "title": "Response Planning", "required_services": ["sns", "lambda"], "category": "Respond"},
            ],
            ComplianceFramework.FEDRAMP: [
                {"id": "AC-2", "title": "Account Management", "required_services": ["iam"], "category": "Access Control"},
                {"id": "AU-2", "title": "Audit Events", "required_services": ["cloudtrail"], "category": "Audit"},
                {"id": "SC-7", "title": "Boundary Protection", "required_services": ["vpc", "waf"], "category": "System Protection"},
                {"id": "SC-28", "title": "Protection at Rest", "required_services": ["kms"], "category": "System Protection"},
                {"id": "SI-4", "title": "System Monitoring", "required_services": ["cloudwatch", "guardduty"], "category": "System Integrity"},
            ],
        }
    
    def assess(self, services: List[str], config: Dict, 
               frameworks: List[ComplianceFramework] = None) -> Dict[ComplianceFramework, ComplianceScore]:
        """Assess architecture against compliance frameworks"""
        
        if frameworks is None:
            frameworks = list(ComplianceFramework)
        
        scores = {}
        services_lower = [s.lower().replace(' ', '_') for s in services]
        
        for framework in frameworks:
            requirements = self.framework_requirements.get(framework, [])
            
            met = 0
            partial = 0
            gaps = []
            
            for req in requirements:
                required = req.get('required_services', [])
                matched = sum(1 for rs in required if rs in services_lower)
                
                if matched == len(required):
                    met += 1
                elif matched > 0:
                    partial += 1
                else:
                    gaps.append(f"{req['id']}: {req['title']}")
            
            total = len(requirements)
            score = int(((met * 100) + (partial * 50)) / max(total, 1))
            
            scores[framework] = ComplianceScore(
                framework=framework,
                score=min(100, score),
                requirements_met=met,
                requirements_partial=partial,
                requirements_gap=total - met - partial,
                total_requirements=total,
                gaps=gaps
            )
        
        return scores


# ============================================================================
# AI LENS ENGINE
# ============================================================================

class ArchitectureAILens:
    """AI-powered architecture analysis and recommendations"""
    
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
    
    def analyze_architecture(self, services: List[str], config: Dict, 
                            waf_scores: Dict[WAFPillar, WAFScore],
                            compliance_scores: Dict[ComplianceFramework, ComplianceScore]) -> List[str]:
        """Generate AI-powered recommendations"""
        
        recommendations = []
        
        # Pattern-based recommendations (always available)
        recommendations.extend(self._pattern_recommendations(services, config, waf_scores))
        
        # AI-powered recommendations (if available)
        if self.ai_client:
            ai_recs = self._ai_recommendations(services, config, waf_scores, compliance_scores)
            if ai_recs:
                recommendations.extend(ai_recs)
        
        return recommendations
    
    def _pattern_recommendations(self, services: List[str], config: Dict,
                                 waf_scores: Dict[WAFPillar, WAFScore]) -> List[str]:
        """Generate pattern-based recommendations"""
        recs = []
        services_lower = [s.lower().replace(' ', '_') for s in services]
        
        # Security patterns
        security_score = waf_scores.get(WAFPillar.SECURITY, WAFScore(pillar=WAFPillar.SECURITY, score=0))
        if security_score.score < 70:
            if 'kms' not in services_lower:
                recs.append("🔒 **Critical**: Add AWS KMS for encryption at rest. Required for SOC2, HIPAA, PCI-DSS compliance.")
            if 'guardduty' not in services_lower:
                recs.append("🔍 **High**: Enable GuardDuty for threat detection. Provides continuous security monitoring.")
            if 'waf' not in services_lower and config.get('public_facing', False):
                recs.append("🛡️ **High**: Add AWS WAF for web application firewall. Essential for public-facing applications.")
        
        # Reliability patterns
        reliability_score = waf_scores.get(WAFPillar.RELIABILITY, WAFScore(pillar=WAFPillar.RELIABILITY, score=0))
        if reliability_score.score < 70:
            if not config.get('multi_az', False):
                recs.append("🌐 **Critical**: Enable Multi-AZ deployment for high availability. Single-AZ is a significant risk.")
            if 'backup' not in services_lower:
                recs.append("💾 **High**: Implement AWS Backup for automated backup and recovery. Required for HIPAA.")
            if 'auto_scaling' not in services_lower:
                recs.append("📈 **Medium**: Add Auto Scaling for demand-based capacity management.")
        
        # Cost patterns
        cost_score = waf_scores.get(WAFPillar.COST_OPTIMIZATION, WAFScore(pillar=WAFPillar.COST_OPTIMIZATION, score=0))
        if cost_score.score < 70:
            if 'lambda' not in services_lower and config.get('workload_type') in ['api', 'event-driven']:
                recs.append("💰 **Medium**: Consider AWS Lambda for serverless cost optimization.")
            if not config.get('reserved_instances', False) and config.get('steady_state', False):
                recs.append("💵 **Medium**: Implement Reserved Instances or Savings Plans for steady-state workloads.")
        
        # Operational Excellence patterns
        ops_score = waf_scores.get(WAFPillar.OPERATIONAL_EXCELLENCE, WAFScore(pillar=WAFPillar.OPERATIONAL_EXCELLENCE, score=0))
        if ops_score.score < 70:
            if 'cloudwatch' not in services_lower:
                recs.append("📊 **High**: Add CloudWatch for monitoring and observability. Essential for operations.")
            if 'cloudtrail' not in services_lower:
                recs.append("📝 **High**: Enable CloudTrail for audit logging. Required for multiple compliance frameworks.")
        
        return recs
    
    def _ai_recommendations(self, services: List[str], config: Dict,
                           waf_scores: Dict[WAFPillar, WAFScore],
                           compliance_scores: Dict[ComplianceFramework, ComplianceScore]) -> List[str]:
        """Generate AI-powered recommendations using Claude"""
        
        prompt = f"""Analyze this AWS architecture and provide 3-5 specific, actionable recommendations:

Architecture:
- Services: {', '.join(services)}
- Configuration: {json.dumps(config, default=str)}

WAF Pillar Scores:
{json.dumps({p.value: s.score for p, s in waf_scores.items()}, indent=2)}

Compliance Status:
{json.dumps({f.value: s.score for f, s in compliance_scores.items()}, indent=2)}

Provide recommendations in this format:
- [PRIORITY] **Category**: Specific recommendation with AWS service names

Focus on:
1. Lowest scoring WAF pillars
2. Compliance gaps
3. Architecture anti-patterns
4. Cost optimization opportunities
5. Security hardening"""

        try:
            response = self.ai_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response into list
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

class ArchitectureDesignerIntegrated:
    """Main Architecture Designer with full WAF, Compliance, AI integration"""
    
    def __init__(self):
        self.waf_assessor = ArchitectureWAFAssessor()
        self.compliance_assessor = ArchitectureComplianceAssessor()
        self.ai_lens = ArchitectureAILens()
    
    @staticmethod
    def render():
        """Render the integrated Architecture Designer"""
        
        st.markdown("# 🏗️ Architecture Designer")
        st.markdown("### Integrated with WAF, Compliance & AI Lens")
        
        # Initialize session state
        if 'arch_services' not in st.session_state:
            st.session_state.arch_services = []
        if 'arch_config' not in st.session_state:
            st.session_state.arch_config = {}
        
        # Create tabs - EXPANDED with Upload & Diagram Generator
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "🎯 Design", 
            "📤 Upload & Analyze",
            "📐 Diagram Generator",
            "📊 WAF Assessment", 
            "🔒 Compliance", 
            "🤖 AI Insights",
            "📥 Export"
        ])
        
        with tab1:
            ArchitectureDesignerIntegrated._render_design_tab()
        
        with tab2:
            ArchitectureDesignerIntegrated._render_upload_tab()
        
        with tab3:
            ArchitectureDesignerIntegrated._render_diagram_tab()
        
        with tab4:
            ArchitectureDesignerIntegrated._render_waf_tab()
        
        with tab5:
            ArchitectureDesignerIntegrated._render_compliance_tab()
        
        with tab6:
            ArchitectureDesignerIntegrated._render_ai_tab()
        
        with tab7:
            ArchitectureDesignerIntegrated._render_export_tab()
    
    @staticmethod
    def _render_design_tab():
        """Render architecture design tab"""
        
        st.markdown("### 🎯 Architecture Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Use Case")
            use_case = st.selectbox(
                "Select Architecture Use Case",
                options=["Greenfield", "Migration", "Cost Optimization", "Security Hardening", "Multi-Region/DR", "Performance"],
                index=0
            )
            
            st.markdown("#### Workload Type")
            workload_type = st.selectbox(
                "Select Workload Type",
                options=["Web Application", "API Backend", "Data Analytics", "Machine Learning", "Event-Driven", "Batch Processing"],
                index=0
            )
            
            scale = st.select_slider(
                "Expected Scale",
                options=["Small", "Medium", "Large", "Enterprise", "Massive"],
                value="Medium"
            )
        
        with col2:
            st.markdown("#### Requirements")
            
            multi_az = st.checkbox("Multi-AZ Deployment", value=True)
            public_facing = st.checkbox("Public Facing", value=True)
            compliance_required = st.multiselect(
                "Compliance Requirements",
                options=[f.value for f in ComplianceFramework],
                default=["SOC 2 Type II"]
            )
            
            steady_state = st.checkbox("Steady-State Workload", value=False)
            reserved_instances = st.checkbox("Use Reserved Instances", value=False)
        
        # Update config
        st.session_state.arch_config = {
            'use_case': use_case,
            'workload_type': workload_type,
            'scale': scale.lower(),
            'multi_az': multi_az,
            'public_facing': public_facing,
            'compliance_required': compliance_required,
            'steady_state': steady_state,
            'reserved_instances': reserved_instances,
            'right_sizing': True
        }
        
        st.markdown("---")
        st.markdown("### 🔧 Select AWS Services")
        
        # Service categories
        service_categories = {
            "Compute": ["EC2", "Lambda", "ECS", "EKS", "Fargate", "Batch"],
            "Storage": ["S3", "EBS", "EFS", "FSx", "Glacier"],
            "Database": ["RDS", "Aurora", "DynamoDB", "ElastiCache", "DocumentDB", "Neptune"],
            "Networking": ["VPC", "ALB", "NLB", "CloudFront", "Route53", "API Gateway", "Global Accelerator"],
            "Security": ["KMS", "WAF", "Shield", "GuardDuty", "Cognito", "Secrets Manager", "Security Hub", "Inspector", "Macie"],
            "Operations": ["CloudWatch", "CloudTrail", "Config", "Systems Manager", "CodePipeline", "CodeCommit"],
            "Integration": ["SNS", "SQS", "EventBridge", "Step Functions"],
        }
        
        selected_services = []
        
        cols = st.columns(3)
        for idx, (category, services) in enumerate(service_categories.items()):
            with cols[idx % 3]:
                st.markdown(f"**{category}**")
                for service in services:
                    if st.checkbox(service, key=f"svc_{service}", value=service in ["VPC", "CloudWatch"]):
                        selected_services.append(service)
        
        st.session_state.arch_services = selected_services
        
        # Quick summary
        if selected_services:
            st.markdown("---")
            st.success(f"✅ Selected {len(selected_services)} services: {', '.join(selected_services[:10])}{'...' if len(selected_services) > 10 else ''}")
            
            # Quick WAF preview
            designer = ArchitectureDesignerIntegrated()
            waf_scores, _ = designer.waf_assessor.assess(selected_services, st.session_state.arch_config)
            
            st.markdown("#### Quick WAF Score Preview")
            cols = st.columns(6)
            for idx, pillar in enumerate(WAFPillar):
                score = waf_scores.get(pillar, WAFScore(pillar=pillar, score=0))
                config = PILLAR_CONFIG[pillar]
                color = "#4CAF50" if score.score >= 80 else "#FF9800" if score.score >= 60 else "#F44336"
                
                with cols[idx]:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 8px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid {config['color']};">
                        <div style="font-size: 20px;">{config['icon']}</div>
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{score.score}</div>
                        <div style="font-size: 9px; color: #666;">{pillar.value[:12]}</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    @staticmethod
    def _render_upload_tab():
        """Render Upload & Analyze tab for existing architecture diagrams"""
        
        st.markdown("### 📤 Upload & Analyze Existing Architecture")
        st.markdown("Upload your existing architecture diagrams or IaC files for automatic WAF assessment")
        
        # File upload section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Upload architecture files",
                type=['tf', 'tfvars', 'yaml', 'yml', 'json', 'py', 'ts', 'txt', 'md', 
                      'pdf', 'docx', 'pptx', 'vsdx', 'vsd', 'drawio', 'dio', 'xml'],
                accept_multiple_files=True,
                help="Supported: Terraform, CloudFormation, CDK, Visio, Draw.io, PDF, Word, PowerPoint",
                key="arch_upload_files"
            )
        
        with col2:
            st.markdown("**Supported Formats:**")
            st.markdown("""
            - 📜 **Terraform** (`.tf`, `.tfvars`)
            - ☁️ **CloudFormation** (`.yaml`, `.json`)
            - 🔧 **AWS CDK** (`.py`, `.ts`)
            - 📐 **Visio** (`.vsdx`, `.vsd`) ⭐
            - 🎨 **Draw.io** (`.drawio`, `.xml`) ⭐
            - 📄 **PDF** Documents
            - 📝 **Word** (`.docx`)
            - 📊 **PowerPoint** (`.pptx`)
            """)
        
        # Text input option
        st.markdown("---")
        st.markdown("### ✏️ Or Describe Your Architecture")
        
        text_input = st.text_area(
            "Paste your architecture code or description",
            height=150,
            placeholder="""Paste Terraform code, CloudFormation template, or describe your architecture:

Example:
"Our application uses CloudFront for CDN, ALB for load balancing, 
ECS Fargate for containers, Aurora PostgreSQL for database, 
and S3 for static assets. We have CloudWatch for monitoring."
""",
            key="arch_text_input"
        )
        
        # Analyze buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            analyze_files = st.button("🔍 Analyze Files", type="primary", disabled=not uploaded_files, key="arch_analyze_files_btn")
        
        with col2:
            analyze_text = st.button("🔍 Analyze Text", type="primary", disabled=not text_input, key="arch_analyze_text_btn")
        
        # Process analysis
        if analyze_files and uploaded_files:
            ArchitectureDesignerIntegrated._process_uploaded_files(uploaded_files)
        
        if analyze_text and text_input:
            ArchitectureDesignerIntegrated._process_text_input(text_input)
        
        # Show analysis results
        if 'arch_upload_results' in st.session_state:
            ArchitectureDesignerIntegrated._display_upload_results()
    
    @staticmethod
    def _process_uploaded_files(uploaded_files):
        """Process uploaded architecture files"""
        try:
            # Try to use the full analyzer
            from architecture_upload_analyzer import ArchitectureAnalyzer, AnalysisResult
            
            with st.spinner("🔄 Analyzing uploaded files..."):
                all_services = []
                all_service_counts = {}
                
                for uploaded_file in uploaded_files:
                    file_content = uploaded_file.read()
                    file_name = uploaded_file.name
                    file_type = file_name.split('.')[-1].lower()
                    
                    result = ArchitectureAnalyzer.analyze_file(file_content, file_name, file_type)
                    all_services.extend(result.detected_services)
                    
                    for svc, count in result.service_counts.items():
                        all_service_counts[svc] = all_service_counts.get(svc, 0) + count
                
                # Update session state with detected services
                all_services = list(set(all_services))
                st.session_state.arch_upload_results = {
                    'services': all_services,
                    'service_counts': all_service_counts,
                    'file_count': len(uploaded_files),
                    'source': 'files'
                }
                
                # Also update the main services list
                st.session_state.arch_services = all_services
                
            st.success(f"✅ Analyzed {len(uploaded_files)} file(s) - Found {len(all_services)} AWS services")
            st.rerun()
            
        except ImportError:
            st.error("Upload analyzer module not available. Please check installation.")
        except Exception as e:
            st.error(f"Error analyzing files: {str(e)}")
    
    @staticmethod
    def _process_text_input(text_input):
        """Process text description of architecture"""
        try:
            from architecture_upload_analyzer import ArchitectureParser
            
            with st.spinner("🔄 Analyzing architecture description..."):
                services, service_counts = ArchitectureParser.parse_text(text_input)
                
                st.session_state.arch_upload_results = {
                    'services': services,
                    'service_counts': service_counts,
                    'file_count': 0,
                    'source': 'text'
                }
                
                # Update the main services list
                st.session_state.arch_services = services
                
            st.success(f"✅ Detected {len(services)} AWS services from description")
            st.rerun()
            
        except ImportError:
            # Fallback basic parser
            import re
            service_patterns = {
                r'\bEC2\b|\binstance\b': 'ec2',
                r'\bLambda\b|\bfunction\b': 'lambda',
                r'\bS3\b|\bbucket\b': 's3',
                r'\bRDS\b|\bdatabase\b': 'rds',
                r'\bAurora\b': 'aurora',
                r'\bDynamoDB\b': 'dynamodb',
                r'\bECS\b|\bFargate\b': 'ecs',
                r'\bEKS\b|\bKubernetes\b': 'eks',
                r'\bALB\b|\bload.?balancer\b': 'alb',
                r'\bCloudFront\b|\bCDN\b': 'cloudfront',
                r'\bCloudWatch\b|\bmonitoring\b': 'cloudwatch',
                r'\bVPC\b|\bnetwork\b': 'vpc',
            }
            
            services = []
            for pattern, service in service_patterns.items():
                if re.search(pattern, text_input, re.IGNORECASE):
                    services.append(service)
            
            st.session_state.arch_upload_results = {
                'services': services,
                'service_counts': {s: 1 for s in services},
                'file_count': 0,
                'source': 'text'
            }
            st.session_state.arch_services = services
            st.success(f"✅ Detected {len(services)} AWS services")
            st.rerun()
    
    @staticmethod
    def _display_upload_results():
        """Display analysis results from uploaded files"""
        results = st.session_state.arch_upload_results
        
        st.markdown("---")
        st.markdown("### 📊 Analysis Results")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Services Detected", len(results['services']))
        col2.metric("Files Analyzed", results.get('file_count', 0))
        col3.metric("Source", results.get('source', 'unknown').title())
        
        if results['services']:
            st.markdown("#### Detected AWS Services")
            
            # Group by category
            service_categories = {
                'Compute': ['ec2', 'lambda', 'ecs', 'eks', 'fargate', 'batch'],
                'Storage': ['s3', 'ebs', 'efs', 'fsx', 'glacier'],
                'Database': ['rds', 'aurora', 'dynamodb', 'elasticache', 'redshift', 'neptune', 'documentdb'],
                'Networking': ['vpc', 'alb', 'nlb', 'cloudfront', 'route53', 'api_gateway', 'nat_gateway'],
                'Security': ['kms', 'waf', 'shield', 'guardduty', 'cognito', 'secrets_manager', 'security_hub', 'iam'],
                'Operations': ['cloudwatch', 'cloudtrail', 'config', 'systems_manager'],
            }
            
            for category, category_services in service_categories.items():
                found = [s for s in results['services'] if s.lower() in category_services]
                if found:
                    with st.expander(f"**{category}** ({len(found)} services)", expanded=True):
                        st.markdown(", ".join([f"`{s.upper()}`" for s in found]))
            
            # Action buttons
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Run WAF Assessment", type="primary", key="upload_run_waf"):
                    st.info("Switch to the WAF Assessment tab to see the full assessment")
            
            with col2:
                if st.button("🔄 Clear Results", key="upload_clear_results"):
                    del st.session_state.arch_upload_results
                    st.session_state.arch_services = []
                    st.rerun()
        else:
            st.warning("No AWS services detected. Try uploading IaC files or providing more details.")
    
    @staticmethod
    def _render_diagram_tab():
        """Render Architecture Diagram Generator tab"""
        
        st.markdown("### 📐 Architecture Diagram Generator")
        st.markdown("Generate professional AWS architecture diagrams from your design")
        
        services = st.session_state.get('arch_services', [])
        config = st.session_state.get('arch_config', {})
        
        if not services:
            st.warning("⚠️ Please select services in the Design tab or upload files in Upload & Analyze tab first")
            
            # Demo option
            st.markdown("---")
            st.markdown("#### 🎮 Demo Mode")
            if st.button("Generate Demo Diagram", key="demo_diagram_btn"):
                services = ['cloudfront', 'alb', 'ecs', 'aurora', 's3', 'cloudwatch', 'waf', 'kms']
                st.session_state.arch_services = services
                st.rerun()
            return
        
        # Diagram configuration
        st.markdown("#### Diagram Settings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            diagram_style = st.selectbox(
                "Diagram Style",
                options=["Three-Tier", "Microservices", "Serverless", "Data Pipeline", "Hub-Spoke"],
                index=0,
                key="diagram_style_select"
            )
        
        with col2:
            color_scheme = st.selectbox(
                "Color Scheme",
                options=["AWS Orange", "Professional Blue", "Dark Mode", "Grayscale"],
                index=0,
                key="color_scheme_select"
            )
        
        with col3:
            include_labels = st.checkbox("Include Labels", value=True, key="include_labels_check")
            include_connections = st.checkbox("Include Connections", value=True, key="include_conn_check")
        
        # Generate button
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            generate_btn = st.button("🎨 Generate Diagram", type="primary", key="generate_diagram_btn")
        
        with col2:
            export_format = st.selectbox("Export Format", ["SVG", "PNG", "PDF"], key="export_format_select")
        
        if generate_btn or 'generated_diagram' in st.session_state:
            st.markdown("---")
            st.markdown("### 🖼️ Generated Architecture Diagram")
            
            # Try to use SVG diagram generator
            try:
                from svg_diagram_generator import SVGDiagramGenerator, DiagramConfig
                
                # Create diagram
                diagram_config = DiagramConfig(
                    title=f"{config.get('workload_type', 'AWS')} Architecture",
                    subtitle=f"Scale: {config.get('scale', 'Medium').title()} | Multi-AZ: {config.get('multi_az', True)}",
                    style=diagram_style.lower().replace("-", "_").replace(" ", "_"),
                    color_scheme=color_scheme.lower().replace(" ", "_"),
                    include_labels=include_labels,
                    include_connections=include_connections
                )
                
                generator = SVGDiagramGenerator()
                svg_content = generator.generate(services, diagram_config)
                
                # Display SVG
                st.markdown(svg_content, unsafe_allow_html=True)
                
                # Store for export
                st.session_state.generated_diagram = svg_content
                
                # Download button
                st.download_button(
                    label=f"📥 Download {export_format}",
                    data=svg_content,
                    file_name=f"architecture_diagram.svg",
                    mime="image/svg+xml",
                    key="download_diagram_btn"
                )
                
            except ImportError:
                # Fallback: Generate simple text-based diagram representation
                st.markdown("#### Architecture Components")
                
                # Create a simple visual representation
                ArchitectureDesignerIntegrated._render_simple_diagram(services, config)
                
            except Exception as e:
                st.error(f"Error generating diagram: {str(e)}")
                ArchitectureDesignerIntegrated._render_simple_diagram(services, config)
    
    @staticmethod
    def _render_simple_diagram(services, config):
        """Render a simple text-based diagram when SVG generator is unavailable"""
        
        # Group services by tier
        tiers = {
            'Edge/CDN': ['cloudfront', 'route53', 'waf', 'shield'],
            'Load Balancing': ['alb', 'nlb', 'api_gateway'],
            'Compute': ['ec2', 'ecs', 'eks', 'lambda', 'fargate'],
            'Database': ['rds', 'aurora', 'dynamodb', 'elasticache', 'redshift'],
            'Storage': ['s3', 'efs', 'ebs'],
            'Security': ['kms', 'secrets_manager', 'cognito', 'guardduty', 'security_hub', 'iam'],
            'Operations': ['cloudwatch', 'cloudtrail', 'config', 'systems_manager']
        }
        
        st.markdown("```")
        st.markdown("┌─────────────────────────────────────────────────────────┐")
        st.markdown("│                   AWS Architecture                       │")
        st.markdown("└─────────────────────────────────────────────────────────┘")
        
        for tier_name, tier_services in tiers.items():
            found = [s.upper() for s in services if s.lower() in tier_services]
            if found:
                st.markdown(f"│ {tier_name:20} │ {', '.join(found):36} │")
        
        st.markdown("```")
        
        # Service count summary
        st.markdown("---")
        st.markdown("#### Service Summary")
        
        cols = st.columns(4)
        for idx, (tier_name, tier_services) in enumerate(tiers.items()):
            found = [s for s in services if s.lower() in tier_services]
            if found:
                with cols[idx % 4]:
                    st.metric(tier_name, len(found))
    
    @staticmethod
    def _render_waf_tab():
        """Render WAF assessment tab"""
        
        st.markdown("### 📊 Well-Architected Framework Assessment")
        
        services = st.session_state.get('arch_services', [])
        config = st.session_state.get('arch_config', {})
        
        if not services:
            st.warning("⚠️ Please select services in the Design tab first")
            return
        
        designer = ArchitectureDesignerIntegrated()
        waf_scores, findings = designer.waf_assessor.assess(services, config)
        
        # Store for other tabs
        st.session_state.arch_waf_scores = waf_scores
        st.session_state.arch_findings = findings
        
        # Overall score
        overall = sum(s.score * PILLAR_CONFIG[p]['weight'] for p, s in waf_scores.items())
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            color = "#4CAF50" if overall >= 80 else "#FF9800" if overall >= 60 else "#F44336"
            st.markdown(f"""
            <div style="text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        border-radius: 15px; color: white;">
                <h2 style="margin: 0;">Overall WAF Score</h2>
                <h1 style="font-size: 72px; margin: 10px 0; color: {color};">{overall:.0f}</h1>
                <p>Based on {len(services)} services</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📈 Pillar Scores")
        
        cols = st.columns(6)
        for idx, pillar in enumerate(WAFPillar):
            score = waf_scores.get(pillar, WAFScore(pillar=pillar, score=0))
            config_p = PILLAR_CONFIG[pillar]
            color = "#4CAF50" if score.score >= 80 else "#FF9800" if score.score >= 60 else "#F44336"
            
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: white; border-radius: 10px; 
                            border: 2px solid {config_p['color']}; margin-bottom: 10px;">
                    <div style="font-size: 28px;">{config_p['icon']}</div>
                    <div style="font-size: 32px; font-weight: bold; color: {color};">{score.score}</div>
                    <div style="font-size: 11px; color: #666; font-weight: bold;">{pillar.value}</div>
                    <div style="font-size: 10px; color: #999;">{score.findings_count} findings</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Findings
        st.markdown("---")
        st.markdown("### 🔍 Architecture Findings")
        
        critical = [f for f in findings if f.severity == "CRITICAL"]
        high = [f for f in findings if f.severity == "HIGH"]
        medium = [f for f in findings if f.severity == "MEDIUM"]
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Findings", len(findings))
        col2.metric("🔴 Critical", len(critical))
        col3.metric("🟠 High", len(high))
        col4.metric("🟡 Medium", len(medium))
        
        for finding in findings:
            severity_color = {"CRITICAL": "#dc3545", "HIGH": "#fd7e14", "MEDIUM": "#ffc107"}.get(finding.severity, "#6c757d")
            severity_icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(finding.severity, "⚪")
            
            with st.expander(f"{severity_icon} [{finding.pillar.value}] {finding.title}"):
                st.markdown(f"**Description:** {finding.description}")
                st.markdown(f"**Recommendation:** {finding.recommendation}")
                if finding.services_to_add:
                    st.info(f"💡 Add services: {', '.join(finding.services_to_add)}")
                if finding.compliance_impact:
                    st.warning(f"⚠️ Compliance Impact: {', '.join([f.value for f in finding.compliance_impact])}")
        
        # Store findings for WAF Review integration
        if findings:
            # Convert to format compatible with main WAF Review
            waf_findings = []
            for f in findings:
                waf_findings.append({
                    'id': f.id,
                    'title': f.title,
                    'description': f.description,
                    'severity': f.severity,
                    'service': 'Architecture',
                    'resource': 'Design',
                    'pillar': f.pillar.value,
                    'recommendation': f.recommendation
                })
            st.session_state['architecture_findings'] = waf_findings
    
    @staticmethod
    def _render_compliance_tab():
        """Render compliance assessment tab"""
        
        st.markdown("### 🔒 Compliance Framework Assessment")
        
        services = st.session_state.get('arch_services', [])
        config = st.session_state.get('arch_config', {})
        
        if not services:
            st.warning("⚠️ Please select services in the Design tab first")
            return
        
        # Get required compliance from config
        required = config.get('compliance_required', [])
        frameworks_to_assess = [f for f in ComplianceFramework if f.value in required] or list(ComplianceFramework)
        
        designer = ArchitectureDesignerIntegrated()
        compliance_scores = designer.compliance_assessor.assess(services, config, frameworks_to_assess)
        
        # Store for other tabs
        st.session_state.arch_compliance_scores = compliance_scores
        
        # Framework cards
        st.markdown("### 📋 Compliance Status by Framework")
        
        cols = st.columns(4)
        for idx, (framework, score) in enumerate(compliance_scores.items()):
            color = "#4CAF50" if score.score >= 80 else "#FF9800" if score.score >= 60 else "#F44336"
            status = "✅" if score.score >= 80 else "⚠️" if score.score >= 60 else "❌"
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div style="padding: 15px; background: white; border-radius: 10px; 
                            border-left: 4px solid {color}; margin-bottom: 15px; min-height: 150px;">
                    <h4 style="margin: 0;">{status} {framework.value}</h4>
                    <h2 style="color: {color}; margin: 10px 0;">{score.score}%</h2>
                    <small>
                        ✅ {score.requirements_met} met<br>
                        ⚠️ {score.requirements_partial} partial<br>
                        ❌ {score.requirements_gap} gaps
                    </small>
                </div>
                """, unsafe_allow_html=True)
        
        # Detailed gaps
        st.markdown("---")
        st.markdown("### 🚨 Compliance Gaps")
        
        all_gaps = []
        for framework, score in compliance_scores.items():
            for gap in score.gaps:
                all_gaps.append({"framework": framework.value, "gap": gap})
        
        if all_gaps:
            for gap in all_gaps:
                st.error(f"**{gap['framework']}**: {gap['gap']}")
        else:
            st.success("✅ No critical compliance gaps detected!")
        
        # Compliance evidence summary
        st.markdown("---")
        st.markdown("### 📄 Compliance Evidence Summary")
        
        evidence = []
        for service in services:
            service_key = service.lower().replace(' ', '_')
            frameworks = SERVICE_COMPLIANCE_MAP.get(service_key, [])
            if frameworks:
                evidence.append({
                    "Service": service,
                    "Compliance Support": ", ".join([f.value for f in frameworks])
                })
        
        if evidence:
            import pandas as pd
            st.dataframe(pd.DataFrame(evidence), use_container_width=True)
    
    @staticmethod
    def _render_ai_tab():
        """Render AI insights tab"""
        
        st.markdown("### 🤖 AI-Powered Architecture Insights")
        
        services = st.session_state.get('arch_services', [])
        config = st.session_state.get('arch_config', {})
        waf_scores = st.session_state.get('arch_waf_scores', {})
        compliance_scores = st.session_state.get('arch_compliance_scores', {})
        
        if not services:
            st.warning("⚠️ Please select services in the Design tab first")
            return
        
        if not waf_scores:
            st.info("💡 Visit the WAF Assessment tab first to generate scores")
            return
        
        designer = ArchitectureDesignerIntegrated()
        
        with st.spinner("🤖 Analyzing architecture with AI..."):
            recommendations = designer.ai_lens.analyze_architecture(
                services, config, waf_scores, compliance_scores
            )
        
        if recommendations:
            st.markdown("### 💡 AI Recommendations")
            
            for idx, rec in enumerate(recommendations, 1):
                # Determine priority color
                if "Critical" in rec or "CRITICAL" in rec:
                    st.error(f"**{idx}.** {rec}")
                elif "High" in rec or "HIGH" in rec:
                    st.warning(f"**{idx}.** {rec}")
                else:
                    st.info(f"**{idx}.** {rec}")
        else:
            st.info("🤖 AI recommendations not available. Pattern-based analysis shown in WAF tab.")
        
        # Architecture improvement suggestions
        st.markdown("---")
        st.markdown("### 🎯 Quick Improvements")
        
        # Find lowest scoring pillars
        if waf_scores:
            sorted_pillars = sorted(waf_scores.items(), key=lambda x: x[1].score)
            
            for pillar, score in sorted_pillars[:3]:
                if score.score < 80:
                    config_p = PILLAR_CONFIG[pillar]
                    st.markdown(f"""
                    <div style="padding: 15px; background: #f8f9fa; border-radius: 10px; 
                                border-left: 4px solid {config_p['color']}; margin-bottom: 10px;">
                        <h4>{config_p['icon']} Improve {pillar.value} (Current: {score.score}%)</h4>
                        <ul>
                            {"".join([f"<li>{s}</li>" for s in score.improvement_suggestions[:3]])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
    
    @staticmethod
    def _render_export_tab():
        """Render export tab"""
        
        st.markdown("### 📥 Export Architecture")
        
        services = st.session_state.get('arch_services', [])
        config = st.session_state.get('arch_config', {})
        waf_scores = st.session_state.get('arch_waf_scores', {})
        compliance_scores = st.session_state.get('arch_compliance_scores', {})
        findings = st.session_state.get('arch_findings', [])
        
        if not services:
            st.warning("⚠️ Please design your architecture first")
            return
        
        col1, col2, col3 = st.columns(3)
        
        # JSON Export
        with col1:
            st.markdown("#### 📋 JSON Export")
            
            export_data = {
                "architecture": {
                    "name": config.get('use_case', 'Custom Architecture'),
                    "services": services,
                    "config": config,
                    "generated_at": datetime.now().isoformat()
                },
                "waf_assessment": {
                    "overall_score": sum(s.score * PILLAR_CONFIG[p]['weight'] for p, s in waf_scores.items()) if waf_scores else 0,
                    "pillar_scores": {p.value: s.score for p, s in waf_scores.items()} if waf_scores else {},
                    "findings_count": len(findings)
                },
                "compliance_assessment": {
                    f.value: {"score": s.score, "gaps": s.gaps} 
                    for f, s in compliance_scores.items()
                } if compliance_scores else {}
            }
            
            st.download_button(
                "📥 Download JSON",
                data=json.dumps(export_data, indent=2, default=str),
                file_name="architecture_assessment.json",
                mime="application/json",
                use_container_width=True,
                key="arch_export_json_btn"
            )
        
        # Findings Export
        with col2:
            st.markdown("#### 🔍 Findings Export")
            
            if findings:
                findings_export = []
                for f in findings:
                    findings_export.append({
                        "ID": f.id,
                        "Pillar": f.pillar.value,
                        "Severity": f.severity,
                        "Title": f.title,
                        "Recommendation": f.recommendation,
                        "Compliance Impact": ", ".join([c.value for c in f.compliance_impact])
                    })
                
                import pandas as pd
                df = pd.DataFrame(findings_export)
                
                st.download_button(
                    "📥 Download Findings CSV",
                    data=df.to_csv(index=False),
                    file_name="architecture_findings.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="arch_export_findings_btn"
                )
            else:
                st.info("No findings to export")
        
        # Integration with WAF Review
        with col3:
            st.markdown("#### 🔗 WAF Review Integration")
            
            if st.button("📤 Send to WAF Review", use_container_width=True, key="arch_send_waf_btn"):
                # Convert findings to WAF Review format
                waf_findings = []
                for f in findings:
                    waf_findings.append({
                        'id': f.id,
                        'title': f.title,
                        'description': f.description,
                        'severity': f.severity,
                        'service': 'Architecture Design',
                        'resource': config.get('use_case', 'Custom'),
                        'account_id': 'architecture',
                        'region': 'global',
                        'pillar': f.pillar.value
                    })
                
                # Store in session state for WAF Review
                if 'architecture_findings_for_waf' not in st.session_state:
                    st.session_state.architecture_findings_for_waf = []
                st.session_state.architecture_findings_for_waf = waf_findings
                
                st.success(f"✅ Sent {len(waf_findings)} findings to WAF Review!")
                st.info("💡 Go to WAF Review → Unified Assessment to see combined results")


# ============================================================================
# ENTRY POINT
# ============================================================================

def render_architecture_designer_integrated():
    """Main entry point for integrated Architecture Designer"""
    ArchitectureDesignerIntegrated.render()


if __name__ == "__main__":
    st.set_page_config(page_title="Architecture Designer - Integrated", layout="wide")
    render_architecture_designer_integrated()
