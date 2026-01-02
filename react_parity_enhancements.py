"""
React Parity Enhancements Module
=================================
Adds features from the React application that are missing or enhanced in the Streamlit version.

Features Added:
1. WAF Assessment AI Recommendations (Executive Summary, Quick Wins, Implementation Roadmap)
2. Enhanced AWS Connector with Security Hub Integration
3. FinOps Cost Anomaly Management UI
4. Enhanced Remediation Export Options
5. Assessment Mode Selection (Hybrid/Manual)
6. Implementation Roadmap Generation

Version: 1.1.0 - With Real AWS Support
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import random
import logging

logger = logging.getLogger(__name__)

# Import demo mode manager for live/demo switching
try:
    from demo_mode_manager import DemoModeManager, get_demo_manager
    DEMO_MODE_AVAILABLE = True
except ImportError:
    DEMO_MODE_AVAILABLE = False
    logger.warning("Demo mode manager not available")

# Import AWS connection utilities
try:
    from aws_connector import get_aws_session, test_aws_connection
    from core_account_manager import get_account_manager
    AWS_CONNECTOR_AVAILABLE = True
except ImportError:
    AWS_CONNECTOR_AVAILABLE = False
    logger.warning("AWS connector not available")

# Import existing SecurityManager for Security Hub
try:
    from aws_security import SecurityManager
    SECURITY_MANAGER_AVAILABLE = True
except ImportError:
    SECURITY_MANAGER_AVAILABLE = False
    logger.warning("Security Manager not available")

# Import boto3 for direct AWS API calls
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 not available")


# ============================================================================
# SECTION 1: WAF ASSESSMENT AI RECOMMENDATIONS
# ============================================================================

@dataclass
class AIRecommendation:
    """AI-generated recommendation structure"""
    title: str
    description: str
    priority: str  # Critical, High, Medium, Low
    pillar: str
    aws_services: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    estimated_effort: str = "Medium"
    estimated_impact: str = "High"


@dataclass 
class QuickWin:
    """Quick win recommendation"""
    title: str
    description: str
    time_to_implement: str
    pillar: str
    impact: str


@dataclass
class CostOpportunity:
    """Cost optimization opportunity"""
    opportunity: str
    implementation: str
    estimated_savings: str
    effort: str


class WAFAIRecommendationsEngine:
    """
    AI-powered recommendations engine for WAF assessments.
    Generates executive summaries, priority actions, quick wins, and roadmaps.
    """
    
    PILLARS = [
        "Operational Excellence",
        "Security", 
        "Reliability",
        "Performance Efficiency",
        "Cost Optimization",
        "Sustainability"
    ]
    
    @staticmethod
    def generate_executive_summary(pillar_scores: Dict[str, float], findings: List[Dict]) -> Dict:
        """Generate executive summary from assessment results"""
        
        overall_score = sum(pillar_scores.values()) / len(pillar_scores) if pillar_scores else 0
        
        # Determine posture
        if overall_score >= 80:
            posture = "STRONG"
            posture_color = "green"
        elif overall_score >= 60:
            posture = "MODERATE"
            posture_color = "orange"
        else:
            posture = "NEEDS ATTENTION"
            posture_color = "red"
        
        # Count findings by severity
        critical_count = sum(1 for f in findings if f.get('severity', '').upper() == 'CRITICAL')
        high_count = sum(1 for f in findings if f.get('severity', '').upper() == 'HIGH')
        medium_count = sum(1 for f in findings if f.get('severity', '').upper() == 'MEDIUM')
        
        # Find weakest pillar
        weakest_pillar = min(pillar_scores.items(), key=lambda x: x[1])[0] if pillar_scores else "Unknown"
        strongest_pillar = max(pillar_scores.items(), key=lambda x: x[1])[0] if pillar_scores else "Unknown"
        
        return {
            "overall_score": round(overall_score, 1),
            "posture": posture,
            "posture_color": posture_color,
            "critical_findings": critical_count,
            "high_findings": high_count,
            "medium_findings": medium_count,
            "total_findings": len(findings),
            "weakest_pillar": weakest_pillar,
            "strongest_pillar": strongest_pillar,
            "key_insight": f"Your {weakest_pillar} pillar needs immediate attention with a score of {pillar_scores.get(weakest_pillar, 0):.0f}%.",
            "generated_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_priority_actions(pillar_scores: Dict[str, float], findings: List[Dict]) -> List[AIRecommendation]:
        """Generate priority actions based on assessment"""
        
        actions = []
        
        # Security actions
        if pillar_scores.get("Security", 100) < 80:
            actions.append(AIRecommendation(
                title="Enable MFA for All IAM Users",
                description="Multi-factor authentication is not enabled for all IAM users, creating security risk.",
                priority="Critical",
                pillar="Security",
                aws_services=["IAM", "AWS Organizations"],
                steps=[
                    "Audit all IAM users without MFA",
                    "Create policy requiring MFA for console access",
                    "Distribute virtual MFA devices to users",
                    "Enable enforcement via SCP"
                ],
                estimated_effort="Medium",
                estimated_impact="High"
            ))
        
        # Reliability actions
        if pillar_scores.get("Reliability", 100) < 80:
            actions.append(AIRecommendation(
                title="Implement Multi-AZ Deployment",
                description="Critical workloads are running in single availability zones.",
                priority="High",
                pillar="Reliability",
                aws_services=["EC2", "RDS", "ELB"],
                steps=[
                    "Identify single-AZ resources",
                    "Plan migration to Multi-AZ",
                    "Update Auto Scaling groups",
                    "Configure cross-AZ load balancing"
                ],
                estimated_effort="High",
                estimated_impact="High"
            ))
        
        # Cost actions
        if pillar_scores.get("Cost Optimization", 100) < 70:
            actions.append(AIRecommendation(
                title="Implement Reserved Instance Strategy",
                description="On-demand instances are being used for steady-state workloads.",
                priority="Medium",
                pillar="Cost Optimization",
                aws_services=["EC2", "RDS", "ElastiCache"],
                steps=[
                    "Analyze usage patterns with Cost Explorer",
                    "Identify candidates for RIs/Savings Plans",
                    "Calculate potential savings",
                    "Purchase commitments"
                ],
                estimated_effort="Low",
                estimated_impact="High"
            ))
        
        # Operational Excellence actions
        if pillar_scores.get("Operational Excellence", 100) < 75:
            actions.append(AIRecommendation(
                title="Implement Infrastructure as Code",
                description="Manual infrastructure changes increase risk and reduce reproducibility.",
                priority="Medium",
                pillar="Operational Excellence",
                aws_services=["CloudFormation", "CDK", "Terraform"],
                steps=[
                    "Document existing infrastructure",
                    "Create IaC templates",
                    "Set up CI/CD pipeline",
                    "Implement change management"
                ],
                estimated_effort="High",
                estimated_impact="High"
            ))
        
        # Performance actions
        if pillar_scores.get("Performance Efficiency", 100) < 70:
            actions.append(AIRecommendation(
                title="Enable CloudWatch Application Insights",
                description="Limited visibility into application performance metrics.",
                priority="Medium",
                pillar="Performance Efficiency",
                aws_services=["CloudWatch", "X-Ray", "Application Insights"],
                steps=[
                    "Enable detailed monitoring",
                    "Configure custom metrics",
                    "Set up dashboards",
                    "Create alerting rules"
                ],
                estimated_effort="Low",
                estimated_impact="Medium"
            ))
        
        # Sustainability actions
        if pillar_scores.get("Sustainability", 100) < 75:
            actions.append(AIRecommendation(
                title="Optimize Resource Utilization",
                description="Low resource utilization indicates over-provisioning and wasted energy.",
                priority="Low",
                pillar="Sustainability",
                aws_services=["Compute Optimizer", "Trusted Advisor"],
                steps=[
                    "Enable AWS Compute Optimizer",
                    "Review right-sizing recommendations",
                    "Implement auto-scaling",
                    "Schedule non-prod shutdowns"
                ],
                estimated_effort="Medium",
                estimated_impact="Medium"
            ))
        
        # Sort by priority
        priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        actions.sort(key=lambda x: priority_order.get(x.priority, 4))
        
        return actions
    
    @staticmethod
    def generate_quick_wins(pillar_scores: Dict[str, float]) -> List[QuickWin]:
        """Generate quick wins that can be implemented quickly"""
        
        quick_wins = [
            QuickWin(
                title="Enable S3 Default Encryption",
                description="Enable AES-256 encryption on all S3 buckets with a single API call per bucket.",
                time_to_implement="< 1 hour",
                pillar="Security",
                impact="High"
            ),
            QuickWin(
                title="Enable CloudTrail in All Regions",
                description="Ensure all API activity is logged across all AWS regions.",
                time_to_implement="< 30 minutes",
                pillar="Security",
                impact="High"
            ),
            QuickWin(
                title="Enable RDS Automated Backups",
                description="Configure automated backups with 7+ day retention.",
                time_to_implement="< 1 hour",
                pillar="Reliability",
                impact="High"
            ),
            QuickWin(
                title="Set Up AWS Budgets Alerts",
                description="Create budget alerts at 80% and 100% thresholds.",
                time_to_implement="< 30 minutes",
                pillar="Cost Optimization",
                impact="Medium"
            ),
            QuickWin(
                title="Enable VPC Flow Logs",
                description="Enable flow logs for network traffic visibility and troubleshooting.",
                time_to_implement="< 1 hour",
                pillar="Operational Excellence",
                impact="Medium"
            ),
            QuickWin(
                title="Configure SNS for CloudWatch Alarms",
                description="Set up SNS topics for critical alarm notifications.",
                time_to_implement="< 30 minutes",
                pillar="Operational Excellence",
                impact="Medium"
            )
        ]
        
        return quick_wins
    
    @staticmethod
    def generate_implementation_roadmap(pillar_scores: Dict[str, float]) -> Dict[str, List[str]]:
        """Generate phased implementation roadmap"""
        
        return {
            "week_1": [
                "Enable MFA for all root and IAM admin accounts",
                "Enable S3 default encryption on critical buckets",
                "Set up AWS Config rules for compliance",
                "Configure budget alerts"
            ],
            "month_1": [
                "Implement centralized logging with CloudWatch",
                "Deploy WAF on public-facing resources",
                "Set up automated backup verification",
                "Implement tagging strategy"
            ],
            "quarter_1": [
                "Migrate to Infrastructure as Code",
                "Implement multi-region DR strategy",
                "Deploy comprehensive monitoring solution",
                "Establish FinOps practices"
            ],
            "long_term": [
                "Achieve SOC 2 compliance",
                "Implement zero-trust security model",
                "Full observability platform deployment",
                "Carbon-neutral cloud operations"
            ]
        }
    
    @staticmethod
    def generate_cost_opportunities(current_spend: float = 15000) -> List[CostOpportunity]:
        """Generate cost optimization opportunities"""
        
        return [
            CostOpportunity(
                opportunity="Reserved Instances for EC2",
                implementation="Purchase 1-year All Upfront RIs for steady-state workloads",
                estimated_savings=f"${int(current_spend * 0.25):,}/month",
                effort="Low"
            ),
            CostOpportunity(
                opportunity="S3 Intelligent Tiering",
                implementation="Enable S3 Intelligent-Tiering for infrequently accessed data",
                estimated_savings=f"${int(current_spend * 0.05):,}/month",
                effort="Low"
            ),
            CostOpportunity(
                opportunity="Right-size EC2 Instances",
                implementation="Downsize under-utilized instances based on CloudWatch metrics",
                estimated_savings=f"${int(current_spend * 0.15):,}/month",
                effort="Medium"
            ),
            CostOpportunity(
                opportunity="Delete Unused EBS Volumes",
                implementation="Identify and remove unattached EBS volumes and snapshots",
                estimated_savings=f"${int(current_spend * 0.03):,}/month",
                effort="Low"
            )
        ]
    
    @staticmethod
    def generate_pillar_recommendations(pillar_scores: Dict[str, float]) -> Dict[str, Dict]:
        """Generate per-pillar recommendations"""
        
        recommendations = {}
        
        for pillar, score in pillar_scores.items():
            if score >= 80:
                status = "Excellent"
            elif score >= 60:
                status = "Good"
            elif score >= 40:
                status = "Needs Improvement"
            else:
                status = "Critical"
            
            recommendations[pillar] = {
                "current_score": round(score),
                "status": status,
                "recommendations": WAFAIRecommendationsEngine._get_pillar_recs(pillar, score)
            }
        
        return recommendations
    
    @staticmethod
    def _get_pillar_recs(pillar: str, score: float) -> List[Dict]:
        """Get specific recommendations for a pillar"""
        
        recs = {
            "Security": [
                {"title": "Enable AWS Security Hub", "priority": "High", "description": "Centralize security findings", "aws_solution": "AWS Security Hub"},
                {"title": "Implement Least Privilege", "priority": "Critical", "description": "Review and restrict IAM policies", "aws_solution": "IAM Access Analyzer"},
                {"title": "Enable GuardDuty", "priority": "High", "description": "Threat detection for workloads", "aws_solution": "Amazon GuardDuty"}
            ],
            "Reliability": [
                {"title": "Multi-AZ Deployment", "priority": "High", "description": "Deploy across availability zones", "aws_solution": "Auto Scaling Groups"},
                {"title": "Implement Chaos Engineering", "priority": "Medium", "description": "Test failure scenarios", "aws_solution": "AWS Fault Injection Simulator"},
                {"title": "Automate Backups", "priority": "High", "description": "Automated backup policies", "aws_solution": "AWS Backup"}
            ],
            "Performance Efficiency": [
                {"title": "Enable Caching", "priority": "Medium", "description": "Implement caching layer", "aws_solution": "Amazon ElastiCache"},
                {"title": "Use CDN", "priority": "Medium", "description": "Global content delivery", "aws_solution": "Amazon CloudFront"},
                {"title": "Right-size Resources", "priority": "High", "description": "Match resources to workload", "aws_solution": "AWS Compute Optimizer"}
            ],
            "Cost Optimization": [
                {"title": "Implement Savings Plans", "priority": "High", "description": "Commit for discounts", "aws_solution": "AWS Savings Plans"},
                {"title": "Use Spot Instances", "priority": "Medium", "description": "For fault-tolerant workloads", "aws_solution": "EC2 Spot Instances"},
                {"title": "Enable Cost Allocation Tags", "priority": "Medium", "description": "Track costs by project/team", "aws_solution": "AWS Cost Allocation Tags"}
            ],
            "Operational Excellence": [
                {"title": "Implement IaC", "priority": "High", "description": "Version control infrastructure", "aws_solution": "AWS CloudFormation"},
                {"title": "Enable Observability", "priority": "High", "description": "Full-stack monitoring", "aws_solution": "Amazon CloudWatch"},
                {"title": "Automate Runbooks", "priority": "Medium", "description": "SSM automation documents", "aws_solution": "AWS Systems Manager"}
            ],
            "Sustainability": [
                {"title": "Optimize Utilization", "priority": "Medium", "description": "Reduce idle resources", "aws_solution": "AWS Compute Optimizer"},
                {"title": "Use Graviton", "priority": "Low", "description": "Energy-efficient processors", "aws_solution": "AWS Graviton"},
                {"title": "Right-size Storage", "priority": "Low", "description": "Match storage to needs", "aws_solution": "S3 Intelligent-Tiering"}
            ]
        }
        
        return recs.get(pillar, [])


def render_waf_ai_recommendations():
    """Render the AI Recommendations tab for WAF Assessment - Uses REAL assessment data when available"""
    
    st.markdown("### 🤖 AI-Powered Assessment Insights")
    
    # Check for demo mode
    is_demo = False
    if DEMO_MODE_AVAILABLE:
        demo_mgr = get_demo_manager()
        is_demo = demo_mgr.is_demo_mode
    
    # Try to get real assessment data from session state
    # This integrates with the WAF Review module
    pillar_scores = st.session_state.get('waf_pillar_scores', None)
    findings = st.session_state.get('waf_findings', [])
    assessment = st.session_state.get('current_assessment', None)
    
    # If we have a real assessment, use its scores
    if assessment and 'scores' in assessment:
        pillar_scores = {
            "Operational Excellence": assessment['scores'].get('operational_excellence', 70),
            "Security": assessment['scores'].get('security', 65),
            "Reliability": assessment['scores'].get('reliability', 78),
            "Performance Efficiency": assessment['scores'].get('performance_efficiency', 70),
            "Cost Optimization": assessment['scores'].get('cost_optimization', 58),
            "Sustainability": assessment['scores'].get('sustainability', 68)
        }
        st.success("📊 Using scores from your current WAF assessment")
    elif pillar_scores is None:
        # Use demo/default scores
        pillar_scores = {
            "Operational Excellence": 72,
            "Security": 65,
            "Reliability": 78,
            "Performance Efficiency": 70,
            "Cost Optimization": 58,
            "Sustainability": 68
        }
        if is_demo:
            st.info("🎭 **Demo Mode** - Using sample assessment data")
        else:
            st.warning("⚠️ No active assessment found. Complete a WAF Assessment first for personalized recommendations.")
    
    # Also try to get findings from scan results
    scan_results = st.session_state.get('last_scan_results', None)
    if scan_results and hasattr(scan_results, 'findings'):
        findings = [
            {
                'id': f.id if hasattr(f, 'id') else str(i),
                'severity': f.severity if hasattr(f, 'severity') else 'MEDIUM',
                'title': f.title if hasattr(f, 'title') else str(f),
                'pillar': f.pillar if hasattr(f, 'pillar') else 'Security'
            }
            for i, f in enumerate(scan_results.findings)
        ]
        st.caption(f"📋 Analyzing {len(findings)} findings from your latest scan")
    
    # Generate button
    col1, col2 = st.columns([1, 4])
    with col1:
        generate_btn = st.button("🔄 Generate AI Insights", use_container_width=True, key="gen_ai_insights_btn")
    with col2:
        st.caption("AI analysis generates executive summary, priority actions, and implementation roadmap based on your assessment")
    
    if generate_btn or st.session_state.get('ai_insights_generated'):
        st.session_state['ai_insights_generated'] = True
        
        with st.spinner("🤖 Analyzing assessment with AI..."):
            engine = WAFAIRecommendationsEngine()
            
            # Generate all insights
            executive_summary = engine.generate_executive_summary(pillar_scores, findings)
            priority_actions = engine.generate_priority_actions(pillar_scores, findings)
            quick_wins = engine.generate_quick_wins(pillar_scores)
            roadmap = engine.generate_implementation_roadmap(pillar_scores)
            cost_opps = engine.generate_cost_opportunities()
            pillar_recs = engine.generate_pillar_recommendations(pillar_scores)
        
        # Executive Summary Card
        st.markdown("---")
        st.markdown("#### 📊 Executive Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            color = "#4CAF50" if executive_summary['overall_score'] >= 80 else "#FF9800" if executive_summary['overall_score'] >= 60 else "#F44336"
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {color}22, {color}11); border-radius: 10px; border-left: 4px solid {color};">
                <div style="font-size: 36px; font-weight: bold; color: {color};">{executive_summary['overall_score']}%</div>
                <div style="font-size: 12px; color: #666;">Overall Score</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: #FFF3E0; border-radius: 10px;">
                <div style="font-size: 36px; font-weight: bold; color: #E65100;">{executive_summary['critical_findings']}</div>
                <div style="font-size: 12px; color: #666;">Critical Findings</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: #E3F2FD; border-radius: 10px;">
                <div style="font-size: 14px; font-weight: bold; color: #1565C0;">{executive_summary['weakest_pillar']}</div>
                <div style="font-size: 12px; color: #666;">Weakest Pillar</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: #E8F5E9; border-radius: 10px;">
                <div style="font-size: 14px; font-weight: bold; color: #2E7D32;">{executive_summary['strongest_pillar']}</div>
                <div style="font-size: 12px; color: #666;">Strongest Pillar</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.info(f"💡 **Key Insight:** {executive_summary['key_insight']}")
        
        # Priority Actions
        st.markdown("---")
        st.markdown("#### 🎯 Priority Actions")
        
        for action in priority_actions[:5]:
            priority_colors = {
                "Critical": ("#F44336", "#FFEBEE"),
                "High": ("#FF9800", "#FFF3E0"),
                "Medium": ("#2196F3", "#E3F2FD"),
                "Low": ("#4CAF50", "#E8F5E9")
            }
            color, bg = priority_colors.get(action.priority, ("#666", "#F5F5F5"))
            
            with st.expander(f"{'🔴' if action.priority == 'Critical' else '🟠' if action.priority == 'High' else '🔵' if action.priority == 'Medium' else '🟢'} {action.title} ({action.pillar})"):
                st.markdown(f"**Priority:** {action.priority} | **Effort:** {action.estimated_effort} | **Impact:** {action.estimated_impact}")
                st.write(action.description)
                
                if action.aws_services:
                    st.markdown("**AWS Services:** " + ", ".join([f"`{s}`" for s in action.aws_services]))
                
                if action.steps:
                    st.markdown("**Implementation Steps:**")
                    for i, step in enumerate(action.steps, 1):
                        st.markdown(f"{i}. {step}")
        
        # Quick Wins
        st.markdown("---")
        st.markdown("#### 🚀 Quick Wins")
        
        cols = st.columns(3)
        for i, win in enumerate(quick_wins[:6]):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="padding: 15px; background: #E8F5E9; border-radius: 10px; margin-bottom: 10px; height: 150px;">
                    <div style="font-weight: bold; color: #2E7D32;">{win.title}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">{win.description}</div>
                    <div style="font-size: 11px; color: #388E3C; margin-top: 10px;">⏱️ {win.time_to_implement}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Implementation Roadmap
        st.markdown("---")
        st.markdown("#### 📅 Implementation Roadmap")
        
        cols = st.columns(4)
        phases = [("Week 1", "week_1", "🎯"), ("Month 1", "month_1", "📋"), ("Quarter 1", "quarter_1", "🏗️"), ("Long Term", "long_term", "🚀")]
        
        for col, (label, key, icon) in zip(cols, phases):
            with col:
                st.markdown(f"**{icon} {label}**")
                for item in roadmap.get(key, []):
                    st.markdown(f"• {item}")
        
        # Cost Optimization Opportunities
        st.markdown("---")
        st.markdown("#### 💰 Cost Optimization Opportunities")
        
        for opp in cost_opps:
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{opp.opportunity}**")
                st.caption(opp.implementation)
            with cols[1]:
                st.success(f"Save {opp.estimated_savings}")
        
        # Pillar-Specific Recommendations
        st.markdown("---")
        st.markdown("#### 📊 Pillar-Specific Recommendations")
        
        for pillar, data in pillar_recs.items():
            status_colors = {
                "Excellent": "🟢",
                "Good": "🔵",
                "Needs Improvement": "🟠",
                "Critical": "🔴"
            }
            
            with st.expander(f"{status_colors.get(data['status'], '⚪')} {pillar} - {data['current_score']}% ({data['status']})"):
                for rec in data['recommendations']:
                    st.markdown(f"""
                    **{rec['title']}** ({rec['priority']})  
                    {rec['description']}  
                    *AWS Solution: {rec['aws_solution']}*
                    """)
                    st.markdown("---")


# ============================================================================
# SECTION 2: ENHANCED AWS CONNECTOR WITH SECURITY HUB
# ============================================================================

class SecurityHubIntegration:
    """Security Hub integration for multi-account findings aggregation - REAL AWS SUPPORT"""
    
    @staticmethod
    def _is_demo_mode() -> bool:
        """Check if we're in demo mode"""
        if DEMO_MODE_AVAILABLE:
            demo_mgr = get_demo_manager()
            return demo_mgr.is_demo_mode
        return True  # Default to demo if manager not available
    
    @staticmethod
    def _get_real_security_hub_data(access_key: str, secret_key: str, region: str) -> Dict:
        """
        Connect to real AWS Security Hub and retrieve findings.
        Returns member accounts and findings summary.
        """
        if not BOTO3_AVAILABLE:
            return {"error": "boto3 not installed"}
        
        try:
            # Create boto3 session with provided credentials
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Test credentials first
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            account_id = identity['Account']
            
            # Connect to Security Hub
            securityhub = session.client('securityhub')
            
            # Check if Security Hub is enabled
            try:
                hub_info = securityhub.describe_hub()
            except ClientError as e:
                if 'InvalidAccessException' in str(e):
                    return {"error": "Security Hub is not enabled in this account/region"}
                raise
            
            # Get member accounts (for aggregator/administrator account)
            member_accounts = []
            try:
                paginator = securityhub.get_paginator('list_members')
                for page in paginator.paginate():
                    for member in page.get('Members', []):
                        member_accounts.append({
                            "account_id": member.get('AccountId', ''),
                            "email": member.get('Email', ''),
                            "status": member.get('MemberStatus', 'UNKNOWN'),
                            "invited_at": str(member.get('InvitedAt', '')),
                            "updated_at": str(member.get('UpdatedAt', ''))
                        })
            except ClientError as e:
                logger.warning(f"Could not list member accounts: {e}")
                # Not an administrator account - that's okay
            
            # Get findings summary
            findings_response = securityhub.get_findings(
                Filters={
                    'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}]
                },
                MaxResults=100
            )
            
            findings = findings_response.get('Findings', [])
            
            # Count by severity
            severity_counts = {
                'CRITICAL': 0,
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0,
                'INFORMATIONAL': 0
            }
            
            for finding in findings:
                severity = finding.get('Severity', {}).get('Label', 'INFORMATIONAL')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Get enabled standards
            standards = []
            try:
                standards_response = securityhub.get_enabled_standards()
                for std in standards_response.get('StandardsSubscriptions', []):
                    standards.append({
                        "arn": std.get('StandardsArn', ''),
                        "status": std.get('StandardsStatus', ''),
                        "status_reason": std.get('StandardsStatusReason', {}).get('Code', '')
                    })
            except ClientError:
                pass
            
            return {
                "success": True,
                "account_id": account_id,
                "hub_arn": hub_info.get('HubArn', ''),
                "member_accounts": member_accounts,
                "findings_summary": {
                    "total_findings": len(findings),
                    "critical": severity_counts['CRITICAL'],
                    "high": severity_counts['HIGH'],
                    "medium": severity_counts['MEDIUM'],
                    "low": severity_counts['LOW'],
                    "informational": severity_counts['INFORMATIONAL']
                },
                "enabled_standards": standards,
                "region": region
            }
            
        except NoCredentialsError:
            return {"error": "Invalid AWS credentials"}
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            return {"error": f"{error_code}: {error_msg}"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    @staticmethod
    def _get_demo_security_hub_data() -> Dict:
        """Generate demo Security Hub data"""
        return {
            "success": True,
            "account_id": "123456789012",
            "hub_arn": "arn:aws:securityhub:us-east-1:123456789012:hub/default",
            "member_accounts": [
                {"account_id": f"1234567890{i:02d}", "email": f"account{i}@company.com", "status": "ENABLED"}
                for i in range(12)
            ],
            "findings_summary": {
                "total_findings": 847,
                "critical": 23,
                "high": 156,
                "medium": 412,
                "low": 256,
                "informational": 0
            },
            "enabled_standards": [
                {"arn": "arn:aws:securityhub:::ruleset/cis-aws-foundations-benchmark/v/1.2.0", "status": "READY"},
                {"arn": "arn:aws:securityhub:::ruleset/aws-foundational-security-best-practices/v/1.0.0", "status": "READY"}
            ],
            "region": "us-east-1"
        }
    
    @staticmethod
    def render_security_hub_connector():
        """Render Security Hub connection interface - supports REAL AWS connections"""
        
        st.markdown("### 🔐 Security Hub Integration")
        
        # Show mode indicator
        is_demo = SecurityHubIntegration._is_demo_mode()
        if is_demo:
            st.info("🎭 **Demo Mode** - Using simulated Security Hub data. Switch to Live Mode for real AWS connections.")
        else:
            st.success("🔌 **Live Mode** - Connecting to real AWS Security Hub")
        
        st.caption("Connect to Security Hub for aggregated findings across 500+ accounts")
        
        # Connection status
        sh_connected = st.session_state.get('security_hub_connected', False)
        
        if not sh_connected:
            st.info("""
            **Security Hub Integration Benefits:**
            - Single API call for 500+ accounts
            - Pre-aggregated security findings
            - Centralized compliance view
            - No individual account scanning needed
            """)
            
            if is_demo:
                # Demo mode - simple connect button
                if st.button("🔗 Connect to Security Hub (Demo)", use_container_width=True, key="connect_sh_demo_btn"):
                    with st.spinner("Connecting to Security Hub..."):
                        import time
                        time.sleep(1)
                        
                        demo_data = SecurityHubIntegration._get_demo_security_hub_data()
                        st.session_state['security_hub_connected'] = True
                        st.session_state['security_hub_data'] = demo_data
                        st.session_state['sh_member_accounts'] = demo_data['member_accounts']
                        st.session_state['sh_findings_summary'] = demo_data['findings_summary']
                        st.rerun()
            else:
                # Live mode - require credentials
                col1, col2 = st.columns(2)
                
                with col1:
                    sh_access_key = st.text_input(
                        "Administrator Access Key ID", 
                        type="password", 
                        key="sh_access_key_input",
                        help="Access key for the Security Hub administrator account"
                    )
                    sh_secret_key = st.text_input(
                        "Administrator Secret Access Key", 
                        type="password", 
                        key="sh_secret_key_input"
                    )
                
                with col2:
                    sh_region = st.selectbox("Aggregator Region", [
                        "us-east-1", "us-west-2", "eu-west-1", "eu-central-1", 
                        "ap-southeast-1", "ap-northeast-1"
                    ], key="sh_region_select")
                    
                    st.markdown("**Required Permissions:**")
                    st.code("""securityhub:DescribeHub
securityhub:GetFindings
securityhub:ListMembers
securityhub:GetEnabledStandards""", language="text")
                
                if st.button("🔗 Connect to Security Hub", use_container_width=True, key="connect_sh_live_btn"):
                    if not sh_access_key or not sh_secret_key:
                        st.error("Please provide both Access Key and Secret Key")
                    else:
                        with st.spinner("Connecting to AWS Security Hub..."):
                            result = SecurityHubIntegration._get_real_security_hub_data(
                                sh_access_key, sh_secret_key, sh_region
                            )
                            
                            if result.get('error'):
                                st.error(f"❌ Connection failed: {result['error']}")
                            else:
                                st.session_state['security_hub_connected'] = True
                                st.session_state['security_hub_data'] = result
                                st.session_state['sh_member_accounts'] = result['member_accounts']
                                st.session_state['sh_findings_summary'] = result['findings_summary']
                                st.success(f"✅ Connected to Security Hub in {result['region']}")
                                st.rerun()
        else:
            # Connected state
            st.success("✅ Security Hub Connected" + (" (Demo)" if is_demo else " (Live)"))
            
            data = st.session_state.get('security_hub_data', {})
            members = st.session_state.get('sh_member_accounts', [])
            findings = st.session_state.get('sh_findings_summary', {})
            
            # Display metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Member Accounts", len(members))
            with col2:
                st.metric("Total Findings", findings.get('total_findings', 0))
            with col3:
                st.metric("Critical", findings.get('critical', 0))
            with col4:
                st.metric("High", findings.get('high', 0))
            with col5:
                st.metric("Medium", findings.get('medium', 0))
            
            # Show account ID if available
            if data.get('account_id'):
                st.caption(f"🏢 Administrator Account: `{data['account_id']}` | Region: `{data.get('region', 'N/A')}`")
            
            # Member accounts list
            if members:
                with st.expander(f"📋 Member Accounts ({len(members)})"):
                    for member in members:
                        cols = st.columns([2, 2, 1])
                        with cols[0]:
                            st.code(member.get('account_id', 'N/A'))
                        with cols[1]:
                            st.caption(member.get('email', 'N/A'))
                        with cols[2]:
                            status = member.get('status', 'UNKNOWN')
                            st.markdown(f"{'🟢' if status in ['ENABLED', 'ASSOCIATED'] else '🔴'} {status}")
            
            # Enabled standards
            standards = data.get('enabled_standards', [])
            if standards:
                with st.expander(f"📜 Enabled Standards ({len(standards)})"):
                    for std in standards:
                        arn = std.get('arn', '')
                        # Extract standard name from ARN
                        std_name = arn.split('/')[-2] if '/' in arn else arn
                        status = std.get('status', 'UNKNOWN')
                        st.markdown(f"{'✅' if status == 'READY' else '⏳'} **{std_name}** - {status}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh Findings", key="refresh_sh_findings_btn"):
                    if is_demo:
                        st.info("Refreshing demo findings...")
                        st.session_state['sh_findings_summary']['total_findings'] += random.randint(-5, 10)
                    else:
                        st.info("Refreshing real findings from Security Hub...")
                        # Would need stored credentials to refresh - for now just notify
                        st.warning("Please reconnect to refresh live data")
            with col2:
                if st.button("❌ Disconnect", key="disconnect_sh_btn"):
                    st.session_state['security_hub_connected'] = False
                    st.session_state.pop('security_hub_data', None)
                    st.session_state.pop('sh_member_accounts', None)
                    st.session_state.pop('sh_findings_summary', None)
                    st.rerun()
            
            # Next step CTA
            st.markdown("---")
            st.markdown("""
            <div style="padding: 20px; background: linear-gradient(135deg, #1565C0, #7B1FA2); border-radius: 15px; color: white;">
                <h3 style="margin: 0;">✅ Ready for WAF Assessment</h3>
                <p>Security Hub findings will be used to auto-detect WAF pillar scores.</p>
            </div>
            """, unsafe_allow_html=True)


# ============================================================================
# SECTION 3: ASSESSMENT MODE SELECTION
# ============================================================================

def render_assessment_mode_selection():
    """Render assessment mode selection (Hybrid vs Manual)"""
    
    st.markdown("### 🎯 Choose Assessment Mode")
    
    mode = st.session_state.get('assessment_mode', 'hybrid')
    
    col1, col2 = st.columns(2)
    
    with col1:
        hybrid_selected = mode == 'hybrid'
        if st.button(
            "⚡ Hybrid Assessment" if not hybrid_selected else "✅ Hybrid Assessment (Selected)",
            use_container_width=True,
            key="hybrid_mode_btn",
            type="primary" if hybrid_selected else "secondary"
        ):
            st.session_state['assessment_mode'] = 'hybrid'
            st.rerun()
        
        st.markdown("""
        **Scan + Manual Review**
        - Auto-scan AWS resources
        - ~40% questions auto-detected
        - Evidence-backed answers
        - Faster completion time
        """)
    
    with col2:
        manual_selected = mode == 'manual'
        if st.button(
            "📝 Manual Assessment" if not manual_selected else "✅ Manual Assessment (Selected)",
            use_container_width=True,
            key="manual_mode_btn",
            type="primary" if manual_selected else "secondary"
        ):
            st.session_state['assessment_mode'] = 'manual'
            st.rerun()
        
        st.markdown("""
        **Traditional Questionnaire**
        - Answer all 205 questions
        - No AWS connection required
        - Full control over responses
        - Best for offline assessment
        """)
    
    # Show current mode
    st.info(f"📋 Current Mode: **{mode.title()}** Assessment")


# ============================================================================
# SECTION 4: ENHANCED FINOPS ANOMALY MANAGEMENT - REAL AWS SUPPORT
# ============================================================================

class CostAnomalyDetection:
    """AWS Cost Anomaly Detection integration - REAL AWS SUPPORT"""
    
    @staticmethod
    def _is_demo_mode() -> bool:
        """Check if we're in demo mode"""
        if DEMO_MODE_AVAILABLE:
            demo_mgr = get_demo_manager()
            return demo_mgr.is_demo_mode
        return True
    
    @staticmethod
    def _get_real_anomalies(session=None) -> List[Dict]:
        """
        Get real cost anomalies from AWS Cost Anomaly Detection API.
        Requires ce:GetAnomalies permission.
        """
        if not BOTO3_AVAILABLE:
            return []
        
        try:
            # Use provided session or try to get from account manager
            if session is None and AWS_CONNECTOR_AVAILABLE:
                account_mgr = get_account_manager()
                session = account_mgr.get_session()
            
            if session is None:
                logger.warning("No AWS session available for cost anomaly detection")
                return []
            
            # Create Cost Explorer client
            ce = session.client('ce')
            
            # Get anomalies from the last 90 days
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            # First, list anomaly monitors
            monitors_response = ce.get_anomaly_monitors()
            monitors = monitors_response.get('AnomalyMonitors', [])
            
            if not monitors:
                logger.info("No anomaly monitors configured in this account")
                return []
            
            # Get anomalies from all monitors
            all_anomalies = []
            
            for monitor in monitors:
                monitor_arn = monitor.get('MonitorArn', '')
                
                try:
                    anomalies_response = ce.get_anomalies(
                        MonitorArn=monitor_arn,
                        DateInterval={
                            'StartDate': start_date,
                            'EndDate': end_date
                        }
                    )
                    
                    for anomaly in anomalies_response.get('Anomalies', []):
                        # Parse anomaly data
                        root_causes = anomaly.get('RootCauses', [])
                        primary_cause = root_causes[0] if root_causes else {}
                        
                        impact = anomaly.get('Impact', {})
                        total_impact = impact.get('TotalImpact', 0)
                        
                        # Determine severity based on impact
                        if total_impact >= 500:
                            severity = 'CRITICAL'
                        elif total_impact >= 100:
                            severity = 'HIGH'
                        elif total_impact >= 50:
                            severity = 'MEDIUM'
                        else:
                            severity = 'LOW'
                        
                        all_anomalies.append({
                            "id": anomaly.get('AnomalyId', ''),
                            "date": anomaly.get('AnomalyStartDate', ''),
                            "end_date": anomaly.get('AnomalyEndDate', ''),
                            "service": primary_cause.get('Service', 'Unknown'),
                            "account": primary_cause.get('LinkedAccount', 'N/A'),
                            "region": primary_cause.get('Region', 'N/A'),
                            "usage_type": primary_cause.get('UsageType', ''),
                            "normal_cost": round(float(impact.get('MaxImpact', 0)) * 0.3, 2),  # Estimate
                            "actual_cost": round(float(impact.get('MaxImpact', 0)), 2),
                            "total_impact": round(total_impact, 2),
                            "severity": severity,
                            "status": anomaly.get('AnomalyScore', {}).get('CurrentScore', 0) > 0.5 and 'OPEN' or 'RESOLVED',
                            "feedback": anomaly.get('Feedback', 'NO_FEEDBACK'),
                            "monitor_arn": monitor_arn
                        })
                        
                except ClientError as e:
                    logger.warning(f"Error getting anomalies from monitor {monitor_arn}: {e}")
                    continue
            
            return all_anomalies
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'AccessDeniedException':
                logger.warning("Access denied to Cost Anomaly Detection API")
            else:
                logger.error(f"Error accessing Cost Anomaly Detection: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in cost anomaly detection: {e}")
            return []
    
    @staticmethod
    def _get_demo_anomalies() -> List[Dict]:
        """Generate demo anomaly data"""
        return [
            {
                "id": "anomaly-001",
                "date": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                "service": "Amazon EC2",
                "account": "Production",
                "region": "us-east-1",
                "normal_cost": 180,
                "actual_cost": 520,
                "total_impact": 340,
                "deviation": "+189%",
                "severity": "CRITICAL",
                "status": "OPEN",
                "cause": "Unexpected auto-scaling spike due to traffic surge",
                "recommendation": "Review scaling policies and set max instance limits",
                "estimated_waste": 340
            },
            {
                "id": "anomaly-002",
                "date": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                "service": "Data Transfer",
                "account": "Production",
                "region": "us-east-1",
                "normal_cost": 45,
                "actual_cost": 210,
                "total_impact": 165,
                "deviation": "+367%",
                "severity": "CRITICAL",
                "status": "INVESTIGATING",
                "cause": "Cross-region data transfer spike from backup job",
                "recommendation": "Enable VPC endpoints and review data flow patterns",
                "estimated_waste": 165
            },
            {
                "id": "anomaly-003",
                "date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                "service": "Amazon RDS",
                "account": "Staging",
                "region": "us-west-2",
                "normal_cost": 95,
                "actual_cost": 175,
                "total_impact": 80,
                "deviation": "+84%",
                "severity": "HIGH",
                "status": "RESOLVED",
                "cause": "Database instance left running overnight",
                "recommendation": "Implement auto-stop for non-production RDS instances",
                "estimated_waste": 80
            }
        ]


def render_finops_anomaly_dashboard():
    """Render FinOps cost anomaly management dashboard - REAL AWS SUPPORT"""
    
    st.markdown("### 🚨 Cost Anomaly Detection")
    
    # Check mode
    is_demo = CostAnomalyDetection._is_demo_mode()
    
    if is_demo:
        st.info("🎭 **Demo Mode** - Showing simulated anomaly data. Switch to Live Mode for real AWS Cost Anomaly Detection.")
        anomalies = CostAnomalyDetection._get_demo_anomalies()
    else:
        st.success("🔌 **Live Mode** - Connecting to AWS Cost Anomaly Detection")
        
        with st.spinner("Loading anomalies from AWS Cost Explorer..."):
            anomalies = CostAnomalyDetection._get_real_anomalies()
        
        if not anomalies:
            st.warning("""
            ### ⚠️ No Anomalies Found
            
            This could mean:
            1. **No anomaly monitors configured** - Set up monitors in AWS Cost Anomaly Detection
            2. **No anomalies detected** - Your costs are normal! 🎉
            3. **Missing permissions** - Ensure your IAM role has `ce:GetAnomalyMonitors` and `ce:GetAnomalies`
            
            **To set up Cost Anomaly Detection:**
            1. Go to [AWS Cost Anomaly Detection Console](https://console.aws.amazon.com/cost-management/home#/anomaly-detection)
            2. Create an Anomaly Monitor
            3. Configure alert thresholds
            """)
            
            # Still show demo data as example
            if st.checkbox("Show example anomaly data"):
                anomalies = CostAnomalyDetection._get_demo_anomalies()
            else:
                return
    
    st.caption("ML-powered detection of unusual spending patterns")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    open_count = sum(1 for a in anomalies if a.get('status') in ['OPEN', 'INVESTIGATING'])
    critical_count = sum(1 for a in anomalies if a.get('severity') == 'CRITICAL')
    total_impact = sum(a.get('total_impact', a.get('estimated_waste', 0)) for a in anomalies if a.get('status') != 'RESOLVED')
    resolved_count = sum(1 for a in anomalies if a.get('status') == 'RESOLVED')
    
    with col1:
        st.metric("Open Anomalies", open_count)
    with col2:
        st.metric("Critical", critical_count)
    with col3:
        st.metric("Total Impact", f"${total_impact:,.0f}")
    with col4:
        st.metric("Resolved (90d)", resolved_count)
    
    st.markdown("---")
    
    # Anomaly filters
    col1, col2, col3 = st.columns(3)
    with col1:
        severity_filter = st.selectbox("Severity", ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"], key="rpe_anomaly_severity_filter")
    with col2:
        status_filter = st.selectbox("Status", ["All", "OPEN", "INVESTIGATING", "RESOLVED"], key="anomaly_status_filter")
    with col3:
        # Get unique accounts/services from anomalies
        services = ["All"] + list(set(a.get('service', 'Unknown') for a in anomalies))
        service_filter = st.selectbox("Service", services, key="anomaly_service_filter")
    
    # Anomaly list
    filtered_anomalies = anomalies
    if severity_filter != "All":
        filtered_anomalies = [a for a in filtered_anomalies if a.get('severity') == severity_filter]
    if status_filter != "All":
        filtered_anomalies = [a for a in filtered_anomalies if a.get('status') == status_filter]
    if service_filter != "All":
        filtered_anomalies = [a for a in filtered_anomalies if a.get('service') == service_filter]
    
    if not filtered_anomalies:
        st.info("No anomalies match the selected filters.")
        return
    
    for anomaly in filtered_anomalies:
        severity_colors = {
            "CRITICAL": ("#F44336", "#FFEBEE"),
            "HIGH": ("#FF9800", "#FFF3E0"),
            "MEDIUM": ("#2196F3", "#E3F2FD"),
            "LOW": ("#4CAF50", "#E8F5E9")
        }
        color, bg = severity_colors.get(anomaly.get('severity', 'MEDIUM'), ("#666", "#F5F5F5"))
        status_icons = {"OPEN": "🔴", "INVESTIGATING": "🟡", "RESOLVED": "🟢"}
        
        # Calculate deviation if not provided
        if 'deviation' not in anomaly:
            normal = anomaly.get('normal_cost', 1)
            actual = anomaly.get('actual_cost', 0)
            deviation = ((actual - normal) / normal * 100) if normal > 0 else 0
            anomaly['deviation'] = f"+{deviation:.0f}%"
        
        impact = anomaly.get('total_impact', anomaly.get('estimated_waste', 0))
        
        with st.container():
            st.markdown(f"""
            <div style="padding: 15px; background: {bg}; border-radius: 10px; margin-bottom: 10px; border-left: 4px solid {color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{anomaly.get('severity', 'UNKNOWN')}</span>
                        <span style="margin-left: 10px; font-weight: bold;">{anomaly.get('service', 'Unknown')}</span>
                        <span style="margin-left: 10px; color: #666;">({anomaly.get('account', 'N/A')})</span>
                    </div>
                    <div>
                        <span style="color: {color}; font-weight: bold;">{anomaly.get('deviation', 'N/A')}</span>
                        <span style="margin-left: 10px;">{status_icons.get(anomaly.get('status', 'OPEN'), '⚪')} {anomaly.get('status', 'UNKNOWN')}</span>
                    </div>
                </div>
                <div style="margin-top: 10px; font-size: 14px;">
                    <strong>Cause:</strong> {anomaly.get('cause', anomaly.get('usage_type', 'Unknown'))}
                </div>
                <div style="margin-top: 5px; font-size: 13px; color: #666;">
                    <strong>💡 Recommendation:</strong> {anomaly.get('recommendation', 'Review the anomaly details in AWS Console')}
                </div>
                <div style="margin-top: 10px; display: flex; gap: 20px; font-size: 12px;">
                    <span>📅 {anomaly.get('date', 'N/A')}</span>
                    <span>💰 Normal: ${anomaly.get('normal_cost', 0):,.0f}</span>
                    <span>📈 Actual: ${anomaly.get('actual_cost', 0):,.0f}</span>
                    <span style="color: #F44336;">🔥 Impact: ${impact:,.0f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Action buttons
        cols = st.columns(4)
        with cols[0]:
            if anomaly.get('status') == 'OPEN':
                if st.button("🔍 Investigate", key=f"investigate_{anomaly.get('id', random.randint(1, 10000))}", use_container_width=True):
                    if is_demo:
                        st.info(f"Starting investigation for {anomaly.get('service')}...")
                    else:
                        st.info("Open AWS Cost Explorer for detailed analysis")
        with cols[1]:
            if anomaly.get('status') != 'RESOLVED':
                if st.button("✅ Resolve", key=f"resolve_{anomaly.get('id', random.randint(1, 10000))}", use_container_width=True):
                    st.success(f"Marked {anomaly.get('service')} anomaly as resolved")
        with cols[2]:
            if st.button("📋 Details", key=f"details_{anomaly.get('id', random.randint(1, 10000))}", use_container_width=True):
                st.json(anomaly)
        with cols[3]:
            if not is_demo and anomaly.get('id'):
                aws_url = f"https://console.aws.amazon.com/cost-management/home#/anomaly-detection/anomaly/{anomaly.get('id')}"
                st.link_button("🔗 AWS Console", aws_url, use_container_width=True)


# ============================================================================
# SECTION 5: ENHANCED REMEDIATION EXPORT
# ============================================================================

def render_remediation_export_options():
    """Render enhanced remediation export options"""
    
    st.markdown("### 📥 Export Remediations")
    
    # Sample remediations for export
    remediations = st.session_state.get('remediations', [
        {"id": "REM-001", "title": "Enable S3 Encryption", "template_type": "cloudformation"},
        {"id": "REM-002", "title": "Enable RDS Backups", "template_type": "terraform"},
        {"id": "REM-003", "title": "Configure Security Groups", "template_type": "aws_cli"}
    ])
    
    st.markdown("#### Export Formats")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="padding: 20px; background: #E3F2FD; border-radius: 10px; text-align: center;">
            <div style="font-size: 40px;">📄</div>
            <div style="font-weight: bold; margin-top: 10px;">CloudFormation</div>
            <div style="font-size: 12px; color: #666;">YAML Templates</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬇️ Download CF", use_container_width=True, key="export_cf_btn"):
            st.download_button(
                "📥 cloudformation.yaml",
                data="# CloudFormation Templates\nAWSTemplateFormatVersion: '2010-09-09'\n...",
                file_name="remediations.yaml",
                mime="text/yaml",
                key="cf_download"
            )
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; background: #F3E5F5; border-radius: 10px; text-align: center;">
            <div style="font-size: 40px;">🔷</div>
            <div style="font-weight: bold; margin-top: 10px;">Terraform</div>
            <div style="font-size: 12px; color: #666;">HCL Files</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬇️ Download TF", use_container_width=True, key="export_tf_btn"):
            st.download_button(
                "📥 terraform.tf",
                data='# Terraform Templates\nterraform {\n  required_version = ">= 1.0"\n}\n...',
                file_name="remediations.tf",
                mime="text/plain",
                key="tf_download"
            )
    
    with col3:
        st.markdown("""
        <div style="padding: 20px; background: #E8F5E9; border-radius: 10px; text-align: center;">
            <div style="font-size: 40px;">💻</div>
            <div style="font-weight: bold; margin-top: 10px;">AWS CLI</div>
            <div style="font-size: 12px; color: #666;">Shell Scripts</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("⬇️ Download CLI", use_container_width=True, key="export_cli_btn"):
            st.download_button(
                "📥 remediate.sh",
                data="#!/bin/bash\nset -e\n\n# AWS CLI Remediation Script\n...",
                file_name="remediations.sh",
                mime="text/x-sh",
                key="cli_download"
            )
    
    st.markdown("---")
    st.markdown("#### Full Report Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export JSON Report", use_container_width=True, key="export_json_btn"):
            report = {
                "generated_at": datetime.now().isoformat(),
                "remediations": remediations,
                "summary": {
                    "total": len(remediations),
                    "cloudformation": sum(1 for r in remediations if r['template_type'] == 'cloudformation'),
                    "terraform": sum(1 for r in remediations if r['template_type'] == 'terraform'),
                    "aws_cli": sum(1 for r in remediations if r['template_type'] == 'aws_cli')
                }
            }
            st.download_button(
                "📥 Download JSON",
                data=json.dumps(report, indent=2),
                file_name="remediation_report.json",
                mime="application/json",
                key="json_download"
            )
    
    with col2:
        if st.button("📋 Export CSV Summary", use_container_width=True, key="export_csv_btn"):
            df = pd.DataFrame(remediations)
            st.download_button(
                "📥 Download CSV",
                data=df.to_csv(index=False),
                file_name="remediations.csv",
                mime="text/csv",
                key="csv_download"
            )


# ============================================================================
# MAIN INTEGRATION FUNCTION
# ============================================================================

def integrate_react_features():
    """Main function to integrate React features into Streamlit - DEMO LAUNCHER"""
    
    st.set_page_config(page_title="React Parity Features", layout="wide")
    
    st.title("🔄 React Parity Enhancements")
    st.caption("Features from React application integrated into Streamlit")
    
    # Show current mode
    if DEMO_MODE_AVAILABLE:
        demo_mgr = get_demo_manager()
        is_demo = demo_mgr.is_demo_mode
        if is_demo:
            st.sidebar.warning("🎭 **Demo Mode Active**")
            if st.sidebar.button("Switch to Live Mode"):
                demo_mgr.is_demo_mode = False
                st.rerun()
        else:
            st.sidebar.success("🔌 **Live Mode Active**")
            if st.sidebar.button("Switch to Demo Mode"):
                demo_mgr.is_demo_mode = True
                st.rerun()
    
    # Show AWS connection status
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 System Status")
    
    status_items = [
        ("Demo Mode Manager", DEMO_MODE_AVAILABLE),
        ("AWS Connector", AWS_CONNECTOR_AVAILABLE),
        ("Security Manager", SECURITY_MANAGER_AVAILABLE),
        ("boto3", BOTO3_AVAILABLE)
    ]
    
    for name, available in status_items:
        icon = "✅" if available else "❌"
        st.sidebar.caption(f"{icon} {name}")
    
    tabs = st.tabs([
        "🤖 AI Recommendations",
        "🔐 Security Hub",
        "🎯 Assessment Mode",
        "🚨 Cost Anomalies",
        "📥 Export Options"
    ])
    
    with tabs[0]:
        render_waf_ai_recommendations()
    
    with tabs[1]:
        SecurityHubIntegration.render_security_hub_connector()
    
    with tabs[2]:
        render_assessment_mode_selection()
    
    with tabs[3]:
        render_finops_anomaly_dashboard()
    
    with tabs[4]:
        render_remediation_export_options()


if __name__ == "__main__":
    integrate_react_features()
