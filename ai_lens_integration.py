"""
AI Lens Integration Module
Provides tight integration between AI Lens and WAF Scanner

Features:
- Auto-detection of AI/ML services in AWS accounts
- Conditional AI Lens questions based on detected services
- Unified scoring with AI/ML Health indicator
- PDF report integration
- Cross-pillar AI/ML findings mapping
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json

# Import AI Lens module
try:
    from ai_lens_module import (
        AILensModule, AILensType, AILensQuestion,
        get_ml_lens_questions, get_genai_lens_questions, 
        get_responsible_ai_lens_questions
    )
    AI_LENS_AVAILABLE = True
except ImportError:
    AI_LENS_AVAILABLE = False


# ============================================================================
# AI/ML SERVICE DETECTION
# ============================================================================

# Comprehensive list of AWS AI/ML services
AI_ML_SERVICES = {
    # Machine Learning Platform
    'sagemaker': {
        'name': 'Amazon SageMaker',
        'category': 'ml_platform',
        'lens': ['machine_learning'],
        'description': 'ML model training, deployment, and MLOps'
    },
    
    # Generative AI
    'bedrock': {
        'name': 'Amazon Bedrock',
        'category': 'generative_ai',
        'lens': ['generative_ai', 'responsible_ai'],
        'description': 'Foundation models and GenAI applications'
    },
    'bedrock-runtime': {
        'name': 'Amazon Bedrock Runtime',
        'category': 'generative_ai',
        'lens': ['generative_ai'],
        'description': 'Bedrock model inference'
    },
    'bedrock-agent': {
        'name': 'Amazon Bedrock Agents',
        'category': 'generative_ai',
        'lens': ['generative_ai', 'responsible_ai'],
        'description': 'AI agents with tool access'
    },
    
    # AI Services - Vision
    'rekognition': {
        'name': 'Amazon Rekognition',
        'category': 'ai_service',
        'lens': ['machine_learning', 'responsible_ai'],
        'description': 'Image and video analysis'
    },
    'textract': {
        'name': 'Amazon Textract',
        'category': 'ai_service',
        'lens': ['machine_learning'],
        'description': 'Document text extraction'
    },
    
    # AI Services - Language
    'comprehend': {
        'name': 'Amazon Comprehend',
        'category': 'ai_service',
        'lens': ['machine_learning', 'responsible_ai'],
        'description': 'NLP and text analysis'
    },
    'translate': {
        'name': 'Amazon Translate',
        'category': 'ai_service',
        'lens': ['machine_learning'],
        'description': 'Language translation'
    },
    'transcribe': {
        'name': 'Amazon Transcribe',
        'category': 'ai_service',
        'lens': ['machine_learning'],
        'description': 'Speech to text'
    },
    'polly': {
        'name': 'Amazon Polly',
        'category': 'ai_service',
        'lens': ['machine_learning'],
        'description': 'Text to speech'
    },
    'lex': {
        'name': 'Amazon Lex',
        'category': 'ai_service',
        'lens': ['machine_learning', 'generative_ai'],
        'description': 'Conversational AI and chatbots'
    },
    
    # AI Services - Search & Recommendations
    'kendra': {
        'name': 'Amazon Kendra',
        'category': 'ai_service',
        'lens': ['machine_learning', 'generative_ai'],
        'description': 'Intelligent search'
    },
    'personalize': {
        'name': 'Amazon Personalize',
        'category': 'ai_service',
        'lens': ['machine_learning', 'responsible_ai'],
        'description': 'Recommendation engine'
    },
    
    # AI Services - Forecasting & Analytics
    'forecast': {
        'name': 'Amazon Forecast',
        'category': 'ai_service',
        'lens': ['machine_learning'],
        'description': 'Time series forecasting'
    },
    'lookoutmetrics': {
        'name': 'Amazon Lookout for Metrics',
        'category': 'ai_service',
        'lens': ['machine_learning'],
        'description': 'Anomaly detection'
    },
    'frauddetector': {
        'name': 'Amazon Fraud Detector',
        'category': 'ai_service',
        'lens': ['machine_learning', 'responsible_ai'],
        'description': 'Fraud detection ML'
    },
    
    # AI Services - Healthcare
    'comprehendmedical': {
        'name': 'Amazon Comprehend Medical',
        'category': 'ai_service',
        'lens': ['machine_learning', 'responsible_ai'],
        'description': 'Medical NLP'
    },
    'healthlake': {
        'name': 'Amazon HealthLake',
        'category': 'ai_service',
        'lens': ['machine_learning', 'responsible_ai'],
        'description': 'Healthcare data lake'
    },
    
    # AI Infrastructure
    'elastic-inference': {
        'name': 'Amazon Elastic Inference',
        'category': 'ml_infrastructure',
        'lens': ['machine_learning'],
        'description': 'GPU inference acceleration'
    },
    'inferentia': {
        'name': 'AWS Inferentia',
        'category': 'ml_infrastructure',
        'lens': ['machine_learning'],
        'description': 'ML inference chips'
    },
    'trainium': {
        'name': 'AWS Trainium',
        'category': 'ml_infrastructure',
        'lens': ['machine_learning'],
        'description': 'ML training chips'
    },
    
    # Data & Feature Store
    'glue': {
        'name': 'AWS Glue',
        'category': 'data_platform',
        'lens': ['machine_learning'],
        'description': 'ETL and data catalog (ML data pipelines)'
    },
}


@dataclass
class AIMLServiceInventory:
    """Inventory of detected AI/ML services"""
    # ML Platform
    sagemaker_notebooks: int = 0
    sagemaker_endpoints: int = 0
    sagemaker_training_jobs: int = 0
    sagemaker_pipelines: int = 0
    sagemaker_models: int = 0
    sagemaker_feature_groups: int = 0
    
    # Generative AI
    bedrock_models_enabled: int = 0
    bedrock_custom_models: int = 0
    bedrock_agents: int = 0
    bedrock_knowledge_bases: int = 0
    bedrock_guardrails: int = 0
    
    # AI Services
    rekognition_projects: int = 0
    comprehend_endpoints: int = 0
    lex_bots: int = 0
    kendra_indexes: int = 0
    personalize_campaigns: int = 0
    forecast_predictors: int = 0
    transcribe_jobs: int = 0
    textract_jobs: int = 0
    
    # Summary flags
    has_ml_workloads: bool = False
    has_genai_workloads: bool = False
    has_ai_services: bool = False
    
    # Detected services list
    detected_services: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'sagemaker_notebooks': self.sagemaker_notebooks,
            'sagemaker_endpoints': self.sagemaker_endpoints,
            'sagemaker_training_jobs': self.sagemaker_training_jobs,
            'sagemaker_pipelines': self.sagemaker_pipelines,
            'sagemaker_models': self.sagemaker_models,
            'bedrock_models_enabled': self.bedrock_models_enabled,
            'bedrock_custom_models': self.bedrock_custom_models,
            'bedrock_agents': self.bedrock_agents,
            'bedrock_knowledge_bases': self.bedrock_knowledge_bases,
            'bedrock_guardrails': self.bedrock_guardrails,
            'rekognition_projects': self.rekognition_projects,
            'comprehend_endpoints': self.comprehend_endpoints,
            'lex_bots': self.lex_bots,
            'kendra_indexes': self.kendra_indexes,
            'personalize_campaigns': self.personalize_campaigns,
            'has_ml_workloads': self.has_ml_workloads,
            'has_genai_workloads': self.has_genai_workloads,
            'has_ai_services': self.has_ai_services,
            'detected_services': self.detected_services
        }


@dataclass 
class AIMLFinding:
    """AI/ML specific finding"""
    id: str
    title: str
    description: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    lens_type: str  # machine_learning, generative_ai, responsible_ai
    waf_pillar: str  # Maps to WAF pillar
    service: str
    affected_resources: List[str] = field(default_factory=list)
    recommendation: str = ""
    remediation_steps: List[str] = field(default_factory=list)
    ai_dimensions: List[str] = field(default_factory=list)  # For RAI


# ============================================================================
# AI/ML SERVICE SCANNER
# ============================================================================

class AIMLServiceScanner:
    """Scans AWS account for AI/ML services and generates findings"""
    
    def __init__(self, session):
        self.session = session
        self.inventory = AIMLServiceInventory()
        self.findings: List[AIMLFinding] = []
        self.scan_errors = {}
        
    def scan_all(self, regions: List[str] = None) -> Tuple[AIMLServiceInventory, List[AIMLFinding]]:
        """Run complete AI/ML service scan"""
        if regions is None:
            regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        
        # Global services (region-independent)
        self._scan_sagemaker_global()
        self._scan_bedrock_global()
        
        # Regional services
        for region in regions:
            try:
                self._scan_sagemaker_regional(region)
                self._scan_bedrock_regional(region)
                self._scan_ai_services_regional(region)
            except Exception as e:
                self.scan_errors[f"region_{region}"] = str(e)
        
        # Update summary flags
        self._update_summary_flags()
        
        # Generate AI-specific findings
        self._generate_ai_findings()
        
        return self.inventory, self.findings
    
    def _scan_sagemaker_global(self):
        """Scan SageMaker global resources"""
        try:
            sm = self.session.client('sagemaker', region_name='us-east-1')
            
            # List notebooks
            try:
                notebooks = sm.list_notebook_instances()
                self.inventory.sagemaker_notebooks = len(notebooks.get('NotebookInstances', []))
                if self.inventory.sagemaker_notebooks > 0:
                    self.inventory.detected_services.append('sagemaker')
            except:
                pass
            
            # List endpoints
            try:
                endpoints = sm.list_endpoints()
                self.inventory.sagemaker_endpoints = len(endpoints.get('Endpoints', []))
            except:
                pass
            
            # List models
            try:
                models = sm.list_models()
                self.inventory.sagemaker_models = len(models.get('Models', []))
            except:
                pass
            
            # List pipelines
            try:
                pipelines = sm.list_pipelines()
                self.inventory.sagemaker_pipelines = len(pipelines.get('PipelineSummaries', []))
            except:
                pass
            
            # List feature groups
            try:
                fg = sm.list_feature_groups()
                self.inventory.sagemaker_feature_groups = len(fg.get('FeatureGroupSummaries', []))
            except:
                pass
                
        except Exception as e:
            self.scan_errors['sagemaker'] = str(e)
    
    def _scan_sagemaker_regional(self, region: str):
        """Scan SageMaker regional resources"""
        try:
            sm = self.session.client('sagemaker', region_name=region)
            
            # Check for recent training jobs
            try:
                jobs = sm.list_training_jobs(MaxResults=10)
                self.inventory.sagemaker_training_jobs += len(jobs.get('TrainingJobSummaries', []))
            except:
                pass
                
        except Exception as e:
            self.scan_errors[f'sagemaker_{region}'] = str(e)
    
    def _scan_bedrock_global(self):
        """Scan Bedrock global resources"""
        try:
            # Bedrock is available in specific regions
            bedrock = self.session.client('bedrock', region_name='us-east-1')
            
            # List foundation models
            try:
                models = bedrock.list_foundation_models()
                # Check if any models are enabled for the account
                self.inventory.bedrock_models_enabled = len(models.get('modelSummaries', []))
                if self.inventory.bedrock_models_enabled > 0:
                    self.inventory.detected_services.append('bedrock')
            except:
                pass
            
            # List custom models
            try:
                custom = bedrock.list_custom_models()
                self.inventory.bedrock_custom_models = len(custom.get('modelSummaries', []))
            except:
                pass
            
            # List guardrails
            try:
                guardrails = bedrock.list_guardrails()
                self.inventory.bedrock_guardrails = len(guardrails.get('guardrails', []))
            except:
                pass
                
        except Exception as e:
            self.scan_errors['bedrock'] = str(e)
    
    def _scan_bedrock_regional(self, region: str):
        """Scan Bedrock regional resources like agents and knowledge bases"""
        try:
            # Bedrock Agent
            try:
                bedrock_agent = self.session.client('bedrock-agent', region_name=region)
                
                # List agents
                try:
                    agents = bedrock_agent.list_agents()
                    self.inventory.bedrock_agents += len(agents.get('agentSummaries', []))
                except:
                    pass
                
                # List knowledge bases
                try:
                    kbs = bedrock_agent.list_knowledge_bases()
                    self.inventory.bedrock_knowledge_bases += len(kbs.get('knowledgeBaseSummaries', []))
                except:
                    pass
            except:
                pass
                
        except Exception as e:
            self.scan_errors[f'bedrock_{region}'] = str(e)
    
    def _scan_ai_services_regional(self, region: str):
        """Scan other AI services in region"""
        
        # Rekognition
        try:
            rek = self.session.client('rekognition', region_name=region)
            projects = rek.describe_projects()
            self.inventory.rekognition_projects += len(projects.get('ProjectDescriptions', []))
            if self.inventory.rekognition_projects > 0:
                self.inventory.detected_services.append('rekognition')
        except:
            pass
        
        # Comprehend
        try:
            comp = self.session.client('comprehend', region_name=region)
            endpoints = comp.list_endpoints()
            self.inventory.comprehend_endpoints += len(endpoints.get('EndpointPropertiesList', []))
            if self.inventory.comprehend_endpoints > 0:
                self.inventory.detected_services.append('comprehend')
        except:
            pass
        
        # Lex
        try:
            lex = self.session.client('lexv2-models', region_name=region)
            bots = lex.list_bots()
            self.inventory.lex_bots += len(bots.get('botSummaries', []))
            if self.inventory.lex_bots > 0:
                self.inventory.detected_services.append('lex')
        except:
            pass
        
        # Kendra
        try:
            kendra = self.session.client('kendra', region_name=region)
            indexes = kendra.list_indices()
            self.inventory.kendra_indexes += len(indexes.get('IndexConfigurationSummaryItems', []))
            if self.inventory.kendra_indexes > 0:
                self.inventory.detected_services.append('kendra')
        except:
            pass
        
        # Personalize
        try:
            pers = self.session.client('personalize', region_name=region)
            campaigns = pers.list_campaigns()
            self.inventory.personalize_campaigns += len(campaigns.get('campaigns', []))
            if self.inventory.personalize_campaigns > 0:
                self.inventory.detected_services.append('personalize')
        except:
            pass
        
        # Forecast
        try:
            forecast = self.session.client('forecast', region_name=region)
            predictors = forecast.list_predictors()
            self.inventory.forecast_predictors += len(predictors.get('Predictors', []))
            if self.inventory.forecast_predictors > 0:
                self.inventory.detected_services.append('forecast')
        except:
            pass
    
    def _update_summary_flags(self):
        """Update summary flags based on detected services"""
        # ML workloads
        if (self.inventory.sagemaker_notebooks > 0 or 
            self.inventory.sagemaker_endpoints > 0 or
            self.inventory.sagemaker_models > 0 or
            self.inventory.forecast_predictors > 0 or
            self.inventory.personalize_campaigns > 0):
            self.inventory.has_ml_workloads = True
        
        # GenAI workloads
        if (self.inventory.bedrock_models_enabled > 0 or
            self.inventory.bedrock_agents > 0 or
            self.inventory.bedrock_knowledge_bases > 0):
            self.inventory.has_genai_workloads = True
        
        # AI Services
        if (self.inventory.rekognition_projects > 0 or
            self.inventory.comprehend_endpoints > 0 or
            self.inventory.lex_bots > 0 or
            self.inventory.kendra_indexes > 0):
            self.inventory.has_ai_services = True
        
        # Deduplicate detected services
        self.inventory.detected_services = list(set(self.inventory.detected_services))
    
    def _generate_ai_findings(self):
        """Generate AI-specific findings based on detected resources"""
        
        # SageMaker findings
        if self.inventory.sagemaker_endpoints > 0:
            # Check for endpoint monitoring
            self.findings.append(AIMLFinding(
                id="AIML-001",
                title="SageMaker Endpoints Detected - Verify Model Monitoring",
                description=f"Found {self.inventory.sagemaker_endpoints} SageMaker endpoints. Ensure Model Monitor is configured for data drift and quality monitoring.",
                severity="MEDIUM",
                lens_type="machine_learning",
                waf_pillar="Operational Excellence",
                service="SageMaker",
                affected_resources=[f"{self.inventory.sagemaker_endpoints} endpoints"],
                recommendation="Enable SageMaker Model Monitor for all production endpoints",
                remediation_steps=[
                    "Navigate to SageMaker console",
                    "Select each endpoint",
                    "Configure Model Monitor with data quality and model quality monitoring",
                    "Set up CloudWatch alerts for drift detection"
                ]
            ))
        
        if self.inventory.sagemaker_notebooks > 0:
            self.findings.append(AIMLFinding(
                id="AIML-002",
                title="SageMaker Notebooks Detected - Verify Security Configuration",
                description=f"Found {self.inventory.sagemaker_notebooks} SageMaker notebook instances. Ensure they are in VPC with no direct internet access.",
                severity="MEDIUM",
                lens_type="machine_learning",
                waf_pillar="Security",
                service="SageMaker",
                affected_resources=[f"{self.inventory.sagemaker_notebooks} notebooks"],
                recommendation="Configure notebooks in VPC with private subnets",
                remediation_steps=[
                    "Review notebook instance network configurations",
                    "Migrate to VPC-only mode if using direct internet access",
                    "Enable encryption for notebook storage"
                ]
            ))
        
        # Bedrock findings
        if self.inventory.bedrock_agents > 0:
            if self.inventory.bedrock_guardrails == 0:
                self.findings.append(AIMLFinding(
                    id="AIML-003",
                    title="Bedrock Agents Without Guardrails",
                    description=f"Found {self.inventory.bedrock_agents} Bedrock agents but no guardrails configured. Agents with tool access need content filtering.",
                    severity="HIGH",
                    lens_type="generative_ai",
                    waf_pillar="Security",
                    service="Bedrock",
                    affected_resources=[f"{self.inventory.bedrock_agents} agents"],
                    recommendation="Configure Bedrock Guardrails for all agents",
                    remediation_steps=[
                        "Navigate to Amazon Bedrock console",
                        "Create guardrails with appropriate content filters",
                        "Associate guardrails with all agents",
                        "Configure denied topics and word filters"
                    ],
                    ai_dimensions=["safety", "controllability"]
                ))
        
        if self.inventory.bedrock_knowledge_bases > 0:
            self.findings.append(AIMLFinding(
                id="AIML-004",
                title="Bedrock Knowledge Bases Detected - Verify RAG Security",
                description=f"Found {self.inventory.bedrock_knowledge_bases} knowledge bases. Ensure data sources are properly secured and access controlled.",
                severity="MEDIUM",
                lens_type="generative_ai",
                waf_pillar="Security",
                service="Bedrock",
                affected_resources=[f"{self.inventory.bedrock_knowledge_bases} knowledge bases"],
                recommendation="Review knowledge base data source permissions and encryption",
                remediation_steps=[
                    "Verify S3 bucket encryption for knowledge base data",
                    "Review IAM roles associated with knowledge bases",
                    "Ensure data sources don't contain sensitive unmasked data"
                ]
            ))
        
        # Personalize/Rekognition - Responsible AI concerns
        if self.inventory.personalize_campaigns > 0:
            self.findings.append(AIMLFinding(
                id="AIML-005",
                title="Personalization ML Detected - Verify Fairness Assessment",
                description=f"Found {self.inventory.personalize_campaigns} Personalize campaigns. Recommendation systems require fairness and bias testing.",
                severity="MEDIUM",
                lens_type="responsible_ai",
                waf_pillar="Responsible AI",
                service="Personalize",
                affected_resources=[f"{self.inventory.personalize_campaigns} campaigns"],
                recommendation="Implement fairness testing for recommendation outputs",
                remediation_steps=[
                    "Analyze recommendation distribution across user segments",
                    "Test for demographic bias in recommendations",
                    "Document fairness metrics and monitoring approach"
                ],
                ai_dimensions=["fairness", "transparency"]
            ))
        
        if self.inventory.rekognition_projects > 0:
            self.findings.append(AIMLFinding(
                id="AIML-006",
                title="Rekognition Detected - Review Responsible AI Practices",
                description=f"Found {self.inventory.rekognition_projects} Rekognition projects. Facial analysis requires careful responsible AI consideration.",
                severity="MEDIUM",
                lens_type="responsible_ai",
                waf_pillar="Responsible AI",
                service="Rekognition",
                affected_resources=[f"{self.inventory.rekognition_projects} projects"],
                recommendation="Ensure Rekognition usage complies with responsible AI guidelines",
                remediation_steps=[
                    "Review use case for facial analysis appropriateness",
                    "Ensure transparency to users about AI analysis",
                    "Implement human review for high-stakes decisions",
                    "Document consent and data handling practices"
                ],
                ai_dimensions=["fairness", "transparency", "privacy"]
            ))


# ============================================================================
# DEMO DATA FOR AI/ML SERVICES
# ============================================================================

def generate_demo_aiml_inventory() -> AIMLServiceInventory:
    """Generate demo AI/ML inventory for demo mode"""
    inventory = AIMLServiceInventory(
        sagemaker_notebooks=3,
        sagemaker_endpoints=5,
        sagemaker_training_jobs=12,
        sagemaker_pipelines=2,
        sagemaker_models=8,
        sagemaker_feature_groups=3,
        bedrock_models_enabled=4,
        bedrock_custom_models=1,
        bedrock_agents=2,
        bedrock_knowledge_bases=3,
        bedrock_guardrails=1,
        rekognition_projects=1,
        comprehend_endpoints=2,
        lex_bots=1,
        kendra_indexes=1,
        personalize_campaigns=1,
        has_ml_workloads=True,
        has_genai_workloads=True,
        has_ai_services=True,
        detected_services=['sagemaker', 'bedrock', 'rekognition', 'comprehend', 'lex', 'kendra', 'personalize']
    )
    return inventory


def generate_demo_aiml_findings() -> List[AIMLFinding]:
    """Generate demo AI/ML findings"""
    return [
        AIMLFinding(
            id="AIML-DEMO-001",
            title="SageMaker Endpoints Without Model Monitor",
            description="3 of 5 SageMaker endpoints do not have Model Monitor configured for drift detection.",
            severity="HIGH",
            lens_type="machine_learning",
            waf_pillar="Operational Excellence",
            service="SageMaker",
            affected_resources=["prod-recommendation-endpoint", "staging-nlp-endpoint", "dev-vision-endpoint"],
            recommendation="Enable SageMaker Model Monitor for all production endpoints",
            remediation_steps=[
                "Configure baseline statistics from training data",
                "Enable data quality monitoring schedule",
                "Set up CloudWatch alarms for violations"
            ]
        ),
        AIMLFinding(
            id="AIML-DEMO-002",
            title="Bedrock Agents Using Outdated Guardrails",
            description="Bedrock guardrail configuration is 90+ days old and may not reflect current content policies.",
            severity="MEDIUM",
            lens_type="generative_ai",
            waf_pillar="Security",
            service="Bedrock",
            affected_resources=["customer-support-agent", "research-assistant-agent"],
            recommendation="Review and update Bedrock Guardrails quarterly",
            remediation_steps=[
                "Review current denied topics list",
                "Update word filters based on recent incidents",
                "Test guardrails with adversarial prompts"
            ],
            ai_dimensions=["safety", "controllability"]
        ),
        AIMLFinding(
            id="AIML-DEMO-003",
            title="Training Jobs Using On-Demand Instances",
            description="Recent SageMaker training jobs are not using Managed Spot Training, missing up to 90% cost savings.",
            severity="MEDIUM",
            lens_type="machine_learning",
            waf_pillar="Cost Optimization",
            service="SageMaker",
            affected_resources=["training-job-20241215", "training-job-20241218"],
            recommendation="Enable Managed Spot Training for fault-tolerant training jobs",
            remediation_steps=[
                "Add checkpointing to training scripts",
                "Configure max wait time and max run time",
                "Enable Managed Spot Training in training job config"
            ]
        ),
        AIMLFinding(
            id="AIML-DEMO-004",
            title="No Explainability Configured for ML Models",
            description="Production ML models do not have SageMaker Clarify configured for feature importance and bias detection.",
            severity="HIGH",
            lens_type="responsible_ai",
            waf_pillar="Responsible AI",
            service="SageMaker",
            affected_resources=["loan-approval-model", "fraud-detection-model"],
            recommendation="Configure SageMaker Clarify for model explainability",
            remediation_steps=[
                "Create Clarify processing job for bias analysis",
                "Configure SHAP baseline for feature importance",
                "Set up monitoring for bias drift"
            ],
            ai_dimensions=["explainability", "fairness"]
        ),
        AIMLFinding(
            id="AIML-DEMO-005",
            title="Bedrock Knowledge Base Using Unencrypted S3",
            description="Knowledge base data source S3 bucket does not have server-side encryption enabled.",
            severity="HIGH",
            lens_type="generative_ai",
            waf_pillar="Security",
            service="Bedrock",
            affected_resources=["kb-documents-bucket"],
            recommendation="Enable S3 SSE-KMS encryption for knowledge base data",
            remediation_steps=[
                "Enable default encryption on S3 bucket",
                "Use customer-managed KMS key for sensitive data",
                "Re-sync knowledge base after encryption enabled"
            ]
        )
    ]


# ============================================================================
# UNIFIED SCORING WITH AI/ML HEALTH
# ============================================================================

@dataclass
class AIMLHealthScore:
    """AI/ML Health Score for dashboard integration"""
    overall_score: int = 0
    ml_lens_score: int = 0
    genai_lens_score: int = 0
    rai_lens_score: int = 0
    
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    
    services_scanned: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'overall_score': self.overall_score,
            'ml_lens_score': self.ml_lens_score,
            'genai_lens_score': self.genai_lens_score,
            'rai_lens_score': self.rai_lens_score,
            'critical_findings': self.critical_findings,
            'high_findings': self.high_findings,
            'medium_findings': self.medium_findings,
            'low_findings': self.low_findings,
            'services_scanned': self.services_scanned,
            'recommendations': self.recommendations
        }


def calculate_aiml_health_score(
    aiml_inventory: AIMLServiceInventory,
    aiml_findings: List[AIMLFinding],
    ai_lens_responses: Dict = None
) -> AIMLHealthScore:
    """Calculate unified AI/ML health score"""
    
    score = AIMLHealthScore()
    score.services_scanned = aiml_inventory.detected_services
    
    # Count findings by severity
    for finding in aiml_findings:
        if finding.severity == "CRITICAL":
            score.critical_findings += 1
        elif finding.severity == "HIGH":
            score.high_findings += 1
        elif finding.severity == "MEDIUM":
            score.medium_findings += 1
        else:
            score.low_findings += 1
    
    # Calculate base score from findings (start at 100, deduct for findings)
    base_score = 100
    base_score -= score.critical_findings * 15
    base_score -= score.high_findings * 10
    base_score -= score.medium_findings * 5
    base_score -= score.low_findings * 2
    base_score = max(0, min(100, base_score))
    
    # If AI Lens responses provided, incorporate those scores
    if ai_lens_responses:
        ml_responses = {k: v for k, v in ai_lens_responses.items() if k.startswith("ml_")}
        genai_responses = {k: v for k, v in ai_lens_responses.items() if k.startswith("genai_")}
        rai_responses = {k: v for k, v in ai_lens_responses.items() if k.startswith("rai_")}
        
        if ml_responses:
            score.ml_lens_score = _calculate_lens_score(ml_responses)
        if genai_responses:
            score.genai_lens_score = _calculate_lens_score(genai_responses)
        if rai_responses:
            score.rai_lens_score = _calculate_lens_score(rai_responses)
        
        # Average with AI Lens scores if available
        lens_scores = [s for s in [score.ml_lens_score, score.genai_lens_score, score.rai_lens_score] if s > 0]
        if lens_scores:
            avg_lens_score = sum(lens_scores) / len(lens_scores)
            score.overall_score = int((base_score + avg_lens_score) / 2)
        else:
            score.overall_score = base_score
    else:
        score.overall_score = base_score
    
    # Generate recommendations based on findings
    if score.critical_findings > 0:
        score.recommendations.append(f"Address {score.critical_findings} critical AI/ML security issues immediately")
    if aiml_inventory.bedrock_guardrails == 0 and aiml_inventory.bedrock_agents > 0:
        score.recommendations.append("Configure Bedrock Guardrails for all AI agents")
    if aiml_inventory.sagemaker_endpoints > 0:
        score.recommendations.append("Enable Model Monitor for production ML endpoints")
    
    return score


def _calculate_lens_score(responses: Dict) -> int:
    """Calculate score from AI Lens responses"""
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
    
    return int(points / total) if total > 0 else 0


# ============================================================================
# KEY AI LENS QUESTIONS FOR UNIFIED ASSESSMENT
# ============================================================================

def get_key_ai_lens_questions(detected_services: List[str]) -> List[AILensQuestion]:
    """Get subset of key AI Lens questions based on detected services"""
    
    key_questions = []
    
    # Always include if any AI/ML detected
    if detected_services:
        # Key ML questions
        ml_questions = get_ml_lens_questions()
        key_ml_ids = ["ML-OPS-002", "ML-OPS-003", "ML-SEC-001", "ML-SEC-002", "ML-COST-001"]
        key_questions.extend([q for q in ml_questions if q.id in key_ml_ids])
    
    # GenAI specific
    if 'bedrock' in detected_services or 'lex' in detected_services:
        genai_questions = get_genai_lens_questions()
        key_genai_ids = ["GENAI-SEC-001", "GENAI-SEC-002", "GENAI-SEC-003", "GENAI-COST-001"]
        key_questions.extend([q for q in genai_questions if q.id in key_genai_ids])
    
    # Responsible AI - always include for high-risk services
    high_risk_services = ['rekognition', 'comprehend', 'personalize', 'frauddetector', 'bedrock']
    if any(s in detected_services for s in high_risk_services):
        rai_questions = get_responsible_ai_lens_questions()
        key_rai_ids = ["RAI-002", "RAI-003", "RAI-005", "RAI-006"]
        key_questions.extend([q for q in rai_questions if q.id in key_rai_ids])
    
    return key_questions


# ============================================================================
# SESSION STATE HELPERS
# ============================================================================

def initialize_aiml_session_state():
    """Initialize AI/ML integration session state"""
    if 'aiml_inventory' not in st.session_state:
        st.session_state.aiml_inventory = None
    if 'aiml_findings' not in st.session_state:
        st.session_state.aiml_findings = []
    if 'aiml_health_score' not in st.session_state:
        st.session_state.aiml_health_score = None
    if 'aiml_scan_completed' not in st.session_state:
        st.session_state.aiml_scan_completed = False


def get_aiml_scan_results() -> Tuple[Optional[AIMLServiceInventory], List[AIMLFinding]]:
    """Get cached AI/ML scan results from session state"""
    return st.session_state.get('aiml_inventory'), st.session_state.get('aiml_findings', [])


def set_aiml_scan_results(inventory: AIMLServiceInventory, findings: List[AIMLFinding]):
    """Store AI/ML scan results in session state"""
    st.session_state.aiml_inventory = inventory
    st.session_state.aiml_findings = findings
    st.session_state.aiml_scan_completed = True


# ============================================================================
# UI COMPONENTS FOR INTEGRATION
# ============================================================================

def render_aiml_detection_banner():
    """Render banner when AI/ML services detected"""
    inventory = st.session_state.get('aiml_inventory')
    
    if inventory and (inventory.has_ml_workloads or inventory.has_genai_workloads or inventory.has_ai_services):
        services_str = ", ".join(inventory.detected_services[:5])
        if len(inventory.detected_services) > 5:
            services_str += f" +{len(inventory.detected_services) - 5} more"
        
        st.info(f"""
        🧠 **AI/ML Workloads Detected**: {services_str}
        
        Enhanced AI Lens assessment available in the **🧠 AI Lens** tab for:
        {"- Machine Learning best practices" if inventory.has_ml_workloads else ""}
        {"- Generative AI security & governance" if inventory.has_genai_workloads else ""}
        {"- Responsible AI practices" if inventory.has_ai_services else ""}
        """)


def render_aiml_health_indicator():
    """Render AI/ML Health indicator for dashboard"""
    health_score = st.session_state.get('aiml_health_score')
    
    if health_score:
        # Determine color based on score
        if health_score.overall_score >= 80:
            color = "#27ae60"  # Green
            status = "Healthy"
        elif health_score.overall_score >= 60:
            color = "#f39c12"  # Orange
            status = "Needs Attention"
        else:
            color = "#e74c3c"  # Red
            status = "At Risk"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    border-radius: 10px; padding: 15px; margin: 10px 0;
                    border-left: 4px solid {color};">
            <h4 style="margin: 0; color: white;">🧠 AI/ML Health: {health_score.overall_score}/100</h4>
            <p style="margin: 5px 0; color: #ccc;">Status: <span style="color: {color}; font-weight: bold;">{status}</span></p>
            <p style="margin: 0; font-size: 0.9em; color: #888;">
                Services: {len(health_score.services_scanned)} | 
                Findings: {health_score.critical_findings + health_score.high_findings + health_score.medium_findings}
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_aiml_summary_card(inventory: AIMLServiceInventory, findings: List[AIMLFinding]):
    """Render AI/ML summary card for reports"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🧠 ML Platform",
            f"{inventory.sagemaker_endpoints + inventory.sagemaker_models} resources",
            delta=f"{inventory.sagemaker_pipelines} pipelines"
        )
    
    with col2:
        st.metric(
            "✨ Generative AI",
            f"{inventory.bedrock_agents + inventory.bedrock_knowledge_bases} resources",
            delta=f"{inventory.bedrock_guardrails} guardrails"
        )
    
    with col3:
        st.metric(
            "⚠️ AI Findings",
            f"{len(findings)} issues",
            delta=f"{len([f for f in findings if f.severity in ['CRITICAL', 'HIGH']])} high priority"
        )


# ============================================================================
# EXPORT FOR INTEGRATION
# ============================================================================

__all__ = [
    'AI_ML_SERVICES',
    'AIMLServiceInventory',
    'AIMLFinding',
    'AIMLServiceScanner',
    'AIMLHealthScore',
    'generate_demo_aiml_inventory',
    'generate_demo_aiml_findings',
    'calculate_aiml_health_score',
    'get_key_ai_lens_questions',
    'initialize_aiml_session_state',
    'get_aiml_scan_results',
    'set_aiml_scan_results',
    'render_aiml_detection_banner',
    'render_aiml_health_indicator',
    'render_aiml_summary_card'
]
