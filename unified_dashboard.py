"""
Unified Dashboard - Enterprise WAF Scanner
==========================================
Single-view dashboard showing status across all application modules.

Features:
- Real-time WAF scores across all modules
- Compliance posture summary with trends
- AI insights aggregation
- Trend tracking over time
- Executive summary PDF generation
- Cross-module correlation
- Priority action queue
- Health monitoring

Version: 1.0.1 - Fixed colors and KeyError
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import io

# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class ModuleType(Enum):
    """Application modules"""
    WAF_REVIEW = "WAF Review"
    ARCHITECTURE = "Architecture Designer"
    EKS = "EKS Modernization"
    COMPLIANCE = "Compliance"
    FINOPS = "FinOps"
    AI_LENS = "AI Lens"
    REMEDIATION = "Remediation"

class WAFPillar(Enum):
    """WAF Pillars"""
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"

class ComplianceFramework(Enum):
    """Compliance frameworks"""
    SOC2 = "SOC 2 Type II"
    HIPAA = "HIPAA"
    PCI_DSS = "PCI-DSS v4.0"
    ISO_27001 = "ISO 27001:2022"
    CIS = "CIS Benchmarks"
    GDPR = "GDPR"
    NIST = "NIST CSF"
    FEDRAMP = "FedRAMP"

class HealthStatus(Enum):
    """Module health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

# Configuration - Professional muted colors
PILLAR_CONFIG = {
    WAFPillar.OPERATIONAL_EXCELLENCE: {"icon": "⚙️", "color": "#5D6D7E"},  # Slate gray
    WAFPillar.SECURITY: {"icon": "🔒", "color": "#2874A6"},               # Professional blue
    WAFPillar.RELIABILITY: {"icon": "🛡️", "color": "#148F77"},            # Teal
    WAFPillar.PERFORMANCE_EFFICIENCY: {"icon": "⚡", "color": "#B9770E"}, # Amber
    WAFPillar.COST_OPTIMIZATION: {"icon": "💰", "color": "#1E8449"},      # Forest green
    WAFPillar.SUSTAINABILITY: {"icon": "🌱", "color": "#117A65"}          # Dark teal
}

MODULE_CONFIG = {
    ModuleType.WAF_REVIEW: {"icon": "🔍", "color": "#2E86AB"},      # Steel blue
    ModuleType.ARCHITECTURE: {"icon": "🏗️", "color": "#6C5B7B"},   # Muted purple
    ModuleType.EKS: {"icon": "☸️", "color": "#C06C52"},            # Terracotta
    ModuleType.COMPLIANCE: {"icon": "🔒", "color": "#2E7D32"},     # Forest green
    ModuleType.FINOPS: {"icon": "💰", "color": "#F9A825"},         # Amber
    ModuleType.AI_LENS: {"icon": "🤖", "color": "#7B1FA2"},        # Deep purple
    ModuleType.REMEDIATION: {"icon": "🔧", "color": "#00695C"}     # Deep teal
}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ModuleStatus:
    """Status of a single module"""
    module: ModuleType
    health: HealthStatus
    last_updated: datetime
    waf_scores: Dict[WAFPillar, int] = field(default_factory=dict)
    overall_score: int = 0
    findings_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    compliance_scores: Dict[str, int] = field(default_factory=dict)
    ai_insights_count: int = 0
    pending_actions: int = 0

@dataclass
class DashboardSnapshot:
    """Point-in-time dashboard snapshot for trending"""
    id: str
    timestamp: datetime
    overall_waf_score: int
    overall_compliance_score: int
    total_findings: int
    critical_findings: int
    modules_status: Dict[str, str]  # module -> health status

@dataclass
class PriorityAction:
    """Priority action item"""
    id: str
    source_module: ModuleType
    severity: str
    title: str
    description: str
    impact: str
    action_required: str
    compliance_frameworks: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ExecutiveSummary:
    """Executive summary data"""
    generated_at: datetime
    reporting_period: str
    overall_posture: str
    waf_score: int
    compliance_score: int
    findings_summary: Dict[str, int]
    top_risks: List[Dict]
    recommendations: List[str]
    trend_direction: str  # improving, stable, declining
    modules_assessed: List[str]

# ============================================================================
# DATA AGGREGATOR
# ============================================================================

class DashboardDataAggregator:
    """Aggregates data from all modules"""
    
    def __init__(self):
        self.modules_data = {}
        # Create pillar name mapping once
        self.pillar_name_map = {p.value: p for p in WAFPillar}
    
    def collect_all_data(self) -> Dict[ModuleType, ModuleStatus]:
        """Collect data from all modules via session state"""
        
        statuses = {}
        
        # WAF Review data
        statuses[ModuleType.WAF_REVIEW] = self._collect_waf_review_data()
        
        # Architecture Designer data
        statuses[ModuleType.ARCHITECTURE] = self._collect_architecture_data()
        
        # EKS Modernization data
        statuses[ModuleType.EKS] = self._collect_eks_data()
        
        # Compliance data
        statuses[ModuleType.COMPLIANCE] = self._collect_compliance_data()
        
        # FinOps data
        statuses[ModuleType.FINOPS] = self._collect_finops_data()
        
        # Remediation data
        statuses[ModuleType.REMEDIATION] = self._collect_remediation_data()
        
        return statuses
    
    def _normalize_pillar_key(self, key) -> Optional[WAFPillar]:
        """Convert any pillar key format to WAFPillar enum"""
        if isinstance(key, WAFPillar):
            return key
        elif isinstance(key, str):
            return self.pillar_name_map.get(key)
        return None
    
    def _extract_score(self, score_val) -> int:
        """Extract integer score from various formats"""
        if score_val is None:
            return 0
        if hasattr(score_val, 'score'):
            return int(score_val.score) if score_val.score else 0
        try:
            return int(score_val)
        except (TypeError, ValueError):
            return 0
    
    def _get_severity(self, finding) -> str:
        """Get severity from a finding (dict or object)"""
        if isinstance(finding, dict):
            return finding.get('severity', '')
        return getattr(finding, 'severity', '')
    
    def _get_pillar(self, finding) -> str:
        """Get pillar from a finding (dict or object)"""
        if isinstance(finding, dict):
            return finding.get('pillar', '')
        return getattr(finding, 'pillar', '')
    
    def _calculate_scores_from_findings(self, findings) -> Dict[WAFPillar, int]:
        """Calculate WAF pillar scores based on findings severity"""
        pillar_scores = {p: 100 for p in WAFPillar}  # Start at 100
        
        for finding in findings:
            severity = self._get_severity(finding)
            pillar_str = self._get_pillar(finding)
            pillar = self._normalize_pillar_key(pillar_str)
            
            if pillar and pillar in pillar_scores:
                # Deduct points based on severity
                if severity == 'CRITICAL':
                    pillar_scores[pillar] = max(0, pillar_scores[pillar] - 15)
                elif severity == 'HIGH':
                    pillar_scores[pillar] = max(0, pillar_scores[pillar] - 10)
                elif severity == 'MEDIUM':
                    pillar_scores[pillar] = max(0, pillar_scores[pillar] - 5)
                elif severity == 'LOW':
                    pillar_scores[pillar] = max(0, pillar_scores[pillar] - 2)
        
        return pillar_scores
    
    def _collect_waf_review_data(self) -> ModuleStatus:
        """Collect WAF Review module data - FIXED to read from waf_review_session"""
        
        findings = []
        waf_scores = {}
        overall = 0
        
        # PRIMARY SOURCE: waf_review_session (from WAF Review Comprehensive module)
        if 'waf_review_session' in st.session_state:
            session = st.session_state.waf_review_session
            
            # Get findings from session
            if hasattr(session, 'findings') and session.findings:
                for f in session.findings:
                    # Convert Finding objects to dict format
                    if hasattr(f, 'severity'):
                        findings.append({
                            'severity': f.severity,
                            'title': getattr(f, 'title', ''),
                            'pillar': getattr(f, 'pillar', ''),
                            'service': getattr(f, 'service', '')
                        })
                    elif isinstance(f, dict):
                        findings.append(f)
            
            # Get pillar scores from session
            if hasattr(session, 'pillar_scores') and session.pillar_scores:
                for pillar_name, score_obj in session.pillar_scores.items():
                    pillar = self._normalize_pillar_key(pillar_name)
                    if pillar:
                        # PillarScore has combined_score attribute
                        if hasattr(score_obj, 'combined_score'):
                            waf_scores[pillar] = int(score_obj.combined_score)
                        elif hasattr(score_obj, 'score'):
                            waf_scores[pillar] = int(score_obj.score)
                        elif isinstance(score_obj, (int, float)):
                            waf_scores[pillar] = int(score_obj)
            
            # Get overall score
            if hasattr(session, 'overall_score') and session.overall_score:
                overall = int(session.overall_score)
        
        # FALLBACK: multi_scan_results (legacy)
        if not findings and 'multi_scan_results' in st.session_state:
            results = st.session_state.multi_scan_results
            for account_id, data in results.items():
                if account_id != 'consolidated_pdf' and isinstance(data, dict):
                    findings.extend(data.get('findings', []))
        
        # FALLBACK: last_findings (legacy)
        if not findings and 'last_findings' in st.session_state:
            findings = st.session_state.last_findings
        
        # FALLBACK: unified_assessment_results
        if not waf_scores and 'unified_assessment_results' in st.session_state:
            results = st.session_state.unified_assessment_results
            if isinstance(results, dict):
                if 'pillar_scores' in results:
                    for p, s in results['pillar_scores'].items():
                        pillar = self._normalize_pillar_key(p)
                        if pillar:
                            waf_scores[pillar] = self._extract_score(s)
                if 'overall_score' in results:
                    overall = int(results['overall_score'])
        
        # FALLBACK: current_integrated_assessment (legacy)
        if not waf_scores and 'current_integrated_assessment' in st.session_state:
            assessment = st.session_state.current_integrated_assessment
            if hasattr(assessment, 'waf_scores'):
                for p, s in assessment.waf_scores.items():
                    pillar = self._normalize_pillar_key(p)
                    if pillar:
                        waf_scores[pillar] = self._extract_score(s)
        
        # Count severities
        critical = 0
        high = 0
        for f in findings:
            sev = f.get('severity', '') if isinstance(f, dict) else getattr(f, 'severity', '')
            if sev == 'CRITICAL':
                critical += 1
            elif sev == 'HIGH':
                high += 1
        
        # FALLBACK: If no explicit scores but we have findings, calculate scores from findings
        if not waf_scores and findings:
            waf_scores = self._calculate_scores_from_findings(findings)
        
        # Determine health
        if critical > 0:
            health = HealthStatus.CRITICAL
        elif high > 5:
            health = HealthStatus.WARNING
        elif findings:
            health = HealthStatus.HEALTHY
        else:
            health = HealthStatus.UNKNOWN
        
        # Calculate overall if not set but we have pillar scores
        if not overall and waf_scores:
            overall = sum(waf_scores.values()) // len(waf_scores)
        
        return ModuleStatus(
            module=ModuleType.WAF_REVIEW,
            health=health,
            last_updated=datetime.now(),
            waf_scores=waf_scores,
            overall_score=overall,
            findings_count=len(findings),
            critical_count=critical,
            high_count=high
        )
    
    def _collect_architecture_data(self) -> ModuleStatus:
        """Collect Architecture Designer data - ENHANCED to calculate scores from findings"""
        
        waf_scores = {}
        findings = []
        compliance_scores = {}
        
        # Get explicit WAF scores if available
        if 'arch_waf_scores' in st.session_state:
            scores = st.session_state.arch_waf_scores
            for p, s in scores.items():
                pillar = self._normalize_pillar_key(p)
                if pillar:
                    waf_scores[pillar] = self._extract_score(s)
        
        # Get findings
        if 'arch_findings' in st.session_state:
            findings = st.session_state.arch_findings
        
        # If no explicit scores but we have findings, calculate scores from findings
        if not waf_scores and findings:
            waf_scores = self._calculate_scores_from_findings(findings)
        
        if 'arch_compliance_scores' in st.session_state:
            scores = st.session_state.arch_compliance_scores
            for f, s in scores.items():
                f_name = f.value if hasattr(f, 'value') else str(f)
                compliance_scores[f_name] = self._extract_score(s)
        
        critical = len([f for f in findings if self._get_severity(f) == 'CRITICAL'])
        high = len([f for f in findings if self._get_severity(f) == 'HIGH'])
        
        health = HealthStatus.UNKNOWN
        if findings:
            if critical > 0:
                health = HealthStatus.CRITICAL
            elif high > 3:
                health = HealthStatus.WARNING
            else:
                health = HealthStatus.HEALTHY
        
        overall = sum(waf_scores.values()) // len(waf_scores) if waf_scores else 0
        
        return ModuleStatus(
            module=ModuleType.ARCHITECTURE,
            health=health,
            last_updated=datetime.now(),
            waf_scores=waf_scores,
            overall_score=overall,
            findings_count=len(findings),
            critical_count=critical,
            high_count=high,
            compliance_scores=compliance_scores
        )
    
    def _collect_eks_data(self) -> ModuleStatus:
        """Collect EKS Modernization data - ENHANCED to calculate scores from findings"""
        
        waf_scores = {}
        findings = []
        compliance_scores = {}
        
        # Get explicit WAF scores if available
        if 'eks_waf_scores' in st.session_state:
            scores = st.session_state.eks_waf_scores
            for p, s in scores.items():
                pillar = self._normalize_pillar_key(p)
                if pillar:
                    waf_scores[pillar] = self._extract_score(s)
        
        # Get findings
        if 'eks_findings' in st.session_state:
            findings = st.session_state.eks_findings
        
        # If no explicit scores but we have findings, calculate scores from findings
        if not waf_scores and findings:
            waf_scores = self._calculate_scores_from_findings(findings)
        
        if 'eks_compliance_scores' in st.session_state:
            scores = st.session_state.eks_compliance_scores
            for f, s in scores.items():
                f_name = f.value if hasattr(f, 'value') else str(f)
                compliance_scores[f_name] = self._extract_score(s)
        
        critical = len([f for f in findings if self._get_severity(f) == 'CRITICAL'])
        high = len([f for f in findings if self._get_severity(f) == 'HIGH'])
        
        health = HealthStatus.UNKNOWN
        if findings:
            if critical > 0:
                health = HealthStatus.CRITICAL
            elif high > 3:
                health = HealthStatus.WARNING
            else:
                health = HealthStatus.HEALTHY
        
        overall = sum(waf_scores.values()) // len(waf_scores) if waf_scores else 0
        
        return ModuleStatus(
            module=ModuleType.EKS,
            health=health,
            last_updated=datetime.now(),
            waf_scores=waf_scores,
            overall_score=overall,
            findings_count=len(findings),
            critical_count=critical,
            high_count=high,
            compliance_scores=compliance_scores
        )
    
    def _collect_compliance_data(self) -> ModuleStatus:
        """Collect Compliance module data"""
        
        compliance_scores = {}
        
        # Try to get from various sources
        sources = [
            'current_integrated_assessment',
            'arch_compliance_scores',
            'eks_compliance_scores'
        ]
        
        for source in sources:
            if source in st.session_state:
                data = st.session_state[source]
                if hasattr(data, 'compliance_status'):
                    for f, s in data.compliance_status.items():
                        f_name = f.value if hasattr(f, 'value') else str(f)
                        compliance_scores[f_name] = self._extract_score(s)
                elif isinstance(data, dict):
                    for f, s in data.items():
                        f_name = f.value if hasattr(f, 'value') else str(f)
                        compliance_scores[f_name] = self._extract_score(s)
        
        # Determine health based on lowest compliance score
        if compliance_scores:
            min_score = min(compliance_scores.values())
            if min_score < 50:
                health = HealthStatus.CRITICAL
            elif min_score < 70:
                health = HealthStatus.WARNING
            else:
                health = HealthStatus.HEALTHY
        else:
            health = HealthStatus.UNKNOWN
        
        overall = sum(compliance_scores.values()) // len(compliance_scores) if compliance_scores else 0
        
        return ModuleStatus(
            module=ModuleType.COMPLIANCE,
            health=health,
            last_updated=datetime.now(),
            overall_score=overall,
            compliance_scores=compliance_scores
        )
    
    def _collect_finops_data(self) -> ModuleStatus:
        """Collect FinOps module data"""
        
        # FinOps data would come from cost analysis
        # For now, return unknown status
        
        return ModuleStatus(
            module=ModuleType.FINOPS,
            health=HealthStatus.UNKNOWN,
            last_updated=datetime.now(),
            overall_score=0
        )
    
    def _collect_remediation_data(self) -> ModuleStatus:
        """Collect Remediation module data"""
        
        actions = st.session_state.get('remediation_actions', [])
        
        if not actions:
            return ModuleStatus(
                module=ModuleType.REMEDIATION,
                health=HealthStatus.UNKNOWN,
                last_updated=datetime.now()
            )
        
        pending = len([a for a in actions if getattr(a, 'status', None) and a.status.value in ['pending', 'approved']])
        deployed = len([a for a in actions if getattr(a, 'status', None) and a.status.value == 'deployed'])
        failed = len([a for a in actions if getattr(a, 'status', None) and a.status.value == 'failed'])
        
        if failed > 0:
            health = HealthStatus.WARNING
        elif pending > 0:
            health = HealthStatus.WARNING
        elif deployed > 0:
            health = HealthStatus.HEALTHY
        else:
            health = HealthStatus.UNKNOWN
        
        return ModuleStatus(
            module=ModuleType.REMEDIATION,
            health=health,
            last_updated=datetime.now(),
            pending_actions=pending,
            findings_count=len(actions)
        )
    
    def get_aggregated_waf_scores(self, statuses: Dict[ModuleType, ModuleStatus]) -> Dict[WAFPillar, int]:
        """Aggregate WAF scores across all modules"""
        
        # Initialize with all pillars set to empty lists
        pillar_scores = {p: [] for p in WAFPillar}
        
        for module, status in statuses.items():
            try:
                if not status.waf_scores:
                    continue
                    
                for pillar_key, score_val in status.waf_scores.items():
                    # Normalize the pillar key
                    pillar = self._normalize_pillar_key(pillar_key)
                    if pillar is None:
                        continue
                    
                    # Extract score value
                    score = self._extract_score(score_val)
                    
                    if score > 0 and pillar in pillar_scores:
                        pillar_scores[pillar].append(score)
                        
            except Exception as e:
                # Skip problematic module data silently
                continue
        
        # Average scores per pillar
        aggregated = {}
        for pillar, scores in pillar_scores.items():
            if scores:
                aggregated[pillar] = sum(scores) // len(scores)
            else:
                aggregated[pillar] = 0
        
        return aggregated
    
    def get_aggregated_compliance(self, statuses: Dict[ModuleType, ModuleStatus]) -> Dict[str, int]:
        """Aggregate compliance scores across all modules"""
        
        framework_scores = {}
        
        for module, status in statuses.items():
            if not status.compliance_scores:
                continue
            for framework, score in status.compliance_scores.items():
                if framework not in framework_scores:
                    framework_scores[framework] = []
                if score > 0:
                    framework_scores[framework].append(score)
        
        # Average scores per framework
        aggregated = {}
        for framework, scores in framework_scores.items():
            if scores:
                aggregated[framework] = sum(scores) // len(scores)
        
        return aggregated
    
    def get_priority_actions(self, statuses: Dict[ModuleType, ModuleStatus]) -> List[PriorityAction]:
        """Generate priority action items from all modules"""
        
        actions = []
        
        # Critical findings from each module
        for module, status in statuses.items():
            if status.critical_count > 0:
                actions.append(PriorityAction(
                    id=f"action-{module.value}-critical",
                    source_module=module,
                    severity="CRITICAL",
                    title=f"{status.critical_count} Critical Findings in {module.value}",
                    description=f"Critical security issues detected requiring immediate attention",
                    impact="Potential security breach or compliance violation",
                    action_required=f"Review and remediate critical findings in {module.value}"
                ))
            
            if status.health == HealthStatus.CRITICAL:
                actions.append(PriorityAction(
                    id=f"action-{module.value}-health",
                    source_module=module,
                    severity="HIGH",
                    title=f"{module.value} Module Health Critical",
                    description=f"Module health status is critical",
                    impact="Reduced security posture",
                    action_required=f"Investigate and resolve issues in {module.value}"
                ))
        
        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        actions.sort(key=lambda x: severity_order.get(x.severity, 4))
        
        return actions[:10]  # Top 10 priority actions


# ============================================================================
# TREND TRACKER
# ============================================================================

class TrendTracker:
    """Tracks dashboard trends over time"""
    
    def __init__(self):
        if 'dashboard_snapshots' not in st.session_state:
            st.session_state.dashboard_snapshots = []
    
    def save_snapshot(self, statuses: Dict[ModuleType, ModuleStatus]):
        """Save a dashboard snapshot"""
        
        total_findings = sum(s.findings_count for s in statuses.values())
        critical_findings = sum(s.critical_count for s in statuses.values())
        
        # Calculate overall scores
        waf_scores = [s.overall_score for s in statuses.values() if s.overall_score > 0]
        compliance_scores = []
        for s in statuses.values():
            compliance_scores.extend(s.compliance_scores.values())
        
        overall_waf = sum(waf_scores) // len(waf_scores) if waf_scores else 0
        overall_compliance = sum(compliance_scores) // len(compliance_scores) if compliance_scores else 0
        
        snapshot = DashboardSnapshot(
            id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8],
            timestamp=datetime.now(),
            overall_waf_score=overall_waf,
            overall_compliance_score=overall_compliance,
            total_findings=total_findings,
            critical_findings=critical_findings,
            modules_status={m.value: s.health.value for m, s in statuses.items()}
        )
        
        st.session_state.dashboard_snapshots.append(snapshot)
        
        # Keep only last 100 snapshots
        if len(st.session_state.dashboard_snapshots) > 100:
            st.session_state.dashboard_snapshots = st.session_state.dashboard_snapshots[-100:]
    
    def get_trend(self, days: int = 7) -> Dict:
        """Get trend data for the specified period"""
        
        snapshots = st.session_state.get('dashboard_snapshots', [])
        
        if len(snapshots) < 2:
            return {"direction": "stable", "change": 0, "data": []}
        
        cutoff = datetime.now() - timedelta(days=days)
        recent = [s for s in snapshots if s.timestamp > cutoff]
        
        if len(recent) < 2:
            return {"direction": "stable", "change": 0, "data": recent}
        
        # Compare first and last
        first = recent[0]
        last = recent[-1]
        
        waf_change = last.overall_waf_score - first.overall_waf_score
        
        if waf_change > 5:
            direction = "improving"
        elif waf_change < -5:
            direction = "declining"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "waf_change": waf_change,
            "compliance_change": last.overall_compliance_score - first.overall_compliance_score,
            "findings_change": last.total_findings - first.total_findings,
            "data": recent
        }


# ============================================================================
# EXECUTIVE SUMMARY GENERATOR
# ============================================================================

class ExecutiveSummaryGenerator:
    """Generates executive summary reports"""
    
    def generate(self, statuses: Dict[ModuleType, ModuleStatus],
                 aggregated_waf: Dict[WAFPillar, int],
                 aggregated_compliance: Dict[str, int],
                 trend: Dict) -> ExecutiveSummary:
        """Generate executive summary"""
        
        # Calculate overall scores
        waf_score = sum(aggregated_waf.values()) // len(aggregated_waf) if aggregated_waf else 0
        compliance_score = sum(aggregated_compliance.values()) // len(aggregated_compliance) if aggregated_compliance else 0
        
        # Determine posture
        if waf_score >= 80 and compliance_score >= 80:
            posture = "Strong"
        elif waf_score >= 60 and compliance_score >= 60:
            posture = "Moderate"
        else:
            posture = "Needs Improvement"
        
        # Findings summary
        findings_summary = {
            "critical": sum(s.critical_count for s in statuses.values()),
            "high": sum(s.high_count for s in statuses.values()),
            "total": sum(s.findings_count for s in statuses.values())
        }
        
        # Top risks
        top_risks = []
        
        # Lowest WAF pillars
        sorted_waf = sorted(aggregated_waf.items(), key=lambda x: x[1])
        for pillar, score in sorted_waf[:3]:
            if score < 70:
                top_risks.append({
                    "category": "WAF Pillar",
                    "item": pillar.value,
                    "score": score,
                    "impact": "High" if score < 50 else "Medium"
                })
        
        # Lowest compliance
        sorted_compliance = sorted(aggregated_compliance.items(), key=lambda x: x[1])
        for framework, score in sorted_compliance[:3]:
            if score < 70:
                top_risks.append({
                    "category": "Compliance",
                    "item": framework,
                    "score": score,
                    "impact": "High" if score < 50 else "Medium"
                })
        
        # Recommendations
        recommendations = []
        
        if findings_summary["critical"] > 0:
            recommendations.append(f"Immediately address {findings_summary['critical']} critical security findings")
        
        for pillar, score in sorted_waf[:2]:
            if score < 70:
                recommendations.append(f"Improve {pillar.value} pillar (current: {score}%)")
        
        for framework, score in sorted_compliance[:2]:
            if score < 70:
                recommendations.append(f"Address {framework} compliance gaps (current: {score}%)")
        
        if not recommendations:
            recommendations.append("Maintain current security posture with regular assessments")
        
        # Modules assessed
        modules_assessed = [m.value for m, s in statuses.items() if s.health != HealthStatus.UNKNOWN]
        
        return ExecutiveSummary(
            generated_at=datetime.now(),
            reporting_period="Current Assessment",
            overall_posture=posture,
            waf_score=waf_score,
            compliance_score=compliance_score,
            findings_summary=findings_summary,
            top_risks=top_risks,
            recommendations=recommendations,
            trend_direction=trend.get("direction", "stable"),
            modules_assessed=modules_assessed
        )
    
    def generate_pdf_report(self, summary: ExecutiveSummary) -> bytes:
        """Generate PDF report from summary"""
        
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#1a237e')
            )
            story.append(Paragraph("Executive Security Summary", title_style))
            story.append(Paragraph(f"Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Overall Posture
            posture_color = {
                "Strong": colors.green,
                "Moderate": colors.orange,
                "Needs Improvement": colors.HexColor('#B45309')
            }.get(summary.overall_posture, colors.gray)
            
            story.append(Paragraph(f"<b>Overall Security Posture:</b> <font color='{posture_color}'>{summary.overall_posture}</font>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            # Scores table
            scores_data = [
                ["Metric", "Score", "Status"],
                ["WAF Score", f"{summary.waf_score}%", "✓" if summary.waf_score >= 70 else "!"],
                ["Compliance Score", f"{summary.compliance_score}%", "✓" if summary.compliance_score >= 70 else "!"],
                ["Critical Findings", str(summary.findings_summary.get('critical', 0)), "!" if summary.findings_summary.get('critical', 0) > 0 else "✓"],
                ["Total Findings", str(summary.findings_summary.get('total', 0)), "-"]
            ]
            
            table = Table(scores_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Top Risks
            story.append(Paragraph("Top Risks", styles['Heading2']))
            for risk in summary.top_risks[:5]:
                story.append(Paragraph(f"• <b>{risk['category']}</b>: {risk['item']} ({risk['score']}%) - Impact: {risk['impact']}", styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Recommendations
            story.append(Paragraph("Recommendations", styles['Heading2']))
            for rec in summary.recommendations[:5]:
                story.append(Paragraph(f"• {rec}", styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Trend
            trend_text = {
                "improving": "Security posture is improving ↑",
                "stable": "Security posture is stable →",
                "declining": "Security posture is declining ↓"
            }.get(summary.trend_direction, "Trend data unavailable")
            story.append(Paragraph(f"<b>Trend:</b> {trend_text}", styles['Normal']))
            
            # Modules assessed
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Modules Assessed:</b> {', '.join(summary.modules_assessed)}", styles['Normal']))
            
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except ImportError:
            # Fallback to text report if reportlab not available
            return self._generate_text_report(summary).encode('utf-8')
    
    def _generate_text_report(self, summary: ExecutiveSummary) -> str:
        """Generate text report as fallback"""
        
        report = f"""
================================================================================
                        EXECUTIVE SECURITY SUMMARY
================================================================================

Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M')}
Reporting Period: {summary.reporting_period}

--------------------------------------------------------------------------------
OVERALL SECURITY POSTURE: {summary.overall_posture.upper()}
--------------------------------------------------------------------------------

SCORES:
  • WAF Score: {summary.waf_score}%
  • Compliance Score: {summary.compliance_score}%
  
FINDINGS:
  • Critical: {summary.findings_summary.get('critical', 0)}
  • High: {summary.findings_summary.get('high', 0)}
  • Total: {summary.findings_summary.get('total', 0)}

--------------------------------------------------------------------------------
TOP RISKS
--------------------------------------------------------------------------------
"""
        for risk in summary.top_risks[:5]:
            report += f"  • {risk['category']}: {risk['item']} ({risk['score']}%) - Impact: {risk['impact']}\n"
        
        report += """
--------------------------------------------------------------------------------
RECOMMENDATIONS
--------------------------------------------------------------------------------
"""
        for rec in summary.recommendations:
            report += f"  • {rec}\n"
        
        report += f"""
--------------------------------------------------------------------------------
TREND: {summary.trend_direction.upper()}
--------------------------------------------------------------------------------

Modules Assessed: {', '.join(summary.modules_assessed)}

================================================================================
"""
        return report


# ============================================================================
# UNIFIED DASHBOARD UI
# ============================================================================

class UnifiedDashboard:
    """Unified Dashboard UI"""
    
    @staticmethod
    def render():
        """Render the unified dashboard"""
        
        st.markdown("# 📊 Unified Security Dashboard")
        st.markdown("### Enterprise WAF Scanner - All Modules at a Glance")
        
        # Initialize components
        aggregator = DashboardDataAggregator()
        trend_tracker = TrendTracker()
        summary_generator = ExecutiveSummaryGenerator()
        
        # Collect data from all modules
        statuses = aggregator.collect_all_data()
        
        # Save snapshot for trending
        trend_tracker.save_snapshot(statuses)
        
        # Get aggregated data
        aggregated_waf = aggregator.get_aggregated_waf_scores(statuses)
        aggregated_compliance = aggregator.get_aggregated_compliance(statuses)
        priority_actions = aggregator.get_priority_actions(statuses)
        trend = trend_tracker.get_trend()
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview",
            "📈 WAF Pillars",
            "🔒 Compliance",
            "🎯 Actions",
            "📄 Reports"
        ])
        
        with tab1:
            UnifiedDashboard._render_overview(statuses, aggregated_waf, aggregated_compliance, trend)
        
        with tab2:
            UnifiedDashboard._render_waf_pillars(statuses, aggregated_waf)
        
        with tab3:
            UnifiedDashboard._render_compliance(statuses, aggregated_compliance)
        
        with tab4:
            UnifiedDashboard._render_actions(priority_actions, statuses)
        
        with tab5:
            summary = summary_generator.generate(statuses, aggregated_waf, aggregated_compliance, trend)
            UnifiedDashboard._render_reports(summary, summary_generator)
    
    @staticmethod
    def _render_overview(statuses: Dict, aggregated_waf: Dict, aggregated_compliance: Dict, trend: Dict):
        """Render overview tab"""
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        # Overall WAF Score
        waf_score = sum(aggregated_waf.values()) // len(aggregated_waf) if aggregated_waf else 0
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2C3E50 0%, #3D5A80 100%); 
                        padding: 20px; border-radius: 15px; text-align: center; color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-weight: 500; opacity: 0.9;">WAF Score</h4>
                <h1 style="font-size: 48px; margin: 10px 0; color: white;">{waf_score}</h1>
                <small style="opacity: 0.8;">Across all modules</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Overall Compliance Score
        compliance_score = sum(aggregated_compliance.values()) // len(aggregated_compliance) if aggregated_compliance else 0
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1D6F5E 0%, #2A9D8F 100%); 
                        padding: 20px; border-radius: 15px; text-align: center; color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-weight: 500; opacity: 0.9;">Compliance</h4>
                <h1 style="font-size: 48px; margin: 10px 0; color: white;">{compliance_score}%</h1>
                <small style="opacity: 0.8;">{len(aggregated_compliance)} frameworks</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Total Findings - AMBER instead of RED
        total_findings = sum(s.findings_count for s in statuses.values())
        critical_findings = sum(s.critical_count for s in statuses.values())
        
        with col3:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #B45309 0%, #D97706 100%); 
                        padding: 20px; border-radius: 15px; text-align: center; color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-weight: 500; opacity: 0.9;">Findings</h4>
                <h1 style="font-size: 48px; margin: 10px 0; color: white;">{total_findings}</h1>
                <small style="opacity: 0.8;">⚠️ {critical_findings} Critical</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Trend
        trend_icon = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(trend.get("direction", "stable"), "➡️")
        
        with col4:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #34495E 0%, #5D6D7E 100%); 
                        padding: 20px; border-radius: 15px; text-align: center; color: white;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h4 style="margin: 0; font-weight: 500; opacity: 0.9;">Trend</h4>
                <h1 style="font-size: 48px; margin: 10px 0; color: white;">{trend_icon}</h1>
                <small style="opacity: 0.8;">{trend.get("direction", "stable").title()}</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Module health cards
        st.markdown("### 🏥 Module Health Status")
        
        cols = st.columns(len(statuses))
        
        for idx, (module, status) in enumerate(statuses.items()):
            # Professional colors for health status - no bright red
            health_color = {
                HealthStatus.HEALTHY: "#2E7D32",    # Forest green
                HealthStatus.WARNING: "#F57C00",    # Orange
                HealthStatus.CRITICAL: "#B45309",   # Amber (was red)
                HealthStatus.UNKNOWN: "#757575"     # Gray
            }.get(status.health, "#757575")
            
            health_icon = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.WARNING: "⚠️",
                HealthStatus.CRITICAL: "🔶",  # Changed from red circle
                HealthStatus.UNKNOWN: "❓"
            }.get(status.health, "❓")
            
            config = MODULE_CONFIG.get(module, {"icon": "📋", "color": "#666"})
            
            with cols[idx]:
                st.markdown(f"""
                <div style="border: 1px solid #E0E0E0; border-left: 4px solid {health_color}; 
                            border-radius: 8px; padding: 15px; 
                            text-align: center; background: #FAFAFA; min-height: 180px;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-size: 28px;">{config['icon']}</div>
                    <h4 style="margin: 5px 0; font-size: 12px; color: #333;">{module.value}</h4>
                    <div style="font-size: 24px; margin: 10px 0;">{health_icon}</div>
                    <div style="font-size: 11px; color: #666;">
                        Score: {status.overall_score}%<br>
                        Findings: {status.findings_count}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # WAF Pillar summary bar
        st.markdown("---")
        st.markdown("### 📊 WAF Pillar Summary")
        
        cols = st.columns(6)
        for idx, pillar in enumerate(WAFPillar):
            score = aggregated_waf.get(pillar, 0)
            config = PILLAR_CONFIG.get(pillar, {"icon": "📋", "color": "#666"})
            # Professional score colors - amber instead of red
            score_color = "#2E7D32" if score >= 80 else "#F57C00" if score >= 60 else "#92400E" if score > 0 else "#757575"
            
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 10px; border-left: 4px solid {config['color']}; 
                            background: #FAFAFA; border-radius: 0 8px 8px 0;
                            box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                    <div style="font-size: 20px;">{config['icon']}</div>
                    <div style="font-size: 24px; font-weight: 600; color: {score_color};">{score}</div>
                    <div style="font-size: 9px; color: #666;">{pillar.value[:12]}</div>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def _render_waf_pillars(statuses: Dict, aggregated_waf: Dict):
        """Render WAF pillars detail tab"""
        
        st.markdown("### 📈 WAF Pillar Analysis")
        
        # Overall pillar scores
        cols = st.columns(6)
        for idx, pillar in enumerate(WAFPillar):
            score = aggregated_waf.get(pillar, 0)
            config = PILLAR_CONFIG.get(pillar, {"icon": "📋", "color": "#666"})
            # Professional score colors - amber instead of red
            score_color = "#2E7D32" if score >= 80 else "#F57C00" if score >= 60 else "#92400E" if score > 0 else "#757575"
            
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; border: 1px solid #E0E0E0; 
                            border-left: 4px solid {config['color']};
                            border-radius: 8px; background: #FAFAFA;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <div style="font-size: 32px;">{config['icon']}</div>
                    <h3 style="font-size: 40px; color: {score_color}; margin: 10px 0;">{score}</h3>
                    <div style="font-size: 11px; font-weight: 500; color: #555;">{pillar.value}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Pillar scores by module
        st.markdown("### 📋 Pillar Scores by Module")
        
        # Create table data
        table_data = {"Module": []}
        for pillar in WAFPillar:
            table_data[pillar.value[:10]] = []
        
        for module, status in statuses.items():
            if status.waf_scores:
                table_data["Module"].append(module.value)
                for pillar in WAFPillar:
                    score = status.waf_scores.get(pillar, 0)
                    table_data[pillar.value[:10]].append(f"{score}%")
        
        if table_data["Module"]:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No WAF scores available. Run assessments in individual modules.")
        
        # Improvement suggestions
        st.markdown("---")
        st.markdown("### 💡 Improvement Suggestions")
        
        sorted_pillars = sorted(aggregated_waf.items(), key=lambda x: x[1])
        
        for pillar, score in sorted_pillars[:3]:
            if score < 80:
                config = PILLAR_CONFIG.get(pillar, {"icon": "📋", "color": "#666"})
                st.markdown(f"""
                <div style="padding: 15px; background: #FEF3C7; border-left: 4px solid {config['color']}; 
                            border-radius: 0 8px 8px 0; margin-bottom: 10px;">
                    <h4>{config['icon']} {pillar.value} (Score: {score}%)</h4>
                    <p>This pillar needs improvement. Review findings and implement recommendations.</p>
                </div>
                """, unsafe_allow_html=True)
    
    @staticmethod
    def _render_compliance(statuses: Dict, aggregated_compliance: Dict):
        """Render compliance detail tab"""
        
        st.markdown("### 🔒 Compliance Framework Status")
        
        if not aggregated_compliance:
            st.info("No compliance data available. Run assessments with compliance frameworks selected.")
            return
        
        # Framework cards - professional colors
        cols = st.columns(4)
        for idx, (framework, score) in enumerate(aggregated_compliance.items()):
            # Professional colors - amber instead of red
            color = "#2E7D32" if score >= 80 else "#F57C00" if score >= 60 else "#92400E"
            status_icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "🔶"
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div style="padding: 20px; background: #FAFAFA; border-radius: 8px; 
                            border-left: 4px solid {color}; margin-bottom: 15px; text-align: center;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0; font-size: 12px; color: #333;">{framework}</h4>
                    <h2 style="color: {color}; margin: 10px 0;">{score}%</h2>
                    <div style="font-size: 20px;">{status_icon}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Compliance heatmap by module
        st.markdown("### 📊 Compliance by Module")
        
        table_data = {"Module": []}
        frameworks = list(aggregated_compliance.keys())[:6]  # Limit to 6 for display
        for fw in frameworks:
            table_data[fw[:8]] = []
        
        for module, status in statuses.items():
            if status.compliance_scores:
                table_data["Module"].append(module.value)
                for fw in frameworks:
                    score = status.compliance_scores.get(fw, "-")
                    if isinstance(score, int):
                        table_data[fw[:8]].append(f"{score}%")
                    else:
                        table_data[fw[:8]].append("-")
        
        if table_data["Module"]:
            import pandas as pd
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Compliance gaps
        st.markdown("---")
        st.markdown("### 🚨 Critical Compliance Gaps")
        
        gaps_found = False
        for framework, score in sorted(aggregated_compliance.items(), key=lambda x: x[1]):
            if score < 70:
                gaps_found = True
                st.warning(f"**{framework}**: Score {score}% - Below acceptable threshold")
        
        if not gaps_found:
            st.success("✅ All compliance frameworks meet minimum thresholds!")
    
    @staticmethod
    def _render_actions(priority_actions: List[PriorityAction], statuses: Dict):
        """Render priority actions tab"""
        
        st.markdown("### 🎯 Priority Action Queue")
        
        if not priority_actions:
            st.success("✅ No critical actions required at this time!")
            return
        
        for action in priority_actions:
            # Professional severity colors - amber instead of red
            severity_color = {
                "CRITICAL": "#B45309",   # Amber
                "HIGH": "#D97706",       # Light amber
                "MEDIUM": "#F59E0B"      # Yellow
            }.get(action.severity, "#6B7280")
            
            severity_icon = {
                "CRITICAL": "🔶",
                "HIGH": "🟠",
                "MEDIUM": "🟡"
            }.get(action.severity, "⚪")
            
            with st.expander(f"{severity_icon} [{action.source_module.value}] {action.title}", expanded=action.severity == "CRITICAL"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Description:** {action.description}")
                    st.markdown(f"**Impact:** {action.impact}")
                    st.markdown(f"**Action Required:** {action.action_required}")
                
                with col2:
                    st.markdown(f"""
                    <div style="background: {severity_color}; color: white; padding: 10px; 
                                border-radius: 5px; text-align: center;">
                        <b>{action.severity}</b>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Quick stats
        st.markdown("---")
        st.markdown("### 📊 Action Summary")
        
        col1, col2, col3 = st.columns(3)
        
        critical = len([a for a in priority_actions if a.severity == "CRITICAL"])
        high = len([a for a in priority_actions if a.severity == "HIGH"])
        medium = len([a for a in priority_actions if a.severity == "MEDIUM"])
        
        col1.metric("🔶 Critical Actions", critical)
        col2.metric("🟠 High Priority", high)
        col3.metric("🟡 Medium Priority", medium)
    
    @staticmethod
    def _render_reports(summary: ExecutiveSummary, generator: ExecutiveSummaryGenerator):
        """Render reports tab"""
        
        st.markdown("### 📄 Executive Reports")
        
        # Summary preview
        st.markdown("#### 📋 Executive Summary Preview")
        
        col1, col2, col3 = st.columns(3)
        
        # Professional posture colors - amber instead of red
        posture_color = {
            "Strong": "#2E7D32",
            "Moderate": "#F57C00",
            "Needs Improvement": "#92400E"
        }.get(summary.overall_posture, "#757575")
        
        with col1:
            st.markdown(f"""
            <div style="padding: 20px; background: #FAFAFA; border-radius: 8px; 
                        border-left: 4px solid {posture_color};
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h4 style="color: #333; margin: 0 0 10px 0;">Overall Posture</h4>
                <h2 style="color: {posture_color}; margin: 0;">{summary.overall_posture}</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="padding: 20px; background: #FAFAFA; border-radius: 8px; 
                        border-left: 4px solid #2C3E50;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h4 style="color: #333; margin: 0 0 10px 0;">WAF Score</h4>
                <h2 style="color: #2C3E50; margin: 0;">{summary.waf_score}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="padding: 20px; background: #FAFAFA; border-radius: 8px; 
                        border-left: 4px solid #1D6F5E;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                <h4 style="color: #333; margin: 0 0 10px 0;">Compliance Score</h4>
                <h2 style="color: #1D6F5E; margin: 0;">{summary.compliance_score}%</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # Top risks
        st.markdown("---")
        st.markdown("#### ⚠️ Top Risks")
        
        for risk in summary.top_risks[:5]:
            # Professional impact colors - amber instead of red
            impact_color = "#92400E" if risk['impact'] == "High" else "#F57C00"
            st.markdown(f"• **{risk['category']}**: {risk['item']} ({risk['score']}%) - <span style='color:{impact_color}'>Impact: {risk['impact']}</span>", unsafe_allow_html=True)
        
        # Recommendations
        st.markdown("---")
        st.markdown("#### 💡 Recommendations")
        
        for rec in summary.recommendations:
            st.markdown(f"• {rec}")
        
        # Export buttons
        st.markdown("---")
        st.markdown("#### 📥 Export Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # PDF Export
            try:
                pdf_data = generator.generate_pdf_report(summary)
                st.download_button(
                    "📥 Download PDF Report",
                    data=pdf_data,
                    file_name=f"security_summary_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning(f"PDF generation requires reportlab: {str(e)[:50]}")
                # Text fallback
                text_report = generator._generate_text_report(summary)
                st.download_button(
                    "📥 Download Text Report",
                    data=text_report,
                    file_name=f"security_summary_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        with col2:
            # JSON Export
            json_data = {
                "generated_at": summary.generated_at.isoformat(),
                "overall_posture": summary.overall_posture,
                "waf_score": summary.waf_score,
                "compliance_score": summary.compliance_score,
                "findings_summary": summary.findings_summary,
                "top_risks": summary.top_risks,
                "recommendations": summary.recommendations,
                "trend": summary.trend_direction,
                "modules_assessed": summary.modules_assessed
            }
            
            st.download_button(
                "📥 Download JSON Data",
                data=json.dumps(json_data, indent=2),
                file_name=f"security_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col3:
            # CSV Export (for findings)
            csv_data = "Category,Item,Score,Impact\n"
            for risk in summary.top_risks:
                csv_data += f"{risk['category']},{risk['item']},{risk['score']},{risk['impact']}\n"
            
            st.download_button(
                "📥 Download CSV Risks",
                data=csv_data,
                file_name=f"security_risks_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )


# ============================================================================
# ENTRY POINT
# ============================================================================

def render_unified_dashboard():
    """Main entry point"""
    UnifiedDashboard.render()


if __name__ == "__main__":
    st.set_page_config(page_title="Unified Security Dashboard", layout="wide")
    render_unified_dashboard()
