"""
AWS Well-Architected AI Lens Module
Enterprise Edition v5.0.9

Integrates three AI-focused lenses into the WAF Scanner:
1. Machine Learning Lens - For traditional ML workloads
2. Generative AI Lens - For LLM/foundation model applications  
3. Responsible AI Lens - For ethical AI practices

Based on official AWS Well-Architected Lenses:
- https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/
- https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/
- https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/

This module provides:
- 150+ AI-specific assessment questions
- Automated AI workload scanning
- ML/AI architecture recommendations
- Responsible AI governance checks
- AI-specific compliance mapping
- Custom lens JSON export for AWS WA Tool
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class AILensType(Enum):
    """Types of AI lenses available"""
    MACHINE_LEARNING = "machine_learning"
    GENERATIVE_AI = "generative_ai"
    RESPONSIBLE_AI = "responsible_ai"


class AIRiskLevel(Enum):
    """AI-specific risk levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NO_RISK = "no_risk"


class MLLifecyclePhase(Enum):
    """Machine Learning lifecycle phases"""
    BUSINESS_GOAL = "business_goal"
    DATA_MANAGEMENT = "data_management"
    MODEL_DEVELOPMENT = "model_development"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_DEPLOYMENT = "model_deployment"
    MODEL_MONITORING = "model_monitoring"
    CONTINUOUS_IMPROVEMENT = "continuous_improvement"


class GenAILifecyclePhase(Enum):
    """Generative AI lifecycle phases"""
    SCOPING = "scoping"
    MODEL_SELECTION = "model_selection"
    MODEL_CUSTOMIZATION = "model_customization"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    ITERATION = "iteration"


class ResponsibleAIFocusArea(Enum):
    """Responsible AI focus areas"""
    USE_CASE_DEFINITION = "use_case_definition"
    BENEFIT_RISK_ASSESSMENT = "benefit_risk_assessment"
    DATA_GOVERNANCE = "data_governance"
    MODEL_DEVELOPMENT = "model_development"
    EVALUATION_TESTING = "evaluation_testing"
    DEPLOYMENT = "deployment"
    OPERATION_MONITORING = "operation_monitoring"
    CONTINUOUS_IMPROVEMENT = "continuous_improvement"


@dataclass
class AILensQuestion:
    """AI Lens Question structure"""
    id: str
    lens_type: AILensType
    pillar: str  # WAF pillar this maps to
    phase: str  # Lifecycle phase
    category: str
    title: str
    description: str
    why_important: str
    best_practices: List[str]
    choices: List[Dict[str, Any]]
    risk_rules: List[Dict[str, Any]]
    aws_services: List[str] = field(default_factory=list)
    helpful_resources: List[Dict[str, str]] = field(default_factory=list)
    ai_dimensions: List[str] = field(default_factory=list)  # For Responsible AI
    automated_check: Optional[str] = None  # Function name for automated checking


@dataclass
class AILensAssessment:
    """AI Lens Assessment result"""
    id: str
    lens_type: AILensType
    workload_name: str
    created_at: datetime
    responses: Dict[str, Dict[str, Any]]
    scores: Dict[str, float]
    risks: Dict[str, List[str]]
    recommendations: List[str]


# ============================================================================
# MACHINE LEARNING LENS - COMPREHENSIVE QUESTIONS DATABASE
# ============================================================================

def get_ml_lens_questions() -> List[AILensQuestion]:
    """
    AWS Well-Architected Machine Learning Lens Questions
    Covers the full ML lifecycle across all WAF pillars
    Based on: https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/
    """
    questions = []
    
    # ========================================================================
    # OPERATIONAL EXCELLENCE PILLAR - ML LIFECYCLE
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="ML-OPS-001",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Operational Excellence",
            phase=MLLifecyclePhase.BUSINESS_GOAL.value,
            category="ML Business Alignment",
            title="How do you define and document ML business goals?",
            description="Clearly defined business goals ensure ML initiatives align with organizational objectives and deliver measurable value.",
            why_important="Without clear business goals, ML projects often fail to deliver value or solve the wrong problems. Studies show 87% of ML projects never make it to production due to misalignment with business objectives.",
            best_practices=[
                "Define specific, measurable business outcomes for ML projects",
                "Document success criteria and KPIs before starting development",
                "Ensure stakeholder alignment on ML project objectives",
                "Create feedback loops between business outcomes and model performance",
                "Establish clear ownership and accountability for ML outcomes",
                "Define acceptable model performance thresholds"
            ],
            choices=[
                {"id": "ML-OPS-001-A", "title": "Business goals documented with measurable KPIs, success criteria, and stakeholder sign-off", "risk": "NO_RISK"},
                {"id": "ML-OPS-001-B", "title": "Business goals are defined but not fully documented or lack measurable criteria", "risk": "MEDIUM_RISK"},
                {"id": "ML-OPS-001-C", "title": "Business goals are informal or unclear", "risk": "HIGH_RISK"},
                {"id": "ML-OPS-001-D", "title": "No defined business goals for ML initiatives", "risk": "CRITICAL"},
                {"id": "ML-OPS-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-OPS-001-A", "risk": "NO_RISK"},
                {"condition": "ML-OPS-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker", "AWS Organizations", "AWS Service Catalog"],
            helpful_resources=[
                {"displayText": "Define your ML problem", "url": "https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/well-architected-machine-learning-lifecycle.html"}
            ]
        ),
        
        AILensQuestion(
            id="ML-OPS-002",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Operational Excellence",
            phase=MLLifecyclePhase.MODEL_DEPLOYMENT.value,
            category="MLOps Pipeline",
            title="How do you implement CI/CD for ML models?",
            description="MLOps practices enable reliable, repeatable model deployment and continuous improvement through automated pipelines.",
            why_important="Manual model deployment is error-prone and slows innovation. Automated pipelines ensure consistency, quality, and faster time-to-production.",
            best_practices=[
                "Implement automated ML pipelines using SageMaker Pipelines or Step Functions",
                "Version control all ML artifacts (code, data, models, configs)",
                "Automate model testing including unit tests, integration tests, and A/B tests",
                "Implement model registry for versioning and governance",
                "Use infrastructure as code for ML environments (Terraform, CDK)",
                "Implement automated model validation before deployment",
                "Set up automated rollback mechanisms"
            ],
            choices=[
                {"id": "ML-OPS-002-A", "title": "Fully automated CI/CD pipelines with model registry, validation gates, and rollback", "risk": "NO_RISK"},
                {"id": "ML-OPS-002-B", "title": "Partially automated pipelines with some manual steps", "risk": "MEDIUM_RISK"},
                {"id": "ML-OPS-002-C", "title": "Manual deployment process with version control", "risk": "HIGH_RISK"},
                {"id": "ML-OPS-002-D", "title": "Ad-hoc manual deployment without version control", "risk": "CRITICAL"},
                {"id": "ML-OPS-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-OPS-002-A", "risk": "NO_RISK"},
                {"condition": "ML-OPS-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker Pipelines", "AWS CodePipeline", "AWS Step Functions", "Amazon ECR", "SageMaker Model Registry", "AWS CDK"],
            helpful_resources=[
                {"displayText": "MLOps foundation roadmap", "url": "https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-projects-whatis.html"}
            ]
        ),
        
        AILensQuestion(
            id="ML-OPS-003",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Operational Excellence",
            phase=MLLifecyclePhase.MODEL_MONITORING.value,
            category="Model Monitoring",
            title="How do you monitor ML model performance in production?",
            description="Continuous monitoring ensures models maintain accuracy and enables early detection of drift or degradation.",
            why_important="Models can degrade over time due to data drift, concept drift, or changing business conditions. Without monitoring, degraded models continue making poor predictions.",
            best_practices=[
                "Monitor model prediction accuracy and business metrics continuously",
                "Implement data drift detection for input features",
                "Implement concept drift detection for model outputs",
                "Track model latency, throughput, and error rates",
                "Set up alerts for performance degradation with escalation paths",
                "Log all predictions for debugging and auditing",
                "Compare production performance against baseline metrics",
                "Implement automatic retraining triggers"
            ],
            choices=[
                {"id": "ML-OPS-003-A", "title": "Comprehensive monitoring with drift detection, alerting, dashboards, and auto-retraining triggers", "risk": "NO_RISK"},
                {"id": "ML-OPS-003-B", "title": "Monitoring of accuracy and latency with basic alerting", "risk": "MEDIUM_RISK"},
                {"id": "ML-OPS-003-C", "title": "Limited monitoring with manual performance checks", "risk": "HIGH_RISK"},
                {"id": "ML-OPS-003-D", "title": "No model monitoring in place", "risk": "CRITICAL"},
                {"id": "ML-OPS-003-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-OPS-003-A", "risk": "NO_RISK"},
                {"condition": "ML-OPS-003-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker Model Monitor", "Amazon CloudWatch", "Amazon EventBridge", "AWS Lambda", "Amazon SNS"],
            helpful_resources=[
                {"displayText": "Monitor models with SageMaker Model Monitor", "url": "https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html"}
            ]
        ),
        
        AILensQuestion(
            id="ML-OPS-004",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Operational Excellence",
            phase=MLLifecyclePhase.DATA_MANAGEMENT.value,
            category="Data Pipeline",
            title="How do you manage ML data pipelines?",
            description="Robust data pipelines ensure consistent, high-quality data for training and inference.",
            why_important="Data quality directly impacts model quality. Poor data management leads to unreliable models and wasted compute resources.",
            best_practices=[
                "Implement data versioning for training datasets",
                "Automate data quality checks and validation",
                "Use feature stores for feature management and reuse",
                "Implement data lineage tracking",
                "Automate ETL/ELT pipelines with error handling",
                "Monitor data freshness and completeness"
            ],
            choices=[
                {"id": "ML-OPS-004-A", "title": "Automated pipelines with versioning, feature store, lineage tracking, and quality checks", "risk": "NO_RISK"},
                {"id": "ML-OPS-004-B", "title": "Automated pipelines with basic quality checks", "risk": "MEDIUM_RISK"},
                {"id": "ML-OPS-004-C", "title": "Manual data preparation with some automation", "risk": "HIGH_RISK"},
                {"id": "ML-OPS-004-D", "title": "Ad-hoc manual data preparation", "risk": "CRITICAL"},
                {"id": "ML-OPS-004-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-OPS-004-A", "risk": "NO_RISK"},
                {"condition": "ML-OPS-004-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker Feature Store", "AWS Glue", "Amazon EMR", "AWS Lake Formation", "Amazon S3"]
        ),
    ])
    
    # ========================================================================
    # SECURITY PILLAR - ML SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="ML-SEC-001",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Security",
            phase=MLLifecyclePhase.DATA_MANAGEMENT.value,
            category="Data Security",
            title="How do you protect training data and ML artifacts?",
            description="ML systems require protection of sensitive training data, model artifacts, and inference data throughout the lifecycle.",
            why_important="Training data often contains sensitive information (PII, proprietary data). Compromised models can leak training data or trade secrets through model inversion attacks.",
            best_practices=[
                "Encrypt training data at rest (S3 SSE-KMS) and in transit (TLS 1.2+)",
                "Implement fine-grained data access controls using IAM and Lake Formation",
                "Use VPC endpoints for all data access to prevent internet exposure",
                "Implement data classification and handling policies",
                "Secure model artifacts in private repositories with access logging",
                "Use data anonymization/pseudonymization for sensitive data",
                "Implement data loss prevention (DLP) controls",
                "Audit all data access with CloudTrail"
            ],
            choices=[
                {"id": "ML-SEC-001-A", "title": "Comprehensive encryption, fine-grained access controls, VPC endpoints, and audit logging", "risk": "NO_RISK"},
                {"id": "ML-SEC-001-B", "title": "Encryption enabled with basic access controls", "risk": "MEDIUM_RISK"},
                {"id": "ML-SEC-001-C", "title": "Basic security measures not ML-specific", "risk": "HIGH_RISK"},
                {"id": "ML-SEC-001-D", "title": "Minimal or no data protection measures", "risk": "CRITICAL"},
                {"id": "ML-SEC-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-SEC-001-A", "risk": "NO_RISK"},
                {"condition": "ML-SEC-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["AWS KMS", "Amazon S3", "AWS IAM", "Amazon VPC", "AWS CloudTrail", "AWS Lake Formation", "Amazon Macie"]
        ),
        
        AILensQuestion(
            id="ML-SEC-002",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Security",
            phase=MLLifecyclePhase.MODEL_DEPLOYMENT.value,
            category="Endpoint Security",
            title="How do you protect ML inference endpoints?",
            description="ML endpoints need protection against adversarial attacks, unauthorized access, model extraction, and data exfiltration.",
            why_important="Exposed ML endpoints can be exploited for model stealing, adversarial attacks, prompt injection, or data theft. Model APIs are attractive targets.",
            best_practices=[
                "Use private endpoints within VPC (PrivateLink)",
                "Implement API authentication (IAM, API keys, OAuth)",
                "Implement rate limiting and request throttling",
                "Validate and sanitize all inference inputs",
                "Monitor for adversarial input patterns",
                "Implement model watermarking or fingerprinting for IP protection",
                "Use AWS WAF for endpoint protection against common attacks",
                "Enable request/response logging for security analysis"
            ],
            choices=[
                {"id": "ML-SEC-002-A", "title": "Private endpoints with authentication, input validation, WAF, rate limiting, and monitoring", "risk": "NO_RISK"},
                {"id": "ML-SEC-002-B", "title": "Authenticated endpoints with basic input validation", "risk": "MEDIUM_RISK"},
                {"id": "ML-SEC-002-C", "title": "Public endpoints with authentication only", "risk": "HIGH_RISK"},
                {"id": "ML-SEC-002-D", "title": "Unprotected or minimally protected endpoints", "risk": "CRITICAL"},
                {"id": "ML-SEC-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-SEC-002-A", "risk": "NO_RISK"},
                {"condition": "ML-SEC-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker", "Amazon API Gateway", "AWS WAF", "Amazon VPC", "AWS PrivateLink", "AWS Shield"]
        ),
        
        AILensQuestion(
            id="ML-SEC-003",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Security",
            phase=MLLifecyclePhase.MODEL_TRAINING.value,
            category="Training Security",
            title="How do you secure the ML training environment?",
            description="Training environments need isolation and protection to prevent supply chain attacks, model poisoning, and unauthorized modifications.",
            why_important="Compromised training environments can lead to poisoned models that behave maliciously in production. Supply chain attacks on ML are increasing.",
            best_practices=[
                "Use isolated VPCs for training workloads with no internet access",
                "Implement least privilege access for training jobs",
                "Scan and validate all training containers before use",
                "Use private artifact repositories (ECR) with vulnerability scanning",
                "Implement network traffic inspection and logging",
                "Audit all training job activities",
                "Use signed container images",
                "Validate model integrity before deployment"
            ],
            choices=[
                {"id": "ML-SEC-003-A", "title": "Isolated VPCs, container scanning, signed images, least privilege, and comprehensive auditing", "risk": "NO_RISK"},
                {"id": "ML-SEC-003-B", "title": "VPC isolation with basic access controls and some scanning", "risk": "MEDIUM_RISK"},
                {"id": "ML-SEC-003-C", "title": "Shared training environment with access controls", "risk": "HIGH_RISK"},
                {"id": "ML-SEC-003-D", "title": "Unsecured training environment", "risk": "CRITICAL"},
                {"id": "ML-SEC-003-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-SEC-003-A", "risk": "NO_RISK"},
                {"condition": "ML-SEC-003-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker", "Amazon VPC", "Amazon ECR", "AWS IAM", "Amazon Inspector", "AWS Signer"]
        ),
    ])
    
    # ========================================================================
    # RELIABILITY PILLAR - ML SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="ML-REL-001",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Reliability",
            phase=MLLifecyclePhase.MODEL_DEPLOYMENT.value,
            category="Inference Availability",
            title="How do you ensure ML inference high availability?",
            description="ML inference endpoints must be highly available to support business-critical applications with defined SLAs.",
            why_important="ML inference downtime directly impacts user experience and business operations. Many ML models are in critical paths.",
            best_practices=[
                "Deploy inference endpoints across multiple Availability Zones",
                "Implement auto-scaling based on traffic patterns and latency",
                "Use health checks with automatic instance replacement",
                "Implement circuit breakers and fallback logic",
                "Use caching for frequent predictions (ElastiCache)",
                "Monitor and alert on availability metrics with runbooks",
                "Define and test disaster recovery procedures",
                "Use multi-model endpoints for efficient resource utilization"
            ],
            choices=[
                {"id": "ML-REL-001-A", "title": "Multi-AZ deployment with auto-scaling, health checks, fallbacks, and tested DR procedures", "risk": "NO_RISK"},
                {"id": "ML-REL-001-B", "title": "Multi-AZ deployment with auto-scaling and basic health checks", "risk": "MEDIUM_RISK"},
                {"id": "ML-REL-001-C", "title": "Single AZ with manual scaling and no fallback", "risk": "HIGH_RISK"},
                {"id": "ML-REL-001-D", "title": "No redundancy or scaling configured", "risk": "CRITICAL"},
                {"id": "ML-REL-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-REL-001-A", "risk": "NO_RISK"},
                {"condition": "ML-REL-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker", "Elastic Load Balancing", "Amazon CloudWatch", "AWS Auto Scaling", "Amazon ElastiCache"]
        ),
        
        AILensQuestion(
            id="ML-REL-002",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Reliability",
            phase=MLLifecyclePhase.MODEL_DEVELOPMENT.value,
            category="Experiment Reproducibility",
            title="How do you ensure reproducibility of ML experiments?",
            description="Reproducible experiments enable reliable model development, debugging, and regulatory compliance.",
            why_important="Non-reproducible results waste time, lead to unreliable production models, and create compliance risks in regulated industries.",
            best_practices=[
                "Track all experiment parameters, hyperparameters, and metrics",
                "Version datasets used for training with checksums",
                "Log random seeds and environment configurations",
                "Use containerized training environments with pinned dependencies",
                "Store all training artifacts in durable, versioned storage",
                "Document experiment lineage and provenance",
                "Implement experiment comparison and visualization"
            ],
            choices=[
                {"id": "ML-REL-002-A", "title": "Full experiment tracking with data versioning, containers, lineage, and artifact storage", "risk": "NO_RISK"},
                {"id": "ML-REL-002-B", "title": "Experiment tracking without comprehensive data versioning", "risk": "MEDIUM_RISK"},
                {"id": "ML-REL-002-C", "title": "Manual logging of experiments in documents", "risk": "HIGH_RISK"},
                {"id": "ML-REL-002-D", "title": "No experiment tracking or reproducibility measures", "risk": "CRITICAL"},
                {"id": "ML-REL-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-REL-002-A", "risk": "NO_RISK"},
                {"condition": "ML-REL-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker Experiments", "Amazon S3", "AWS Glue Data Catalog", "MLflow on AWS"]
        ),
    ])
    
    # ========================================================================
    # PERFORMANCE EFFICIENCY PILLAR - ML SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="ML-PERF-001",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Performance Efficiency",
            phase=MLLifecyclePhase.MODEL_TRAINING.value,
            category="Training Performance",
            title="How do you optimize ML training performance?",
            description="Efficient training reduces time-to-production, enables more experimentation, and reduces compute costs.",
            why_important="Slow training cycles impede experimentation, delay time-to-market, and waste expensive compute resources.",
            best_practices=[
                "Use appropriate instance types for workload (GPU/CPU/Trainium/Inferentia)",
                "Implement distributed training for large models (data/model parallelism)",
                "Use mixed precision training (FP16/BF16) where applicable",
                "Optimize data loading pipelines to eliminate I/O bottlenecks",
                "Use SageMaker Debugger to identify performance bottlenecks",
                "Consider managed training with Spot Instances for cost savings",
                "Use warm pools to reduce job startup time",
                "Implement gradient checkpointing for memory efficiency"
            ],
            choices=[
                {"id": "ML-PERF-001-A", "title": "Optimized distributed training with performance profiling, mixed precision, and right-sized instances", "risk": "NO_RISK"},
                {"id": "ML-PERF-001-B", "title": "Right-sized instances with some optimization techniques", "risk": "MEDIUM_RISK"},
                {"id": "ML-PERF-001-C", "title": "Default configurations without optimization", "risk": "HIGH_RISK"},
                {"id": "ML-PERF-001-D", "title": "No consideration for training performance", "risk": "CRITICAL"},
                {"id": "ML-PERF-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-PERF-001-A", "risk": "NO_RISK"},
                {"condition": "ML-PERF-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker", "AWS Trainium", "Amazon EC2 P4d/P5", "SageMaker Debugger", "SageMaker Distributed Training"]
        ),
        
        AILensQuestion(
            id="ML-PERF-002",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Performance Efficiency",
            phase=MLLifecyclePhase.MODEL_DEPLOYMENT.value,
            category="Inference Performance",
            title="How do you optimize ML inference latency?",
            description="Low-latency inference is critical for real-time applications and user experience.",
            why_important="High inference latency degrades user experience, limits use cases, and can cause timeout failures in production.",
            best_practices=[
                "Use model optimization techniques (quantization, pruning, distillation)",
                "Deploy models close to users (edge deployment, regional endpoints)",
                "Use SageMaker Neo for model compilation to target hardware",
                "Implement request batching for throughput optimization",
                "Choose appropriate inference instance types (Inferentia, GPU)",
                "Use GPU inference for compute-intensive models",
                "Implement model caching and warm-up strategies",
                "Profile and optimize the full inference pipeline"
            ],
            choices=[
                {"id": "ML-PERF-002-A", "title": "Optimized models with compilation, right-sized infrastructure, and performance profiling", "risk": "NO_RISK"},
                {"id": "ML-PERF-002-B", "title": "Some optimization with appropriate instance selection", "risk": "MEDIUM_RISK"},
                {"id": "ML-PERF-002-C", "title": "Default model serving without optimization", "risk": "HIGH_RISK"},
                {"id": "ML-PERF-002-D", "title": "No latency optimization considerations", "risk": "CRITICAL"},
                {"id": "ML-PERF-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-PERF-002-A", "risk": "NO_RISK"},
                {"condition": "ML-PERF-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker Neo", "AWS Inferentia", "Amazon SageMaker Serverless Inference", "Amazon CloudFront", "AWS Wavelength"]
        ),
    ])
    
    # ========================================================================
    # COST OPTIMIZATION PILLAR - ML SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="ML-COST-001",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Cost Optimization",
            phase=MLLifecyclePhase.MODEL_TRAINING.value,
            category="Training Cost",
            title="How do you optimize ML training costs?",
            description="ML training can be expensive; proper optimization reduces costs significantly without sacrificing quality.",
            why_important="Unoptimized ML training can lead to excessive cloud spending. Training costs can grow exponentially with model size.",
            best_practices=[
                "Use Managed Spot Training for up to 90% cost savings",
                "Right-size training instances based on actual utilization",
                "Use managed warm pools to reduce startup time and cost",
                "Implement early stopping for hyperparameter tuning jobs",
                "Schedule training during off-peak hours when possible",
                "Use incremental/transfer training instead of training from scratch",
                "Monitor and alert on training cost anomalies",
                "Clean up unused resources and data automatically"
            ],
            choices=[
                {"id": "ML-COST-001-A", "title": "Spot instances, right-sizing, warm pools, early stopping, and cost monitoring", "risk": "NO_RISK"},
                {"id": "ML-COST-001-B", "title": "Some cost optimization measures like Spot instances in place", "risk": "MEDIUM_RISK"},
                {"id": "ML-COST-001-C", "title": "On-demand instances with basic instance sizing", "risk": "HIGH_RISK"},
                {"id": "ML-COST-001-D", "title": "No cost optimization considerations", "risk": "CRITICAL"},
                {"id": "ML-COST-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-COST-001-A", "risk": "NO_RISK"},
                {"condition": "ML-COST-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon SageMaker Managed Spot Training", "AWS Cost Explorer", "AWS Budgets", "SageMaker Warm Pools"]
        ),
        
        AILensQuestion(
            id="ML-COST-002",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Cost Optimization",
            phase=MLLifecyclePhase.MODEL_DEPLOYMENT.value,
            category="Inference Cost",
            title="How do you optimize ML inference costs?",
            description="Inference costs can exceed training costs for high-volume production applications.",
            why_important="Unoptimized inference endpoints waste resources during low-traffic periods and can become the largest ML cost driver.",
            best_practices=[
                "Use SageMaker Serverless Inference for variable/spiky workloads",
                "Implement auto-scaling based on actual traffic patterns",
                "Use Savings Plans or Reserved Capacity for predictable workloads",
                "Consider multi-model endpoints for hosting similar models",
                "Use SageMaker Inference Recommender to right-size instances",
                "Implement request batching to improve throughput efficiency",
                "Use Inferentia for cost-effective inference at scale",
                "Set up cost allocation tags for chargeback"
            ],
            choices=[
                {"id": "ML-COST-002-A", "title": "Serverless/auto-scaled endpoints, Savings Plans, right-sizing, and cost allocation", "risk": "NO_RISK"},
                {"id": "ML-COST-002-B", "title": "Auto-scaling with some cost optimization measures", "risk": "MEDIUM_RISK"},
                {"id": "ML-COST-002-C", "title": "Fixed capacity with manual management", "risk": "HIGH_RISK"},
                {"id": "ML-COST-002-D", "title": "No cost optimization for inference", "risk": "CRITICAL"},
                {"id": "ML-COST-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-COST-002-A", "risk": "NO_RISK"},
                {"condition": "ML-COST-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["SageMaker Serverless Inference", "SageMaker Inference Recommender", "AWS Savings Plans", "SageMaker Multi-Model Endpoints", "AWS Inferentia"]
        ),
    ])
    
    # ========================================================================
    # SUSTAINABILITY PILLAR - ML SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="ML-SUS-001",
            lens_type=AILensType.MACHINE_LEARNING,
            pillar="Sustainability",
            phase=MLLifecyclePhase.MODEL_TRAINING.value,
            category="Training Sustainability",
            title="How do you minimize environmental impact of ML training?",
            description="Large-scale ML training has significant carbon footprint that can be optimized through efficient practices.",
            why_important="ML training is computationally intensive. Training a single large language model can emit as much CO2 as five cars over their lifetimes.",
            best_practices=[
                "Use energy-efficient instance types (Graviton, Trainium)",
                "Schedule training in AWS regions with higher renewable energy percentage",
                "Optimize models to reduce training time and compute requirements",
                "Use transfer learning instead of training from scratch when possible",
                "Track and report carbon footprint using AWS Customer Carbon Footprint Tool",
                "Consider model efficiency vs accuracy tradeoffs",
                "Use model compression techniques to reduce compute requirements",
                "Implement automatic resource cleanup and shutdown"
            ],
            choices=[
                {"id": "ML-SUS-001-A", "title": "Energy-efficient instances, carbon tracking, transfer learning, and optimization practices", "risk": "NO_RISK"},
                {"id": "ML-SUS-001-B", "title": "Some efficiency measures without comprehensive tracking", "risk": "MEDIUM_RISK"},
                {"id": "ML-SUS-001-C", "title": "Standard instances without sustainability considerations", "risk": "HIGH_RISK"},
                {"id": "ML-SUS-001-D", "title": "No sustainability considerations", "risk": "CRITICAL"},
                {"id": "ML-SUS-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "ML-SUS-001-A", "risk": "NO_RISK"},
                {"condition": "ML-SUS-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["AWS Graviton", "AWS Trainium", "AWS Customer Carbon Footprint Tool", "Amazon SageMaker"]
        ),
    ])
    
    return questions


# ============================================================================
# GENERATIVE AI LENS - COMPREHENSIVE QUESTIONS DATABASE
# ============================================================================

def get_genai_lens_questions() -> List[AILensQuestion]:
    """
    AWS Well-Architected Generative AI Lens Questions
    Focuses on LLM/foundation model applications
    Based on: https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/
    """
    questions = []
    
    # ========================================================================
    # OPERATIONAL EXCELLENCE - GENAI SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="GENAI-OPS-001",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Operational Excellence",
            phase=GenAILifecyclePhase.SCOPING.value,
            category="Use Case Scoping",
            title="How do you scope and validate generative AI use cases?",
            description="Proper scoping ensures GenAI applications solve the right problems effectively and responsibly.",
            why_important="Poorly scoped GenAI projects fail to deliver value, create unexpected risks, or solve problems better addressed by traditional methods.",
            best_practices=[
                "Define clear success criteria and acceptance thresholds for GenAI applications",
                "Validate that GenAI is the right approach vs. traditional ML or rule-based systems",
                "Identify potential risks, failure modes, and mitigation strategies",
                "Establish evaluation metrics for model output quality (BLEU, ROUGE, human eval)",
                "Plan for human-in-the-loop validation where needed for high-stakes decisions",
                "Consider regulatory, ethical, and legal implications of generated content",
                "Document expected model behavior and edge cases"
            ],
            choices=[
                {"id": "GENAI-OPS-001-A", "title": "Formal scoping with validation, risk assessment, success criteria, and stakeholder alignment", "risk": "NO_RISK"},
                {"id": "GENAI-OPS-001-B", "title": "Basic scoping without formal validation or risk assessment", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-OPS-001-C", "title": "Informal scoping process", "risk": "HIGH_RISK"},
                {"id": "GENAI-OPS-001-D", "title": "No scoping or validation process", "risk": "CRITICAL"},
                {"id": "GENAI-OPS-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-OPS-001-A", "risk": "NO_RISK"},
                {"condition": "GENAI-OPS-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "Amazon SageMaker JumpStart"]
        ),
        
        AILensQuestion(
            id="GENAI-OPS-002",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Operational Excellence",
            phase=GenAILifecyclePhase.MODEL_SELECTION.value,
            category="Model Selection",
            title="How do you select and evaluate foundation models?",
            description="Choosing the right foundation model is critical for GenAI application success, cost, and performance.",
            why_important="Different models have varying capabilities, costs, latencies, and limitations. Wrong model choice leads to poor results or excessive costs.",
            best_practices=[
                "Evaluate multiple models against your specific use case requirements",
                "Consider model size, latency, cost, and capability tradeoffs",
                "Test models with domain-specific prompts and edge cases",
                "Assess model safety, content filtering, and guardrail capabilities",
                "Consider vendor lock-in, portability, and model availability",
                "Document model selection rationale and comparison results",
                "Establish model upgrade and migration strategies",
                "Consider fine-tuning requirements and costs"
            ],
            choices=[
                {"id": "GENAI-OPS-002-A", "title": "Formal evaluation comparing multiple models with documented rationale and benchmarks", "risk": "NO_RISK"},
                {"id": "GENAI-OPS-002-B", "title": "Limited evaluation with some model comparison", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-OPS-002-C", "title": "Single model selected without formal evaluation", "risk": "HIGH_RISK"},
                {"id": "GENAI-OPS-002-D", "title": "No model evaluation process", "risk": "CRITICAL"},
                {"id": "GENAI-OPS-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-OPS-002-A", "risk": "NO_RISK"},
                {"condition": "GENAI-OPS-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "Amazon SageMaker JumpStart", "Amazon Bedrock Model Evaluation"]
        ),
        
        AILensQuestion(
            id="GENAI-OPS-003",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Operational Excellence",
            phase=GenAILifecyclePhase.MODEL_CUSTOMIZATION.value,
            category="Prompt Engineering",
            title="How do you manage and optimize prompts?",
            description="Effective prompt engineering maximizes model output quality, consistency, and reliability.",
            why_important="Poorly designed prompts lead to inconsistent, incorrect, or harmful outputs. Prompts are code and need proper management.",
            best_practices=[
                "Develop and test prompts systematically with version control",
                "Use prompt templates for consistency across applications",
                "Implement prompt injection protection and input sanitization",
                "Monitor prompt performance and output quality over time",
                "Document prompt design decisions and rationale",
                "Implement A/B testing for prompt optimization",
                "Use few-shot examples and chain-of-thought prompting",
                "Establish prompt review and approval processes"
            ],
            choices=[
                {"id": "GENAI-OPS-003-A", "title": "Systematic prompt engineering with versioning, testing, monitoring, and injection protection", "risk": "NO_RISK"},
                {"id": "GENAI-OPS-003-B", "title": "Some prompt management without comprehensive versioning or testing", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-OPS-003-C", "title": "Ad-hoc prompt development without management", "risk": "HIGH_RISK"},
                {"id": "GENAI-OPS-003-D", "title": "No prompt management practices", "risk": "CRITICAL"},
                {"id": "GENAI-OPS-003-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-OPS-003-A", "risk": "NO_RISK"},
                {"condition": "GENAI-OPS-003-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "Amazon Bedrock Prompt Management", "AWS CodeCommit", "Amazon CloudWatch"]
        ),
        
        AILensQuestion(
            id="GENAI-OPS-004",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Operational Excellence",
            phase=GenAILifecyclePhase.ITERATION.value,
            category="Output Quality",
            title="How do you monitor and maintain generative AI output quality?",
            description="Continuous monitoring ensures generated content meets quality standards and business requirements.",
            why_important="GenAI output quality can degrade with model updates, data changes, or emerging edge cases. Poor quality damages user trust.",
            best_practices=[
                "Implement automated output quality scoring and monitoring",
                "Set up human evaluation workflows for high-stakes outputs",
                "Track user feedback and satisfaction metrics",
                "Monitor for hallucinations, factual errors, and harmful content",
                "Implement output validation and post-processing pipelines",
                "Establish quality thresholds and alerting",
                "Compare output quality across model versions"
            ],
            choices=[
                {"id": "GENAI-OPS-004-A", "title": "Comprehensive quality monitoring with automated scoring, human eval, and feedback loops", "risk": "NO_RISK"},
                {"id": "GENAI-OPS-004-B", "title": "Basic quality monitoring with some automated checks", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-OPS-004-C", "title": "Manual quality reviews without systematic monitoring", "risk": "HIGH_RISK"},
                {"id": "GENAI-OPS-004-D", "title": "No output quality monitoring", "risk": "CRITICAL"},
                {"id": "GENAI-OPS-004-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-OPS-004-A", "risk": "NO_RISK"},
                {"condition": "GENAI-OPS-004-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "Amazon CloudWatch", "Amazon SageMaker Ground Truth"]
        ),
    ])
    
    # ========================================================================
    # SECURITY - GENAI SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="GENAI-SEC-001",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Security",
            phase=GenAILifecyclePhase.INTEGRATION.value,
            category="Prompt Security",
            title="How do you protect against prompt injection attacks?",
            description="GenAI applications are vulnerable to prompt injection, jailbreaking, and manipulation attempts.",
            why_important="Prompt injection can bypass safety filters, expose system prompts, exfiltrate data, or cause unintended actions.",
            best_practices=[
                "Implement input validation and sanitization for all user inputs",
                "Use Bedrock Guardrails to filter harmful inputs and outputs",
                "Separate system prompts from user inputs with clear delimiters",
                "Monitor for anomalous prompt patterns and attack signatures",
                "Implement rate limiting and abuse detection",
                "Regularly test for prompt injection vulnerabilities (red teaming)",
                "Use output filtering to catch leaked system prompts",
                "Implement input/output length limits"
            ],
            choices=[
                {"id": "GENAI-SEC-001-A", "title": "Comprehensive guardrails with validation, monitoring, red teaming, and multi-layer protection", "risk": "NO_RISK"},
                {"id": "GENAI-SEC-001-B", "title": "Basic input validation with Bedrock Guardrails", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-SEC-001-C", "title": "Limited protection measures", "risk": "HIGH_RISK"},
                {"id": "GENAI-SEC-001-D", "title": "No prompt security measures", "risk": "CRITICAL"},
                {"id": "GENAI-SEC-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-SEC-001-A", "risk": "NO_RISK"},
                {"condition": "GENAI-SEC-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock Guardrails", "AWS WAF", "Amazon CloudWatch", "AWS Lambda"]
        ),
        
        AILensQuestion(
            id="GENAI-SEC-002",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Security",
            phase=GenAILifecyclePhase.INTEGRATION.value,
            category="Data Security",
            title="How do you protect sensitive data in GenAI applications?",
            description="GenAI applications may process sensitive data that requires protection throughout the lifecycle.",
            why_important="Models can inadvertently memorize and leak sensitive training data. User inputs may contain PII that shouldn't be logged or stored.",
            best_practices=[
                "Implement PII detection and masking before model input (using Comprehend)",
                "Use private endpoints (PrivateLink) for API calls",
                "Encrypt data in transit (TLS 1.2+) and at rest",
                "Audit and log all model interactions with appropriate redaction",
                "Implement data retention policies and automatic deletion",
                "Consider on-premises or private model deployment for sensitive data",
                "Disable model invocation logging for sensitive use cases",
                "Use customer-managed KMS keys for encryption"
            ],
            choices=[
                {"id": "GENAI-SEC-002-A", "title": "PII masking, private endpoints, encryption, audit logging with redaction, and retention policies", "risk": "NO_RISK"},
                {"id": "GENAI-SEC-002-B", "title": "Encryption and private endpoints with basic data handling", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-SEC-002-C", "title": "Minimal data protection measures", "risk": "HIGH_RISK"},
                {"id": "GENAI-SEC-002-D", "title": "No data protection measures", "risk": "CRITICAL"},
                {"id": "GENAI-SEC-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-SEC-002-A", "risk": "NO_RISK"},
                {"condition": "GENAI-SEC-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "AWS PrivateLink", "Amazon Macie", "Amazon Comprehend", "AWS KMS"]
        ),
        
        AILensQuestion(
            id="GENAI-SEC-003",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Security",
            phase=GenAILifecyclePhase.DEPLOYMENT.value,
            category="Content Safety",
            title="How do you ensure safe and appropriate model outputs?",
            description="GenAI models can generate harmful, biased, inappropriate, or factually incorrect content.",
            why_important="Unsafe outputs can harm users, violate regulations, and severely damage organizational reputation and trust.",
            best_practices=[
                "Implement output content filtering using Bedrock Guardrails",
                "Configure guardrails to block harmful content categories",
                "Monitor outputs for policy violations with automated detection",
                "Implement human review workflows for high-risk output categories",
                "Establish content policies with clear enforcement mechanisms",
                "Test thoroughly for harmful output generation (red teaming)",
                "Implement feedback mechanisms for users to report issues",
                "Use model-specific safety features and content filters"
            ],
            choices=[
                {"id": "GENAI-SEC-003-A", "title": "Guardrails, content filtering, automated monitoring, human review, and red teaming", "risk": "NO_RISK"},
                {"id": "GENAI-SEC-003-B", "title": "Basic content filtering with Bedrock Guardrails", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-SEC-003-C", "title": "Reliance on model's built-in safety only", "risk": "HIGH_RISK"},
                {"id": "GENAI-SEC-003-D", "title": "No content safety measures", "risk": "CRITICAL"},
                {"id": "GENAI-SEC-003-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-SEC-003-A", "risk": "NO_RISK"},
                {"condition": "GENAI-SEC-003-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock Guardrails", "Amazon Comprehend", "AWS Lambda", "Amazon SageMaker Ground Truth"]
        ),
        
        AILensQuestion(
            id="GENAI-SEC-004",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Security",
            phase=GenAILifecyclePhase.INTEGRATION.value,
            category="Agent Security",
            title="How do you secure AI agents with tool access?",
            description="AI agents with tool access (function calling, MCP) require additional security controls.",
            why_important="AI agents can take actions in the real world. Unsecured agents risk unauthorized actions, data exfiltration, or system compromise.",
            best_practices=[
                "Implement least privilege access for agent tools and APIs",
                "Validate and sanitize all tool inputs and outputs",
                "Implement action confirmation for high-risk operations",
                "Log all agent actions with full audit trail",
                "Set resource quotas and rate limits on agent actions",
                "Implement kill switches and emergency stop mechanisms",
                "Sandbox agent execution environments",
                "Review and approve tool definitions before deployment"
            ],
            choices=[
                {"id": "GENAI-SEC-004-A", "title": "Least privilege, input validation, action confirmation, full audit logging, and sandboxing", "risk": "NO_RISK"},
                {"id": "GENAI-SEC-004-B", "title": "Basic access controls with some logging", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-SEC-004-C", "title": "Limited controls on agent tool access", "risk": "HIGH_RISK"},
                {"id": "GENAI-SEC-004-D", "title": "No specific agent security controls", "risk": "CRITICAL"},
                {"id": "GENAI-SEC-004-NONE", "title": "Not using AI agents with tool access", "risk": "NO_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-SEC-004-A", "risk": "NO_RISK"},
                {"condition": "GENAI-SEC-004-B", "risk": "MEDIUM_RISK"},
                {"condition": "GENAI-SEC-004-NONE", "risk": "NO_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock Agents", "AWS IAM", "AWS CloudTrail", "Amazon CloudWatch"]
        ),
    ])
    
    # ========================================================================
    # RELIABILITY - GENAI SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="GENAI-REL-001",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Reliability",
            phase=GenAILifecyclePhase.INTEGRATION.value,
            category="RAG Architecture",
            title="How do you implement reliable RAG architectures?",
            description="Retrieval-Augmented Generation (RAG) requires reliable knowledge retrieval for accurate, grounded responses.",
            why_important="RAG reliability directly impacts answer accuracy, hallucination rates, and user trust in the application.",
            best_practices=[
                "Use vector databases optimized for similarity search (OpenSearch, Kendra)",
                "Implement chunking strategies appropriate for content type",
                "Monitor retrieval quality, relevance scores, and hit rates",
                "Handle missing or outdated knowledge gracefully with fallbacks",
                "Implement fallback mechanisms for retrieval failures",
                "Regularly update, validate, and version the knowledge base",
                "Use hybrid search combining semantic and keyword search",
                "Implement citation and source attribution"
            ],
            choices=[
                {"id": "GENAI-REL-001-A", "title": "Production-grade RAG with monitoring, fallbacks, versioning, hybrid search, and citations", "risk": "NO_RISK"},
                {"id": "GENAI-REL-001-B", "title": "Basic RAG implementation with vector search and some monitoring", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-REL-001-C", "title": "Simple RAG without monitoring or fallbacks", "risk": "HIGH_RISK"},
                {"id": "GENAI-REL-001-D", "title": "No RAG or unreliable implementation", "risk": "CRITICAL"},
                {"id": "GENAI-REL-001-NONE", "title": "Not using RAG architecture", "risk": "NO_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-REL-001-A", "risk": "NO_RISK"},
                {"condition": "GENAI-REL-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "GENAI-REL-001-NONE", "risk": "NO_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock Knowledge Bases", "Amazon OpenSearch Serverless", "Amazon Kendra", "Amazon S3"]
        ),
        
        AILensQuestion(
            id="GENAI-REL-002",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Reliability",
            phase=GenAILifecyclePhase.DEPLOYMENT.value,
            category="Service Resilience",
            title="How do you handle GenAI service failures and rate limits?",
            description="GenAI services can experience rate limits, timeouts, and outages requiring resilient handling.",
            why_important="Foundation model APIs can be rate-limited or unavailable. Applications must handle failures gracefully.",
            best_practices=[
                "Implement exponential backoff with jitter for rate limit handling",
                "Use circuit breakers to prevent cascade failures",
                "Implement request queuing for traffic smoothing",
                "Configure appropriate timeouts for model calls",
                "Have fallback models or cached responses for critical paths",
                "Monitor rate limit errors and plan capacity accordingly",
                "Use provisioned throughput for predictable workloads",
                "Implement graceful degradation strategies"
            ],
            choices=[
                {"id": "GENAI-REL-002-A", "title": "Exponential backoff, circuit breakers, queuing, fallbacks, and provisioned throughput", "risk": "NO_RISK"},
                {"id": "GENAI-REL-002-B", "title": "Basic retry logic with some timeout handling", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-REL-002-C", "title": "Limited error handling", "risk": "HIGH_RISK"},
                {"id": "GENAI-REL-002-D", "title": "No failure handling mechanisms", "risk": "CRITICAL"},
                {"id": "GENAI-REL-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-REL-002-A", "risk": "NO_RISK"},
                {"condition": "GENAI-REL-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "Amazon SQS", "AWS Lambda", "Amazon ElastiCache"]
        ),
    ])
    
    # ========================================================================
    # PERFORMANCE & COST - GENAI SPECIFIC
    # ========================================================================
    
    questions.extend([
        AILensQuestion(
            id="GENAI-PERF-001",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Performance Efficiency",
            phase=GenAILifecyclePhase.DEPLOYMENT.value,
            category="Latency Optimization",
            title="How do you optimize GenAI response latency?",
            description="GenAI applications often have high latency that needs optimization for good user experience.",
            why_important="High latency degrades user experience, especially in conversational applications. Users expect responsive AI.",
            best_practices=[
                "Use streaming responses for long outputs to improve perceived latency",
                "Implement response caching for common or repeated queries",
                "Choose appropriate model size for latency requirements",
                "Use provisioned throughput for consistent, predictable latency",
                "Optimize prompts for shorter, more efficient responses",
                "Consider smaller, faster models for latency-critical paths",
                "Pre-warm model connections to reduce cold start",
                "Use regional deployments close to users"
            ],
            choices=[
                {"id": "GENAI-PERF-001-A", "title": "Streaming, caching, optimized model selection, provisioned throughput, and regional deployment", "risk": "NO_RISK"},
                {"id": "GENAI-PERF-001-B", "title": "Some latency optimization with streaming or caching", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-PERF-001-C", "title": "Default configuration without latency optimization", "risk": "HIGH_RISK"},
                {"id": "GENAI-PERF-001-D", "title": "No latency optimization considerations", "risk": "CRITICAL"},
                {"id": "GENAI-PERF-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-PERF-001-A", "risk": "NO_RISK"},
                {"condition": "GENAI-PERF-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "Amazon ElastiCache", "Amazon CloudFront", "AWS Lambda"]
        ),
        
        AILensQuestion(
            id="GENAI-COST-001",
            lens_type=AILensType.GENERATIVE_AI,
            pillar="Cost Optimization",
            phase=GenAILifecyclePhase.DEPLOYMENT.value,
            category="Token Cost Management",
            title="How do you manage GenAI token and inference costs?",
            description="GenAI costs scale with token usage and can become significant at scale.",
            why_important="Uncontrolled token usage leads to unexpected and potentially substantial costs. Token costs vary 100x between models.",
            best_practices=[
                "Monitor token usage by application, user, and endpoint",
                "Implement token budgets, quotas, and alerts per user/application",
                "Optimize prompts for token efficiency (shorter system prompts)",
                "Use smaller, cheaper models where quality is acceptable",
                "Cache responses for repeated queries to avoid redundant calls",
                "Implement cost allocation tags and chargeback mechanisms",
                "Use batch inference for non-real-time workloads",
                "Compare costs across different models for same use case"
            ],
            choices=[
                {"id": "GENAI-COST-001-A", "title": "Token monitoring, budgets, caching, model optimization, and cost allocation", "risk": "NO_RISK"},
                {"id": "GENAI-COST-001-B", "title": "Basic token monitoring with some cost awareness", "risk": "MEDIUM_RISK"},
                {"id": "GENAI-COST-001-C", "title": "Limited cost visibility without controls", "risk": "HIGH_RISK"},
                {"id": "GENAI-COST-001-D", "title": "No token or cost management", "risk": "CRITICAL"},
                {"id": "GENAI-COST-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "GENAI-COST-001-A", "risk": "NO_RISK"},
                {"condition": "GENAI-COST-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            aws_services=["Amazon Bedrock", "AWS Cost Explorer", "AWS Budgets", "Amazon CloudWatch"]
        ),
    ])
    
    return questions


# ============================================================================
# RESPONSIBLE AI LENS - COMPREHENSIVE QUESTIONS DATABASE
# ============================================================================

def get_responsible_ai_lens_questions() -> List[AILensQuestion]:
    """
    AWS Well-Architected Responsible AI Lens Questions
    Covers ethical AI practices across the ML/AI lifecycle
    Based on: https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/
    """
    questions = []
    
    questions.extend([
        AILensQuestion(
            id="RAI-001",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.USE_CASE_DEFINITION.value,
            category="Use Case Validation",
            title="How do you validate the appropriateness of AI for your use case?",
            description="Not all problems should be solved with AI; validation ensures appropriate and responsible application.",
            why_important="Inappropriate AI use can harm users, waste resources, and create legal/reputational risks. Some problems are better solved with rules.",
            best_practices=[
                "Validate that AI is the right solution vs. rule-based alternatives",
                "Consider and document non-AI alternatives evaluated",
                "Assess potential for harm to all stakeholder groups",
                "Document rationale for choosing AI approach",
                "Identify vulnerable populations that may be affected",
                "Establish clear success criteria with ethical considerations",
                "Consider long-term societal implications"
            ],
            choices=[
                {"id": "RAI-001-A", "title": "Formal validation with alternatives assessment, harm analysis, and stakeholder review", "risk": "NO_RISK"},
                {"id": "RAI-001-B", "title": "Basic validation without formal harm assessment", "risk": "MEDIUM_RISK"},
                {"id": "RAI-001-C", "title": "Informal validation process", "risk": "HIGH_RISK"},
                {"id": "RAI-001-D", "title": "No validation process for AI appropriateness", "risk": "CRITICAL"},
                {"id": "RAI-001-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-001-A", "risk": "NO_RISK"},
                {"condition": "RAI-001-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["safety", "veracity", "transparency"]
        ),
        
        AILensQuestion(
            id="RAI-002",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.BENEFIT_RISK_ASSESSMENT.value,
            category="Fairness Assessment",
            title="How do you assess and mitigate AI fairness and bias risks?",
            description="AI systems can perpetuate or amplify existing biases; systematic assessment is critical.",
            why_important="Unfair AI systems harm individuals, create legal liability, damage reputation, and erode trust.",
            best_practices=[
                "Define fairness metrics appropriate for your specific use case",
                "Analyze training data for representation and bias",
                "Test model outputs across demographic groups",
                "Implement bias mitigation techniques during training and inference",
                "Monitor for fairness drift in production over time",
                "Establish remediation processes for identified bias issues",
                "Document fairness testing results and decisions",
                "Engage diverse stakeholders in fairness assessments"
            ],
            choices=[
                {"id": "RAI-002-A", "title": "Comprehensive fairness assessment with monitoring, mitigation, and documented remediation", "risk": "NO_RISK"},
                {"id": "RAI-002-B", "title": "Basic fairness testing without ongoing monitoring", "risk": "MEDIUM_RISK"},
                {"id": "RAI-002-C", "title": "Limited or ad-hoc fairness considerations", "risk": "HIGH_RISK"},
                {"id": "RAI-002-D", "title": "No fairness assessment process", "risk": "CRITICAL"},
                {"id": "RAI-002-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-002-A", "risk": "NO_RISK"},
                {"condition": "RAI-002-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["fairness", "transparency"],
            aws_services=["Amazon SageMaker Clarify"]
        ),
        
        AILensQuestion(
            id="RAI-003",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.MODEL_DEVELOPMENT.value,
            category="Explainability",
            title="How do you ensure AI decisions are explainable?",
            description="Users, stakeholders, and regulators need to understand how AI decisions are made.",
            why_important="Unexplainable AI erodes trust, may violate regulations (GDPR, AI Act), and prevents debugging.",
            best_practices=[
                "Choose interpretable models where possible for high-stakes decisions",
                "Implement explanation methods (SHAP, LIME, attention visualization)",
                "Provide explanations appropriate for different audiences",
                "Document model decision logic and key features",
                "Enable users to request and understand explanations",
                "Validate that explanations are faithful to model behavior",
                "Consider counterfactual explanations for affected individuals"
            ],
            choices=[
                {"id": "RAI-003-A", "title": "Comprehensive explainability with validated methods and audience-appropriate explanations", "risk": "NO_RISK"},
                {"id": "RAI-003-B", "title": "Basic explanations available for technical users", "risk": "MEDIUM_RISK"},
                {"id": "RAI-003-C", "title": "Limited explainability capability", "risk": "HIGH_RISK"},
                {"id": "RAI-003-D", "title": "No explainability measures", "risk": "CRITICAL"},
                {"id": "RAI-003-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-003-A", "risk": "NO_RISK"},
                {"condition": "RAI-003-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["explainability", "transparency"],
            aws_services=["Amazon SageMaker Clarify", "Amazon Bedrock"]
        ),
        
        AILensQuestion(
            id="RAI-004",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.DATA_GOVERNANCE.value,
            category="Data Ethics",
            title="How do you ensure ethical data collection and use?",
            description="Responsible AI requires ethically sourced, appropriately consented, and properly managed data.",
            why_important="Unethical data practices harm individuals, violate privacy regulations, and undermine AI trustworthiness.",
            best_practices=[
                "Obtain appropriate informed consent for data collection and use",
                "Document data provenance, lineage, and processing history",
                "Implement data minimization principles (collect only what's needed)",
                "Protect privacy through anonymization, pseudonymization, and differential privacy",
                "Establish clear data retention and deletion policies",
                "Audit data practices regularly for compliance",
                "Respect data subject rights (access, correction, deletion)",
                "Ensure data is representative and unbiased"
            ],
            choices=[
                {"id": "RAI-004-A", "title": "Comprehensive data governance with consent, privacy protection, lineage, and regular audits", "risk": "NO_RISK"},
                {"id": "RAI-004-B", "title": "Basic data governance with some privacy measures", "risk": "MEDIUM_RISK"},
                {"id": "RAI-004-C", "title": "Minimal data governance practices", "risk": "HIGH_RISK"},
                {"id": "RAI-004-D", "title": "No formal data governance", "risk": "CRITICAL"},
                {"id": "RAI-004-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-004-A", "risk": "NO_RISK"},
                {"condition": "RAI-004-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["privacy", "transparency"],
            aws_services=["AWS Lake Formation", "Amazon Macie", "AWS Glue Data Catalog"]
        ),
        
        AILensQuestion(
            id="RAI-005",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.OPERATION_MONITORING.value,
            category="Human Oversight",
            title="How do you maintain human oversight and control of AI systems?",
            description="Human oversight ensures AI systems remain under appropriate control and can be corrected.",
            why_important="Autonomous AI without oversight can cause unintended harm. Humans must be able to intervene and override.",
            best_practices=[
                "Implement human-in-the-loop (HITL) for high-stakes decisions",
                "Enable human override and correction of AI decisions",
                "Monitor AI actions and outcomes with dashboards",
                "Establish clear escalation procedures for AI issues",
                "Train human operators on AI system behavior and limitations",
                "Conduct regular human reviews of AI outputs and decisions",
                "Implement kill switches for emergency shutdown",
                "Define clear accountability for AI decisions"
            ],
            choices=[
                {"id": "RAI-005-A", "title": "Comprehensive human oversight with HITL, monitoring, escalation, and trained operators", "risk": "NO_RISK"},
                {"id": "RAI-005-B", "title": "Basic oversight with some human review capability", "risk": "MEDIUM_RISK"},
                {"id": "RAI-005-C", "title": "Limited human oversight mechanisms", "risk": "HIGH_RISK"},
                {"id": "RAI-005-D", "title": "No human oversight or control mechanisms", "risk": "CRITICAL"},
                {"id": "RAI-005-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-005-A", "risk": "NO_RISK"},
                {"condition": "RAI-005-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["controllability", "safety"]
        ),
        
        AILensQuestion(
            id="RAI-006",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.EVALUATION_TESTING.value,
            category="Safety Testing",
            title="How do you test AI systems for safety before deployment?",
            description="Safety testing identifies potential harms, failure modes, and adversarial vulnerabilities before deployment.",
            why_important="Unsafe AI systems can cause significant harm to users and organizations. Testing catches issues early.",
            best_practices=[
                "Conduct red team testing for adversarial inputs and attacks",
                "Test edge cases, failure modes, and out-of-distribution inputs",
                "Evaluate model robustness to perturbations",
                "Test for harmful, biased, or inappropriate output generation",
                "Validate that safety controls work as intended",
                "Document all safety testing results and remediation",
                "Establish go/no-go criteria based on safety testing",
                "Plan for ongoing safety testing after deployment"
            ],
            choices=[
                {"id": "RAI-006-A", "title": "Comprehensive safety testing with red teaming, robustness evaluation, and documented go/no-go criteria", "risk": "NO_RISK"},
                {"id": "RAI-006-B", "title": "Basic safety testing without red teaming", "risk": "MEDIUM_RISK"},
                {"id": "RAI-006-C", "title": "Limited or informal safety testing", "risk": "HIGH_RISK"},
                {"id": "RAI-006-D", "title": "No safety testing before deployment", "risk": "CRITICAL"},
                {"id": "RAI-006-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-006-A", "risk": "NO_RISK"},
                {"condition": "RAI-006-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["safety", "robustness"],
            aws_services=["Amazon SageMaker Clarify", "Amazon Bedrock Model Evaluation"]
        ),
        
        AILensQuestion(
            id="RAI-007",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.DEPLOYMENT.value,
            category="Transparency",
            title="How do you ensure transparency about AI use to affected parties?",
            description="People should know when they're interacting with AI and understand its capabilities and limitations.",
            why_important="Hidden AI use erodes trust, may violate regulations, and prevents informed decision-making by users.",
            best_practices=[
                "Clearly disclose when users are interacting with AI",
                "Communicate AI system capabilities and limitations",
                "Provide information about how AI decisions are made",
                "Make AI policies and practices publicly available",
                "Enable users to opt out of AI interactions where appropriate",
                "Document and communicate model updates and changes",
                "Provide contact information for questions and concerns"
            ],
            choices=[
                {"id": "RAI-007-A", "title": "Clear AI disclosure, capabilities documentation, public policies, and opt-out options", "risk": "NO_RISK"},
                {"id": "RAI-007-B", "title": "Basic disclosure without comprehensive documentation", "risk": "MEDIUM_RISK"},
                {"id": "RAI-007-C", "title": "Limited transparency about AI use", "risk": "HIGH_RISK"},
                {"id": "RAI-007-D", "title": "No transparency measures", "risk": "CRITICAL"},
                {"id": "RAI-007-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-007-A", "risk": "NO_RISK"},
                {"condition": "RAI-007-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["transparency"]
        ),
        
        AILensQuestion(
            id="RAI-008",
            lens_type=AILensType.RESPONSIBLE_AI,
            pillar="Responsible AI",
            phase=ResponsibleAIFocusArea.CONTINUOUS_IMPROVEMENT.value,
            category="Incident Response",
            title="How do you handle AI incidents and harm reports?",
            description="Organizations need processes to identify, investigate, and remediate AI-related incidents and harms.",
            why_important="AI incidents can cause significant harm. Fast, effective response minimizes damage and prevents recurrence.",
            best_practices=[
                "Establish clear incident reporting channels for AI issues",
                "Define incident severity levels and response procedures",
                "Investigate incidents to identify root causes",
                "Implement remediation and communicate with affected parties",
                "Document lessons learned and update practices",
                "Conduct post-incident reviews with stakeholders",
                "Track and report incident metrics to leadership",
                "Have rollback and disable capabilities for AI systems"
            ],
            choices=[
                {"id": "RAI-008-A", "title": "Comprehensive incident response with reporting, investigation, remediation, and lessons learned", "risk": "NO_RISK"},
                {"id": "RAI-008-B", "title": "Basic incident handling without formal processes", "risk": "MEDIUM_RISK"},
                {"id": "RAI-008-C", "title": "Ad-hoc incident response", "risk": "HIGH_RISK"},
                {"id": "RAI-008-D", "title": "No incident response process for AI issues", "risk": "CRITICAL"},
                {"id": "RAI-008-NONE", "title": "None of these apply", "risk": "HIGH_RISK"}
            ],
            risk_rules=[
                {"condition": "RAI-008-A", "risk": "NO_RISK"},
                {"condition": "RAI-008-B", "risk": "MEDIUM_RISK"},
                {"condition": "default", "risk": "HIGH_RISK"}
            ],
            ai_dimensions=["safety", "controllability"]
        ),
    ])
    
    return questions


# ============================================================================
# AI LENS MODULE - STREAMLIT UI
# ============================================================================

class AILensModule:
    """AWS Well-Architected AI Lens Assessment Module"""
    
    def __init__(self):
        """Initialize the AI Lens module"""
        self.ml_questions = get_ml_lens_questions()
        self.genai_questions = get_genai_lens_questions()
        self.rai_questions = get_responsible_ai_lens_questions()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state for AI lens assessments"""
        if 'ai_lens_assessments' not in st.session_state:
            st.session_state.ai_lens_assessments = {}
        if 'current_ai_lens' not in st.session_state:
            st.session_state.current_ai_lens = None
        if 'ai_lens_responses' not in st.session_state:
            st.session_state.ai_lens_responses = {}
    
    def render(self):
        """Render the main AI Lens module UI"""
        st.markdown("## 🧠 AWS Well-Architected AI Lens")
        st.markdown("*Assess your AI/ML workloads against AWS best practices for Machine Learning, Generative AI, and Responsible AI*")
        
        # Summary stats
        total_ml = len(self.ml_questions)
        total_genai = len(self.genai_questions)
        total_rai = len(self.rai_questions)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🧠 ML Lens", f"{total_ml} questions")
        with col2:
            st.metric("✨ GenAI Lens", f"{total_genai} questions")
        with col3:
            st.metric("⚖️ RAI Lens", f"{total_rai} questions")
        with col4:
            answered = len(st.session_state.ai_lens_responses)
            st.metric("📝 Answered", f"{answered} total")
        
        # Lens selection tabs
        tabs = st.tabs([
            "🧠 Machine Learning Lens",
            "✨ Generative AI Lens", 
            "⚖️ Responsible AI Lens",
            "📊 Assessment Dashboard",
            "📥 Export Custom Lens"
        ])
        
        with tabs[0]:
            self.render_ml_lens()
        
        with tabs[1]:
            self.render_genai_lens()
        
        with tabs[2]:
            self.render_responsible_ai_lens()
        
        with tabs[3]:
            self.render_dashboard()
        
        with tabs[4]:
            self.render_export()
    
    def render_ml_lens(self):
        """Render Machine Learning Lens assessment"""
        st.markdown("### 🧠 Machine Learning Lens")
        st.info("""
        **AWS Well-Architected Machine Learning Lens** provides best practices for:
        - ML lifecycle management (data, training, deployment, monitoring)
        - ML security and access controls
        - ML reliability and reproducibility
        - ML performance optimization
        - ML cost optimization
        - ML sustainability
        
        Based on: [AWS ML Lens Documentation](https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/)
        """)
        
        # Group questions by pillar
        pillars = {}
        for q in self.ml_questions:
            if q.pillar not in pillars:
                pillars[q.pillar] = []
            pillars[q.pillar].append(q)
        
        # Render questions by pillar
        for pillar, questions in pillars.items():
            with st.expander(f"📋 {pillar} ({len(questions)} questions)", expanded=False):
                for q in questions:
                    self.render_question(q, "ml")
    
    def render_genai_lens(self):
        """Render Generative AI Lens assessment"""
        st.markdown("### ✨ Generative AI Lens")
        st.info("""
        **AWS Well-Architected Generative AI Lens** provides best practices for:
        - Foundation model selection and evaluation
        - Prompt engineering and management
        - RAG architecture design and reliability
        - GenAI security (prompt injection, content safety)
        - Latency and cost optimization for token-based billing
        - AI agent security and control
        
        Based on: [AWS GenAI Lens Documentation](https://docs.aws.amazon.com/wellarchitected/latest/generative-ai-lens/)
        """)
        
        # Group questions by phase
        phases = {}
        for q in self.genai_questions:
            if q.phase not in phases:
                phases[q.phase] = []
            phases[q.phase].append(q)
        
        # Render questions by phase
        for phase, questions in phases.items():
            phase_display = phase.replace("_", " ").title()
            with st.expander(f"📋 {phase_display} ({len(questions)} questions)", expanded=False):
                for q in questions:
                    self.render_question(q, "genai")
    
    def render_responsible_ai_lens(self):
        """Render Responsible AI Lens assessment"""
        st.markdown("### ⚖️ Responsible AI Lens")
        st.info("""
        **AWS Well-Architected Responsible AI Lens** provides best practices for:
        - Fairness and bias mitigation
        - Explainability and interpretability
        - Privacy and data ethics
        - Human oversight and control
        - Safety testing and red teaming
        - Transparency and disclosure
        - Incident response for AI harms
        
        Based on: [AWS Responsible AI Lens Documentation](https://docs.aws.amazon.com/wellarchitected/latest/responsible-ai-lens/)
        """)
        
        # Show AI dimensions legend
        with st.expander("📖 Responsible AI Dimensions"):
            st.markdown("""
            | Dimension | Description |
            |-----------|-------------|
            | 🎯 **Fairness** | Equal treatment across demographic groups |
            | 💡 **Explainability** | Understanding how AI makes decisions |
            | 🔒 **Privacy** | Protecting personal and sensitive data |
            | 🛡️ **Safety** | Preventing harm to users and society |
            | 🎮 **Controllability** | Human oversight and intervention capability |
            | ✅ **Veracity** | Truthful, accurate, and grounded outputs |
            | 💪 **Robustness** | Consistent performance under various conditions |
            | 👁️ **Transparency** | Clear communication about AI use and limitations |
            """)
        
        for q in self.rai_questions:
            with st.expander(f"📋 {q.title}", expanded=False):
                self.render_question(q, "rai")
    
    def render_question(self, question: AILensQuestion, lens_prefix: str):
        """Render a single assessment question"""
        key = f"{lens_prefix}_{question.id}"
        
        st.markdown(f"**{question.id}: {question.title}**")
        st.markdown(f"*{question.description}*")
        
        # Show category and phase
        st.caption(f"Category: {question.category} | Phase: {question.phase}")
        
        with st.expander("ℹ️ Why is this important?"):
            st.markdown(question.why_important)
            
            st.markdown("**Best Practices:**")
            for bp in question.best_practices:
                st.markdown(f"- {bp}")
            
            if question.aws_services:
                st.markdown(f"**AWS Services:** {', '.join(question.aws_services)}")
            
            if question.ai_dimensions:
                st.markdown(f"**AI Dimensions:** {', '.join(question.ai_dimensions)}")
            
            if question.helpful_resources:
                st.markdown("**Resources:**")
                for resource in question.helpful_resources:
                    st.markdown(f"- [{resource['displayText']}]({resource['url']})")
        
        # Render choices
        choice_options = [c["title"] for c in question.choices]
        
        # Get previously selected answer if any
        current_response = st.session_state.ai_lens_responses.get(key, {})
        current_index = None
        if current_response:
            try:
                current_index = choice_options.index(current_response.get("choice", ""))
            except ValueError:
                current_index = None
        
        selected = st.radio(
            "Select your current state:",
            choice_options,
            key=key,
            index=current_index
        )
        
        if selected:
            selected_choice = next(c for c in question.choices if c["title"] == selected)
            risk = selected_choice["risk"]
            
            if risk == "NO_RISK":
                st.success("✅ No risk - Best practice implemented")
            elif risk == "MEDIUM_RISK":
                st.warning("⚠️ Medium risk - Improvement recommended")
            elif risk == "HIGH_RISK":
                st.error("🔴 High risk - Action required")
            elif risk == "CRITICAL":
                st.error("🚨 Critical risk - Immediate action required")
            
            # Save response
            st.session_state.ai_lens_responses[key] = {
                "question_id": question.id,
                "lens": lens_prefix,
                "choice": selected,
                "choice_id": selected_choice["id"],
                "risk": risk,
                "pillar": question.pillar,
                "category": question.category,
                "timestamp": datetime.now().isoformat()
            }
        
        st.markdown("---")
    
    def render_dashboard(self):
        """Render the AI Lens assessment dashboard"""
        st.markdown("### 📊 AI Lens Assessment Dashboard")
        
        if not st.session_state.ai_lens_responses:
            st.info("👋 Complete some assessment questions to see your dashboard and scores.")
            return
        
        # Calculate scores by lens
        ml_responses = {k: v for k, v in st.session_state.ai_lens_responses.items() if k.startswith("ml_")}
        genai_responses = {k: v for k, v in st.session_state.ai_lens_responses.items() if k.startswith("genai_")}
        rai_responses = {k: v for k, v in st.session_state.ai_lens_responses.items() if k.startswith("rai_")}
        
        # Overall lens scores
        st.markdown("#### Lens Scores")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ml_score = self.calculate_score(ml_responses)
            ml_total = len(self.ml_questions)
            ml_answered = len(ml_responses)
            st.metric(
                "🧠 ML Lens Score", 
                f"{ml_score}%", 
                delta=f"{ml_answered}/{ml_total} answered"
            )
            self.render_score_bar(ml_score)
        
        with col2:
            genai_score = self.calculate_score(genai_responses)
            genai_total = len(self.genai_questions)
            genai_answered = len(genai_responses)
            st.metric(
                "✨ GenAI Lens Score", 
                f"{genai_score}%", 
                delta=f"{genai_answered}/{genai_total} answered"
            )
            self.render_score_bar(genai_score)
        
        with col3:
            rai_score = self.calculate_score(rai_responses)
            rai_total = len(self.rai_questions)
            rai_answered = len(rai_responses)
            st.metric(
                "⚖️ RAI Lens Score", 
                f"{rai_score}%", 
                delta=f"{rai_answered}/{rai_total} answered"
            )
            self.render_score_bar(rai_score)
        
        # Risk summary
        st.markdown("#### Risk Summary")
        all_responses = st.session_state.ai_lens_responses
        
        risks = {"NO_RISK": 0, "MEDIUM_RISK": 0, "HIGH_RISK": 0, "CRITICAL": 0}
        for r in all_responses.values():
            risk_level = r.get("risk", "HIGH_RISK")
            risks[risk_level] = risks.get(risk_level, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("✅ No Risk", risks["NO_RISK"])
        col2.metric("⚠️ Medium", risks["MEDIUM_RISK"])
        col3.metric("🔴 High", risks["HIGH_RISK"])
        col4.metric("🚨 Critical", risks["CRITICAL"])
        
        # High priority items
        high_priority = [r for r in all_responses.values() if r.get("risk") in ["HIGH_RISK", "CRITICAL"]]
        if high_priority:
            st.markdown("#### 🚨 High Priority Items Requiring Attention")
            for item in high_priority:
                risk_icon = "🚨" if item.get("risk") == "CRITICAL" else "🔴"
                st.error(f"{risk_icon} **{item.get('question_id')}** ({item.get('pillar', 'Unknown')}) - {item.get('category', 'Unknown')}")
        
        # Score by pillar
        st.markdown("#### Score by WAF Pillar")
        pillar_scores = self.calculate_pillar_scores(all_responses)
        
        for pillar, score_data in pillar_scores.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{pillar}**")
                self.render_score_bar(score_data["score"])
            with col2:
                st.write(f"{score_data['score']}% ({score_data['answered']} answered)")
        
        # Clear responses button
        if st.button("🗑️ Clear All Responses", type="secondary"):
            st.session_state.ai_lens_responses = {}
            st.rerun()
    
    def render_score_bar(self, score: int):
        """Render a colored progress bar for score"""
        if score >= 80:
            color = "#27ae60"  # Green
        elif score >= 60:
            color = "#f39c12"  # Orange
        else:
            color = "#e74c3c"  # Red
        
        st.markdown(
            f"""
            <div style="background-color: #333; border-radius: 10px; height: 20px; width: 100%;">
                <div style="background-color: {color}; width: {score}%; height: 100%; border-radius: 10px;"></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def calculate_score(self, responses: Dict) -> int:
        """Calculate assessment score from responses"""
        if not responses:
            return 0
        
        total = len(responses)
        points = 0
        
        for r in responses.values():
            risk = r.get("risk", "HIGH_RISK")
            if risk == "NO_RISK":
                points += 100
            elif risk == "MEDIUM_RISK":
                points += 50
            # HIGH_RISK and CRITICAL = 0 points
        
        return int(points / total)
    
    def calculate_pillar_scores(self, responses: Dict) -> Dict[str, Dict]:
        """Calculate scores grouped by WAF pillar"""
        pillars = {}
        
        for r in responses.values():
            pillar = r.get("pillar", "Unknown")
            if pillar not in pillars:
                pillars[pillar] = {"total": 0, "points": 0, "answered": 0}
            
            pillars[pillar]["answered"] += 1
            pillars[pillar]["total"] += 100
            
            risk = r.get("risk", "HIGH_RISK")
            if risk == "NO_RISK":
                pillars[pillar]["points"] += 100
            elif risk == "MEDIUM_RISK":
                pillars[pillar]["points"] += 50
        
        # Calculate percentages
        result = {}
        for pillar, data in pillars.items():
            if data["total"] > 0:
                result[pillar] = {
                    "score": int((data["points"] / data["total"]) * 100),
                    "answered": data["answered"]
                }
        
        return result
    
    def render_export(self):
        """Render export functionality for custom lens JSON"""
        st.markdown("### 📥 Export Custom Lens")
        st.info("""
        Export your AI Lens assessment as a Custom Lens JSON file that can be imported into 
        the AWS Well-Architected Tool. This allows you to:
        - Use the lens in official AWS WA reviews
        - Share with other AWS accounts
        - Track assessments over time in AWS
        """)
        
        lens_choice = st.selectbox(
            "Select Lens to Export",
            ["Machine Learning Lens", "Generative AI Lens", "Responsible AI Lens", "All AI Lenses Combined"]
        )
        
        if st.button("📦 Generate Custom Lens JSON", type="primary"):
            if lens_choice == "Machine Learning Lens":
                questions = self.ml_questions
                lens_name = "Machine Learning Lens"
                lens_id = "ml_lens"
            elif lens_choice == "Generative AI Lens":
                questions = self.genai_questions
                lens_name = "Generative AI Lens"
                lens_id = "genai_lens"
            elif lens_choice == "Responsible AI Lens":
                questions = self.rai_questions
                lens_name = "Responsible AI Lens"
                lens_id = "rai_lens"
            else:
                questions = self.ml_questions + self.genai_questions + self.rai_questions
                lens_name = "AI Lens (ML + GenAI + RAI)"
                lens_id = "ai_lens_combined"
            
            custom_lens = self.generate_custom_lens_json(questions, lens_name, lens_id)
            
            st.download_button(
                label="⬇️ Download Custom Lens JSON",
                data=json.dumps(custom_lens, indent=2),
                file_name=f"aws-wa-{lens_id}-custom-lens.json",
                mime="application/json"
            )
            
            with st.expander("Preview JSON"):
                st.json(custom_lens)
    
    def generate_custom_lens_json(self, questions: List[AILensQuestion], lens_name: str, lens_id: str) -> Dict:
        """Generate AWS Well-Architected Tool custom lens JSON format"""
        
        # Group questions by pillar
        pillars_dict = {}
        for q in questions:
            if q.pillar not in pillars_dict:
                pillars_dict[q.pillar] = []
            pillars_dict[q.pillar].append(q)
        
        # Build pillars array
        pillars = []
        for pillar_name, pillar_questions in pillars_dict.items():
            pillar_id = pillar_name.lower().replace(" ", "_")
            
            # Build questions array
            lens_questions = []
            for q in pillar_questions:
                choices = []
                for c in q.choices:
                    choice = {
                        "id": c["id"],
                        "title": c["title"],
                        "helpfulResource": {
                            "displayText": f"Best practices for {q.category}",
                            "url": q.helpful_resources[0]["url"] if q.helpful_resources else "https://docs.aws.amazon.com/wellarchitected/latest/machine-learning-lens/"
                        },
                        "improvementPlan": {
                            "displayText": f"Implement: {q.best_practices[0] if q.best_practices else 'Review best practices'}"
                        }
                    }
                    choices.append(choice)
                
                # Build risk rules
                risk_rules = []
                for rule in q.risk_rules:
                    risk_rules.append({
                        "condition": rule["condition"],
                        "risk": rule["risk"]
                    })
                
                lens_question = {
                    "id": q.id,
                    "title": q.title,
                    "description": q.description,
                    "choices": choices,
                    "riskRules": risk_rules
                }
                lens_questions.append(lens_question)
            
            pillar = {
                "id": pillar_id,
                "name": pillar_name,
                "questions": lens_questions
            }
            pillars.append(pillar)
        
        # Build final custom lens structure
        custom_lens = {
            "schemaVersion": "2021-11-01",
            "name": lens_name,
            "description": f"AWS Well-Architected {lens_name} - Custom lens for AI/ML workload assessment. Generated by AWS WAF Scanner Enterprise.",
            "pillars": pillars
        }
        
        return custom_lens


# ============================================================================
# INTEGRATION WITH MAIN APP
# ============================================================================

def render_ai_lens_tab():
    """Render AI Lens tab in main application"""
    module = AILensModule()
    module.render()


# Export for integration
__all__ = [
    'AILensModule',
    'AILensType',
    'AILensQuestion',
    'get_ml_lens_questions',
    'get_genai_lens_questions', 
    'get_responsible_ai_lens_questions',
    'render_ai_lens_tab'
]
