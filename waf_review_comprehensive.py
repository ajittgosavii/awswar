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

Version: 1.3.0 - Integrated real remediation engine with CloudFormation deployment
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

# Import Firebase for questionnaire persistence
try:
    from auth_database_firebase import get_database_manager
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    def get_database_manager():
        return None

# Import complete 195-question database
try:
    from waf_questions_complete import WAF_QUESTIONS_COMPLETE, WAFPillar as WAFPillarComplete
    USE_COMPLETE_QUESTIONS = True
except ImportError:
    USE_COMPLETE_QUESTIONS = False
    WAFPillarComplete = None

# Import real remediation engine for CloudFormation deployment
try:
    from remediation_engine_integrated import (
        RemediationEngine,
        RemediationAction,
        RemediationStatus,
        RiskLevel,
        DeploymentMethod,
        CloudFormationDeployer,
        CLIExecutor
    )
    REMEDIATION_ENGINE_AVAILABLE = True
except ImportError:
    REMEDIATION_ENGINE_AVAILABLE = False
    RemediationEngine = None
    RemediationAction = None
    RemediationStatus = None

# Import paginated questionnaire wizard for better UX with 200+ questions
try:
    from waf_questionnaire_wizard import (
        WAFQuestionnaireWizard,
        render_paginated_questionnaire,
        QuestionResponse as WizardQuestionResponse
    )
    WIZARD_AVAILABLE = True
except ImportError:
    WIZARD_AVAILABLE = False
    print("Paginated questionnaire wizard not available - using legacy mode")

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
# WAF QUESTIONNAIRE DEFINITIONS - 195+ Questions
# ============================================================================

# Use complete 195-question database if available, otherwise use fallback
if USE_COMPLETE_QUESTIONS:
    # Convert keys from waf_questions_complete's WAFPillar to our local WAFPillar
    # This is needed because Python enums with same values are different objects
    WAF_QUESTIONS = {}
    for pillar in WAFPillar:
        # Find matching key in WAF_QUESTIONS_COMPLETE by value
        for key in WAF_QUESTIONS_COMPLETE.keys():
            if key.value == pillar.value:
                WAF_QUESTIONS[pillar] = WAF_QUESTIONS_COMPLETE[key]
                break
else:
    # Fallback: Basic 43-question set (if waf_questions_complete.py not found)
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
    
    def _get_user_id(self) -> Optional[str]:
        """Get current user ID for Firebase storage"""
        user_info = st.session_state.get('user_info', {})
        return user_info.get('id') or user_info.get('email', 'anonymous')
    
    def save_progress(self) -> bool:
        """Save questionnaire progress to Firebase"""
        if not FIREBASE_AVAILABLE:
            st.warning("⚠️ Firebase not available - progress saved locally only")
            return False
        
        try:
            db = get_database_manager()
            if not db or not db.db_ref:
                st.warning("⚠️ Database connection not available")
                return False
            
            user_id = self._get_user_id()
            if not user_id:
                st.warning("⚠️ Please log in to save progress")
                return False
            
            # Prepare data for saving
            progress_data = {
                'session_id': self.session.session_id,
                'updated_at': datetime.now().isoformat(),
                'current_phase': self.session.current_phase.value,
                'scan_completed': self.session.scan_completed,
                'questionnaire_completed': self.session.questionnaire_completed,
                'responses': [
                    {
                        'question_id': r.question_id,
                        'pillar': r.pillar,
                        'response': r.response,
                        'auto_detected': r.auto_detected,
                        'confidence': r.confidence,
                        'notes': r.notes
                    }
                    for r in self.session.responses
                ],
                'accounts': self.session.accounts,
                'overall_score': self.session.overall_score,
                'pillar_scores': {
                    k: {
                        'scan_score': v.scan_score,
                        'questionnaire_score': v.questionnaire_score,
                        'combined_score': v.combined_score,
                        'findings_count': v.findings_count
                    }
                    for k, v in self.session.pillar_scores.items()
                } if self.session.pillar_scores else {}
            }
            
            # Save to Firebase under user's progress
            db.db_ref.child('waf_progress').child(user_id).set(progress_data)
            return True
            
        except Exception as e:
            st.error(f"❌ Error saving progress: {str(e)}")
            return False
    
    def load_progress(self) -> bool:
        """Load saved questionnaire progress from Firebase"""
        if not FIREBASE_AVAILABLE:
            return False
        
        try:
            db = get_database_manager()
            if not db or not db.db_ref:
                return False
            
            user_id = self._get_user_id()
            if not user_id:
                return False
            
            # Load from Firebase
            progress_data = db.db_ref.child('waf_progress').child(user_id).get()
            
            if not progress_data:
                return False
            
            # Restore responses
            saved_responses = progress_data.get('responses', [])
            if saved_responses:
                self.session.responses = []
                for r in saved_responses:
                    self.session.responses.append(QuestionResponse(
                        question_id=r.get('question_id', ''),
                        pillar=r.get('pillar', ''),
                        question_text='',  # Will be filled from questions database
                        response=r.get('response', ''),
                        auto_detected=r.get('auto_detected', False),
                        confidence=r.get('confidence', 0.0),
                        notes=r.get('notes', '')
                    ))
            
            # Restore other state
            phase_value = progress_data.get('current_phase', 'setup')
            for phase in ReviewPhase:
                if phase.value == phase_value:
                    self.session.current_phase = phase
                    break
            
            self.session.scan_completed = progress_data.get('scan_completed', False)
            self.session.questionnaire_completed = progress_data.get('questionnaire_completed', False)
            self.session.accounts = progress_data.get('accounts', [])
            self.session.overall_score = progress_data.get('overall_score', 0.0)
            
            return True
            
        except Exception as e:
            print(f"Error loading progress: {e}")
            return False
    
    def has_saved_progress(self) -> Tuple[bool, Optional[str]]:
        """Check if user has saved progress"""
        if not FIREBASE_AVAILABLE:
            return False, None
        
        try:
            db = get_database_manager()
            if not db or not db.db_ref:
                return False, None
            
            user_id = self._get_user_id()
            if not user_id:
                return False, None
            
            progress_data = db.db_ref.child('waf_progress').child(user_id).get()
            
            if progress_data:
                updated_at = progress_data.get('updated_at', '')
                responses_count = len(progress_data.get('responses', []))
                answered = len([r for r in progress_data.get('responses', []) if r.get('response')])
                return True, f"Last saved: {updated_at[:16]} ({answered} answers)"
            
            return False, None
            
        except Exception:
            return False, None
    
    def clear_saved_progress(self) -> bool:
        """Clear saved progress from Firebase"""
        if not FIREBASE_AVAILABLE:
            return False
        
        try:
            db = get_database_manager()
            if not db or not db.db_ref:
                return False
            
            user_id = self._get_user_id()
            if not user_id:
                return False
            
            db.db_ref.child('waf_progress').child(user_id).delete()
            return True
            
        except Exception:
            return False
    
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
                # Use pillar from scan if available, otherwise map from service
                pillar = finding.get('pillar', '') or self._map_service_to_pillar(finding.get('service', ''))
                
                findings.append(Finding(
                    id=hashlib.md5(f"{account_id}-{finding.get('resource', '')}-{finding.get('title', '')}".encode()).hexdigest()[:8],
                    title=finding.get('title', 'Unknown'),
                    description=finding.get('description', ''),
                    severity=finding.get('severity', 'MEDIUM'),
                    pillar=pillar,
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
        
        # Update session state for dashboard - store findings immediately
        findings_list = []
        for f in findings:
            if hasattr(f, '__dict__'):
                findings_list.append({
                    'severity': getattr(f, 'severity', 'MEDIUM'),
                    'title': getattr(f, 'title', ''),
                    'pillar': getattr(f, 'pillar', ''),
                    'service': getattr(f, 'service', ''),
                })
            elif isinstance(f, dict):
                findings_list.append(f)
        st.session_state['last_findings'] = findings_list
        
        st.rerun()
    
    def _map_service_to_pillar(self, service: str) -> str:
        """Map AWS service to WAF pillar"""
        service = service.upper() if service else ''
        service_pillar_map = {
            # Security pillar
            'IAM': WAFPillar.SECURITY.value,
            'S3': WAFPillar.SECURITY.value,
            'VPC': WAFPillar.SECURITY.value,
            'KMS': WAFPillar.SECURITY.value,
            'CLOUDTRAIL': WAFPillar.SECURITY.value,
            'GUARDDUTY': WAFPillar.SECURITY.value,
            'SECURITY HUB': WAFPillar.SECURITY.value,
            'SECURITYHUB': WAFPillar.SECURITY.value,
            'WAF': WAFPillar.SECURITY.value,
            'SHIELD': WAFPillar.SECURITY.value,
            'SECRETS MANAGER': WAFPillar.SECURITY.value,
            'SECRETSMANAGER': WAFPillar.SECURITY.value,
            'ACM': WAFPillar.SECURITY.value,
            'INSPECTOR': WAFPillar.SECURITY.value,
            'MACIE': WAFPillar.SECURITY.value,
            'NETWORK FIREWALL': WAFPillar.SECURITY.value,
            
            # Reliability pillar
            'EC2': WAFPillar.RELIABILITY.value,
            'RDS': WAFPillar.RELIABILITY.value,
            'ELB': WAFPillar.RELIABILITY.value,
            'ELB/ALB': WAFPillar.RELIABILITY.value,
            'ALB': WAFPillar.RELIABILITY.value,
            'NLB': WAFPillar.RELIABILITY.value,
            'AUTO SCALING': WAFPillar.RELIABILITY.value,
            'AUTOSCALING': WAFPillar.RELIABILITY.value,
            'ROUTE53': WAFPillar.RELIABILITY.value,
            'ROUTE 53': WAFPillar.RELIABILITY.value,
            'BACKUP': WAFPillar.RELIABILITY.value,
            'ELASTICACHE': WAFPillar.RELIABILITY.value,
            'DYNAMODB': WAFPillar.RELIABILITY.value,
            'SQS': WAFPillar.RELIABILITY.value,
            'SNS': WAFPillar.RELIABILITY.value,
            
            # Operational Excellence pillar
            'CLOUDWATCH': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'CLOUDFORMATION': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'CONFIG': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'SYSTEMS MANAGER': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'SSM': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'X-RAY': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'XRAY': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'CODEPIPELINE': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'CODEBUILD': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'CODEDEPLOY': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            'EVENTBRIDGE': WAFPillar.OPERATIONAL_EXCELLENCE.value,
            
            # Performance Efficiency pillar
            'LAMBDA': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'ECS': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'EKS': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'FARGATE': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'CLOUDFRONT': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'API GATEWAY': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'APIGATEWAY': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            'GLOBAL ACCELERATOR': WAFPillar.PERFORMANCE_EFFICIENCY.value,
            
            # Cost Optimization pillar
            'COST EXPLORER': WAFPillar.COST_OPTIMIZATION.value,
            'TRUSTED ADVISOR': WAFPillar.COST_OPTIMIZATION.value,
            'BUDGETS': WAFPillar.COST_OPTIMIZATION.value,
            'SAVINGS PLANS': WAFPillar.COST_OPTIMIZATION.value,
            'RESERVED INSTANCES': WAFPillar.COST_OPTIMIZATION.value,
            'COMPUTE OPTIMIZER': WAFPillar.COST_OPTIMIZATION.value,
            
            # Sustainability pillar
            'SUSTAINABILITY': WAFPillar.SUSTAINABILITY.value,
            'GRAVITON': WAFPillar.SUSTAINABILITY.value,
        }
        return service_pillar_map.get(service, WAFPillar.SECURITY.value)
    
    # ========================================================================
    # PHASE 2: SCANNING
    # ========================================================================
    
    def _render_scanning_phase(self):
        """Render scanning phase - contained to prevent UI bleeding to other tabs"""
        
        # Use a container to isolate the scanning UI
        scanning_container = st.container()
        
        with scanning_container:
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
        """Scan using Security Hub - FIXED VERSION"""
        findings = []
        
        connected_accounts = st.session_state.get('connected_accounts', [])
        
        if not connected_accounts:
            if st.session_state.get('aws_access_key') and st.session_state.get('aws_secret_key'):
                connected_accounts = [{
                    'name': 'Primary Account',
                    'access_key': st.session_state.get('aws_access_key'),
                    'secret_key': st.session_state.get('aws_secret_key'),
                    'region': st.session_state.get('aws_region', 'us-east-1')
                }]
        
        if not connected_accounts:
            return []
        
        for account in connected_accounts:
            try:
                # Create session using the same pattern as streamlit_app.py
                session = self._create_account_session(account)
                
                if not session:
                    continue
                
                # Query Security Hub
                securityhub = session.client('securityhub')
                
                # Get findings
                paginator = securityhub.get_paginator('get_findings')
                
                filters = {
                    'RecordState': [{'Value': 'ACTIVE', 'Comparison': 'EQUALS'}],
                    'WorkflowStatus': [{'Value': 'NEW', 'Comparison': 'EQUALS'}]
                }
                
                for page in paginator.paginate(Filters=filters, MaxResults=100):
                    for sh_finding in page.get('Findings', []):
                        severity = sh_finding.get('Severity', {}).get('Label', 'MEDIUM')
                        finding_type = sh_finding.get('Type', [''])[0] if sh_finding.get('Type') else ''
                        pillar = self._map_securityhub_to_pillar(finding_type)
                        
                        finding = Finding(
                            id=sh_finding.get('Id', ''),
                            title=sh_finding.get('Title', 'Unknown'),
                            description=sh_finding.get('Description', ''),
                            severity=severity,
                            pillar=pillar,
                            service='Security Hub',
                            resource=sh_finding.get('Resources', [{}])[0].get('Id', 'N/A'),
                            account_id=sh_finding.get('AwsAccountId', ''),
                            region=sh_finding.get('Region', ''),
                            recommendation=sh_finding.get('Remediation', {}).get('Recommendation', {}).get('Text', '')
                        )
                        findings.append(finding)
                
            except Exception as e:
                st.warning(f"Security Hub query failed for {account.get('name', 'account')}: {str(e)}")
        
        return findings
    
    def _map_securityhub_to_pillar(self, finding_type: str) -> str:
        """Map Security Hub finding type to WAF pillar"""
        finding_type_lower = finding_type.lower()
        
        if any(x in finding_type_lower for x in ['iam', 'encryption', 'kms', 'secret', 'password', 'access']):
            return 'Security'
        elif any(x in finding_type_lower for x in ['backup', 'availability', 'redundancy', 'failover']):
            return 'Reliability'
        elif any(x in finding_type_lower for x in ['performance', 'latency', 'throughput']):
            return 'Performance Efficiency'
        elif any(x in finding_type_lower for x in ['cost', 'unused', 'idle', 'savings']):
            return 'Cost Optimization'
        elif any(x in finding_type_lower for x in ['logging', 'monitoring', 'cloudwatch', 'cloudtrail']):
            return 'Operational Excellence'
        else:
            return 'Security'
    
    def _create_account_session(self, account: dict):
        """Create boto3 session for an account - matches streamlit_app.py pattern"""
        try:
            # Pattern 1: Organizations import with credentials sub-dict
            if account.get('connection_type') == 'organizations':
                return boto3.Session(
                    aws_access_key_id=account['credentials']['access_key'],
                    aws_secret_access_key=account['credentials']['secret_key'],
                    region_name=account.get('region', 'us-east-1')
                )
            
            # Pattern 2: AssumeRole authentication
            elif account.get('auth_method') == 'assume_role':
                # Check for hub credentials
                if 'multi_hub_access_key' not in st.session_state or 'multi_hub_secret_key' not in st.session_state:
                    st.error(f"❌ Hub credentials not configured. Please set them in Multi-Account → AssumeRole Setup (Step 1)")
                    return None
                
                # Create base session with hub credentials
                base_session = boto3.Session(
                    aws_access_key_id=st.session_state.multi_hub_access_key,
                    aws_secret_access_key=st.session_state.multi_hub_secret_key
                )
                
                # Import and use the assume_role helper
                try:
                    from aws_connector import assume_role
                except ImportError:
                    st.error("❌ aws_connector module not available")
                    return None
                
                # Assume the role
                assumed_creds = assume_role(
                    base_session,
                    account['role_arn'],
                    account.get('external_id'),
                    session_name="WAFReviewScan"
                )
                
                if not assumed_creds:
                    st.error(f"❌ Failed to assume role: {account.get('role_arn')}")
                    return None
                
                # Create session with assumed credentials
                return boto3.Session(
                    aws_access_key_id=assumed_creds.access_key_id,
                    aws_secret_access_key=assumed_creds.secret_access_key,
                    aws_session_token=assumed_creds.session_token,
                    region_name=account.get('region', 'us-east-1')
                )
            
            # Pattern 3: Direct manual credentials
            else:
                access_key = account.get('access_key')
                secret_key = account.get('secret_key')
                
                if not access_key or not secret_key:
                    st.warning(f"⚠️ No credentials for {account.get('name', 'account')}")
                    return None
                
                return boto3.Session(
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=account.get('region', 'us-east-1')
                )
                
        except Exception as e:
            st.error(f"❌ Session creation failed for {account.get('name', 'account')}: {str(e)}")
            return None
    
    def _scan_direct_api(self) -> List[Finding]:
        """Scan using direct AWS API calls - FIXED VERSION using AWSLandscapeScanner"""
        findings = []
        
        # Check if we have connected accounts
        connected_accounts = st.session_state.get('connected_accounts', [])
        
        if not connected_accounts:
            # Try single account from session
            if st.session_state.get('aws_access_key') and st.session_state.get('aws_secret_key'):
                connected_accounts = [{
                    'name': 'Primary Account',
                    'access_key': st.session_state.get('aws_access_key'),
                    'secret_key': st.session_state.get('aws_secret_key'),
                    'region': st.session_state.get('aws_region', 'us-east-1')
                }]
        
        if not connected_accounts:
            st.warning("⚠️ No AWS accounts connected. Please connect accounts in the AWS Connector tab.")
            return []
        
        # Import scanner
        try:
            from landscape_scanner import AWSLandscapeScanner
        except ImportError:
            st.error("❌ Landscape scanner module not available")
            return []
        
        total_accounts = len(connected_accounts)
        
        for idx, account in enumerate(connected_accounts):
            account_name = account.get('name', f'Account {idx+1}')
            
            st.markdown(f"**Scanning {account_name}...** ({idx+1}/{total_accounts})")
            
            try:
                # Create boto3 session using the unified method
                session = self._create_account_session(account)
                
                if not session:
                    st.warning(f"⚠️ Could not create session for {account_name}")
                    continue
                
                # Get account ID
                try:
                    sts = session.client('sts')
                    account_id = sts.get_caller_identity()['Account']
                except Exception as e:
                    account_id = account.get('account_id', 'unknown')
                    st.warning(f"Could not get account ID: {str(e)}")
                
                # Initialize scanner with session
                scanner = AWSLandscapeScanner(session)
                
                # Run scan
                regions = [account.get('region', 'us-east-1')]
                
                assessment = scanner.run_scan(regions=regions)
                
                # Convert landscape findings to our Finding format
                for lf in assessment.findings:
                    finding = Finding(
                        id=lf.id,
                        title=lf.title,
                        description=lf.description,
                        severity=lf.severity,
                        pillar=lf.pillar,
                        service=lf.source_service,
                        resource=', '.join(lf.affected_resources[:3]) if lf.affected_resources else 'N/A',
                        account_id=account_id,
                        region=lf.region or regions[0],
                        recommendation=lf.recommendation
                    )
                    findings.append(finding)
                
                st.success(f"✅ {account_name}: Found {len(assessment.findings)} findings")
                
            except Exception as e:
                st.error(f"❌ Error scanning {account_name}: {str(e)}")
                import traceback
                with st.expander("Error Details"):
                    st.code(traceback.format_exc())
        
        return findings
    
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
    
    def _get_pending_questions_by_pillar(self) -> Dict[str, List[Dict]]:
        """Get pending (unanswered) questions organized by pillar"""
        pending_by_pillar = {}
        
        for pillar in WAFPillar:
            questions = WAF_QUESTIONS.get(pillar, [])
            pillar_responses = {r.question_id: r for r in self.session.responses if r.pillar == pillar.value}
            
            pending = []
            for q in questions:
                response = pillar_responses.get(q['id'])
                if not response or not response.response:
                    pending.append(q)
            
            if pending:
                pending_by_pillar[pillar.value] = pending
        
        return pending_by_pillar
    
    def _render_questionnaire_phase(self):
        """
        Render WAF questionnaire phase
        Uses paginated wizard for better UX with 200+ questions
        """
        
        st.markdown("## 📝 Step 3: WAF Questionnaire")
        
        # Mode toggle - only show if wizard is available
        use_wizard = st.session_state.get('use_paginated_questionnaire', True)
        
        col_header, col_toggle = st.columns([3, 1])
        with col_header:
            st.markdown("""
            Answer questions about your workload to complete the assessment.
            Questions that can be auto-detected from scan results are pre-filled.
            """)
        
        with col_toggle:
            if WIZARD_AVAILABLE:
                new_mode = st.toggle(
                    "📄 One per page",
                    value=use_wizard,
                    help="Show one question per page (recommended for 200+ questions)"
                )
                if new_mode != use_wizard:
                    st.session_state.use_paginated_questionnaire = new_mode
                    st.rerun()
        
        # Check for saved progress
        has_saved, saved_info = self.has_saved_progress()
        if has_saved and not self.session.responses:
            st.info(f"📂 **Saved progress found!** {saved_info}")
            col_restore, col_new = st.columns(2)
            with col_restore:
                if st.button("📥 Restore Saved Progress", type="primary", use_container_width=True):
                    if self.load_progress():
                        st.success("✅ Progress restored!")
                        st.rerun()
                    else:
                        st.error("❌ Could not restore progress")
            with col_new:
                if st.button("🆕 Start Fresh", use_container_width=True):
                    self.clear_saved_progress()
                    self._auto_detect_answers()
                    st.rerun()
            st.markdown("---")
        
        # Auto-detect answers from findings (if no responses yet)
        if not self.session.responses:
            self._auto_detect_answers()
        
        # Render based on mode
        if WIZARD_AVAILABLE and use_wizard:
            self._render_questionnaire_wizard()
        else:
            self._render_questionnaire_legacy()
    
    def _render_questionnaire_wizard(self):
        """Render paginated questionnaire wizard - one question per page"""
        
        # Convert WAF_QUESTIONS to wizard format
        questions_for_wizard = {}
        for pillar in WAFPillar:
            questions_for_wizard[pillar] = WAF_QUESTIONS.get(pillar, [])
        
        # Define callbacks
        def on_save(responses):
            """Called when user saves progress in wizard"""
            self.session.responses = responses
            if self.save_progress():
                st.toast("✅ Progress saved!", icon="💾")
        
        def on_complete(responses):
            """Called when questionnaire is completed via wizard"""
            self.session.responses = responses
            self.session.questionnaire_completed = True
            self.session.current_phase = ReviewPhase.SCORING
            self.session.updated_at = datetime.now()
            self.save_progress()
            st.rerun()
        
        # Render the paginated wizard
        render_paginated_questionnaire(
            questions=questions_for_wizard,
            responses=self.session.responses,
            on_save=on_save,
            on_complete=on_complete
        )
        
        # Back button (separate from wizard navigation)
        st.markdown("---")
        if st.button("⬅️ Back to Scan Results", use_container_width=False):
            self.session.current_phase = ReviewPhase.SCANNING
            st.rerun()
    
    def _render_questionnaire_legacy(self):
        """Render legacy questionnaire - all questions at once (original method)"""
        
        # Show progress - count correctly
        total_questions = sum(len(q) for q in WAF_QUESTIONS.values())
        # Auto-detected = questions with auto-filled answers
        auto_detected = len([r for r in self.session.responses if r.auto_detected and r.response])
        # Answered = questions with any response (auto or manual)
        answered = len([r for r in self.session.responses if r.response])
        # Pending = questions without answers
        pending = total_questions - answered
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Auto-Detected", auto_detected)
        with col3:
            st.metric("Answered", f"{answered}/{total_questions}")
        with col4:
            st.metric("Pending", pending)
        
        st.progress(answered / total_questions if total_questions > 0 else 0)
        
        # Get pending questions by pillar
        pending_by_pillar = self._get_pending_questions_by_pillar()
        
        # Show pending questions summary if there are any
        if pending > 0:
            st.markdown("---")
            
            # Filter toggle
            show_pending_only = st.checkbox("🔍 **Show Pending Questions Only**", key="show_pending_filter")
            
            # Show which pillars have pending questions
            pending_pillars = []
            for pillar in WAFPillar:
                pillar_pending = pending_by_pillar.get(pillar.value, [])
                if pillar_pending:
                    pending_pillars.append(f"{PILLAR_ICONS[pillar]} {pillar.value} ({len(pillar_pending)})")
            
            if pending_pillars:
                st.warning(f"⚠️ **Pending questions in:** {', '.join(pending_pillars)}")
                
                # Quick jump to pending questions
                with st.expander("📋 **View All Pending Questions**", expanded=False):
                    for pillar_name, questions in pending_by_pillar.items():
                        st.markdown(f"**{pillar_name}:**")
                        for q in questions:
                            st.markdown(f"- `{q['id']}`: {q['question'][:80]}...")
        else:
            show_pending_only = False
            st.success("✅ **All questions answered!** You can now calculate scores.")
        
        st.markdown("---")
        
        # Build pillar tab labels with pending counts
        pillar_tab_labels = []
        for p in WAFPillar:
            pillar_pending = pending_by_pillar.get(p.value, [])
            if pillar_pending:
                pillar_tab_labels.append(f"{PILLAR_ICONS[p]} {p.value} ⚠️({len(pillar_pending)})")
            else:
                pillar_tab_labels.append(f"{PILLAR_ICONS[p]} {p.value} ✅")
        
        # Render questions by pillar
        pillar_tabs = st.tabs(pillar_tab_labels)
        
        for idx, pillar in enumerate(WAFPillar):
            with pillar_tabs[idx]:
                self._render_pillar_questions(pillar, show_pending_only=show_pending_only)
        
        st.markdown("---")
        
        # Navigation with Save button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Scan Results", use_container_width=True):
                self.session.current_phase = ReviewPhase.SCANNING
                st.rerun()
        with col2:
            # Save Progress button
            if st.button("💾 Save Progress", use_container_width=True, type="secondary"):
                if self.save_progress():
                    st.success("✅ Progress saved! You can continue later.")
                    time.sleep(1)
                    st.rerun()
        with col3:
            if st.button("▶️ Calculate Scores", type="primary", use_container_width=True):
                # Auto-save before moving to next phase
                self.save_progress()
                self.session.questionnaire_completed = True
                self.session.current_phase = ReviewPhase.SCORING
                self.session.updated_at = datetime.now()
                st.rerun()
        
        # Show last saved info
        has_saved, saved_info = self.has_saved_progress()
        if has_saved:
            st.caption(f"💾 {saved_info}")
    
    def _auto_detect_answers(self):
        """Auto-detect questionnaire answers from scan findings"""
        
        # Debug: Show findings count
        total_findings = len(self.session.findings)
        
        for pillar in WAFPillar:
            questions = WAF_QUESTIONS.get(pillar, [])
            pillar_findings = [f for f in self.session.findings if f.pillar == pillar.value]
            
            # Debug info - show what we're working with
            scan_detectable_qs = [q for q in questions if q.get('scan_detectable', False)]
            
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
                        else:
                            response = "partial"  # Medium/Low findings = partial
                            confidence = 0.7
                        
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
                        # No findings for this question - could NOT detect, needs manual review
                        self.session.responses.append(QuestionResponse(
                            question_id=q['id'],
                            pillar=pillar.value,
                            question_text=q['question'],
                            response="",  # Empty - needs manual answer
                            auto_detected=False,
                            confidence=0.0,
                            evidence=["No scan data available for this question"]
                        ))
                else:
                    # Manual question - cannot be auto-detected
                    self.session.responses.append(QuestionResponse(
                        question_id=q['id'],
                        pillar=pillar.value,
                        question_text=q['question'],
                        response="",  # Empty - needs manual answer
                        auto_detected=False
                    ))
        
        # Count only questions with actual auto-detected answers (non-empty)
        self.session.auto_detected_count = len([r for r in self.session.responses if r.auto_detected and r.response])
        self.session.manual_required_count = len([r for r in self.session.responses if not r.response])
    
    def _render_pillar_questions(self, pillar: WAFPillar, show_pending_only: bool = False):
        """Render questions for a specific pillar"""
        
        questions = WAF_QUESTIONS.get(pillar, [])
        pillar_responses = {r.question_id: r for r in self.session.responses if r.pillar == pillar.value}
        
        # Debug: Show question count for this pillar
        if not questions:
            st.warning(f"⚠️ No questions found for {pillar.value}. WAF_QUESTIONS has {len(WAF_QUESTIONS)} pillars with keys: {[k.value for k in WAF_QUESTIONS.keys()]}")
            return
        
        # Count answered vs pending for this pillar
        answered_count = len([q for q in questions if pillar_responses.get(q['id']) and pillar_responses[q['id']].response])
        pending_count = len(questions) - answered_count
        
        # Show summary
        if pending_count > 0:
            st.caption(f"📝 {len(questions)} questions | ✅ {answered_count} answered | ⚠️ {pending_count} pending")
        else:
            st.caption(f"📝 {len(questions)} questions | ✅ All answered!")
        
        # Filter questions if showing pending only
        if show_pending_only:
            questions_to_show = [q for q in questions if not pillar_responses.get(q['id']) or not pillar_responses[q['id']].response]
            if not questions_to_show:
                st.success("✅ All questions in this pillar are answered!")
                return
            st.info(f"🔍 Showing {len(questions_to_show)} pending questions only")
        else:
            questions_to_show = questions
        
        for q in questions_to_show:
            response = pillar_responses.get(q['id'])
            
            # Determine if question has an answer
            has_answer = response and response.response in ["yes", "partial", "no", "not_applicable"]
            
            # Add visual indicator for pending questions
            q_label = f"**{q['id']}**: {q['question']}"
            if not has_answer:
                q_label = f"⚠️ **{q['id']}**: {q['question']}"
            
            with st.expander(q_label, expanded=not has_answer):
                st.markdown(f"*{q.get('description', '')}*")
                
                # Show auto-detection status
                if response and response.auto_detected and response.response:
                    confidence_color = "green" if response.confidence > 0.7 else "orange" if response.confidence > 0.5 else "red"
                    st.markdown(f"""
                    <div style="background: #e8f5e9; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        🤖 <b>Auto-detected</b> (Confidence: 
                        <span style="color: {confidence_color}">{response.confidence:.0%}</span>)
                        <br><small>Evidence: {', '.join(response.evidence[:3])}</small>
                    </div>
                    """, unsafe_allow_html=True)
                elif not has_answer:
                    st.markdown("""
                    <div style="background: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                        ⚠️ <b>Answer required</b> - Please select an option below
                    </div>
                    """, unsafe_allow_html=True)
                
                # Response options - include "Not answered" option
                options = ["", "yes", "partial", "no", "not_applicable"]
                labels = {"": "⬜ Select...", "yes": "✅ Yes", "partial": "⚠️ Partial", "no": "❌ No", "not_applicable": "➖ N/A"}
                
                current_response = response.response if response else ""
                current_index = options.index(current_response) if current_response in options else 0
                
                new_response = st.radio(
                    "Your assessment:",
                    options,
                    index=current_index,
                    format_func=lambda x: labels.get(x, x),
                    key=f"q_{q['id']}",
                    horizontal=True
                )
                
                # Update response ONLY if it changed (prevents infinite rerun)
                if new_response != current_response:
                    if response:
                        response.response = new_response
                    elif new_response:
                        # Create new response if user answers a question that wasn't tracked
                        self.session.responses.append(QuestionResponse(
                            question_id=q['id'],
                            pillar=pillar.value,
                            question_text=q['question'],
                            response=new_response,
                            auto_detected=False
                        ))
                
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
        
        # Update session state for dashboard to read
        self._update_dashboard_session_state()
        
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
    
    def _update_dashboard_session_state(self):
        """Update session state keys for the unified dashboard to read"""
        
        # Store findings in format dashboard expects
        findings_list = []
        for f in self.session.findings:
            if hasattr(f, '__dict__'):
                findings_list.append({
                    'severity': getattr(f, 'severity', 'MEDIUM'),
                    'title': getattr(f, 'title', ''),
                    'pillar': getattr(f, 'pillar', ''),
                    'service': getattr(f, 'service', ''),
                    'description': getattr(f, 'description', ''),
                })
            elif isinstance(f, dict):
                findings_list.append(f)
        
        st.session_state['last_findings'] = findings_list
        
        # Store pillar scores in format dashboard expects
        pillar_scores_dict = {}
        for pillar_name, score_obj in self.session.pillar_scores.items():
            if hasattr(score_obj, 'combined_score'):
                pillar_scores_dict[pillar_name] = int(score_obj.combined_score)
            elif hasattr(score_obj, 'score'):
                pillar_scores_dict[pillar_name] = int(score_obj.score)
            elif isinstance(score_obj, (int, float)):
                pillar_scores_dict[pillar_name] = int(score_obj)
        
        # Store in unified_assessment_results for backward compatibility
        st.session_state['unified_assessment_results'] = {
            'overall_score': self.session.overall_score,
            'pillar_scores': pillar_scores_dict,
            'findings': findings_list,
            'scan_completed': self.session.scan_completed,
            'questionnaire_completed': self.session.questionnaire_completed,
        }
        
        # Store in last_scan for backward compatibility
        st.session_state['last_scan'] = {
            'findings': self.session.findings,
            'pillar_scores': self.session.pillar_scores,
            'overall_score': self.session.overall_score,
            'scan_time': datetime.now().isoformat(),
            'accounts': self.session.accounts,
            'regions': self.session.regions,
        }
    
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
    # PHASE 5: REMEDIATION (Integrated with Real CloudFormation Deployment)
    # ========================================================================
    
    def _get_remediation_engine(self):
        """Get or create remediation engine instance"""
        if not hasattr(self, '_remediation_engine') or self._remediation_engine is None:
            if REMEDIATION_ENGINE_AVAILABLE:
                self._remediation_engine = RemediationEngine()
            else:
                self._remediation_engine = None
        return self._remediation_engine
    
    def _render_remediation_phase(self):
        """Render AI-powered remediation phase with real CloudFormation deployment"""
        
        st.markdown("## 🔨 Step 5: AI-Powered Remediation")
        
        # Check if real remediation engine is available
        if REMEDIATION_ENGINE_AVAILABLE:
            st.markdown("""
            Review and deploy automated fixes for your findings.
            **Real CloudFormation deployment** is enabled - changes will be applied to your AWS account.
            """)
            st.success("✅ **Real Deployment Mode** - CloudFormation stacks will be created in your AWS account")
        else:
            st.markdown("""
            Review remediation code for your findings.
            Export CloudFormation/Terraform code for manual deployment.
            """)
            st.warning("⚠️ **Export Only Mode** - Remediation engine not available. Code will be generated for manual deployment.")
        
        # Generate remediation items if not done
        if not self.session.remediation_items:
            self._generate_remediation_items()
        
        # Store findings for remediation tab integration
        st.session_state['waf_review_findings'] = [
            {
                'id': f.id,
                'title': f.title,
                'service': f.service,
                'severity': f.severity,
                'resource': f.resource,
                'account_id': f.account_id,
                'region': getattr(f, 'region', 'us-east-1'),
                'pillar': f.pillar
            }
            for f in self.session.findings
        ]
        
        # Summary metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Findings", len(self.session.findings))
        with col2:
            remediatable = len([r for r in self.session.remediation_items if r.cloudformation])
            st.metric("Auto-Remediatable", remediatable)
        with col3:
            approved = len([r for r in self.session.remediation_items if r.status == "approved"])
            st.metric("Approved", approved)
        with col4:
            deployed = len([r for r in self.session.remediation_items if r.status == "deployed"])
            st.metric("Deployed", deployed)
        with col5:
            failed = len([r for r in self.session.remediation_items if r.status == "failed"])
            st.metric("Failed", failed, delta_color="inverse" if failed > 0 else "off")
        
        st.markdown("---")
        
        # Deployment method selection (only if real engine available)
        if REMEDIATION_ENGINE_AVAILABLE:
            deployment_method = st.radio(
                "Deployment Method",
                ["🚀 Auto Deploy (CloudFormation)", "📥 Export Only (Manual)"],
                horizontal=True,
                help="Auto Deploy will create CloudFormation stacks directly. Export Only generates code for manual deployment."
            )
            self._use_auto_deploy = "Auto Deploy" in deployment_method
        else:
            self._use_auto_deploy = False
        
        st.markdown("---")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
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
        with col3:
            status_filter = st.multiselect(
                "Filter by Status",
                ["pending", "approved", "deployed", "failed"],
                default=["pending", "approved"]
            )
        
        # Filtered items
        filtered_items = [
            r for r in self.session.remediation_items
            if r.severity in severity_filter and r.pillar in pillar_filter and r.status in status_filter
        ]
        
        st.markdown(f"### 📋 Remediation Items ({len(filtered_items)})")
        
        # Bulk actions
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button("✅ Approve All Filtered", use_container_width=True):
                approved_count = 0
                for item in filtered_items:
                    if item.status == "pending":
                        item.status = "approved"
                        item.approved_at = datetime.now().isoformat()
                        approved_count += 1
                if approved_count > 0:
                    st.success(f"✅ Approved {approved_count} items!")
                    st.rerun()
                else:
                    st.info("No pending items to approve")
        
        with col2:
            approved_items = [r for r in filtered_items if r.status == "approved"]
            if st.button(f"🚀 Deploy Approved ({len(approved_items)})", type="primary", use_container_width=True, disabled=len(approved_items) == 0):
                self._deploy_approved_items_real()
        
        with col3:
            if st.button("🔄 Refresh Status", use_container_width=True):
                self._refresh_deployment_status()
                st.rerun()
        
        with col4:
            if st.button("📥 Export All Code", use_container_width=True):
                self._export_remediation_code()
        
        st.markdown("---")
        
        # Show deployment progress if any deployments are in progress
        deploying_items = [r for r in self.session.remediation_items if r.status == "deploying"]
        if deploying_items:
            st.warning(f"⏳ {len(deploying_items)} deployment(s) in progress...")
            for item in deploying_items:
                st.markdown(f"- `{item.stack_name}`: {item.finding_title}")
        
        # Render each remediation item
        for idx, item in enumerate(filtered_items):
            self._render_remediation_item_enhanced(item, idx)
        
        st.markdown("---")
        
        # Navigation
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Back to Scores", use_container_width=True):
                self.session.current_phase = ReviewPhase.SCORING
                st.rerun()
        
        with col2:
            # Save progress
            if st.button("💾 Save Progress", use_container_width=True):
                if self.save_progress():
                    st.success("✅ Progress saved!")
        
        with col3:
            deployed_count = len([r for r in self.session.remediation_items if r.status == "deployed"])
            if deployed_count > 0:
                if st.button("▶️ Verify Fixes (Re-scan)", type="primary", use_container_width=True):
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
    
    def _render_remediation_item_enhanced(self, item: RemediationItem, idx: int):
        """Render a single remediation item with enhanced deployment options"""
        
        severity_colors = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }
        
        status_badges = {
            "pending": "⏳ Pending",
            "approved": "✅ Approved",
            "deploying": "🔄 Deploying...",
            "deployed": "🚀 Deployed",
            "verified": "✅ Verified",
            "failed": "❌ Failed",
            "rolled_back": "↩️ Rolled Back"
        }
        
        # Determine if this item has real remediation code
        has_remediation = item.cloudformation and not item.cloudformation.startswith('#')
        
        status_display = status_badges.get(item.status, item.status)
        expander_label = f"{severity_colors.get(item.severity, '⚪')} **{item.severity}** - {item.finding_title} | {status_display}"
        
        with st.expander(expander_label, expanded=(item.status == "failed")):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Service:** {item.service}")
                st.markdown(f"**Resource:** `{item.resource}`")
                st.markdown(f"**Account:** {item.account_id}")
                st.markdown(f"**Pillar:** {item.pillar}")
                
                # Show stack info if deployed
                if item.stack_name and item.status in ["deployed", "deploying", "verified"]:
                    st.markdown(f"**Stack Name:** `{item.stack_name}`")
                if item.stack_id:
                    st.markdown(f"**Stack ID:** `{item.stack_id[:50]}...`")
                if item.deployed_at:
                    st.markdown(f"**Deployed:** {item.deployed_at}")
            
            with col2:
                # Action buttons based on status
                if item.status == "pending":
                    if has_remediation:
                        if st.button("✅ Approve", key=f"approve_{idx}_{item.finding_id}", use_container_width=True):
                            item.status = "approved"
                            item.approved_at = datetime.now().isoformat()
                            st.rerun()
                    else:
                        st.info("Manual remediation required")
                
                elif item.status == "approved":
                    if has_remediation and getattr(self, '_use_auto_deploy', False):
                        if st.button("🚀 Deploy Now", key=f"deploy_{idx}_{item.finding_id}", type="primary", use_container_width=True):
                            self._deploy_single_item_real(item)
                            st.rerun()
                    else:
                        st.info("Export code below")
                
                elif item.status == "deploying":
                    st.info("⏳ Deployment in progress...")
                    if st.button("🔄 Check Status", key=f"check_{idx}_{item.finding_id}", use_container_width=True):
                        self._check_deployment_status(item)
                        st.rerun()
                
                elif item.status == "deployed":
                    st.success("✅ Successfully deployed")
                    if st.button("↩️ Rollback", key=f"rollback_{idx}_{item.finding_id}", use_container_width=True):
                        self._rollback_deployment(item)
                        st.rerun()
                
                elif item.status == "failed":
                    st.error("❌ Deployment failed")
                    if st.button("🔄 Retry", key=f"retry_{idx}_{item.finding_id}", use_container_width=True):
                        item.status = "approved"
                        st.rerun()
            
            # Code tabs
            if item.cloudformation or item.terraform:
                code_tabs = st.tabs(["☁️ CloudFormation", "🏗️ Terraform", "💻 AWS CLI", "📋 Copy"])
                
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
                
                with code_tabs[3]:
                    # Copyable text area
                    if item.cloudformation:
                        st.text_area("CloudFormation (Copy)", item.cloudformation, height=150, key=f"copy_cfn_{idx}")
                    if item.aws_cli:
                        st.text_area("AWS CLI (Copy)", "\n".join(item.aws_cli), height=100, key=f"copy_cli_{idx}")
    
    def _deploy_single_item_real(self, item: RemediationItem):
        """Deploy a single remediation item using real CloudFormation"""
        
        if not REMEDIATION_ENGINE_AVAILABLE:
            st.error("❌ Remediation engine not available")
            return
        
        try:
            # Create remediation engine
            engine = self._get_remediation_engine()
            
            if engine is None:
                st.error("❌ Could not initialize remediation engine")
                item.status = "failed"
                return
            
            # Set stack name if not set
            if not item.stack_name:
                item.stack_name = f"waf-fix-{item.finding_id[:8]}-{int(time.time())}"
            
            # Prepare region
            region = getattr(item, 'region', None) or 'us-east-1'
            
            # Deploy via CloudFormation
            with st.spinner(f"🚀 Deploying {item.finding_title}..."):
                try:
                    # Use boto3 directly for CloudFormation deployment
                    session = boto3.Session()
                    cf_client = session.client('cloudformation', region_name=region)
                    
                    # Create stack
                    response = cf_client.create_stack(
                        StackName=item.stack_name,
                        TemplateBody=item.cloudformation,
                        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
                        Tags=[
                            {'Key': 'CreatedBy', 'Value': 'WAF-Scanner'},
                            {'Key': 'FindingId', 'Value': item.finding_id},
                            {'Key': 'Severity', 'Value': item.severity},
                            {'Key': 'Pillar', 'Value': item.pillar},
                        ],
                        OnFailure='ROLLBACK'
                    )
                    
                    item.stack_id = response.get('StackId', '')
                    item.status = "deploying"
                    item.deployed_at = datetime.now().isoformat()
                    
                    st.success(f"✅ Stack creation initiated: {item.stack_name}")
                    st.info("Stack is being created. Click 'Refresh Status' to check progress.")
                    
                except Exception as e:
                    error_msg = str(e)
                    if 'AlreadyExistsException' in error_msg:
                        st.warning(f"⚠️ Stack {item.stack_name} already exists. Checking status...")
                        self._check_deployment_status(item)
                    else:
                        item.status = "failed"
                        st.error(f"❌ CloudFormation deployment failed: {error_msg}")
                    
        except Exception as e:
            item.status = "failed"
            st.error(f"❌ Deployment error: {str(e)}")
    
    def _deploy_approved_items_real(self):
        """Deploy all approved remediation items using real CloudFormation"""
        
        approved_items = [r for r in self.session.remediation_items if r.status == "approved"]
        
        if not approved_items:
            st.warning("No approved items to deploy")
            return
        
        if not REMEDIATION_ENGINE_AVAILABLE and getattr(self, '_use_auto_deploy', False):
            st.error("❌ Remediation engine not available for auto-deployment")
            return
        
        # Confirmation dialog
        st.warning(f"⚠️ You are about to deploy {len(approved_items)} remediation(s) to your AWS account.")
        
        col1, col2 = st.columns(2)
        with col1:
            confirm = st.checkbox("I understand this will create CloudFormation stacks", key="deploy_confirm")
        
        if not confirm:
            st.info("Check the box above to confirm deployment")
            return
        
        # Deploy each item
        progress = st.progress(0)
        status_container = st.empty()
        results = {"success": 0, "failed": 0}
        
        for idx, item in enumerate(approved_items):
            status_container.markdown(f"🚀 Deploying ({idx + 1}/{len(approved_items)}): {item.finding_title}...")
            progress.progress((idx + 1) / len(approved_items))
            
            self._deploy_single_item_real(item)
            
            if item.status in ["deploying", "deployed"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            time.sleep(0.5)  # Brief pause between deployments
        
        progress.progress(100)
        
        if results["failed"] == 0:
            status_container.success(f"✅ All {results['success']} deployment(s) initiated successfully!")
        else:
            status_container.warning(f"⚠️ {results['success']} succeeded, {results['failed']} failed")
        
        self.session.remediation_deployed = len([r for r in self.session.remediation_items if r.status in ["deployed", "deploying"]])
        
        time.sleep(1)
        st.rerun()
    
    def _check_deployment_status(self, item: RemediationItem):
        """Check the status of a CloudFormation deployment"""
        
        if not item.stack_name:
            return
        
        try:
            region = getattr(item, 'region', None) or 'us-east-1'
            session = boto3.Session()
            cf_client = session.client('cloudformation', region_name=region)
            
            response = cf_client.describe_stacks(StackName=item.stack_name)
            
            if response.get('Stacks'):
                stack = response['Stacks'][0]
                stack_status = stack.get('StackStatus', '')
                
                if stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                    item.status = "deployed"
                    st.success(f"✅ Stack {item.stack_name} deployed successfully!")
                elif stack_status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
                    item.status = "deploying"
                    st.info(f"⏳ Stack {item.stack_name} is still being created...")
                elif stack_status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE', 'ROLLBACK_FAILED', 'DELETE_COMPLETE']:
                    item.status = "failed"
                    reason = stack.get('StackStatusReason', 'Unknown reason')
                    st.error(f"❌ Stack {item.stack_name} failed: {reason}")
                else:
                    st.info(f"Stack status: {stack_status}")
                    
        except Exception as e:
            if 'does not exist' in str(e):
                item.status = "failed"
                st.error(f"❌ Stack {item.stack_name} does not exist or was deleted")
            else:
                st.error(f"❌ Error checking status: {str(e)}")
    
    def _refresh_deployment_status(self):
        """Refresh status of all deploying items"""
        
        deploying_items = [r for r in self.session.remediation_items if r.status == "deploying"]
        
        for item in deploying_items:
            self._check_deployment_status(item)
    
    def _rollback_deployment(self, item: RemediationItem):
        """Rollback a deployed CloudFormation stack"""
        
        if not item.stack_name:
            st.error("No stack name to rollback")
            return
        
        try:
            region = getattr(item, 'region', None) or 'us-east-1'
            session = boto3.Session()
            cf_client = session.client('cloudformation', region_name=region)
            
            with st.spinner(f"↩️ Rolling back {item.stack_name}..."):
                cf_client.delete_stack(StackName=item.stack_name)
                item.status = "rolled_back"
                st.success(f"✅ Stack {item.stack_name} deletion initiated")
                
        except Exception as e:
            st.error(f"❌ Rollback failed: {str(e)}")
    
    def _export_remediation_code(self):
        """Export all remediation code to downloadable files"""
        
        # Create combined CloudFormation template
        cfn_templates = []
        tf_templates = []
        cli_commands = []
        
        for item in self.session.remediation_items:
            if item.cloudformation and not item.cloudformation.startswith('#'):
                cfn_templates.append(f"# ====== {item.finding_title} ======\n{item.cloudformation}\n")
            if item.terraform:
                tf_templates.append(f"# ====== {item.finding_title} ======\n{item.terraform}\n")
            if item.aws_cli:
                cli_commands.append(f"# ====== {item.finding_title} ======\n" + "\n".join(item.aws_cli) + "\n")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if cfn_templates:
                cfn_content = "\n".join(cfn_templates)
                st.download_button(
                    "📥 Download CloudFormation",
                    cfn_content,
                    file_name="waf_remediation_cloudformation.yaml",
                    mime="text/yaml"
                )
        
        with col2:
            if tf_templates:
                tf_content = "\n".join(tf_templates)
                st.download_button(
                    "📥 Download Terraform",
                    tf_content,
                    file_name="waf_remediation_terraform.tf",
                    mime="text/plain"
                )
        
        with col3:
            if cli_commands:
                cli_content = "#!/bin/bash\n" + "\n".join(cli_commands)
                st.download_button(
                    "📥 Download CLI Script",
                    cli_content,
                    file_name="waf_remediation_cli.sh",
                    mime="text/x-sh"
                )
        
        st.success(f"📦 Exported {len(cfn_templates)} CloudFormation, {len(tf_templates)} Terraform, {len(cli_commands)} CLI")
    
    # Keep old function for backward compatibility
    def _render_remediation_item(self, item: RemediationItem, idx: int):
        """Legacy function - redirects to enhanced version"""
        self._render_remediation_item_enhanced(item, idx)
    
    def _deploy_single_item(self, item: RemediationItem):
        """Legacy function - redirects to real deployment"""
        self._deploy_single_item_real(item)
    
    def _deploy_approved_items(self):
        """Legacy function - redirects to real deployment"""
        self._deploy_approved_items_real()
    
    # ========================================================================
    # PHASE 6: RE-SCAN (Real Verification)
    # ========================================================================
    
    def _render_rescan_phase(self):
        """Render re-scan verification phase with real AWS scanning"""
        
        st.markdown("## ✅ Step 6: Verify Remediation")
        st.markdown("Re-scan your accounts to verify fixes have been applied and measure improvement.")
        
        deployed_count = len([r for r in self.session.remediation_items if r.status == "deployed"])
        deploying_count = len([r for r in self.session.remediation_items if r.status == "deploying"])
        
        # Show deployment summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Deployed", deployed_count)
        with col2:
            st.metric("In Progress", deploying_count)
        with col3:
            st.metric("Initial Score", f"{self.session.initial_score:.0f}")
        with col4:
            if self.session.rescan_completed:
                st.metric("Final Score", f"{self.session.final_score:.0f}", delta=f"+{self.session.score_improvement:.0f}")
            else:
                st.metric("Final Score", "Pending")
        
        st.markdown("---")
        
        # Check if deployments are still in progress
        if deploying_count > 0:
            st.warning(f"⏳ {deploying_count} deployment(s) still in progress. Wait for completion before verifying.")
            
            if st.button("🔄 Refresh Deployment Status", use_container_width=True):
                self._refresh_deployment_status()
                st.rerun()
            
            with st.expander("📋 Deployments in Progress"):
                for item in self.session.remediation_items:
                    if item.status == "deploying":
                        st.markdown(f"- **{item.finding_title}** - Stack: `{item.stack_name}`")
        
        if not self.session.rescan_completed:
            st.info(f"📊 {deployed_count} remediation(s) deployed. Run a verification scan to measure improvement.")
            
            # Verification options
            st.markdown("### 🔍 Verification Options")
            
            verification_method = st.radio(
                "Choose verification method:",
                ["🔄 Full Re-scan (Recommended)", "⚡ Quick Check (Stack Status Only)", "📊 Estimated Score"],
                help="Full re-scan will run the same scan again to find remaining issues. Quick check verifies stack status only."
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if "Full Re-scan" in verification_method:
                    if st.button("🔍 Run Verification Scan", type="primary", use_container_width=True, disabled=deploying_count > 0):
                        self._run_verification_scan_real()
                elif "Quick Check" in verification_method:
                    if st.button("⚡ Quick Verify", type="primary", use_container_width=True):
                        self._run_quick_verification()
                else:
                    if st.button("📊 Calculate Estimated Score", type="primary", use_container_width=True):
                        self._calculate_estimated_improvement()
        
        else:
            # Show before/after comparison
            st.markdown("### 📊 Before & After Comparison")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"""
                <div style="background: #ffebee; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>Before Remediation</h4>
                    <h1 style="color: #c62828;">{self.session.initial_score:.0f}</h1>
                    <p>{self.session.initial_findings_count} findings</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                improvement = self.session.final_score - self.session.initial_score
                findings_fixed = getattr(self.session, 'findings_fixed', deployed_count)
                st.markdown(f"""
                <div style="background: #e8f5e9; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>Improvement</h4>
                    <h1 style="color: #2e7d32;">+{improvement:.0f}</h1>
                    <p>{findings_fixed} findings fixed</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                remaining_findings = getattr(self.session, 'remaining_findings_count', 0)
                st.markdown(f"""
                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; text-align: center;">
                    <h4>After Remediation</h4>
                    <h1 style="color: #1565c0;">{self.session.final_score:.0f}</h1>
                    <p>{remaining_findings} findings remaining</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Show fixed vs remaining findings
            if hasattr(self.session, 'fixed_findings') and self.session.fixed_findings:
                st.markdown("### ✅ Verified Fixed")
                with st.expander(f"Fixed Findings ({len(self.session.fixed_findings)})", expanded=False):
                    for f in self.session.fixed_findings[:10]:
                        st.markdown(f"- ✅ **{f.get('title', f.get('finding_title', 'Unknown'))}**")
                    if len(self.session.fixed_findings) > 10:
                        st.markdown(f"... and {len(self.session.fixed_findings) - 10} more")
            
            if hasattr(self.session, 'remaining_findings') and self.session.remaining_findings:
                st.markdown("### ⚠️ Remaining Issues")
                with st.expander(f"Remaining Findings ({len(self.session.remaining_findings)})", expanded=False):
                    for f in self.session.remaining_findings[:10]:
                        severity = f.get('severity', 'UNKNOWN')
                        st.markdown(f"- {'🔴' if severity == 'CRITICAL' else '🟠' if severity == 'HIGH' else '🟡'} **{f.get('title', 'Unknown')}** ({severity})")
                    if len(self.session.remaining_findings) > 10:
                        st.markdown(f"... and {len(self.session.remaining_findings) - 10} more")
            
            # Pillar comparison
            if hasattr(self.session, 'pillar_comparison') and self.session.pillar_comparison:
                st.markdown("### 📈 Improvement by Pillar")
                for pillar, data in self.session.pillar_comparison.items():
                    before = data.get('before', 0)
                    after = data.get('after', 0)
                    delta = after - before
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.progress(after / 100 if after else 0)
                    with col2:
                        st.markdown(f"**{pillar}**: {before:.0f} → {after:.0f} (+{delta:.0f})")
            
            st.markdown("---")
            
            # Navigation
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("🔄 Re-scan Again", use_container_width=True):
                    self.session.rescan_completed = False
                    st.rerun()
            with col2:
                if st.button("⬅️ Back to Remediate", use_container_width=True):
                    self.session.current_phase = ReviewPhase.REMEDIATION
                    st.rerun()
            with col3:
                if st.button("▶️ Complete Review", type="primary", use_container_width=True):
                    self.session.current_phase = ReviewPhase.COMPLETE
                    self.session.updated_at = datetime.now()
                    st.rerun()
    
    def _run_verification_scan_real(self):
        """Run real verification scan after remediation"""
        
        progress = st.progress(0)
        status = st.empty()
        
        # Store initial findings count
        self.session.initial_findings_count = len(self.session.findings)
        initial_finding_ids = {f.id for f in self.session.findings}
        
        status.markdown("🔍 **Initiating verification scan...**")
        progress.progress(10)
        
        try:
            # Re-run the scan using the same configuration
            from landscape_scanner import LandscapeScanner
            
            scanner = LandscapeScanner()
            new_findings = []
            
            # Scan each account that was originally scanned
            for idx, account in enumerate(self.session.accounts):
                account_id = account.get('account_id', account.get('id', 'unknown'))
                status.markdown(f"🔍 **Scanning account {account_id}...**")
                progress.progress(10 + int((idx + 1) / len(self.session.accounts) * 60))
                
                try:
                    # Scan account
                    results = scanner.scan_account(
                        account_id=account_id,
                        regions=self.session.regions
                    )
                    new_findings.extend(results.get('findings', []))
                except Exception as e:
                    st.warning(f"⚠️ Could not scan {account_id}: {str(e)}")
            
            progress.progress(80)
            status.markdown("📊 **Analyzing results...**")
            
            # Compare findings
            new_finding_ids = {f.get('id', f.get('finding_id', '')) for f in new_findings}
            
            # Fixed = in original but not in new
            fixed_ids = initial_finding_ids - new_finding_ids
            self.session.fixed_findings = [f for f in self.session.findings if f.id in fixed_ids]
            self.session.findings_fixed = len(fixed_ids)
            
            # Remaining = still present
            self.session.remaining_findings = new_findings
            self.session.remaining_findings_count = len(new_findings)
            
            # Calculate new score
            # Score improvement based on findings fixed vs total
            if self.session.initial_findings_count > 0:
                fix_rate = self.session.findings_fixed / self.session.initial_findings_count
                self.session.score_improvement = fix_rate * 30  # Max 30 points improvement
            else:
                self.session.score_improvement = 0
            
            self.session.final_score = min(100, self.session.initial_score + self.session.score_improvement)
            
            # Pillar comparison
            self.session.pillar_comparison = {}
            for pillar in WAFPillar:
                before_count = len([f for f in self.session.findings if f.pillar == pillar.value])
                after_count = len([f for f in new_findings if f.get('pillar') == pillar.value])
                
                before_score = self.session.pillar_scores.get(pillar.value, PillarScore(pillar=pillar.value)).combined_score
                # Estimate after score based on reduction
                if before_count > 0:
                    reduction = (before_count - after_count) / before_count
                    after_score = min(100, before_score + (reduction * 20))
                else:
                    after_score = before_score
                
                self.session.pillar_comparison[pillar.value] = {
                    'before': before_score,
                    'after': after_score,
                    'findings_before': before_count,
                    'findings_after': after_count
                }
            
            progress.progress(100)
            status.markdown("✅ **Verification scan complete!**")
            
        except ImportError:
            # Fallback to estimated improvement if scanner not available
            status.markdown("⚠️ **Scanner not available, using estimated improvement...**")
            self._calculate_estimated_improvement()
            return
        except Exception as e:
            st.error(f"❌ Verification scan failed: {str(e)}")
            status.markdown("⚠️ **Using estimated improvement due to scan error...**")
            self._calculate_estimated_improvement()
            return
        
        self.session.rescan_completed = True
        self.session.rescan_timestamp = datetime.now()
        
        time.sleep(1)
        st.rerun()
    
    def _run_quick_verification(self):
        """Quick verification by checking stack status only"""
        
        progress = st.progress(0)
        status = st.empty()
        
        status.markdown("⚡ **Checking deployment status...**")
        
        verified_count = 0
        failed_count = 0
        
        deployed_items = [r for r in self.session.remediation_items if r.status in ["deployed", "deploying"]]
        
        for idx, item in enumerate(deployed_items):
            progress.progress(int((idx + 1) / len(deployed_items) * 100))
            
            if item.stack_name:
                self._check_deployment_status(item)
                
                if item.status == "deployed":
                    verified_count += 1
                elif item.status == "failed":
                    failed_count += 1
        
        # Calculate score based on verified deployments
        self.session.findings_fixed = verified_count
        self.session.initial_findings_count = len(self.session.findings)
        
        if self.session.initial_findings_count > 0:
            fix_rate = verified_count / self.session.initial_findings_count
            self.session.score_improvement = fix_rate * 25
        else:
            self.session.score_improvement = 0
        
        self.session.final_score = min(100, self.session.initial_score + self.session.score_improvement)
        self.session.remaining_findings_count = self.session.initial_findings_count - verified_count
        
        self.session.rescan_completed = True
        self.session.rescan_timestamp = datetime.now()
        
        status.markdown(f"✅ **Quick verification complete!** {verified_count} verified, {failed_count} failed")
        
        time.sleep(1)
        st.rerun()
    
    def _calculate_estimated_improvement(self):
        """Calculate estimated score improvement based on deployments"""
        
        deployed_count = len([r for r in self.session.remediation_items if r.status == "deployed"])
        
        self.session.initial_findings_count = len(self.session.findings)
        self.session.findings_fixed = deployed_count
        self.session.remaining_findings_count = max(0, self.session.initial_findings_count - deployed_count)
        
        # Estimate improvement: ~3 points per fix, max 30
        self.session.score_improvement = min(deployed_count * 3, 30)
        self.session.final_score = min(100, self.session.initial_score + self.session.score_improvement)
        
        self.session.rescan_completed = True
        self.session.rescan_timestamp = datetime.now()
        
        st.success(f"📊 Estimated improvement calculated: +{self.session.score_improvement:.0f} points")
        time.sleep(1)
        st.rerun()
    
    # Keep legacy function for compatibility
    def _run_verification_scan(self):
        """Legacy function - redirects to real verification"""
        self._run_verification_scan_real()
    
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