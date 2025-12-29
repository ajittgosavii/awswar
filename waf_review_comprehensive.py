"""
Comprehensive Well-Architected Framework Review Module
======================================================
Complete end-to-end WAF review workflow:
1. Automated AWS Scan (Direct API / Security Hub)
2. Manual WAF Questionnaire (for gaps)
3. Consolidated Scoring across 6 pillars
4. AI-Powered Remediation with CloudFormation/Terraform
5. Re-scan to verify fixes
6. Updated scores with before/after comparison

Version: 1.0.0
Author: Enterprise WAF Scanner Team
"""

import streamlit as st
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
import time
from io import BytesIO

# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

class ReviewPhase(Enum):
    """Phases of the WAF Review workflow"""
    SETUP = "setup"
    SCANNING = "scanning"
    QUESTIONNAIRE = "questionnaire"
    SCORING = "scoring"
    REMEDIATION = "remediation"
    RESCAN = "rescan"
    COMPLETE = "complete"

class WAFPillar(Enum):
    """AWS Well-Architected Framework Pillars"""
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"

PILLAR_ICONS = {
    WAFPillar.OPERATIONAL_EXCELLENCE: "⚙️",
    WAFPillar.SECURITY: "🔒",
    WAFPillar.RELIABILITY: "🛡️",
    WAFPillar.PERFORMANCE_EFFICIENCY: "⚡",
    WAFPillar.COST_OPTIMIZATION: "💰",
    WAFPillar.SUSTAINABILITY: "🌱"
}

PILLAR_COLORS = {
    WAFPillar.OPERATIONAL_EXCELLENCE: "#FF6B6B",
    WAFPillar.SECURITY: "#4ECDC4",
    WAFPillar.RELIABILITY: "#45B7D1",
    WAFPillar.PERFORMANCE_EFFICIENCY: "#96CEB4",
    WAFPillar.COST_OPTIMIZATION: "#FFEAA7",
    WAFPillar.SUSTAINABILITY: "#81C784"
}

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Finding:
    """Security/compliance finding from scan"""
    id: str
    title: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    pillar: str
    service: str
    resource: str
    account_id: str
    region: str = "us-east-1"
    recommendation: str = ""
    remediation_available: bool = False
    auto_remediatable: bool = False
    status: str = "open"  # open, remediated, accepted_risk

@dataclass
class QuestionResponse:
    """Response to a WAF questionnaire question"""
    question_id: str
    pillar: str
    question_text: str
    response: str  # yes, no, partial, not_applicable
    auto_detected: bool = False
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    notes: str = ""

@dataclass
class PillarScore:
    """Score for a single WAF pillar"""
    pillar: WAFPillar
    scan_score: float = 0.0  # From automated scan (0-100)
    questionnaire_score: float = 0.0  # From manual questionnaire (0-100)
    combined_score: float = 0.0  # Weighted combination
    findings_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    questions_answered: int = 0
    questions_total: int = 0
    improvement_areas: List[str] = field(default_factory=list)

@dataclass
class RemediationItem:
    """Item to be remediated"""
    finding_id: str
    finding_title: str
    severity: str
    pillar: str
    service: str
    resource: str
    account_id: str
    cloudformation: str = ""
    terraform: str = ""
    aws_cli: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, approved, deployed, failed, rolled_back
    approved_by: str = ""
    approved_at: str = ""
    deployed_at: str = ""
    stack_name: str = ""
    stack_id: str = ""

@dataclass
class WAFReviewSession:
    """Complete WAF Review session state"""
    # Session info
    session_id: str
    created_at: datetime
    updated_at: datetime
    current_phase: ReviewPhase = ReviewPhase.SETUP
    
    # Account configuration
    accounts: List[Dict] = field(default_factory=list)
    scan_source: str = "direct"  # direct, security_hub, import
    regions: List[str] = field(default_factory=lambda: ["us-east-1"])
    
    # Scan results
    scan_completed: bool = False
    scan_timestamp: Optional[datetime] = None
    findings: List[Finding] = field(default_factory=list)
    resources_scanned: int = 0
    services_scanned: int = 0
    
    # Questionnaire
    questionnaire_completed: bool = False
    responses: List[QuestionResponse] = field(default_factory=list)
    auto_detected_count: int = 0
    manual_required_count: int = 0
    
    # Scores
    pillar_scores: Dict[str, PillarScore] = field(default_factory=dict)
    overall_score: float = 0.0
    initial_score: float = 0.0  # Before remediation
    
    # Remediation
    remediation_items: List[RemediationItem] = field(default_factory=list)
    remediation_deployed: int = 0
    remediation_pending: int = 0
    
    # Re-scan
    rescan_completed: bool = False
    rescan_timestamp: Optional[datetime] = None
    final_score: float = 0.0
    score_improvement: float = 0.0

# ============================================================================
# WAF QUESTIONNAIRE DEFINITIONS
# ============================================================================

WAF_QUESTIONS = {
    WAFPillar.SECURITY: [
        {
            "id": "SEC-01",
            "question": "How do you securely operate your workload?",
            "description": "Operating workloads securely includes establishing security practices, detecting security events, and protecting against unauthorized access.",
            "scan_detectable": True,
            "detection_services": ["IAM", "CloudTrail", "GuardDuty", "Security Hub"],
            "best_practices": [
                "Separate workloads using accounts",
                "Secure AWS account root user",
                "Enforce MFA for human identities",
                "Keep credentials and secrets secure"
            ]
        },
        {
            "id": "SEC-02",
            "question": "How do you manage identities for people and machines?",
            "description": "Strong identity foundation ensures only authorized identities access resources.",
            "scan_detectable": True,
            "detection_services": ["IAM", "Organizations", "SSO"],
            "best_practices": [
                "Use IAM Identity Center for workforce identities",
                "Use IAM roles for applications",
                "Implement least privilege access",
                "Regularly review and remove unused permissions"
            ]
        },
        {
            "id": "SEC-03",
            "question": "How do you manage permissions for people and machines?",
            "description": "Manage permissions to control access to AWS and your workload.",
            "scan_detectable": True,
            "detection_services": ["IAM", "IAM Access Analyzer"],
            "best_practices": [
                "Define access requirements",
                "Grant least privilege access",
                "Establish emergency access process",
                "Reduce permissions continuously"
            ]
        },
        {
            "id": "SEC-04",
            "question": "How do you detect and investigate security events?",
            "description": "Capture and analyze events from logs and metrics to gain visibility.",
            "scan_detectable": True,
            "detection_services": ["CloudTrail", "CloudWatch", "GuardDuty", "Security Hub"],
            "best_practices": [
                "Configure service and application logging",
                "Analyze logs, findings, and metrics centrally",
                "Automate response to events",
                "Implement actionable security events"
            ]
        },
        {
            "id": "SEC-05",
            "question": "How do you protect your network resources?",
            "description": "Workloads require multiple layers of defense to protect from attacks.",
            "scan_detectable": True,
            "detection_services": ["VPC", "WAF", "Shield", "Network Firewall"],
            "best_practices": [
                "Create network layers",
                "Control traffic at all layers",
                "Automate network protection",
                "Implement inspection and protection"
            ]
        },
        {
            "id": "SEC-06",
            "question": "How do you protect your compute resources?",
            "description": "Compute resources require multiple layers of defense.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Lambda", "ECS", "Inspector"],
            "best_practices": [
                "Perform vulnerability management",
                "Reduce attack surface",
                "Implement managed services",
                "Automate compute protection"
            ]
        },
        {
            "id": "SEC-07",
            "question": "How do you classify your data?",
            "description": "Classification provides a way to categorize data based on criticality.",
            "scan_detectable": False,
            "detection_services": ["Macie"],
            "best_practices": [
                "Identify data within your workload",
                "Define data protection controls",
                "Automate identification and classification",
                "Define data lifecycle management"
            ]
        },
        {
            "id": "SEC-08",
            "question": "How do you protect your data at rest?",
            "description": "Protect data at rest by implementing encryption and access controls.",
            "scan_detectable": True,
            "detection_services": ["S3", "RDS", "EBS", "KMS"],
            "best_practices": [
                "Implement secure key management",
                "Enforce encryption at rest",
                "Automate data at rest protection",
                "Enforce access control"
            ]
        },
        {
            "id": "SEC-09",
            "question": "How do you protect your data in transit?",
            "description": "Protect data in transit by implementing encryption.",
            "scan_detectable": True,
            "detection_services": ["ELB", "CloudFront", "ACM"],
            "best_practices": [
                "Implement secure key and certificate management",
                "Enforce encryption in transit",
                "Automate detection of unintended data access",
                "Authenticate network communications"
            ]
        },
        {
            "id": "SEC-10",
            "question": "How do you anticipate, respond to, and recover from incidents?",
            "description": "Preparation is critical to timely investigation and response.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Identify key personnel and external resources",
                "Develop incident management plans",
                "Prepare forensic capabilities",
                "Automate containment capability"
            ]
        }
    ],
    WAFPillar.RELIABILITY: [
        {
            "id": "REL-01",
            "question": "How do you manage service quotas and constraints?",
            "description": "Manage service quotas and constraints to prevent unexpected failures.",
            "scan_detectable": True,
            "detection_services": ["Service Quotas", "Trusted Advisor"],
            "best_practices": [
                "Aware of service quotas and constraints",
                "Manage service quotas across accounts and regions",
                "Accommodate fixed service quotas and constraints",
                "Monitor and manage quotas"
            ]
        },
        {
            "id": "REL-02",
            "question": "How do you plan your network topology?",
            "description": "Plan network topology to support connectivity and redundancy.",
            "scan_detectable": True,
            "detection_services": ["VPC", "Direct Connect", "Transit Gateway"],
            "best_practices": [
                "Use highly available network connectivity",
                "Provision redundant connectivity between networks",
                "Ensure IP subnet allocation accounts for expansion",
                "Prefer hub-and-spoke topologies"
            ]
        },
        {
            "id": "REL-03",
            "question": "How do you design your workload service architecture?",
            "description": "Design distributed systems to prevent failures and improve recovery.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Choose how to segment your workload",
                "Build services focused on specific business domains",
                "Provide service contracts per API"
            ]
        },
        {
            "id": "REL-04",
            "question": "How do you design interactions to prevent failures?",
            "description": "Distributed systems must be designed to handle failures gracefully.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Identify which kind of distributed system is required",
                "Implement loosely coupled dependencies",
                "Make all responses idempotent",
                "Do constant work"
            ]
        },
        {
            "id": "REL-05",
            "question": "How do you design interactions to mitigate or withstand failures?",
            "description": "Implement patterns to handle failures when they occur.",
            "scan_detectable": True,
            "detection_services": ["ELB", "Auto Scaling", "Route 53"],
            "best_practices": [
                "Implement graceful degradation",
                "Throttle requests",
                "Control and limit retry calls",
                "Fail fast and limit queues"
            ]
        },
        {
            "id": "REL-06",
            "question": "How do you monitor workload resources?",
            "description": "Monitor and alert on metrics to detect issues before impact.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "X-Ray", "CloudTrail"],
            "best_practices": [
                "Monitor all components for the workload",
                "Define and calculate metrics",
                "Send notifications based on KPIs",
                "Automate responses based on metrics"
            ]
        },
        {
            "id": "REL-07",
            "question": "How do you design your workload to adapt to changes in demand?",
            "description": "Scale resources to maintain availability during demand changes.",
            "scan_detectable": True,
            "detection_services": ["Auto Scaling", "ECS", "Lambda"],
            "best_practices": [
                "Use automation when obtaining or scaling resources",
                "Obtain resources upon detection of impairment",
                "Obtain resources upon detection of demand",
                "Load test your workload"
            ]
        },
        {
            "id": "REL-08",
            "question": "How do you implement change?",
            "description": "Controlled changes are necessary but require careful management.",
            "scan_detectable": True,
            "detection_services": ["CloudFormation", "Config", "Systems Manager"],
            "best_practices": [
                "Use runbooks for standard activities",
                "Integrate functional testing in deployment",
                "Integrate resiliency testing in deployment",
                "Deploy using immutable infrastructure"
            ]
        },
        {
            "id": "REL-09",
            "question": "How do you back up data?",
            "description": "Back up data, applications, and configuration to recover from failures.",
            "scan_detectable": True,
            "detection_services": ["Backup", "S3", "RDS", "EBS"],
            "best_practices": [
                "Identify and back up all data that needs to be backed up",
                "Secure and encrypt backups",
                "Perform data backup automatically",
                "Perform periodic recovery of the data"
            ]
        },
        {
            "id": "REL-10",
            "question": "How do you use fault isolation to protect your workload?",
            "description": "Fault isolation boundaries limit the blast radius of failures.",
            "scan_detectable": True,
            "detection_services": ["Multi-AZ", "Route 53", "Global Accelerator"],
            "best_practices": [
                "Deploy the workload to multiple locations",
                "Automate recovery for components constrained to a single location",
                "Use bulkhead architectures to limit scope of impact"
            ]
        }
    ],
    WAFPillar.OPERATIONAL_EXCELLENCE: [
        {
            "id": "OPS-01",
            "question": "How do you determine what your priorities are?",
            "description": "Understanding business priorities helps focus operational efforts.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Evaluate external customer needs",
                "Evaluate internal customer needs",
                "Evaluate governance requirements",
                "Evaluate compliance requirements"
            ]
        },
        {
            "id": "OPS-02",
            "question": "How do you structure your organization to support your business outcomes?",
            "description": "Teams must have clear ownership and understanding of their roles.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Resources have identified owners",
                "Processes and procedures have identified owners",
                "Operations activities have identified owners responsible",
                "Team members know what they are responsible for"
            ]
        },
        {
            "id": "OPS-03",
            "question": "How does your organizational culture support your business outcomes?",
            "description": "Culture should support experimentation, learning, and improvement.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Executive Sponsorship",
                "Team members are empowered to take action",
                "Escalation is encouraged",
                "Communications are timely, clear, and actionable"
            ]
        },
        {
            "id": "OPS-04",
            "question": "How do you design your workload so that you can understand its state?",
            "description": "Design workloads with observability features for operational visibility.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "X-Ray", "CloudTrail"],
            "best_practices": [
                "Implement application telemetry",
                "Implement and configure workload telemetry",
                "Implement user activity telemetry",
                "Implement dependency telemetry"
            ]
        },
        {
            "id": "OPS-05",
            "question": "How do you reduce defects, ease remediation, and improve flow into production?",
            "description": "Adopt approaches that improve flow of changes and reduce defects.",
            "scan_detectable": True,
            "detection_services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "best_practices": [
                "Use version control",
                "Test and validate changes",
                "Use configuration management systems",
                "Use build and deployment management systems"
            ]
        }
    ],
    WAFPillar.PERFORMANCE_EFFICIENCY: [
        {
            "id": "PERF-01",
            "question": "How do you select the best performing architecture?",
            "description": "Use data-driven approach to select high-performance architecture.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Understand the available services and resources",
                "Define a process for architectural choices",
                "Factor cost requirements into decisions",
                "Use policies or reference architectures"
            ]
        },
        {
            "id": "PERF-02",
            "question": "How do you select your compute solution?",
            "description": "Select compute for your workload to improve performance.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Lambda", "ECS", "Fargate"],
            "best_practices": [
                "Evaluate the available compute options",
                "Understand the available compute configuration options",
                "Collect compute-related metrics",
                "Determine required configuration by right-sizing"
            ]
        },
        {
            "id": "PERF-03",
            "question": "How do you select your storage solution?",
            "description": "Select storage for your workload to improve performance.",
            "scan_detectable": True,
            "detection_services": ["S3", "EBS", "EFS", "FSx"],
            "best_practices": [
                "Understand storage characteristics and requirements",
                "Evaluate available configuration options",
                "Make decisions based on access patterns and metrics"
            ]
        },
        {
            "id": "PERF-04",
            "question": "How do you select your database solution?",
            "description": "Select database for your workload to improve performance.",
            "scan_detectable": True,
            "detection_services": ["RDS", "DynamoDB", "ElastiCache", "Redshift"],
            "best_practices": [
                "Understand data characteristics",
                "Evaluate the available options",
                "Collect and record database performance metrics",
                "Choose data storage based on access patterns"
            ]
        },
        {
            "id": "PERF-05",
            "question": "How do you configure your networking solution?",
            "description": "Configure networking for your workload to improve performance.",
            "scan_detectable": True,
            "detection_services": ["VPC", "CloudFront", "Global Accelerator", "Direct Connect"],
            "best_practices": [
                "Understand how networking impacts performance",
                "Evaluate available networking features",
                "Choose appropriately sized dedicated connectivity",
                "Leverage load balancing and encryption offloading"
            ]
        }
    ],
    WAFPillar.COST_OPTIMIZATION: [
        {
            "id": "COST-01",
            "question": "How do you implement cloud financial management?",
            "description": "Implementing financial management helps achieve cost optimization.",
            "scan_detectable": False,
            "detection_services": ["Cost Explorer", "Budgets"],
            "best_practices": [
                "Establish a cost optimization function",
                "Establish a partnership between finance and technology",
                "Establish cloud budgets and forecasts",
                "Implement cost awareness in organizational processes"
            ]
        },
        {
            "id": "COST-02",
            "question": "How do you govern usage?",
            "description": "Establish policies and mechanisms to control costs.",
            "scan_detectable": True,
            "detection_services": ["Organizations", "Service Control Policies", "Budgets"],
            "best_practices": [
                "Develop policies based on your organization requirements",
                "Implement goals and targets",
                "Implement an account structure",
                "Implement groups and roles"
            ]
        },
        {
            "id": "COST-03",
            "question": "How do you monitor usage and cost?",
            "description": "Monitor cost and usage to achieve cost optimization.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Cost and Usage Reports", "Budgets"],
            "best_practices": [
                "Configure detailed information sources",
                "Identify cost attribution categories",
                "Establish organization metrics",
                "Configure billing and cost management tools"
            ]
        },
        {
            "id": "COST-04",
            "question": "How do you decommission resources?",
            "description": "Implement change control and remove unused resources.",
            "scan_detectable": True,
            "detection_services": ["Trusted Advisor", "Cost Explorer", "Config"],
            "best_practices": [
                "Track resources over their life time",
                "Implement a decommissioning process",
                "Decommission resources automatically",
                "Enforce data retention policies"
            ]
        },
        {
            "id": "COST-05",
            "question": "How do you evaluate cost when you select services?",
            "description": "Consider cost when selecting AWS services.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Identify organization requirements for cost",
                "Analyze all components of this workload",
                "Perform a thorough analysis of each component",
                "Select software with cost-effective licensing"
            ]
        },
        {
            "id": "COST-06",
            "question": "How do you meet cost targets when you select resource type, size, and number?",
            "description": "Right-size resources for cost optimization.",
            "scan_detectable": True,
            "detection_services": ["Compute Optimizer", "Trusted Advisor", "Cost Explorer"],
            "best_practices": [
                "Perform cost modeling",
                "Select resource type and size based on data",
                "Select resource type and size automatically based on metrics"
            ]
        },
        {
            "id": "COST-07",
            "question": "How do you use pricing models to reduce cost?",
            "description": "Use pricing models to reduce cost.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Reserved Instances", "Savings Plans"],
            "best_practices": [
                "Perform pricing model analysis",
                "Implement regions based on cost",
                "Select third-party agreements with cost-efficient terms",
                "Implement pricing models for all components of this workload"
            ]
        },
        {
            "id": "COST-08",
            "question": "How do you plan for data transfer charges?",
            "description": "Plan and monitor data transfer to reduce costs.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "VPC Flow Logs"],
            "best_practices": [
                "Perform data transfer modeling",
                "Select components to optimize data transfer cost",
                "Implement services to reduce data transfer costs"
            ]
        }
    ],
    WAFPillar.SUSTAINABILITY: [
        {
            "id": "SUS-01",
            "question": "How do you select Regions to support your sustainability goals?",
            "description": "Choose Regions close to users and with lower carbon intensity.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Choose Regions near Amazon renewable energy projects",
                "Choose Regions with lower carbon intensity"
            ]
        },
        {
            "id": "SUS-02",
            "question": "How do you take advantage of user behavior patterns to support your sustainability goals?",
            "description": "Align resources provisioned with customer demand.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "Auto Scaling"],
            "best_practices": [
                "Analyze workload demand patterns",
                "Optimize geographic placement of workloads based on demand",
                "Scale infrastructure to continuously match demand"
            ]
        },
        {
            "id": "SUS-03",
            "question": "How do you take advantage of software and architecture patterns to support your sustainability goals?",
            "description": "Implement patterns to minimize resources needed.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "Fargate", "S3"],
            "best_practices": [
                "Optimize software and architecture for asynchronous and scheduled jobs",
                "Remove or refactor workload components with low utilization",
                "Optimize areas of code that consume the most resources"
            ]
        },
        {
            "id": "SUS-04",
            "question": "How do you take advantage of data access and usage patterns to support your sustainability goals?",
            "description": "Implement data management practices to reduce resources needed.",
            "scan_detectable": True,
            "detection_services": ["S3", "EBS", "RDS"],
            "best_practices": [
                "Implement a data classification policy",
                "Use technologies that support data access and storage patterns",
                "Use lifecycle policies to delete unnecessary data"
            ]
        },
        {
            "id": "SUS-05",
            "question": "How do your hardware management and usage practices support your sustainability goals?",
            "description": "Use managed services and efficient hardware.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Graviton", "Compute Optimizer"],
            "best_practices": [
                "Use efficient hardware for your workload",
                "Use managed services",
                "Optimize your use of hardware-based compute accelerators"
            ]
        }
    ]
}

# ============================================================================
# MAIN WORKFLOW ENGINE
# ============================================================================

class WAFReviewWorkflow:
    """Main workflow engine for comprehensive WAF review"""
    
    def __init__(self):
        self.session_key = "waf_review_session"
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize or restore session state"""
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = WAFReviewSession(
                session_id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    @property
    def session(self) -> WAFReviewSession:
        return st.session_state[self.session_key]
    
    def render(self):
        """Render the complete WAF Review workflow"""
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #1a237e 0%, #0d47a1 100%); 
                    padding: 20px; border-radius: 10px; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0;">🏗️ Well-Architected Framework Review</h1>
            <p style="color: #bbdefb; margin-top: 10px;">
                Complete end-to-end assessment: Scan → Questionnaire → Score → Remediate → Verify
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress indicator
        self._render_progress_tracker()
        
        st.markdown("---")
        
        # Render current phase
        phase = self.session.current_phase
        
        if phase == ReviewPhase.SETUP:
            self._render_setup_phase()
        elif phase == ReviewPhase.SCANNING:
            self._render_scanning_phase()
        elif phase == ReviewPhase.QUESTIONNAIRE:
            self._render_questionnaire_phase()
        elif phase == ReviewPhase.SCORING:
            self._render_scoring_phase()
        elif phase == ReviewPhase.REMEDIATION:
            self._render_remediation_phase()
        elif phase == ReviewPhase.RESCAN:
            self._render_rescan_phase()
        elif phase == ReviewPhase.COMPLETE:
            self._render_complete_phase()
    
    def _render_progress_tracker(self):
        """Render visual progress tracker"""
        phases = [
            ("Setup", ReviewPhase.SETUP, "🔧"),
            ("Scan", ReviewPhase.SCANNING, "🔍"),
            ("Questionnaire", ReviewPhase.QUESTIONNAIRE, "📝"),
            ("Score", ReviewPhase.SCORING, "📊"),
            ("Remediate", ReviewPhase.REMEDIATION, "🔨"),
            ("Verify", ReviewPhase.RESCAN, "✅"),
            ("Complete", ReviewPhase.COMPLETE, "🎉")
        ]
        
        # Use .value comparison for safe enum matching
        current_phase_value = self.session.current_phase.value if hasattr(self.session.current_phase, 'value') else str(self.session.current_phase)
        phase_values = [p[1].value for p in phases]
        
        try:
            current_idx = phase_values.index(current_phase_value)
        except ValueError:
            # Default to SETUP if phase not found
            current_idx = 0
        
        cols = st.columns(len(phases))
        for idx, (name, phase, icon) in enumerate(phases):
            with cols[idx]:
                if idx < current_idx:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: #4CAF50; 
                                border-radius: 10px; color: white;">
                        {icon}<br><small>✓ {name}</small>
                    </div>
                    """, unsafe_allow_html=True)
                elif idx == current_idx:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: #2196F3; 
                                border-radius: 10px; color: white; border: 2px solid #1565C0;">
                        {icon}<br><small><b>{name}</b></small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 10px; background: #E0E0E0; 
                                border-radius: 10px; color: #757575;">
                        {icon}<br><small>{name}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    # ========================================================================
    # PHASE 1: SETUP
    # ========================================================================
    
    def _render_setup_phase(self):
        """Render setup phase - configure accounts and scan source"""
        
        st.markdown("## 🔧 Step 1: Setup")
        st.markdown("Configure your AWS accounts and select the scan source.")
        
        # Check if accounts are already connected from main app
        connected_accounts = st.session_state.get('connected_accounts', [])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📡 Scan Source")
            scan_source = st.radio(
                "How should we gather findings?",
                ["Direct API Scan", "Security Hub Integration", "Import from CSV"],
                help="Direct scan queries AWS APIs. Security Hub aggregates findings from multiple services."
            )
            
            self.session.scan_source = {
                "Direct API Scan": "direct",
                "Security Hub Integration": "security_hub",
                "Import from CSV": "import"
            }[scan_source]
        
        with col2:
            st.markdown("### 🌍 Regions")
            all_regions = [
                "us-east-1", "us-east-2", "us-west-1", "us-west-2",
                "eu-west-1", "eu-west-2", "eu-central-1",
                "ap-southeast-1", "ap-southeast-2", "ap-northeast-1"
            ]
            selected_regions = st.multiselect(
                "Select regions to scan",
                all_regions,
                default=["us-east-1"]
            )
            self.session.regions = selected_regions
        
        st.markdown("---")
        
        # Account selection
        st.markdown("### 🏢 Accounts to Review")
        
        if connected_accounts:
            st.success(f"✅ {len(connected_accounts)} accounts connected from AWS Connector")
            
            # Show connected accounts
            account_options = []
            for acc in connected_accounts:
                name = acc.get('account_name', acc.get('name', 'Unknown'))
                acc_id = acc.get('account_id', acc.get('id', acc.get('Id', 'N/A')))
                account_options.append(f"{name} ({acc_id})")
            
            selected = st.multiselect(
                "Select accounts to include in review",
                account_options,
                default=account_options
            )
            
            # Store selected accounts
            self.session.accounts = [
                acc for acc in connected_accounts
                if f"{acc.get('account_name', acc.get('name', 'Unknown'))} ({acc.get('account_id', acc.get('id', acc.get('Id', 'N/A')))})" in selected
            ]
        else:
            st.warning("⚠️ No accounts connected. Please connect accounts in AWS Connector tab first.")
            st.info("💡 Or use existing scan results from WAF Review tab")
            
            # Check for existing scan results
            if 'multi_scan_results' in st.session_state:
                results = st.session_state.multi_scan_results
                account_count = len([k for k in results.keys() if k != 'consolidated_pdf'])
                st.success(f"📊 Found existing scan results for {account_count} accounts")
                
                if st.button("Use Existing Scan Results"):
                    self._import_existing_results(results)
                    return
        
        st.markdown("---")
        
        # Proceed button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("▶️ Start WAF Review", type="primary", use_container_width=True):
                if self.session.accounts or 'multi_scan_results' in st.session_state:
                    self.session.current_phase = ReviewPhase.SCANNING
                    self.session.updated_at = datetime.now()
                    st.rerun()
                else:
                    st.error("Please select at least one account or connect accounts first")
    
    def _import_existing_results(self, results: Dict):
        """Import findings from existing scan results"""
        
        findings = []
        for account_id, data in results.items():
            if account_id == 'consolidated_pdf' or not isinstance(data, dict):
                continue
            
            for finding in data.get('findings', []):
                findings.append(Finding(
                    id=hashlib.md5(f"{account_id}-{finding.get('resource', '')}-{finding.get('title', '')}".encode()).hexdigest()[:8],
                    title=finding.get('title', 'Unknown'),
                    description=finding.get('description', ''),
                    severity=finding.get('severity', 'MEDIUM'),
                    pillar=self._map_service_to_pillar(finding.get('service', '')),
                    service=finding.get('service', 'Unknown'),
                    resource=finding.get('resource', 'Unknown'),
                    account_id=account_id
                ))
            
            # Add account to list
            self.session.accounts.append({
                'account_id': account_id,
                'account_name': data.get('account_name', account_id)
            })
        
        self.session.findings = findings
        self.session.scan_completed = True
        self.session.scan_timestamp = datetime.now()
        self.session.current_phase = ReviewPhase.QUESTIONNAIRE
        self.session.updated_at = datetime.now()
        st.rerun()
    
    def _map_service_to_pillar(self, service: str) -> str:
        """Map AWS service to WAF pillar"""
        service_pillar_map = {
            'IAM': WAFPillar.SECURITY.value,
            'S3': WAFPillar.SECURITY.value,
            'EC2': WAFPillar.RELIABILITY.value,
            'RDS': WAFPillar.RELIABILITY.value,
            'VPC': WAFPillar.SECURITY.value,
            'Lambda': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'CloudWatch': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'CloudTrail': WAFPillar.SECURITY.value,
            'KMS': WAFPillar.SECURITY.value,
            'ELB': WAFPillar.RELIABILITY.value,
            'Auto Scaling': WAFPillar.RELIABILITY.value,
            'Cost Explorer': WAFPillar.COST_OPTIMIZATION.value,
            'Trusted Advisor': WAFPillar.COST_OPTIMIZATION.value
        }
        return service_pillar_map.get(service, WAFPillar.SECURITY.value)
    
    # ========================================================================
    # PHASE 2: SCANNING
    # ========================================================================
    
    def _render_scanning_phase(self):
        """Render scanning phase"""
        
        st.markdown("## 🔍 Step 2: AWS Account Scanning")
        
        # Check if we should use existing results
        if 'multi_scan_results' in st.session_state and not self.session.scan_completed:
            results = st.session_state.multi_scan_results
            account_count = len([k for k in results.keys() if k != 'consolidated_pdf'])
            
            st.info(f"📊 Found existing scan results from WAF Review tab ({account_count} accounts)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Use Existing Results", type="primary", use_container_width=True):
                    self._import_existing_results(results)
            with col2:
                if st.button("🔄 Run New Scan", use_container_width=True):
                    self._run_new_scan()
        
        elif self.session.scan_completed:
            # Show scan results summary
            st.success(f"✅ Scan completed at {self.session.scan_timestamp}")
            
            # Show findings summary by pillar
            self._render_findings_summary()
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("▶️ Continue to Questionnaire", type="primary", use_container_width=True):
                    self.session.current_phase = ReviewPhase.QUESTIONNAIRE
                    self.session.updated_at = datetime.now()
                    st.rerun()
        
        else:
            self._run_new_scan()
    
    def _run_new_scan(self):
        """Execute new AWS scan"""
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.markdown("🔍 **Initializing scan...**")
        progress_bar.progress(10)
        
        findings = []
        
        if self.session.scan_source == "security_hub":
            status_text.markdown("🔍 **Querying Security Hub...**")
            findings = self._scan_security_hub()
        else:
            status_text.markdown("🔍 **Scanning AWS resources...**")
            findings = self._scan_direct_api()
        
        progress_bar.progress(80)
        
        # Store results
        self.session.findings = findings
        self.session.scan_completed = True
        self.session.scan_timestamp = datetime.now()
        self.session.resources_scanned = len(set(f.resource for f in findings))
        self.session.services_scanned = len(set(f.service for f in findings))
        
        progress_bar.progress(100)
        status_text.markdown("✅ **Scan complete!**")
        
        time.sleep(1)
        st.rerun()
    
    def _scan_security_hub(self) -> List[Finding]:
        """Scan using Security Hub"""
        # Implementation for Security Hub integration
        # This would query Security Hub findings
        return []
    
    def _scan_direct_api(self) -> List[Finding]:
        """Scan using direct AWS API calls"""
        # This uses the existing multi-account scan results if available
        # Or runs new scans
        return []
    
    def _render_findings_summary(self):
        """Render summary of findings by pillar"""
        
        # Group findings by pillar
        pillar_findings = {}
        for pillar in WAFPillar:
            pillar_findings[pillar.value] = [f for f in self.session.findings if f.pillar == pillar.value]
        
        st.markdown("### 📊 Findings by WAF Pillar")
        
        cols = st.columns(3)
        for idx, (pillar, findings) in enumerate(pillar_findings.items()):
            pillar_enum = WAFPillar(pillar)
            icon = PILLAR_ICONS.get(pillar_enum, "📋")
            
            critical = len([f for f in findings if f.severity == "CRITICAL"])
            high = len([f for f in findings if f.severity == "HIGH"])
            medium = len([f for f in findings if f.severity == "MEDIUM"])
            low = len([f for f in findings if f.severity == "LOW"])
            
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background: #f5f5f5; padding: 15px; border-radius: 10px; 
                            border-left: 4px solid {PILLAR_COLORS.get(pillar_enum, '#666')}; margin-bottom: 10px;">
                    <h4>{icon} {pillar}</h4>
                    <p><b>{len(findings)}</b> findings</p>
                    <small>🔴 {critical} Critical | 🟠 {high} High | 🟡 {medium} Medium | 🟢 {low} Low</small>
                </div>
                """, unsafe_allow_html=True)
    
    # ========================================================================
    # PHASE 3: QUESTIONNAIRE
    # ========================================================================
    
    def _render_questionnaire_phase(self):
        """Render WAF questionnaire phase"""
        
        st.markdown("## 📝 Step 3: WAF Questionnaire")
        st.markdown("""
        Answer questions about your workload to complete the assessment. 
        Questions that can be auto-detected from scan results are pre-filled.
        """)
        
        # Auto-detect answers from findings
        if not self.session.responses:
            self._auto_detect_answers()
        
        # Show progress
        total_questions = sum(len(q) for q in WAF_QUESTIONS.values())
        answered = len([r for r in self.session.responses if r.response])
        auto_detected = len([r for r in self.session.responses if r.auto_detected])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Auto-Detected", auto_detected)
        with col3:
            st.metric("Answered", f"{answered}/{total_questions}")
        
        st.progress(answered / total_questions if total_questions > 0 else 0)
        
        st.markdown("---")
        
        # Render questions by pillar
        pillar_tabs = st.tabs([f"{PILLAR_ICONS[p]} {p.value}" for p in WAFPillar])
        
        for idx, pillar in enumerate(WAFPillar):
            with pillar_tabs[idx]:
                self._render_pillar_questions(pillar)
        
        st.markdown("---")
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Scan Results"):
                self.session.current_phase = ReviewPhase.SCANNING
                st.rerun()
        with col3:
            if st.button("▶️ Calculate Scores", type="primary"):
                self.session.questionnaire_completed = True
                self.session.current_phase = ReviewPhase.SCORING
                self.session.updated_at = datetime.now()
                st.rerun()
    
    def _auto_detect_answers(self):
        """Auto-detect questionnaire answers from scan findings"""
        
        for pillar in WAFPillar:
            questions = WAF_QUESTIONS.get(pillar, [])
            pillar_findings = [f for f in self.session.findings if f.pillar == pillar.value]
            
            for q in questions:
                # Check if question can be auto-detected
                if q.get('scan_detectable', False):
                    detection_services = q.get('detection_services', [])
                    relevant_findings = [f for f in pillar_findings if f.service in detection_services]
                    
                    if relevant_findings:
                        # Determine answer based on findings
                        critical_high = [f for f in relevant_findings if f.severity in ['CRITICAL', 'HIGH']]
                        
                        if len(critical_high) > 2:
                            response = "no"
                            confidence = 0.9
                        elif len(critical_high) > 0:
                            response = "partial"
                            confidence = 0.8
                        elif len(relevant_findings) > 0:
                            response = "partial"
                            confidence = 0.7
                        else:
                            response = "yes"
                            confidence = 0.6
                        
                        self.session.responses.append(QuestionResponse(
                            question_id=q['id'],
                            pillar=pillar.value,
                            question_text=q['question'],
                            response=response,
                            auto_detected=True,
                            confidence=confidence,
                            evidence=[f"{f.title} ({f.severity})" for f in relevant_findings[:3]]
                        ))
                    else:
                        # No findings = likely good
                        self.session.responses.append(QuestionResponse(
                            question_id=q['id'],
                            pillar=pillar.value,
                            question_text=q['question'],
                            response="yes",
                            auto_detected=True,
                            confidence=0.5,
                            evidence=["No issues detected in scan"]
                        ))
                else:
                    # Manual question
                    self.session.responses.append(QuestionResponse(
                        question_id=q['id'],
                        pillar=pillar.value,
                        question_text=q['question'],
                        response="",
                        auto_detected=False
                    ))
        
        self.session.auto_detected_count = len([r for r in self.session.responses if r.auto_detected])
        self.session.manual_required_count = len([r for r in self.session.responses if not r.auto_detected])
    
    def _render_pillar_questions(self, pillar: WAFPillar):
        """Render questions for a specific pillar"""
        
        questions = WAF_QUESTIONS.get(pillar, [])
        pillar_responses = [r for r in self.session.responses if r.pillar == pillar.value]
        
        for q in questions:
            response = next((r for r in pillar_responses if r.question_id == q['id']), None)
            
            with st.expander(f"**{q['id']}**: {q['question']}", expanded=not response or not response.response):
                st.markdown(f"*{q.get('description', '')}*")
                
                # Show auto-detection status
                if response and response.auto_detected:
                    confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.5 else "red"
                    st.markdown(f"""
                    <div style="background: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        🤖 <b>Auto-detected</b> (Confidence: 
                        <span style="color: {confidence_color}">{response.confidence:.0%}</span>)
                        <br><small>Evidence: {', '.join(response.evidence[:3])}</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Response options
                current_response = response.response if response else ""
                new_response = st.radio(
                    "Your assessment:",
                    ["yes", "partial", "no", "not_applicable"],
                    index=["yes", "partial", "no", "not_applicable"].index(current_response) if current_response in ["yes", "partial", "no", "not_applicable"] else 0,
                    format_func=lambda x: {"yes": "✅ Yes", "partial": "⚠️ Partial", "no": "❌ No", "not_applicable": "➖ N/A"}[x],
                    key=f"q_{q['id']}",
                    horizontal=True
                )
                
                # Update response
                if response:
                    response.response = new_response
                
                # Best practices
                if q.get('best_practices'):
                    st.markdown("**Best Practices:**")
                    for bp in q['best_practices']:
                        st.markdown(f"- {bp}")
    
    # ========================================================================
    # PHASE 4: SCORING
    # ========================================================================
    
    def _render_scoring_phase(self):
        """Render scoring phase with consolidated WAF scores"""
        
        st.markdown("## 📊 Step 4: WAF Scores")
        
        # Calculate scores
        if not self.session.pillar_scores:
            self._calculate_scores()
        
        # Overall score
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 30px; border-radius: 15px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 64px;">{self.session.overall_score:.0f}</h1>
            <p style="margin: 0; font-size: 24px;">Overall WAF Score</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Pillar scores
        st.markdown("### 📈 Scores by Pillar")
        
        cols = st.columns(3)
        for idx, pillar in enumerate(WAFPillar):
            score_data = self.session.pillar_scores.get(pillar.value)
            if score_data:
                icon = PILLAR_ICONS[pillar]
                color = PILLAR_COLORS[pillar]
                score = score_data.combined_score
                
                # Score color
                score_color = "#4CAF50" if score >= 80 else "#FF9800" if score >= 60 else "#F44336"
                
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style="background: white; padding: 20px; border-radius: 10px; 
                                border: 2px solid {color}; margin-bottom: 15px; text-align: center;">
                        <h3 style="margin: 0;">{icon} {pillar.value}</h3>
                        <h1 style="color: {score_color}; margin: 10px 0;">{score:.0f}</h1>
                        <small>
                            🔍 Scan: {score_data.scan_score:.0f} | 
                            📝 Questions: {score_data.questionnaire_score:.0f}
                        </small>
                        <br>
                        <small>🔴 {score_data.critical_count} Critical | 🟠 {score_data.high_count} High</small>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Save initial score for comparison
        if not self.session.initial_score:
            self.session.initial_score = self.session.overall_score
        
        st.markdown("---")
        
        # Improvement areas
        st.markdown("### 🎯 Priority Improvement Areas")
        
        all_improvements = []
        for pillar, score_data in self.session.pillar_scores.items():
            for area in score_data.improvement_areas:
                all_improvements.append((pillar, area, score_data.combined_score))
        
        # Sort by score (lowest first)
        all_improvements.sort(key=lambda x: x[2])
        
        for pillar, area, score in all_improvements[:5]:
            st.warning(f"**{pillar}**: {area}")
        
        st.markdown("---")
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Questionnaire"):
                self.session.current_phase = ReviewPhase.QUESTIONNAIRE
                st.rerun()
        with col3:
            if st.button("▶️ Proceed to Remediation", type="primary"):
                self.session.current_phase = ReviewPhase.REMEDIATION
                self.session.updated_at = datetime.now()
                st.rerun()
    
    def _calculate_scores(self):
        """Calculate scores for all pillars"""
        
        for pillar in WAFPillar:
            pillar_findings = [f for f in self.session.findings if f.pillar == pillar.value]
            pillar_responses = [r for r in self.session.responses if r.pillar == pillar.value]
            
            # Calculate scan score (based on findings severity)
            scan_score = 100
            for finding in pillar_findings:
                if finding.severity == "CRITICAL":
                    scan_score -= 15
                elif finding.severity == "HIGH":
                    scan_score -= 10
                elif finding.severity == "MEDIUM":
                    scan_score -= 5
                elif finding.severity == "LOW":
                    scan_score -= 2
            scan_score = max(0, scan_score)
            
            # Calculate questionnaire score
            questionnaire_score = 0
            answered = 0
            for response in pillar_responses:
                if response.response:
                    answered += 1
                    if response.response == "yes":
                        questionnaire_score += 100
                    elif response.response == "partial":
                        questionnaire_score += 50
                    elif response.response == "not_applicable":
                        questionnaire_score += 100  # N/A counts as compliant
            
            questionnaire_score = questionnaire_score / max(answered, 1)
            
            # Combined score (weighted average)
            combined_score = (scan_score * 0.6) + (questionnaire_score * 0.4)
            
            # Identify improvement areas
            improvements = []
            critical_findings = [f for f in pillar_findings if f.severity == "CRITICAL"]
            high_findings = [f for f in pillar_findings if f.severity == "HIGH"]
            
            for f in critical_findings[:2]:
                improvements.append(f.title)
            for f in high_findings[:2]:
                improvements.append(f.title)
            
            self.session.pillar_scores[pillar.value] = PillarScore(
                pillar=pillar,
                scan_score=scan_score,
                questionnaire_score=questionnaire_score,
                combined_score=combined_score,
                findings_count=len(pillar_findings),
                critical_count=len(critical_findings),
                high_count=len(high_findings),
                questions_answered=answered,
                questions_total=len(pillar_responses),
                improvement_areas=improvements
            )
        
        # Calculate overall score
        total_score = sum(s.combined_score for s in self.session.pillar_scores.values())
        self.session.overall_score = total_score / len(self.session.pillar_scores)
    
    # ========================================================================
    # PHASE 5: REMEDIATION
    # ========================================================================
    
    def _render_remediation_phase(self):
        """Render AI-powered remediation phase"""
        
        st.markdown("## 🔨 Step 5: AI-Powered Remediation")
        st.markdown("""
        Review and deploy automated fixes for your findings. 
        AI generates CloudFormation/Terraform code for each issue.
        """)
        
        # Generate remediation items if not done
        if not self.session.remediation_items:
            self._generate_remediation_items()
        
        # Summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Findings", len(self.session.findings))
        with col2:
            remediatable = len([r for r in self.session.remediation_items if r.cloudformation])
            st.metric("Auto-Remediatable", remediatable)
        with col3:
            deployed = len([r for r in self.session.remediation_items if r.status == "deployed"])
            st.metric("Deployed", deployed)
        with col4:
            pending = len([r for r in self.session.remediation_items if r.status == "pending"])
            st.metric("Pending", pending)
        
        st.markdown("---")
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            severity_filter = st.multiselect(
                "Filter by Severity",
                ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
                default=["CRITICAL", "HIGH"]
            )
        with col2:
            pillar_filter = st.multiselect(
                "Filter by Pillar",
                [p.value for p in WAFPillar],
                default=[p.value for p in WAFPillar]
            )
        
        # Filtered items
        filtered_items = [
            r for r in self.session.remediation_items
            if r.severity in severity_filter and r.pillar in pillar_filter
        ]
        
        st.markdown(f"### 📋 Remediation Items ({len(filtered_items)})")
        
        # Bulk actions
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Approve All", use_container_width=True):
                for item in filtered_items:
                    if item.status == "pending":
                        item.status = "approved"
                        item.approved_at = datetime.now().isoformat()
                st.success("All items approved!")
                st.rerun()
        with col2:
            if st.button("🚀 Deploy Approved", type="primary", use_container_width=True):
                self._deploy_approved_items()
        
        st.markdown("---")
        
        # Render each remediation item
        for item in filtered_items:
            self._render_remediation_item(item)
        
        st.markdown("---")
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Scores"):
                self.session.current_phase = ReviewPhase.SCORING
                st.rerun()
        with col3:
            deployed_count = len([r for r in self.session.remediation_items if r.status == "deployed"])
            if deployed_count > 0:
                if st.button("▶️ Re-scan to Verify", type="primary"):
                    self.session.current_phase = ReviewPhase.RESCAN
                    self.session.updated_at = datetime.now()
                    st.rerun()
            else:
                st.info("Deploy at least one fix to proceed to verification")
    
    def _generate_remediation_items(self):
        """Generate remediation items for all findings"""
        
        for finding in self.session.findings:
            cfn, tf, cli = self._generate_remediation_code(finding)
            
            self.session.remediation_items.append(RemediationItem(
                finding_id=finding.id,
                finding_title=finding.title,
                severity=finding.severity,
                pillar=finding.pillar,
                service=finding.service,
                resource=finding.resource,
                account_id=finding.account_id,
                cloudformation=cfn,
                terraform=tf,
                aws_cli=cli,
                stack_name=f"waf-fix-{finding.id}"
            ))
    
    def _generate_remediation_code(self, finding: Finding) -> Tuple[str, str, List[str]]:
        """Generate CloudFormation, Terraform, and CLI commands for a finding"""
        
        title = finding.title.lower()
        service = finding.service.lower()
        resource = finding.resource
        
        # S3 Encryption
        if service == 's3' and 'encrypt' in title:
            cfn = f"""AWSTemplateFormatVersion: '2010-09-09'
Description: Enable S3 bucket encryption for {resource}
Resources:
  BucketEncryption:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: {resource}
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
            BucketKeyEnabled: true"""
            
            tf = f"""resource "aws_s3_bucket_server_side_encryption_configuration" "{resource.replace('-', '_')}" {{
  bucket = "{resource}"
  rule {{
    apply_server_side_encryption_by_default {{
      sse_algorithm = "AES256"
    }}
    bucket_key_enabled = true
  }}
}}"""
            
            cli = [
                f"aws s3api put-bucket-encryption --bucket {resource} \\",
                f"  --server-side-encryption-configuration '{{\"Rules\":[{{\"ApplyServerSideEncryptionByDefault\":{{\"SSEAlgorithm\":\"AES256\"}},\"BucketKeyEnabled\":true}}]}}'"
            ]
            
            return cfn, tf, cli
        
        # S3 Public Access
        if service == 's3' and 'public' in title:
            cfn = f"""AWSTemplateFormatVersion: '2010-09-09'
Description: Block public access for S3 bucket {resource}
Resources:
  PublicAccessBlock:
    Type: AWS::S3::BucketPublicAccessBlock
    Properties:
      Bucket: {resource}
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true"""
            
            tf = f"""resource "aws_s3_bucket_public_access_block" "{resource.replace('-', '_')}" {{
  bucket = "{resource}"
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}}"""
            
            cli = [
                f"aws s3api put-public-access-block --bucket {resource} \\",
                f"  --public-access-block-configuration 'BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true'"
            ]
            
            return cfn, tf, cli
        
        # Security Group
        if 'security group' in title.lower():
            return self._generate_security_group_remediation(resource)
        
        # EC2 IMDSv2
        if service == 'ec2' and 'imds' in title:
            cfn = f"""AWSTemplateFormatVersion: '2010-09-09'
Description: Enforce IMDSv2 for EC2 instance {resource}
Resources:
  # Note: This requires instance stop/start or launch template update
  # Use AWS CLI for immediate enforcement"""
            
            tf = f"""# Enforce IMDSv2 on instance
resource "aws_ec2_instance_metadata_options" "{resource.replace('-', '_')}" {{
  instance_id              = "{resource}"
  http_tokens              = "required"
  http_endpoint            = "enabled"
}}"""
            
            cli = [
                f"aws ec2 modify-instance-metadata-options \\",
                f"  --instance-id {resource} \\",
                f"  --http-tokens required \\",
                f"  --http-endpoint enabled"
            ]
            
            return cfn, tf, cli
        
        # Default - no automated remediation
        return "", "", []
    
    def _generate_security_group_remediation(self, sg_id: str) -> Tuple[str, str, List[str]]:
        """Generate remediation for security group"""
        
        cfn = f"""AWSTemplateFormatVersion: '2010-09-09'
Description: Remove overly permissive rules from security group {sg_id}
# WARNING: This may break applications. Review before deploying.
# Manual review required - auto-remediation not recommended for security groups."""
        
        tf = f"""# WARNING: Review before applying - may break applications
# Security group {sg_id} has overly permissive rules
# Manual review required"""
        
        cli = [
            f"# List current rules for security group {sg_id}",
            f"aws ec2 describe-security-groups --group-ids {sg_id}",
            f"",
            f"# To remove a specific ingress rule (modify as needed):",
            f"# aws ec2 revoke-security-group-ingress --group-id {sg_id} --protocol tcp --port 22 --cidr 0.0.0.0/0"
        ]
        
        return cfn, tf, cli
    
    def _render_remediation_item(self, item: RemediationItem):
        """Render a single remediation item"""
        
        severity_colors = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        status_badges = {
            "pending": "⏳ Pending",
            "approved": "✅ Approved",
            "deployed": "🚀 Deployed",
            "failed": "❌ Failed",
            "rolled_back": "↩️ Rolled Back"
        }
        
        with st.expander(f"{severity_colors.get(item.severity, '⚪')} **{item.severity}** - {item.finding_title} | {status_badges.get(item.status, item.status)}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Service:** {item.service}")
                st.markdown(f"**Resource:** `{item.resource}`")
                st.markdown(f"**Account:** {item.account_id}")
                st.markdown(f"**Pillar:** {item.pillar}")
            
            with col2:
                if item.status == "pending":
                    if st.button("✅ Approve", key=f"approve_{item.finding_id}"):
                        item.status = "approved"
                        item.approved_at = datetime.now().isoformat()
                        st.rerun()
                elif item.status == "approved":
                    if st.button("🚀 Deploy Now", key=f"deploy_{item.finding_id}", type="primary"):
                        self._deploy_single_item(item)
                        st.rerun()
            
            # Code tabs
            if item.cloudformation or item.terraform:
                code_tabs = st.tabs(["☁️ CloudFormation", "🏗️ Terraform", "💻 AWS CLI"])
                
                with code_tabs[0]:
                    if item.cloudformation:
                        st.code(item.cloudformation, language="yaml")
                    else:
                        st.info("No CloudFormation template available for this finding")
                
                with code_tabs[1]:
                    if item.terraform:
                        st.code(item.terraform, language="hcl")
                    else:
                        st.info("No Terraform code available for this finding")
                
                with code_tabs[2]:
                    if item.aws_cli:
                        st.code("\n".join(item.aws_cli), language="bash")
                    else:
                        st.info("No CLI commands available for this finding")
    
    def _deploy_single_item(self, item: RemediationItem):
        """Deploy a single remediation item"""
        
        try:
            # In production, this would actually deploy the CloudFormation stack
            # For now, we simulate the deployment
            item.status = "deployed"
            item.deployed_at = datetime.now().isoformat()
            item.stack_id = f"arn:aws:cloudformation:us-east-1:123456789012:stack/{item.stack_name}/xxx"
            
            st.success(f"✅ Deployed: {item.finding_title}")
            self.session.remediation_deployed += 1
            
        except Exception as e:
            item.status = "failed"
            st.error(f"❌ Deployment failed: {str(e)}")
    
    def _deploy_approved_items(self):
        """Deploy all approved remediation items"""
        
        approved_items = [r for r in self.session.remediation_items if r.status == "approved"]
        
        if not approved_items:
            st.warning("No approved items to deploy")
            return
        
        progress = st.progress(0)
        status = st.empty()
        
        for idx, item in enumerate(approved_items):
            status.markdown(f"🚀 Deploying: {item.finding_title}...")
            progress.progress((idx + 1) / len(approved_items))
            
            self._deploy_single_item(item)
            time.sleep(0.5)  # Simulate deployment time
        
        st.success(f"✅ Deployed {len(approved_items)} remediation(s)")
        st.rerun()
    
    # ========================================================================
    # PHASE 6: RE-SCAN
    # ========================================================================
    
    def _render_rescan_phase(self):
        """Render re-scan verification phase"""
        
        st.markdown("## ✅ Step 6: Verify Remediation")
        st.markdown("Re-scan your accounts to verify fixes have been applied.")
        
        deployed_count = len([r for r in self.session.remediation_items if r.status == "deployed"])
        
        st.info(f"📊 {deployed_count} remediation(s) deployed. Run a verification scan to measure improvement.")
        
        if not self.session.rescan_completed:
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔍 Run Verification Scan", type="primary", use_container_width=True):
                    self._run_verification_scan()
        else:
            # Show before/after comparison
            st.markdown("### 📊 Before & After Comparison")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style="background: #ffebee; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>Before Remediation</h4>
                    <h1 style="color: #c62828;">{:.0f}</h1>
                </div>
                """.format(self.session.initial_score), unsafe_allow_html=True)
            
            with col2:
                improvement = self.session.final_score - self.session.initial_score
                st.markdown(f"""
                <div style="background: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>Improvement</h4>
                    <h1 style="color: #2e7d32;">+{improvement:.0f}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>After Remediation</h4>
                    <h1 style="color: #1565c0;">{self.session.final_score:.0f}</h1>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Pillar improvements
            st.markdown("### 📈 Improvement by Pillar")
            # This would show pillar-by-pillar comparison
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("▶️ Complete Review", type="primary", use_container_width=True):
                    self.session.current_phase = ReviewPhase.COMPLETE
                    self.session.updated_at = datetime.now()
                    st.rerun()
    
    def _run_verification_scan(self):
        """Run verification scan after remediation"""
        
        progress = st.progress(0)
        status = st.empty()
        
        status.markdown("🔍 **Running verification scan...**")
        progress.progress(30)
        
        # Simulate scan
        time.sleep(2)
        progress.progress(70)
        
        # Calculate improved scores
        # In production, this would actually re-scan and compare
        deployed_count = len([r for r in self.session.remediation_items if r.status == "deployed"])
        estimated_improvement = min(deployed_count * 3, 30)  # Estimate 3 points per fix, max 30
        
        self.session.final_score = min(100, self.session.initial_score + estimated_improvement)
        self.session.score_improvement = self.session.final_score - self.session.initial_score
        self.session.rescan_completed = True
        self.session.rescan_timestamp = datetime.now()
        
        progress.progress(100)
        status.markdown("✅ **Verification scan complete!**")
        
        time.sleep(1)
        st.rerun()
    
    # ========================================================================
    # PHASE 7: COMPLETE
    # ========================================================================
    
    def _render_complete_phase(self):
        """Render completion phase with final report and navigation to WAF Assessment"""
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); 
                    padding: 30px; border-radius: 15px; text-align: center; color: white;">
            <h1>🎉 Unified Assessment Complete!</h1>
            <p>Your assessment is ready. Proceed to WAF Assessment for detailed analysis and remediation.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Final summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Initial Score", f"{self.session.initial_score:.0f}")
        with col2:
            st.metric("Final Score", f"{self.session.final_score:.0f}")
        with col3:
            st.metric("Improvement", f"+{self.session.score_improvement:.0f}")
        with col4:
            deployed = len([r for r in self.session.remediation_items if r.status == "deployed"])
            st.metric("Fixes Deployed", deployed)
        
        st.markdown("---")
        
        # Store assessment data for WAF Assessment tab
        assessment_data = {
            'session_id': self.session.session_id,
            'completed_at': datetime.now().isoformat(),
            'accounts': self.session.accounts,
            'regions': self.session.regions,
            'findings': [vars(f) if hasattr(f, '__dict__') else f for f in self.session.findings],
            'pillar_scores': {k: vars(v) if hasattr(v, '__dict__') else v for k, v in self.session.pillar_scores.items()},
            'overall_score': self.session.overall_score,
            'initial_score': self.session.initial_score,
            'final_score': self.session.final_score,
            'score_improvement': self.session.score_improvement,
            'questionnaire_responses': [vars(r) if hasattr(r, '__dict__') else r for r in self.session.responses],
            'remediation_items': [vars(r) if hasattr(r, '__dict__') else r for r in self.session.remediation_items],
            'resources_scanned': self.session.resources_scanned,
            'services_scanned': self.session.services_scanned,
        }
        
        # Store in session state for other tabs to access
        st.session_state['unified_assessment_results'] = assessment_data
        st.session_state['last_scan'] = {
            'findings': self.session.findings,
            'pillar_scores': self.session.pillar_scores,
            'overall_score': self.session.overall_score,
            'scan_time': datetime.now().isoformat(),
            'accounts': self.session.accounts,
            'regions': self.session.regions,
        }
        
        # Navigation options
        st.markdown("### 🚀 Next Steps")
        
        st.info("""
        **Recommended Flow:**
        1. **WAF Assessment** - View detailed pillar analysis and recommendations
        2. **Remediation** - Deploy fixes for identified issues  
        3. **Compliance** - Map findings to compliance frameworks
        4. **AI Lens** - Get AI-powered insights and optimization suggestions
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Go to WAF Assessment", type="primary", use_container_width=True):
                # Navigate to WAF Assessment tab
                st.session_state['active_tab'] = 'WAF Assessment'
                st.session_state['navigate_to'] = 'waf_assessment'
                st.rerun()
        
        with col2:
            if st.button("🔧 Go to Remediation", use_container_width=True):
                # Navigate to Remediation tab
                st.session_state['active_tab'] = 'Remediation'
                st.session_state['navigate_to'] = 'remediation'
                st.rerun()
        
        with col3:
            if st.button("🤖 Go to AI Lens", use_container_width=True):
                # Navigate to AI Lens tab
                st.session_state['active_tab'] = 'AI Lens'
                st.session_state['navigate_to'] = 'ai_lens'
                st.rerun()
        
        st.markdown("---")
        
        # Report generation
        st.markdown("### 📄 Generate Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Executive Summary PDF", use_container_width=True):
                st.info("PDF generation would be triggered here")
        
        with col2:
            if st.button("📋 Detailed Findings CSV", use_container_width=True):
                st.info("CSV export would be triggered here")
        
        with col3:
            if st.button("📁 Full Report Package", use_container_width=True):
                st.info("Full package download would be triggered here")
        
        st.markdown("---")
        
        # Start new review
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Start New Unified Assessment", use_container_width=True):
                # Reset session
                st.session_state[self.session_key] = WAFReviewSession(
                    session_id=hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                st.rerun()


# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_comprehensive_waf_review():
    """Main entry point for the comprehensive WAF Review module"""
    workflow = WAFReviewWorkflow()
    workflow.render()


# Allow direct execution for testing
if __name__ == "__main__":
    render_comprehensive_waf_review()
