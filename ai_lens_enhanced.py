"""
Enhanced AI Lens Module for AWS WAF Scanner Enterprise
=======================================================
Version: 2.0.0

This module transforms the generic AI Lens into an intelligent, automated assessment:
1. Auto-detects AI/ML services in AWS accounts
2. Shows only relevant questions based on detected services
3. Generates findings from actual infrastructure
4. Uses Claude AI for contextual recommendations
5. Integrates with WAF pillars for unified scoring
6. Provides actionable improvement roadmap

Based on:
- AWS Well-Architected Machine Learning Lens
- AWS Well-Architected Generative AI Lens  
- AWS Responsible AI Lens
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os

# Optional imports
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class AIServiceCategory(Enum):
    """Categories of AI/ML services"""
    ML_PLATFORM = "ml_platform"
    GENERATIVE_AI = "generative_ai"
    AI_VISION = "ai_vision"
    AI_LANGUAGE = "ai_language"
    AI_SEARCH = "ai_search"
    AI_ANALYTICS = "ai_analytics"
    AI_HEALTHCARE = "ai_healthcare"


class ResponsibleAIDimension(Enum):
    """AWS 8 Dimensions of Responsible AI"""
    FAIRNESS = "fairness"
    EXPLAINABILITY = "explainability"
    PRIVACY_SECURITY = "privacy_security"
    SAFETY = "safety"
    CONTROLLABILITY = "controllability"
    VERACITY_ROBUSTNESS = "veracity_robustness"
    GOVERNANCE = "governance"
    TRANSPARENCY = "transparency"


class FindingSeverity(Enum):
    """Finding severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class AIMLService:
    """Detected AI/ML service"""
    service_name: str
    display_name: str
    category: AIServiceCategory
    applicable_lenses: List[str]
    resource_count: int = 0
    resources: List[Dict] = field(default_factory=list)
    region: str = "us-east-1"


@dataclass
class AIMLInventory:
    """Complete AI/ML service inventory"""
    # SageMaker
    sagemaker_notebooks: int = 0
    sagemaker_endpoints: int = 0
    sagemaker_models: int = 0
    sagemaker_pipelines: int = 0
    sagemaker_feature_groups: int = 0
    sagemaker_training_jobs: int = 0
    sagemaker_monitoring_schedules: int = 0
    
    # Bedrock
    bedrock_models_enabled: int = 0
    bedrock_custom_models: int = 0
    bedrock_agents: int = 0
    bedrock_knowledge_bases: int = 0
    bedrock_guardrails: int = 0
    bedrock_provisioned_throughput: int = 0
    
    # AI Services
    rekognition_projects: int = 0
    rekognition_collections: int = 0
    comprehend_endpoints: int = 0
    comprehend_flywheels: int = 0
    lex_bots: int = 0
    kendra_indexes: int = 0
    personalize_campaigns: int = 0
    personalize_datasets: int = 0
    forecast_predictors: int = 0
    transcribe_vocabularies: int = 0
    textract_adapters: int = 0
    translate_terminologies: int = 0
    frauddetector_detectors: int = 0
    
    # Flags
    has_ml_workloads: bool = False
    has_genai_workloads: bool = False
    has_ai_services: bool = False
    has_responsible_ai_concerns: bool = False
    
    # Lists
    detected_services: List[str] = field(default_factory=list)
    scan_errors: Dict[str, str] = field(default_factory=dict)
    scan_timestamp: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'sagemaker': {
                'notebooks': self.sagemaker_notebooks,
                'endpoints': self.sagemaker_endpoints,
                'models': self.sagemaker_models,
                'pipelines': self.sagemaker_pipelines,
                'feature_groups': self.sagemaker_feature_groups,
                'monitoring_schedules': self.sagemaker_monitoring_schedules
            },
            'bedrock': {
                'models_enabled': self.bedrock_models_enabled,
                'custom_models': self.bedrock_custom_models,
                'agents': self.bedrock_agents,
                'knowledge_bases': self.bedrock_knowledge_bases,
                'guardrails': self.bedrock_guardrails
            },
            'ai_services': {
                'rekognition_projects': self.rekognition_projects,
                'comprehend_endpoints': self.comprehend_endpoints,
                'lex_bots': self.lex_bots,
                'kendra_indexes': self.kendra_indexes,
                'personalize_campaigns': self.personalize_campaigns,
                'forecast_predictors': self.forecast_predictors,
                'frauddetector_detectors': self.frauddetector_detectors
            },
            'flags': {
                'has_ml_workloads': self.has_ml_workloads,
                'has_genai_workloads': self.has_genai_workloads,
                'has_ai_services': self.has_ai_services,
                'has_responsible_ai_concerns': self.has_responsible_ai_concerns
            },
            'detected_services': self.detected_services,
            'scan_timestamp': self.scan_timestamp
        }


@dataclass
class AIMLFinding:
    """AI/ML specific finding"""
    id: str
    title: str
    description: str
    severity: FindingSeverity
    lens_type: str  # machine_learning, generative_ai, responsible_ai
    waf_pillar: str
    service: str
    affected_resources: List[str] = field(default_factory=list)
    recommendation: str = ""
    remediation_steps: List[str] = field(default_factory=list)
    aws_solution: str = ""
    estimated_effort: str = ""
    ai_dimensions: List[ResponsibleAIDimension] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'lens_type': self.lens_type,
            'waf_pillar': self.waf_pillar,
            'service': self.service,
            'affected_resources': self.affected_resources,
            'recommendation': self.recommendation,
            'remediation_steps': self.remediation_steps,
            'aws_solution': self.aws_solution,
            'estimated_effort': self.estimated_effort,
            'ai_dimensions': [d.value for d in self.ai_dimensions]
        }


# ============================================================================
# AI/ML SERVICE AUTO-DETECTION ENGINE
# ============================================================================

class AIMLAutoDetector:
    """Automatically detect AI/ML services in AWS account"""
    
    def __init__(self, session=None):
        self.session = session
        self.inventory = AIMLInventory()
        self.errors = {}
        
    def scan_all(self, regions: List[str] = None) -> AIMLInventory:
        """Scan all AI/ML services across regions"""
        if not BOTO3_AVAILABLE:
            return self._get_demo_inventory()
            
        if regions is None:
            regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        
        self.inventory.scan_timestamp = datetime.now().isoformat()
        
        # Scan each service
        self._scan_sagemaker(regions)
        self._scan_bedrock(regions)
        self._scan_rekognition(regions)
        self._scan_comprehend(regions)
        self._scan_lex(regions)
        self._scan_kendra(regions)
        self._scan_personalize(regions)
        self._scan_forecast(regions)
        self._scan_frauddetector(regions)
        
        # Update flags
        self._update_flags()
        
        return self.inventory
    
    def _scan_sagemaker(self, regions: List[str]):
        """Scan SageMaker resources"""
        for region in regions:
            try:
                sm = self.session.client('sagemaker', region_name=region)
                
                # Notebooks
                try:
                    notebooks = sm.list_notebook_instances()
                    count = len(notebooks.get('NotebookInstances', []))
                    self.inventory.sagemaker_notebooks += count
                    if count > 0 and 'sagemaker' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('sagemaker')
                except Exception:
                    pass
                
                # Endpoints
                try:
                    endpoints = sm.list_endpoints()
                    self.inventory.sagemaker_endpoints += len(endpoints.get('Endpoints', []))
                except Exception:
                    pass
                
                # Models
                try:
                    models = sm.list_models(MaxResults=100)
                    self.inventory.sagemaker_models += len(models.get('Models', []))
                except Exception:
                    pass
                
                # Pipelines
                try:
                    pipelines = sm.list_pipelines()
                    self.inventory.sagemaker_pipelines += len(pipelines.get('PipelineSummaries', []))
                except Exception:
                    pass
                
                # Feature Groups
                try:
                    fg = sm.list_feature_groups()
                    self.inventory.sagemaker_feature_groups += len(fg.get('FeatureGroupSummaries', []))
                except Exception:
                    pass
                
                # Monitoring Schedules
                try:
                    mon = sm.list_monitoring_schedules()
                    self.inventory.sagemaker_monitoring_schedules += len(mon.get('MonitoringScheduleSummaries', []))
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'sagemaker_{region}'] = str(e)
    
    def _scan_bedrock(self, regions: List[str]):
        """Scan Bedrock resources"""
        # Bedrock is only available in specific regions
        bedrock_regions = [r for r in regions if r in ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-northeast-1']]
        
        for region in bedrock_regions:
            try:
                bedrock = self.session.client('bedrock', region_name=region)
                
                # Foundation models (check if any enabled)
                try:
                    models = bedrock.list_foundation_models()
                    model_count = len([m for m in models.get('modelSummaries', []) 
                                      if m.get('modelLifecycle', {}).get('status') == 'ACTIVE'])
                    if model_count > 0:
                        self.inventory.bedrock_models_enabled = model_count
                        if 'bedrock' not in self.inventory.detected_services:
                            self.inventory.detected_services.append('bedrock')
                except Exception:
                    pass
                
                # Custom models
                try:
                    custom = bedrock.list_custom_models()
                    self.inventory.bedrock_custom_models += len(custom.get('modelSummaries', []))
                except Exception:
                    pass
                
                # Guardrails
                try:
                    guardrails = bedrock.list_guardrails()
                    self.inventory.bedrock_guardrails += len(guardrails.get('guardrails', []))
                except Exception:
                    pass
                
                # Provisioned throughput
                try:
                    pt = bedrock.list_provisioned_model_throughputs()
                    self.inventory.bedrock_provisioned_throughput += len(pt.get('provisionedModelSummaries', []))
                except Exception:
                    pass
                
                # Agents (bedrock-agent client)
                try:
                    bedrock_agent = self.session.client('bedrock-agent', region_name=region)
                    agents = bedrock_agent.list_agents()
                    self.inventory.bedrock_agents += len(agents.get('agentSummaries', []))
                    
                    # Knowledge bases
                    kbs = bedrock_agent.list_knowledge_bases()
                    self.inventory.bedrock_knowledge_bases += len(kbs.get('knowledgeBaseSummaries', []))
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'bedrock_{region}'] = str(e)
    
    def _scan_rekognition(self, regions: List[str]):
        """Scan Rekognition resources"""
        for region in regions:
            try:
                rek = self.session.client('rekognition', region_name=region)
                
                # Projects
                try:
                    projects = rek.describe_projects()
                    count = len(projects.get('ProjectDescriptions', []))
                    self.inventory.rekognition_projects += count
                    if count > 0 and 'rekognition' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('rekognition')
                except Exception:
                    pass
                
                # Collections
                try:
                    collections = rek.list_collections()
                    self.inventory.rekognition_collections += len(collections.get('CollectionIds', []))
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'rekognition_{region}'] = str(e)
    
    def _scan_comprehend(self, regions: List[str]):
        """Scan Comprehend resources"""
        for region in regions:
            try:
                comp = self.session.client('comprehend', region_name=region)
                
                # Endpoints
                try:
                    endpoints = comp.list_endpoints()
                    count = len(endpoints.get('EndpointPropertiesList', []))
                    self.inventory.comprehend_endpoints += count
                    if count > 0 and 'comprehend' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('comprehend')
                except Exception:
                    pass
                
                # Flywheels
                try:
                    flywheels = comp.list_flywheels()
                    self.inventory.comprehend_flywheels += len(flywheels.get('FlywheelSummaryList', []))
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'comprehend_{region}'] = str(e)
    
    def _scan_lex(self, regions: List[str]):
        """Scan Lex resources"""
        for region in regions:
            try:
                lex = self.session.client('lexv2-models', region_name=region)
                
                try:
                    bots = lex.list_bots()
                    count = len(bots.get('botSummaries', []))
                    self.inventory.lex_bots += count
                    if count > 0 and 'lex' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('lex')
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'lex_{region}'] = str(e)
    
    def _scan_kendra(self, regions: List[str]):
        """Scan Kendra resources"""
        for region in regions:
            try:
                kendra = self.session.client('kendra', region_name=region)
                
                try:
                    indexes = kendra.list_indices()
                    count = len(indexes.get('IndexConfigurationSummaryItems', []))
                    self.inventory.kendra_indexes += count
                    if count > 0 and 'kendra' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('kendra')
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'kendra_{region}'] = str(e)
    
    def _scan_personalize(self, regions: List[str]):
        """Scan Personalize resources"""
        for region in regions:
            try:
                pers = self.session.client('personalize', region_name=region)
                
                try:
                    campaigns = pers.list_campaigns()
                    count = len(campaigns.get('campaigns', []))
                    self.inventory.personalize_campaigns += count
                    if count > 0 and 'personalize' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('personalize')
                except Exception:
                    pass
                
                try:
                    datasets = pers.list_datasets()
                    self.inventory.personalize_datasets += len(datasets.get('datasets', []))
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'personalize_{region}'] = str(e)
    
    def _scan_forecast(self, regions: List[str]):
        """Scan Forecast resources"""
        for region in regions:
            try:
                forecast = self.session.client('forecast', region_name=region)
                
                try:
                    predictors = forecast.list_predictors()
                    count = len(predictors.get('Predictors', []))
                    self.inventory.forecast_predictors += count
                    if count > 0 and 'forecast' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('forecast')
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'forecast_{region}'] = str(e)
    
    def _scan_frauddetector(self, regions: List[str]):
        """Scan Fraud Detector resources"""
        for region in regions:
            try:
                fd = self.session.client('frauddetector', region_name=region)
                
                try:
                    detectors = fd.get_detectors()
                    count = len(detectors.get('detectors', []))
                    self.inventory.frauddetector_detectors += count
                    if count > 0 and 'frauddetector' not in self.inventory.detected_services:
                        self.inventory.detected_services.append('frauddetector')
                except Exception:
                    pass
                    
            except Exception as e:
                self.errors[f'frauddetector_{region}'] = str(e)
    
    def _update_flags(self):
        """Update inventory flags based on detected resources"""
        # ML workloads (SageMaker)
        if (self.inventory.sagemaker_notebooks > 0 or
            self.inventory.sagemaker_endpoints > 0 or
            self.inventory.sagemaker_pipelines > 0):
            self.inventory.has_ml_workloads = True
        
        # GenAI workloads (Bedrock)
        if (self.inventory.bedrock_agents > 0 or
            self.inventory.bedrock_knowledge_bases > 0 or
            self.inventory.bedrock_custom_models > 0):
            self.inventory.has_genai_workloads = True
        
        # AI Services
        if (self.inventory.rekognition_projects > 0 or
            self.inventory.comprehend_endpoints > 0 or
            self.inventory.lex_bots > 0 or
            self.inventory.personalize_campaigns > 0):
            self.inventory.has_ai_services = True
        
        # Responsible AI concerns (services that handle personal data or make decisions)
        if (self.inventory.personalize_campaigns > 0 or
            self.inventory.rekognition_projects > 0 or
            self.inventory.rekognition_collections > 0 or
            self.inventory.frauddetector_detectors > 0):
            self.inventory.has_responsible_ai_concerns = True
        
        self.inventory.scan_errors = self.errors
    
    def _get_demo_inventory(self) -> AIMLInventory:
        """Return demo inventory for demo mode"""
        return AIMLInventory(
            sagemaker_notebooks=3,
            sagemaker_endpoints=5,
            sagemaker_models=12,
            sagemaker_pipelines=2,
            sagemaker_feature_groups=3,
            sagemaker_monitoring_schedules=2,
            bedrock_models_enabled=8,
            bedrock_custom_models=1,
            bedrock_agents=2,
            bedrock_knowledge_bases=3,
            bedrock_guardrails=1,
            rekognition_projects=2,
            rekognition_collections=5,
            comprehend_endpoints=1,
            lex_bots=2,
            kendra_indexes=1,
            personalize_campaigns=2,
            personalize_datasets=4,
            forecast_predictors=1,
            frauddetector_detectors=1,
            has_ml_workloads=True,
            has_genai_workloads=True,
            has_ai_services=True,
            has_responsible_ai_concerns=True,
            detected_services=['sagemaker', 'bedrock', 'rekognition', 'comprehend', 
                             'lex', 'kendra', 'personalize', 'forecast', 'frauddetector'],
            scan_timestamp=datetime.now().isoformat()
        )


# ============================================================================
# FINDINGS GENERATOR
# ============================================================================

class AIMLFindingsGenerator:
    """Generate AI/ML specific findings based on inventory"""
    
    def __init__(self, inventory: AIMLInventory):
        self.inventory = inventory
        self.findings: List[AIMLFinding] = []
    
    def generate_all(self) -> List[AIMLFinding]:
        """Generate all findings based on inventory"""
        self._generate_sagemaker_findings()
        self._generate_bedrock_findings()
        self._generate_responsible_ai_findings()
        self._generate_mlops_findings()
        return self.findings
    
    def _generate_sagemaker_findings(self):
        """Generate SageMaker-related findings"""
        
        # Endpoints without monitoring
        if self.inventory.sagemaker_endpoints > 0:
            if self.inventory.sagemaker_monitoring_schedules < self.inventory.sagemaker_endpoints:
                unmonitored = self.inventory.sagemaker_endpoints - self.inventory.sagemaker_monitoring_schedules
                self.findings.append(AIMLFinding(
                    id="AIML-SM-001",
                    title="SageMaker Endpoints Without Model Monitor",
                    description=f"{unmonitored} of {self.inventory.sagemaker_endpoints} SageMaker endpoints do not have Model Monitor configured. This means data drift and model degradation cannot be detected automatically.",
                    severity=FindingSeverity.HIGH,
                    lens_type="machine_learning",
                    waf_pillar="Operational Excellence",
                    service="SageMaker",
                    affected_resources=[f"{unmonitored} unmonitored endpoints"],
                    recommendation="Configure SageMaker Model Monitor for all production endpoints",
                    remediation_steps=[
                        "Capture baseline statistics from training data",
                        "Create a MonitoringSchedule for each endpoint",
                        "Configure data quality and model quality monitors",
                        "Set up CloudWatch alarms for drift violations",
                        "Establish automated retraining triggers"
                    ],
                    aws_solution="Amazon SageMaker Model Monitor",
                    estimated_effort="2-4 hours per endpoint"
                ))
        
        # Notebooks in production regions
        if self.inventory.sagemaker_notebooks > 0:
            self.findings.append(AIMLFinding(
                id="AIML-SM-002",
                title="SageMaker Notebook Instances Detected",
                description=f"Found {self.inventory.sagemaker_notebooks} notebook instances. Ensure they are in VPC with no direct internet access, have encryption enabled, and follow least-privilege IAM.",
                severity=FindingSeverity.MEDIUM,
                lens_type="machine_learning",
                waf_pillar="Security",
                service="SageMaker",
                affected_resources=[f"{self.inventory.sagemaker_notebooks} notebooks"],
                recommendation="Review notebook security configuration and migrate to SageMaker Studio",
                remediation_steps=[
                    "Audit notebook network configuration (VPC vs direct internet)",
                    "Enable encryption at rest and in transit",
                    "Review IAM execution role permissions",
                    "Consider migrating to SageMaker Studio for better governance",
                    "Implement lifecycle configurations for security policies"
                ],
                aws_solution="Amazon SageMaker Studio with VPC-only mode",
                estimated_effort="1-2 days for migration"
            ))
        
        # No feature store
        if self.inventory.sagemaker_endpoints > 0 and self.inventory.sagemaker_feature_groups == 0:
            self.findings.append(AIMLFinding(
                id="AIML-SM-003",
                title="ML Endpoints Without Feature Store",
                description="SageMaker endpoints detected but no Feature Groups. Feature Store ensures training-serving consistency and prevents training-serving skew.",
                severity=FindingSeverity.MEDIUM,
                lens_type="machine_learning",
                waf_pillar="Reliability",
                service="SageMaker",
                recommendation="Implement SageMaker Feature Store for feature management",
                remediation_steps=[
                    "Identify features used in model training",
                    "Create Feature Groups for each feature set",
                    "Configure online store for real-time inference",
                    "Set up offline store for training data",
                    "Update inference pipeline to use Feature Store"
                ],
                aws_solution="Amazon SageMaker Feature Store",
                estimated_effort="1-2 weeks"
            ))
        
        # No pipelines (manual ML)
        if self.inventory.sagemaker_endpoints > 0 and self.inventory.sagemaker_pipelines == 0:
            self.findings.append(AIMLFinding(
                id="AIML-SM-004",
                title="No MLOps Pipelines Detected",
                description="Production endpoints exist but no SageMaker Pipelines. This indicates manual ML workflows without CI/CD automation.",
                severity=FindingSeverity.MEDIUM,
                lens_type="machine_learning",
                waf_pillar="Operational Excellence",
                service="SageMaker",
                recommendation="Implement SageMaker Pipelines for automated ML workflows",
                remediation_steps=[
                    "Define ML workflow steps (preprocessing, training, evaluation)",
                    "Create SageMaker Pipeline with appropriate steps",
                    "Implement model approval workflow",
                    "Set up automatic retraining triggers",
                    "Integrate with CI/CD for code changes"
                ],
                aws_solution="Amazon SageMaker Pipelines + AWS CodePipeline",
                estimated_effort="2-4 weeks"
            ))
    
    def _generate_bedrock_findings(self):
        """Generate Bedrock-related findings"""
        
        # Agents without guardrails (CRITICAL)
        if self.inventory.bedrock_agents > 0 and self.inventory.bedrock_guardrails == 0:
            self.findings.append(AIMLFinding(
                id="AIML-BR-001",
                title="Bedrock Agents Without Guardrails - CRITICAL",
                description=f"Found {self.inventory.bedrock_agents} Bedrock agents but no guardrails configured. Agents can access tools and take actions - without guardrails, they may generate harmful content or be vulnerable to prompt injection.",
                severity=FindingSeverity.CRITICAL,
                lens_type="generative_ai",
                waf_pillar="Security",
                service="Bedrock",
                affected_resources=[f"{self.inventory.bedrock_agents} agents without guardrails"],
                recommendation="Immediately configure Bedrock Guardrails for all agents",
                remediation_steps=[
                    "Create Bedrock Guardrail with content filters",
                    "Configure denied topics relevant to your use case",
                    "Add word filters for sensitive terms",
                    "Enable PII detection and redaction",
                    "Associate guardrails with all agents",
                    "Test with adversarial prompts"
                ],
                aws_solution="Amazon Bedrock Guardrails",
                estimated_effort="2-4 hours",
                ai_dimensions=[ResponsibleAIDimension.SAFETY, ResponsibleAIDimension.CONTROLLABILITY]
            ))
        
        # Knowledge bases security
        if self.inventory.bedrock_knowledge_bases > 0:
            self.findings.append(AIMLFinding(
                id="AIML-BR-002",
                title="Bedrock Knowledge Bases - Verify RAG Security",
                description=f"Found {self.inventory.bedrock_knowledge_bases} knowledge bases. RAG architectures can expose sensitive data through retrieval. Verify data sources don't contain unmasked PII or confidential information.",
                severity=FindingSeverity.MEDIUM,
                lens_type="generative_ai",
                waf_pillar="Security",
                service="Bedrock",
                affected_resources=[f"{self.inventory.bedrock_knowledge_bases} knowledge bases"],
                recommendation="Audit knowledge base data sources for sensitive information",
                remediation_steps=[
                    "Review S3 bucket contents for PII/confidential data",
                    "Implement data masking before ingestion",
                    "Configure IAM roles with least privilege",
                    "Enable encryption for data sources",
                    "Set up access logging for audit trail"
                ],
                aws_solution="Amazon Macie for PII detection + S3 encryption",
                estimated_effort="1-2 days",
                ai_dimensions=[ResponsibleAIDimension.PRIVACY_SECURITY]
            ))
        
        # Custom models without evaluation
        if self.inventory.bedrock_custom_models > 0:
            self.findings.append(AIMLFinding(
                id="AIML-BR-003",
                title="Custom Bedrock Models - Verify Evaluation Framework",
                description=f"Found {self.inventory.bedrock_custom_models} custom/fine-tuned models. Custom models require systematic evaluation for quality, safety, and bias before production deployment.",
                severity=FindingSeverity.MEDIUM,
                lens_type="generative_ai",
                waf_pillar="Reliability",
                service="Bedrock",
                recommendation="Implement model evaluation framework for custom models",
                remediation_steps=[
                    "Define evaluation metrics (BLEU, ROUGE, custom metrics)",
                    "Create benchmark dataset for testing",
                    "Test for harmful outputs and edge cases",
                    "Conduct red-teaming exercises",
                    "Document evaluation results and approval"
                ],
                aws_solution="Amazon Bedrock Model Evaluation",
                estimated_effort="1 week",
                ai_dimensions=[ResponsibleAIDimension.VERACITY_ROBUSTNESS, ResponsibleAIDimension.SAFETY]
            ))
        
        # No provisioned throughput (cost/latency)
        if self.inventory.bedrock_agents > 0 and self.inventory.bedrock_provisioned_throughput == 0:
            self.findings.append(AIMLFinding(
                id="AIML-BR-004",
                title="Bedrock Using On-Demand Throughput Only",
                description="No provisioned throughput configured. Production GenAI workloads may benefit from provisioned capacity for consistent latency and cost optimization.",
                severity=FindingSeverity.LOW,
                lens_type="generative_ai",
                waf_pillar="Performance Efficiency",
                service="Bedrock",
                recommendation="Evaluate provisioned throughput for production workloads",
                remediation_steps=[
                    "Analyze current token usage patterns",
                    "Calculate cost comparison (on-demand vs provisioned)",
                    "Test latency with provisioned throughput",
                    "Consider Reserved Capacity for predictable workloads"
                ],
                aws_solution="Amazon Bedrock Provisioned Throughput",
                estimated_effort="1 day analysis"
            ))
    
    def _generate_responsible_ai_findings(self):
        """Generate Responsible AI findings"""
        
        # Personalization without fairness testing
        if self.inventory.personalize_campaigns > 0:
            self.findings.append(AIMLFinding(
                id="AIML-RAI-001",
                title="Recommendation System Without Fairness Assessment",
                description=f"Found {self.inventory.personalize_campaigns} Personalize campaigns. Recommendation systems can perpetuate bias. Fairness testing across user segments is required for responsible AI.",
                severity=FindingSeverity.HIGH,
                lens_type="responsible_ai",
                waf_pillar="Security",
                service="Personalize",
                affected_resources=[f"{self.inventory.personalize_campaigns} campaigns"],
                recommendation="Implement fairness testing for recommendation outputs",
                remediation_steps=[
                    "Define protected attributes for fairness analysis",
                    "Analyze recommendation distribution across user segments",
                    "Test for demographic parity and equal opportunity",
                    "Document fairness metrics and thresholds",
                    "Implement monitoring for fairness drift"
                ],
                aws_solution="Custom fairness analysis + SageMaker Clarify",
                estimated_effort="2-3 weeks",
                ai_dimensions=[ResponsibleAIDimension.FAIRNESS, ResponsibleAIDimension.TRANSPARENCY]
            ))
        
        # Facial recognition
        if self.inventory.rekognition_projects > 0 or self.inventory.rekognition_collections > 0:
            self.findings.append(AIMLFinding(
                id="AIML-RAI-002",
                title="Facial Analysis Detected - Review Responsible AI Practices",
                description=f"Rekognition projects/collections detected. Facial analysis requires careful responsible AI consideration including consent, bias testing, and appropriate use case validation.",
                severity=FindingSeverity.HIGH,
                lens_type="responsible_ai",
                waf_pillar="Security",
                service="Rekognition",
                recommendation="Ensure facial analysis complies with responsible AI guidelines",
                remediation_steps=[
                    "Document use case justification and appropriateness",
                    "Verify user consent mechanisms are in place",
                    "Test for demographic bias across skin tones/ages",
                    "Implement human review for high-stakes decisions",
                    "Create transparency notices for end users",
                    "Review compliance with regional regulations (GDPR, BIPA)"
                ],
                aws_solution="Amazon Rekognition with appropriate confidence thresholds",
                estimated_effort="2-4 weeks for compliance review",
                ai_dimensions=[
                    ResponsibleAIDimension.FAIRNESS,
                    ResponsibleAIDimension.TRANSPARENCY,
                    ResponsibleAIDimension.PRIVACY_SECURITY,
                    ResponsibleAIDimension.GOVERNANCE
                ]
            ))
        
        # Fraud detection
        if self.inventory.frauddetector_detectors > 0:
            self.findings.append(AIMLFinding(
                id="AIML-RAI-003",
                title="Fraud Detection ML - Verify Explainability",
                description=f"Found {self.inventory.frauddetector_detectors} fraud detectors. Fraud detection decisions may affect customer access to services. Explainability and appeal mechanisms are required.",
                severity=FindingSeverity.MEDIUM,
                lens_type="responsible_ai",
                waf_pillar="Operational Excellence",
                service="Fraud Detector",
                recommendation="Implement explainability and human review for fraud decisions",
                remediation_steps=[
                    "Enable explanation outputs in Fraud Detector",
                    "Create human review queue for borderline cases",
                    "Document appeal process for false positives",
                    "Monitor false positive rates by customer segment",
                    "Implement feedback loop for model improvement"
                ],
                aws_solution="Amazon Fraud Detector with rule insights",
                estimated_effort="1-2 weeks",
                ai_dimensions=[ResponsibleAIDimension.EXPLAINABILITY, ResponsibleAIDimension.TRANSPARENCY]
            ))
    
    def _generate_mlops_findings(self):
        """Generate MLOps-related findings"""
        
        # No model versioning indicators
        if self.inventory.sagemaker_models > 5:
            self.findings.append(AIMLFinding(
                id="AIML-MLOPS-001",
                title="Multiple Models Without Registry",
                description=f"Found {self.inventory.sagemaker_models} models. Use SageMaker Model Registry for versioning, approval workflows, and lineage tracking.",
                severity=FindingSeverity.MEDIUM,
                lens_type="machine_learning",
                waf_pillar="Operational Excellence",
                service="SageMaker",
                recommendation="Implement SageMaker Model Registry for model governance",
                remediation_steps=[
                    "Create Model Package Groups for each use case",
                    "Register models with metadata and metrics",
                    "Implement approval workflow before production",
                    "Track model lineage and data dependencies",
                    "Set up model approval notifications"
                ],
                aws_solution="Amazon SageMaker Model Registry",
                estimated_effort="1 week"
            ))


# ============================================================================
# CLAUDE AI RECOMMENDATIONS ENGINE
# ============================================================================

class AILensRecommender:
    """Use Claude AI for intelligent, contextual recommendations"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception:
                pass
    
    def generate_recommendations(
        self, 
        inventory: AIMLInventory, 
        findings: List[AIMLFinding],
        assessment_responses: Dict = None
    ) -> Dict:
        """Generate AI-powered recommendations"""
        
        if not self.client:
            return self._get_fallback_recommendations(inventory, findings)
        
        context = self._prepare_context(inventory, findings, assessment_responses)
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": f"""You are an AWS Well-Architected Framework expert specializing in AI/ML workloads.
Analyze this AI/ML infrastructure assessment and provide actionable recommendations.

## Assessment Context
{json.dumps(context, indent=2, default=str)}

## Your Task
Provide comprehensive, prioritized recommendations. Be specific about AWS services and configurations.

Respond in JSON format:
{{
    "executive_summary": "2-3 paragraph analysis of AI/ML posture",
    
    "maturity_assessment": {{
        "ml_ops_maturity": "Ad-hoc/Managed/Automated/Optimized",
        "genai_readiness": "Exploring/Piloting/Scaling/Optimizing",
        "responsible_ai_maturity": "Basic/Developing/Advanced/Leading"
    }},
    
    "critical_actions": [
        {{
            "priority": 1,
            "title": "Action title",
            "description": "Detailed description",
            "lens": "ML/GenAI/RAI",
            "waf_pillar": "Security/Reliability/etc",
            "aws_services": ["Service 1", "Service 2"],
            "effort": "Hours/Days/Weeks",
            "impact": "Description of impact",
            "steps": ["Step 1", "Step 2"]
        }}
    ],
    
    "quick_wins": [
        {{
            "title": "Quick win",
            "description": "What to do",
            "time": "< X hours/days",
            "impact": "Impact description"
        }}
    ],
    
    "responsible_ai_assessment": {{
        "overall_score": "X/100",
        "dimensions": {{
            "fairness": {{"score": X, "issues": ["Issue 1"]}},
            "explainability": {{"score": X, "issues": []}},
            "privacy_security": {{"score": X, "issues": []}},
            "safety": {{"score": X, "issues": []}},
            "controllability": {{"score": X, "issues": []}},
            "veracity_robustness": {{"score": X, "issues": []}},
            "governance": {{"score": X, "issues": []}},
            "transparency": {{"score": X, "issues": []}}
        }}
    }},
    
    "implementation_roadmap": {{
        "week_1": ["Actions"],
        "week_2_4": ["Actions"],
        "month_2_3": ["Actions"],
        "ongoing": ["Actions"]
    }},
    
    "cost_optimization": [
        {{
            "opportunity": "Description",
            "estimated_savings": "$X/month",
            "implementation": "How to implement"
        }}
    ]
}}

Be specific and actionable. Reference actual AWS services and best practices.
Respond ONLY with valid JSON."""
                }]
            )
            
            # Parse response
            text = response.content[0].text
            start = text.find('{')
            end = text.rfind('}') + 1
            
            if start != -1 and end > start:
                result = json.loads(text[start:end])
                result['ai_powered'] = True
                result['generated_at'] = datetime.now().isoformat()
                return result
            
        except Exception as e:
            pass
        
        return self._get_fallback_recommendations(inventory, findings)
    
    def _prepare_context(self, inventory: AIMLInventory, findings: List[AIMLFinding], responses: Dict = None) -> Dict:
        """Prepare context for AI analysis"""
        return {
            'inventory': inventory.to_dict(),
            'findings_summary': {
                'total': len(findings),
                'by_severity': {
                    'CRITICAL': len([f for f in findings if f.severity == FindingSeverity.CRITICAL]),
                    'HIGH': len([f for f in findings if f.severity == FindingSeverity.HIGH]),
                    'MEDIUM': len([f for f in findings if f.severity == FindingSeverity.MEDIUM]),
                    'LOW': len([f for f in findings if f.severity == FindingSeverity.LOW])
                },
                'by_lens': {
                    'machine_learning': len([f for f in findings if f.lens_type == 'machine_learning']),
                    'generative_ai': len([f for f in findings if f.lens_type == 'generative_ai']),
                    'responsible_ai': len([f for f in findings if f.lens_type == 'responsible_ai'])
                },
                'top_findings': [f.to_dict() for f in findings[:10]]
            },
            'assessment_responses': responses or {}
        }
    
    def _get_fallback_recommendations(self, inventory: AIMLInventory, findings: List[AIMLFinding]) -> Dict:
        """Generate fallback recommendations when AI is not available"""
        
        critical_count = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
        high_count = len([f for f in findings if f.severity == FindingSeverity.HIGH])
        
        return {
            'ai_powered': False,
            'generated_at': datetime.now().isoformat(),
            'executive_summary': f"""
Based on the automated scan, your AWS account has {len(inventory.detected_services)} AI/ML services deployed.
The assessment identified {len(findings)} findings, including {critical_count} critical and {high_count} high severity issues.

Key areas requiring attention:
- {'Bedrock agents need guardrails configuration' if inventory.bedrock_agents > 0 and inventory.bedrock_guardrails == 0 else 'GenAI security is configured'}
- {'SageMaker endpoints need Model Monitor' if inventory.sagemaker_endpoints > inventory.sagemaker_monitoring_schedules else 'ML monitoring is in place'}
- {'Responsible AI assessment needed for Personalize/Rekognition' if inventory.has_responsible_ai_concerns else 'No high-risk AI services detected'}
            """.strip(),
            'critical_actions': [f.to_dict() for f in findings if f.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]],
            'quick_wins': [
                {
                    'title': 'Enable Bedrock Guardrails',
                    'description': 'Configure content filtering for all agents',
                    'time': '< 4 hours',
                    'impact': 'Prevents harmful content generation'
                } if inventory.bedrock_agents > 0 and inventory.bedrock_guardrails == 0 else None,
                {
                    'title': 'Enable SageMaker Model Monitor',
                    'description': 'Configure drift detection for endpoints',
                    'time': '< 1 day per endpoint',
                    'impact': 'Detect model degradation automatically'
                } if inventory.sagemaker_endpoints > 0 else None
            ]
        }


# ============================================================================
# ENHANCED AI LENS UI MODULE
# ============================================================================

class EnhancedAILensModule:
    """Enhanced AI Lens Module with auto-detection and intelligent recommendations"""
    
    def __init__(self):
        self.detector = None
        self.inventory = None
        self.findings = []
        self.recommendations = None
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state"""
        if 'ai_lens_inventory' not in st.session_state:
            st.session_state.ai_lens_inventory = None
        if 'ai_lens_findings' not in st.session_state:
            st.session_state.ai_lens_findings = []
        if 'ai_lens_recommendations' not in st.session_state:
            st.session_state.ai_lens_recommendations = None
        if 'ai_lens_scan_complete' not in st.session_state:
            st.session_state.ai_lens_scan_complete = False
    
    def render(self):
        """Render the enhanced AI Lens module"""
        st.markdown("## 🧠 Enhanced AI Lens Assessment")
        st.markdown("*Intelligent AI/ML workload assessment with auto-detection and Claude AI recommendations*")
        
        # Mode selection
        col1, col2 = st.columns([2, 1])
        with col1:
            mode = st.radio(
                "Assessment Mode",
                ["🔍 Auto-Detect (Scan AWS)", "📋 Demo Mode"],
                horizontal=True,
                key="ai_lens_mode"
            )
        
        with col2:
            if st.button("🔄 Reset Assessment", key="reset_ai_lens"):
                st.session_state.ai_lens_inventory = None
                st.session_state.ai_lens_findings = []
                st.session_state.ai_lens_recommendations = None
                st.session_state.ai_lens_scan_complete = False
                st.rerun()
        
        st.divider()
        
        # Main tabs
        tabs = st.tabs([
            "🔍 Discovery & Scan",
            "📊 AI/ML Inventory",
            "⚠️ Findings",
            "🤖 AI Recommendations",
            "📋 Assessment Questions",
            "📥 Export"
        ])
        
        with tabs[0]:
            self._render_discovery_tab(mode)
        
        with tabs[1]:
            self._render_inventory_tab()
        
        with tabs[2]:
            self._render_findings_tab()
        
        with tabs[3]:
            self._render_recommendations_tab()
        
        with tabs[4]:
            self._render_questions_tab()
        
        with tabs[5]:
            self._render_export_tab()
    
    def _render_discovery_tab(self, mode: str):
        """Render the discovery and scan tab"""
        st.markdown("### 🔍 AI/ML Service Discovery")
        
        if "Demo" in mode:
            st.info("📋 **Demo Mode**: Using simulated AI/ML inventory for demonstration")
            
            if st.button("🚀 Run Demo Scan", type="primary", key="run_demo_scan"):
                with st.spinner("Simulating AI/ML service scan..."):
                    import time
                    time.sleep(1)
                    
                    # Get demo inventory
                    detector = AIMLAutoDetector()
                    st.session_state.ai_lens_inventory = detector._get_demo_inventory()
                    
                    # Generate findings
                    generator = AIMLFindingsGenerator(st.session_state.ai_lens_inventory)
                    st.session_state.ai_lens_findings = generator.generate_all()
                    
                    st.session_state.ai_lens_scan_complete = True
                    st.success(f"✅ Demo scan complete! Found {len(st.session_state.ai_lens_inventory.detected_services)} AI/ML services")
                    st.rerun()
        else:
            st.info("🔍 **Live Mode**: Connect to AWS to scan for AI/ML services")
            
            # AWS credentials input
            with st.expander("🔐 AWS Credentials", expanded=not st.session_state.ai_lens_scan_complete):
                cred_method = st.radio(
                    "Authentication Method",
                    ["Environment Variables / IAM Role", "Manual Credentials"],
                    key="ai_lens_cred_method"
                )
                
                if cred_method == "Manual Credentials":
                    col1, col2 = st.columns(2)
                    with col1:
                        access_key = st.text_input("AWS Access Key ID", type="password", key="ai_lens_access_key")
                    with col2:
                        secret_key = st.text_input("AWS Secret Access Key", type="password", key="ai_lens_secret_key")
                    
                    session_token = st.text_input("Session Token (optional)", type="password", key="ai_lens_session_token")
                
                regions = st.multiselect(
                    "Regions to Scan",
                    ['us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1', 'ap-northeast-1', 'ap-southeast-1'],
                    default=['us-east-1', 'us-west-2'],
                    key="ai_lens_regions"
                )
                
                if st.button("🚀 Start AI/ML Scan", type="primary", key="start_ai_scan"):
                    if not BOTO3_AVAILABLE:
                        st.error("boto3 not available. Using demo mode.")
                        return
                    
                    try:
                        # Create session
                        if cred_method == "Manual Credentials" and access_key and secret_key:
                            session = boto3.Session(
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key,
                                aws_session_token=session_token if session_token else None
                            )
                        else:
                            session = boto3.Session()
                        
                        # Run scan
                        with st.spinner("Scanning AI/ML services across regions..."):
                            detector = AIMLAutoDetector(session)
                            st.session_state.ai_lens_inventory = detector.scan_all(regions)
                            
                            # Generate findings
                            generator = AIMLFindingsGenerator(st.session_state.ai_lens_inventory)
                            st.session_state.ai_lens_findings = generator.generate_all()
                            
                            st.session_state.ai_lens_scan_complete = True
                        
                        st.success(f"✅ Scan complete! Found {len(st.session_state.ai_lens_inventory.detected_services)} AI/ML services")
                        st.rerun()
                        
                    except NoCredentialsError:
                        st.error("❌ No AWS credentials found. Please provide credentials or configure IAM role.")
                    except Exception as e:
                        st.error(f"❌ Scan failed: {str(e)}")
        
        # Show scan status
        if st.session_state.ai_lens_scan_complete and st.session_state.ai_lens_inventory:
            inv = st.session_state.ai_lens_inventory
            
            st.markdown("### 📊 Scan Results Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Services Detected", len(inv.detected_services))
            with col2:
                st.metric("Findings", len(st.session_state.ai_lens_findings))
            with col3:
                critical = len([f for f in st.session_state.ai_lens_findings if f.severity == FindingSeverity.CRITICAL])
                st.metric("Critical Issues", critical, delta=None if critical == 0 else f"-{critical}", delta_color="inverse")
            with col4:
                st.metric("Scan Time", inv.scan_timestamp[:19] if inv.scan_timestamp else "N/A")
            
            # Quick status badges
            st.markdown("#### Service Categories")
            col1, col2, col3 = st.columns(3)
            with col1:
                if inv.has_ml_workloads:
                    st.success("✅ ML Workloads Detected")
                else:
                    st.info("ℹ️ No ML Workloads")
            with col2:
                if inv.has_genai_workloads:
                    st.success("✅ GenAI Workloads Detected")
                else:
                    st.info("ℹ️ No GenAI Workloads")
            with col3:
                if inv.has_responsible_ai_concerns:
                    st.warning("⚠️ RAI Review Needed")
                else:
                    st.success("✅ Low RAI Risk")
    
    def _render_inventory_tab(self):
        """Render AI/ML inventory dashboard"""
        st.markdown("### 📊 AI/ML Service Inventory")
        
        if not st.session_state.ai_lens_inventory:
            st.info("👆 Run a scan first to see your AI/ML inventory")
            return
        
        inv = st.session_state.ai_lens_inventory
        
        # SageMaker section
        with st.expander("🧪 Amazon SageMaker (ML Platform)", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Notebook Instances", inv.sagemaker_notebooks)
                st.metric("Models", inv.sagemaker_models)
            with col2:
                st.metric("Endpoints", inv.sagemaker_endpoints)
                st.metric("Pipelines", inv.sagemaker_pipelines)
            with col3:
                st.metric("Feature Groups", inv.sagemaker_feature_groups)
                st.metric("Monitoring Schedules", inv.sagemaker_monitoring_schedules)
            
            # Health indicator
            if inv.sagemaker_endpoints > 0:
                monitored_pct = (inv.sagemaker_monitoring_schedules / inv.sagemaker_endpoints) * 100
                if monitored_pct >= 80:
                    st.success(f"✅ {monitored_pct:.0f}% endpoints monitored")
                elif monitored_pct >= 50:
                    st.warning(f"⚠️ {monitored_pct:.0f}% endpoints monitored")
                else:
                    st.error(f"❌ Only {monitored_pct:.0f}% endpoints monitored")
        
        # Bedrock section
        with st.expander("✨ Amazon Bedrock (Generative AI)", expanded=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Foundation Models", inv.bedrock_models_enabled)
                st.metric("Custom Models", inv.bedrock_custom_models)
            with col2:
                st.metric("Agents", inv.bedrock_agents)
                st.metric("Knowledge Bases", inv.bedrock_knowledge_bases)
            with col3:
                st.metric("Guardrails", inv.bedrock_guardrails)
                st.metric("Provisioned Throughput", inv.bedrock_provisioned_throughput)
            
            # Security indicator
            if inv.bedrock_agents > 0:
                if inv.bedrock_guardrails > 0:
                    st.success("✅ Guardrails configured")
                else:
                    st.error("❌ CRITICAL: No guardrails for agents!")
        
        # AI Services section
        with st.expander("🔧 AWS AI Services", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Rekognition Projects", inv.rekognition_projects)
                st.metric("Comprehend Endpoints", inv.comprehend_endpoints)
            with col2:
                st.metric("Lex Bots", inv.lex_bots)
                st.metric("Kendra Indexes", inv.kendra_indexes)
            with col3:
                st.metric("Personalize Campaigns", inv.personalize_campaigns)
                st.metric("Forecast Predictors", inv.forecast_predictors)
            with col4:
                st.metric("Fraud Detector", inv.frauddetector_detectors)
        
        # Detected services list
        st.markdown("#### Detected Services")
        if inv.detected_services:
            st.write(", ".join([f"**{s}**" for s in inv.detected_services]))
        else:
            st.info("No AI/ML services detected")
    
    def _render_findings_tab(self):
        """Render findings tab"""
        st.markdown("### ⚠️ AI/ML Assessment Findings")
        
        if not st.session_state.ai_lens_findings:
            st.info("👆 Run a scan first to generate findings")
            return
        
        findings = st.session_state.ai_lens_findings
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            critical = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
            st.metric("Critical", critical, delta=None if critical == 0 else "Needs attention", delta_color="inverse")
        with col2:
            high = len([f for f in findings if f.severity == FindingSeverity.HIGH])
            st.metric("High", high)
        with col3:
            medium = len([f for f in findings if f.severity == FindingSeverity.MEDIUM])
            st.metric("Medium", medium)
        with col4:
            low = len([f for f in findings if f.severity == FindingSeverity.LOW])
            st.metric("Low", low)
        
        st.divider()
        
        # Filter
        severity_filter = st.multiselect(
            "Filter by Severity",
            ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
            default=["CRITICAL", "HIGH", "MEDIUM"],
            key="findings_severity_filter"
        )
        
        lens_filter = st.multiselect(
            "Filter by Lens",
            ["machine_learning", "generative_ai", "responsible_ai"],
            default=["machine_learning", "generative_ai", "responsible_ai"],
            key="findings_lens_filter"
        )
        
        # Display findings
        filtered = [f for f in findings 
                   if f.severity.value in severity_filter 
                   and f.lens_type in lens_filter]
        
        for finding in filtered:
            severity_colors = {
                FindingSeverity.CRITICAL: "🔴",
                FindingSeverity.HIGH: "🟠",
                FindingSeverity.MEDIUM: "🟡",
                FindingSeverity.LOW: "🟢"
            }
            
            with st.expander(f"{severity_colors.get(finding.severity, '⚪')} {finding.title}", expanded=finding.severity == FindingSeverity.CRITICAL):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Severity:** {finding.severity.value}")
                with col2:
                    st.markdown(f"**Lens:** {finding.lens_type.replace('_', ' ').title()}")
                with col3:
                    st.markdown(f"**WAF Pillar:** {finding.waf_pillar}")
                
                st.markdown(f"**Description:** {finding.description}")
                
                if finding.affected_resources:
                    st.markdown(f"**Affected Resources:** {', '.join(finding.affected_resources)}")
                
                st.markdown(f"**Recommendation:** {finding.recommendation}")
                
                if finding.remediation_steps:
                    st.markdown("**Remediation Steps:**")
                    for i, step in enumerate(finding.remediation_steps, 1):
                        st.markdown(f"{i}. {step}")
                
                if finding.aws_solution:
                    st.markdown(f"**AWS Solution:** {finding.aws_solution}")
                
                if finding.estimated_effort:
                    st.markdown(f"**Estimated Effort:** {finding.estimated_effort}")
                
                if finding.ai_dimensions:
                    st.markdown(f"**Responsible AI Dimensions:** {', '.join([d.value for d in finding.ai_dimensions])}")
    
    def _render_recommendations_tab(self):
        """Render AI recommendations tab"""
        st.markdown("### 🤖 Claude AI Recommendations")
        
        if not st.session_state.ai_lens_inventory:
            st.info("👆 Run a scan first to get AI recommendations")
            return
        
        # Check for API key
        api_key = os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("anthropic_api_key")
        
        if not api_key:
            with st.expander("🔑 Configure Claude API Key", expanded=True):
                st.markdown("""
                To get AI-powered recommendations, enter your Anthropic API key.
                This enables Claude to analyze your AI/ML infrastructure and provide contextual recommendations.
                """)
                api_key_input = st.text_input("Anthropic API Key", type="password", key="ai_lens_api_key_input")
                if api_key_input:
                    st.session_state.anthropic_api_key = api_key_input
                    api_key = api_key_input
        
        if st.button("🚀 Generate AI Recommendations", type="primary", key="generate_ai_recommendations"):
            with st.spinner("Claude is analyzing your AI/ML infrastructure..."):
                recommender = AILensRecommender(api_key)
                st.session_state.ai_lens_recommendations = recommender.generate_recommendations(
                    st.session_state.ai_lens_inventory,
                    st.session_state.ai_lens_findings
                )
            st.rerun()
        
        # Display recommendations
        if st.session_state.ai_lens_recommendations:
            recs = st.session_state.ai_lens_recommendations
            
            # AI-powered badge
            if recs.get('ai_powered'):
                st.success("✨ AI-Powered Analysis by Claude")
            else:
                st.info("📋 Rule-Based Recommendations (Add API key for AI-powered analysis)")
            
            # Executive Summary
            if recs.get('executive_summary'):
                st.markdown("#### 📋 Executive Summary")
                st.markdown(recs['executive_summary'])
            
            # Maturity Assessment
            if recs.get('maturity_assessment'):
                st.markdown("#### 📊 Maturity Assessment")
                ma = recs['maturity_assessment']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("MLOps Maturity", ma.get('ml_ops_maturity', 'N/A'))
                with col2:
                    st.metric("GenAI Readiness", ma.get('genai_readiness', 'N/A'))
                with col3:
                    st.metric("RAI Maturity", ma.get('responsible_ai_maturity', 'N/A'))
            
            # Critical Actions
            if recs.get('critical_actions'):
                st.markdown("#### 🚨 Critical Actions")
                for action in recs['critical_actions'][:5]:
                    if isinstance(action, dict):
                        with st.expander(f"**{action.get('title', 'Action')}**"):
                            st.markdown(action.get('description', ''))
                            if action.get('aws_services'):
                                st.markdown(f"**AWS Services:** {', '.join(action['aws_services'])}")
                            if action.get('effort'):
                                st.markdown(f"**Effort:** {action['effort']}")
            
            # Quick Wins
            if recs.get('quick_wins'):
                st.markdown("#### ⚡ Quick Wins")
                for win in recs['quick_wins']:
                    if win:
                        st.markdown(f"- **{win.get('title', '')}**: {win.get('description', '')} ({win.get('time', '')})")
            
            # Responsible AI Assessment
            if recs.get('responsible_ai_assessment'):
                st.markdown("#### ⚖️ Responsible AI Assessment")
                rai = recs['responsible_ai_assessment']
                st.metric("Overall RAI Score", rai.get('overall_score', 'N/A'))
                
                if rai.get('dimensions'):
                    cols = st.columns(4)
                    for i, (dim, data) in enumerate(rai['dimensions'].items()):
                        with cols[i % 4]:
                            if isinstance(data, dict):
                                st.metric(dim.replace('_', ' ').title(), f"{data.get('score', 'N/A')}/100")
            
            # Implementation Roadmap
            if recs.get('implementation_roadmap'):
                st.markdown("#### 🗺️ Implementation Roadmap")
                roadmap = recs['implementation_roadmap']
                for phase, actions in roadmap.items():
                    if actions:
                        st.markdown(f"**{phase.replace('_', ' ').title()}**")
                        for action in actions:
                            st.markdown(f"- {action}")
    
    def _render_questions_tab(self):
        """Render conditional questions tab"""
        st.markdown("### 📋 Assessment Questions")
        st.info("Questions are filtered based on detected services. Only relevant questions are shown.")
        
        if not st.session_state.ai_lens_inventory:
            st.warning("👆 Run a scan first to see relevant questions")
            return
        
        inv = st.session_state.ai_lens_inventory
        
        # Determine which question sets to show
        if inv.has_ml_workloads:
            with st.expander("🧪 Machine Learning Lens Questions", expanded=True):
                self._render_ml_questions()
        
        if inv.has_genai_workloads:
            with st.expander("✨ Generative AI Lens Questions", expanded=True):
                self._render_genai_questions()
        
        if inv.has_responsible_ai_concerns:
            with st.expander("⚖️ Responsible AI Lens Questions", expanded=True):
                self._render_rai_questions()
    
    def _render_ml_questions(self):
        """Render ML-specific questions"""
        questions = [
            {
                "id": "ML-DATA-01",
                "title": "How do you manage and version training data?",
                "pillar": "Operational Excellence",
                "options": ["Data versioning with S3 versioning/DVC", "Manual tracking", "No versioning"]
            },
            {
                "id": "ML-TRAIN-01", 
                "title": "How do you track ML experiments?",
                "pillar": "Operational Excellence",
                "options": ["SageMaker Experiments/MLflow", "Manual notebooks", "No tracking"]
            },
            {
                "id": "ML-DEPLOY-01",
                "title": "How do you deploy models to production?",
                "pillar": "Reliability",
                "options": ["CI/CD with SageMaker Pipelines", "Manual deployment", "No formal process"]
            },
            {
                "id": "ML-MONITOR-01",
                "title": "How do you monitor model performance in production?",
                "pillar": "Operational Excellence",
                "options": ["SageMaker Model Monitor", "Custom metrics only", "No monitoring"]
            },
            {
                "id": "ML-SEC-01",
                "title": "How do you secure ML notebooks and endpoints?",
                "pillar": "Security",
                "options": ["VPC + encryption + IAM", "Basic IAM only", "Default settings"]
            }
        ]
        
        for q in questions:
            st.markdown(f"**{q['id']}**: {q['title']}")
            st.radio(
                f"({q['pillar']})",
                q['options'],
                key=f"q_{q['id']}",
                horizontal=True
            )
            st.divider()
    
    def _render_genai_questions(self):
        """Render GenAI-specific questions"""
        questions = [
            {
                "id": "GENAI-SEC-01",
                "title": "How do you protect against prompt injection attacks?",
                "pillar": "Security",
                "options": ["Bedrock Guardrails + input validation", "Basic input filtering", "No protection"]
            },
            {
                "id": "GENAI-RAG-01",
                "title": "How do you secure RAG data sources?",
                "pillar": "Security",
                "options": ["Encrypted + IAM + PII detection", "Basic encryption", "No special handling"]
            },
            {
                "id": "GENAI-COST-01",
                "title": "How do you optimize GenAI costs?",
                "pillar": "Cost Optimization",
                "options": ["Caching + right-sized models + monitoring", "Basic monitoring", "No optimization"]
            },
            {
                "id": "GENAI-PERF-01",
                "title": "How do you handle GenAI latency requirements?",
                "pillar": "Performance Efficiency",
                "options": ["Provisioned throughput + caching", "On-demand only", "No consideration"]
            },
            {
                "id": "GENAI-EVAL-01",
                "title": "How do you evaluate model outputs?",
                "pillar": "Reliability",
                "options": ["Systematic evaluation framework", "Manual review", "No evaluation"]
            }
        ]
        
        for q in questions:
            st.markdown(f"**{q['id']}**: {q['title']}")
            st.radio(
                f"({q['pillar']})",
                q['options'],
                key=f"q_{q['id']}",
                horizontal=True
            )
            st.divider()
    
    def _render_rai_questions(self):
        """Render Responsible AI questions"""
        questions = [
            {
                "id": "RAI-FAIR-01",
                "title": "How do you test for bias in AI outputs?",
                "pillar": "Fairness",
                "options": ["Systematic bias testing across demographics", "Ad-hoc testing", "No testing"]
            },
            {
                "id": "RAI-EXPLAIN-01",
                "title": "How do you provide explanations for AI decisions?",
                "pillar": "Explainability",
                "options": ["SHAP/LIME + user-facing explanations", "Technical logs only", "No explainability"]
            },
            {
                "id": "RAI-PRIVACY-01",
                "title": "How do you protect user privacy in AI systems?",
                "pillar": "Privacy",
                "options": ["PII detection + anonymization + consent", "Basic data protection", "No special handling"]
            },
            {
                "id": "RAI-HUMAN-01",
                "title": "Do you have human oversight for high-stakes AI decisions?",
                "pillar": "Controllability",
                "options": ["Mandatory human review + appeal process", "Optional review", "No oversight"]
            },
            {
                "id": "RAI-AUDIT-01",
                "title": "How do you maintain audit trails for AI systems?",
                "pillar": "Governance",
                "options": ["Comprehensive logging + retention", "Basic logging", "No audit trail"]
            }
        ]
        
        for q in questions:
            st.markdown(f"**{q['id']}**: {q['title']}")
            st.radio(
                f"({q['pillar']})",
                q['options'],
                key=f"q_{q['id']}",
                horizontal=True
            )
            st.divider()
    
    def _render_export_tab(self):
        """Render export options"""
        st.markdown("### 📥 Export Assessment")
        
        if not st.session_state.ai_lens_inventory:
            st.info("👆 Run a scan first to enable exports")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 Export Formats")
            
            # JSON export
            if st.button("📥 Export as JSON", key="export_json"):
                export_data = {
                    'inventory': st.session_state.ai_lens_inventory.to_dict(),
                    'findings': [f.to_dict() for f in st.session_state.ai_lens_findings],
                    'recommendations': st.session_state.ai_lens_recommendations,
                    'exported_at': datetime.now().isoformat()
                }
                st.download_button(
                    "⬇️ Download JSON",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name="ai_lens_assessment.json",
                    mime="application/json",
                    key="download_json"
                )
            
            # CSV findings export
            if st.button("📥 Export Findings CSV", key="export_csv"):
                import io
                csv_data = "ID,Title,Severity,Lens,WAF Pillar,Service,Recommendation\n"
                for f in st.session_state.ai_lens_findings:
                    csv_data += f'"{f.id}","{f.title}","{f.severity.value}","{f.lens_type}","{f.waf_pillar}","{f.service}","{f.recommendation}"\n'
                
                st.download_button(
                    "⬇️ Download CSV",
                    data=csv_data,
                    file_name="ai_lens_findings.csv",
                    mime="text/csv",
                    key="download_csv"
                )
        
        with col2:
            st.markdown("#### 🔧 AWS WA Tool Export")
            st.info("Export as Custom Lens JSON for import into AWS Well-Architected Tool")
            
            if st.button("📥 Generate Custom Lens JSON", key="export_custom_lens"):
                custom_lens = self._generate_custom_lens_json()
                st.download_button(
                    "⬇️ Download Custom Lens",
                    data=json.dumps(custom_lens, indent=2),
                    file_name="ai-ml-custom-lens.json",
                    mime="application/json",
                    key="download_custom_lens"
                )
    
    def _generate_custom_lens_json(self) -> Dict:
        """Generate AWS WA Tool compatible custom lens JSON"""
        return {
            "schemaVersion": "2021-11-01",
            "name": "AI/ML Assessment Lens",
            "description": "Custom lens for AI/ML workload assessment combining ML, GenAI, and Responsible AI best practices",
            "pillars": [
                {
                    "id": "ml_operational_excellence",
                    "name": "ML Operational Excellence",
                    "questions": [
                        {
                            "id": "mlops_experiment_tracking",
                            "title": "How do you track ML experiments and model versions?",
                            "description": "Experiment tracking enables reproducibility and comparison of model iterations",
                            "choices": [
                                {"id": "mlops_exp_1", "title": "We use SageMaker Experiments or MLflow for systematic tracking"},
                                {"id": "mlops_exp_2", "title": "We track experiments in notebooks with manual documentation"},
                                {"id": "mlops_exp_3", "title": "We do not formally track experiments"}
                            ],
                            "riskRules": [
                                {"condition": "mlops_exp_3", "risk": "HIGH_RISK"},
                                {"condition": "mlops_exp_2", "risk": "MEDIUM_RISK"},
                                {"condition": "mlops_exp_1", "risk": "NO_RISK"}
                            ]
                        }
                    ]
                },
                {
                    "id": "genai_security",
                    "name": "Generative AI Security",
                    "questions": [
                        {
                            "id": "genai_guardrails",
                            "title": "How do you protect against prompt injection and harmful outputs?",
                            "description": "GenAI applications require content filtering and input validation",
                            "choices": [
                                {"id": "genai_guard_1", "title": "We use Bedrock Guardrails with comprehensive content filters"},
                                {"id": "genai_guard_2", "title": "We have basic input validation only"},
                                {"id": "genai_guard_3", "title": "We do not have specific protections"}
                            ],
                            "riskRules": [
                                {"condition": "genai_guard_3", "risk": "HIGH_RISK"},
                                {"condition": "genai_guard_2", "risk": "MEDIUM_RISK"},
                                {"condition": "genai_guard_1", "risk": "NO_RISK"}
                            ]
                        }
                    ]
                },
                {
                    "id": "responsible_ai",
                    "name": "Responsible AI",
                    "questions": [
                        {
                            "id": "rai_fairness",
                            "title": "How do you assess and mitigate bias in AI systems?",
                            "description": "AI systems should be tested for fairness across different user groups",
                            "choices": [
                                {"id": "rai_fair_1", "title": "We conduct systematic bias testing with SageMaker Clarify"},
                                {"id": "rai_fair_2", "title": "We perform ad-hoc bias reviews"},
                                {"id": "rai_fair_3", "title": "We do not specifically test for bias"}
                            ],
                            "riskRules": [
                                {"condition": "rai_fair_3", "risk": "HIGH_RISK"},
                                {"condition": "rai_fair_2", "risk": "MEDIUM_RISK"},
                                {"condition": "rai_fair_1", "risk": "NO_RISK"}
                            ]
                        }
                    ]
                }
            ]
        }


# ============================================================================
# ENTRY POINT
# ============================================================================

def render_enhanced_ai_lens():
    """Main entry point for Enhanced AI Lens module"""
    module = EnhancedAILensModule()
    module.render()


# Export for integration
__all__ = [
    'EnhancedAILensModule',
    'AIMLAutoDetector',
    'AIMLFindingsGenerator',
    'AILensRecommender',
    'AIMLInventory',
    'AIMLFinding',
    'render_enhanced_ai_lens'
]
