"""
WAF AI Question Helper
======================
AI-powered assistance for understanding and answering WAF questions.
Provides simplified explanations, verification steps, and recommendations.

Works with both Streamlit and React (FastAPI) backends.
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# CONFIGURATION
# ============================================================================

class AIProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    BEDROCK = "bedrock"
    MOCK = "mock"  # For demo/testing

# Try to import AI providers
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class QuestionHelp:
    """Structured help response for a WAF question"""
    question_id: str
    simple_explanation: str
    what_it_means: str
    why_it_matters: str
    how_to_check: List[str]
    aws_cli_commands: List[Dict[str, str]]
    console_steps: List[str]
    evidence_to_collect: List[str]
    if_yes_means: str
    if_no_means: str
    recommendations: List[str]
    related_services: List[str]
    risk_level: str
    estimated_effort: str


# ============================================================================
# PRE-BUILT KNOWLEDGE BASE
# ============================================================================

# Pre-built help for common questions (no AI needed)
WAF_QUESTION_KNOWLEDGE_BASE: Dict[str, Dict] = {
    # Security Questions
    "SEC-IAM-01": {
        "simple_explanation": "Are you using temporary credentials instead of long-term access keys?",
        "what_it_means": "AWS recommends using IAM Roles and temporary credentials (like those from STS) instead of storing permanent access keys.",
        "why_it_matters": "Long-term credentials can be leaked, stolen, or compromised. Temporary credentials automatically expire, reducing security risk.",
        "how_to_check": [
            "Check if your applications use IAM Roles instead of access keys",
            "Look for any hardcoded credentials in your code",
            "Review IAM users that have access keys older than 90 days"
        ],
        "aws_cli_commands": [
            {
                "description": "List all IAM users with access keys",
                "command": "aws iam list-users --query 'Users[*].[UserName]' --output table"
            },
            {
                "description": "Check access key age for a user",
                "command": "aws iam list-access-keys --user-name USERNAME"
            },
            {
                "description": "Generate credential report",
                "command": "aws iam generate-credential-report && aws iam get-credential-report --query 'Content' --output text | base64 -d"
            }
        ],
        "console_steps": [
            "Go to IAM Console → Users",
            "Click on each user → Security credentials tab",
            "Check 'Access keys' section for key age",
            "Review IAM → Credential Report for overview"
        ],
        "evidence_to_collect": [
            "IAM Credential Report",
            "List of IAM Roles used by applications",
            "Screenshot of EC2 instances using instance profiles"
        ],
        "if_yes_means": "Your workload follows security best practices by using temporary credentials that automatically rotate.",
        "if_no_means": "You have long-term credentials that could be compromised. Consider migrating to IAM Roles.",
        "recommendations": [
            "Replace access keys with IAM Roles for EC2, Lambda, ECS",
            "Use AWS SSO for human access",
            "Enable access key rotation policy",
            "Use AWS Secrets Manager for any required credentials"
        ],
        "related_services": ["IAM", "STS", "AWS SSO", "Secrets Manager"],
        "risk_level": "HIGH",
        "estimated_effort": "Medium (1-2 weeks to migrate)"
    },
    
    "SEC-IAM-02": {
        "simple_explanation": "Do you follow the principle of least privilege - giving only the minimum permissions needed?",
        "what_it_means": "Users and services should only have access to exactly what they need, nothing more.",
        "why_it_matters": "Excessive permissions increase blast radius if credentials are compromised. An attacker with admin access can do much more damage than one with read-only access.",
        "how_to_check": [
            "Review IAM policies for wildcards (*) in actions or resources",
            "Check for policies with 'Action': '*' or 'Resource': '*'",
            "Use IAM Access Analyzer to find unused permissions"
        ],
        "aws_cli_commands": [
            {
                "description": "List policies with admin access",
                "command": "aws iam list-policies --query 'Policies[?contains(PolicyName, `Admin`)]'"
            },
            {
                "description": "Get policy details",
                "command": "aws iam get-policy-version --policy-arn POLICY_ARN --version-id v1"
            },
            {
                "description": "Find unused permissions with Access Analyzer",
                "command": "aws accessanalyzer list-findings --analyzer-arn ANALYZER_ARN"
            }
        ],
        "console_steps": [
            "Go to IAM Console → Access Analyzer",
            "Review 'Findings' for external access",
            "Use 'Policy generation' to create least-privilege policies",
            "Check IAM → Policies for overly permissive policies"
        ],
        "evidence_to_collect": [
            "IAM Access Analyzer findings",
            "List of policies with wildcards",
            "Service Control Policies (SCPs) in use"
        ],
        "if_yes_means": "Your permissions are tightly scoped, limiting potential damage from compromised credentials.",
        "if_no_means": "Overly permissive policies increase your security risk. Review and tighten permissions.",
        "recommendations": [
            "Use IAM Access Analyzer to generate least-privilege policies",
            "Replace wildcard (*) permissions with specific actions",
            "Implement permission boundaries",
            "Use Service Control Policies (SCPs) as guardrails"
        ],
        "related_services": ["IAM", "IAM Access Analyzer", "Organizations"],
        "risk_level": "CRITICAL",
        "estimated_effort": "High (2-4 weeks for full review)"
    },
    
    # Reliability Questions
    "REL-BACKUP-01": {
        "simple_explanation": "Do you have backups for all your important data, and can you actually restore from them?",
        "what_it_means": "You should have automated backups for databases, files, and configurations, with tested restore procedures.",
        "why_it_matters": "Without backups, data loss from hardware failure, human error, or ransomware could be catastrophic and unrecoverable.",
        "how_to_check": [
            "Verify AWS Backup plans exist for critical resources",
            "Check RDS automated backups are enabled",
            "Confirm S3 versioning is enabled for important buckets",
            "Test restore procedures regularly"
        ],
        "aws_cli_commands": [
            {
                "description": "List AWS Backup plans",
                "command": "aws backup list-backup-plans"
            },
            {
                "description": "Check RDS backup settings",
                "command": "aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,BackupRetentionPeriod]'"
            },
            {
                "description": "Check S3 versioning",
                "command": "aws s3api get-bucket-versioning --bucket BUCKET_NAME"
            }
        ],
        "console_steps": [
            "Go to AWS Backup Console → Backup plans",
            "Check RDS Console → Databases → Maintenance & backups",
            "Review S3 Console → Bucket → Properties → Versioning"
        ],
        "evidence_to_collect": [
            "AWS Backup plan configurations",
            "RDS backup retention settings",
            "S3 versioning status",
            "Last successful restore test date"
        ],
        "if_yes_means": "Your data is protected and you can recover from disasters.",
        "if_no_means": "You risk permanent data loss. Implement backup strategy immediately.",
        "recommendations": [
            "Enable AWS Backup for centralized backup management",
            "Set RDS backup retention to at least 7 days",
            "Enable S3 versioning and cross-region replication",
            "Schedule quarterly restore tests"
        ],
        "related_services": ["AWS Backup", "RDS", "S3", "EBS Snapshots"],
        "risk_level": "CRITICAL",
        "estimated_effort": "Low (1-2 days to configure)"
    },
    
    # Cost Optimization Questions
    "COST-OPT-01": {
        "simple_explanation": "Do you know what you're spending on AWS and why?",
        "what_it_means": "You should have visibility into your AWS costs, understand what drives them, and have budgets/alerts in place.",
        "why_it_matters": "Without cost visibility, spending can spiral out of control. Many organizations are surprised by their AWS bills.",
        "how_to_check": [
            "Verify Cost Explorer is being used",
            "Check if AWS Budgets are configured",
            "Confirm cost allocation tags are applied",
            "Review if there are any anomaly alerts"
        ],
        "aws_cli_commands": [
            {
                "description": "Get current month costs",
                "command": "aws ce get-cost-and-usage --time-period Start=$(date -d '1 day ago' +%Y-%m-01),End=$(date +%Y-%m-%d) --granularity MONTHLY --metrics BlendedCost"
            },
            {
                "description": "List budgets",
                "command": "aws budgets describe-budgets --account-id $(aws sts get-caller-identity --query Account --output text)"
            },
            {
                "description": "Check for cost anomalies",
                "command": "aws ce get-anomalies --date-interval Start=$(date -d '30 days ago' +%Y-%m-%d),End=$(date +%Y-%m-%d)"
            }
        ],
        "console_steps": [
            "Go to AWS Cost Explorer → Review spending trends",
            "Check AWS Budgets → Budgets for alerts",
            "Review Billing → Cost allocation tags",
            "Enable Cost Anomaly Detection"
        ],
        "evidence_to_collect": [
            "Monthly cost reports",
            "Budget configurations and thresholds",
            "Cost allocation tag coverage report",
            "Anomaly detection alerts"
        ],
        "if_yes_means": "You have financial visibility and can optimize spending proactively.",
        "if_no_means": "You may be overspending without knowing. Set up cost management tools.",
        "recommendations": [
            "Enable Cost Explorer and review weekly",
            "Create budgets with alerts at 80% and 100%",
            "Implement mandatory cost allocation tags",
            "Enable Cost Anomaly Detection"
        ],
        "related_services": ["Cost Explorer", "AWS Budgets", "Cost Anomaly Detection"],
        "risk_level": "MEDIUM",
        "estimated_effort": "Low (1 day to set up)"
    },
    
    # Performance Questions
    "PERF-COMPUTE-01": {
        "simple_explanation": "Are your EC2 instances the right size - not too big (wasting money) or too small (poor performance)?",
        "what_it_means": "Instance types should match your workload requirements. Over-provisioned instances waste money; under-provisioned ones hurt performance.",
        "why_it_matters": "Right-sizing can save 20-40% on compute costs while maintaining or improving performance.",
        "how_to_check": [
            "Review CloudWatch CPU/Memory utilization metrics",
            "Check AWS Compute Optimizer recommendations",
            "Analyze instance utilization patterns over time"
        ],
        "aws_cli_commands": [
            {
                "description": "Get Compute Optimizer recommendations",
                "command": "aws compute-optimizer get-ec2-instance-recommendations"
            },
            {
                "description": "Check EC2 CPU utilization",
                "command": "aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=INSTANCE_ID --start-time $(date -d '7 days ago' -Iseconds) --end-time $(date -Iseconds) --period 3600 --statistics Average"
            }
        ],
        "console_steps": [
            "Go to Compute Optimizer → EC2 instances",
            "Review 'Finding' column for optimization opportunities",
            "Check CloudWatch → EC2 → Per-Instance Metrics",
            "Look for consistently low (<20%) or high (>80%) CPU"
        ],
        "evidence_to_collect": [
            "Compute Optimizer recommendations report",
            "CloudWatch utilization dashboards",
            "Instance type vs utilization mapping"
        ],
        "if_yes_means": "Your compute resources are efficiently matched to your workload.",
        "if_no_means": "You may be over or under-provisioned. Review Compute Optimizer recommendations.",
        "recommendations": [
            "Enable Compute Optimizer for all accounts",
            "Right-size instances based on actual utilization",
            "Consider Graviton (ARM) instances for 20-40% savings",
            "Use Auto Scaling to match capacity to demand"
        ],
        "related_services": ["Compute Optimizer", "CloudWatch", "EC2 Auto Scaling"],
        "risk_level": "MEDIUM",
        "estimated_effort": "Medium (1 week for analysis and migration)"
    },
    
    # Operational Excellence
    "OPS-MONITOR-01": {
        "simple_explanation": "Can you see what's happening inside your applications and infrastructure in real-time?",
        "what_it_means": "You should have dashboards, metrics, logs, and traces that show you the health and behavior of your systems.",
        "why_it_matters": "Without observability, you're flying blind. Problems go undetected, root causes are hard to find, and recovery takes longer.",
        "how_to_check": [
            "Verify CloudWatch metrics are being collected",
            "Check if CloudWatch Logs are configured",
            "Confirm X-Ray tracing is enabled for applications",
            "Review if dashboards exist for key metrics"
        ],
        "aws_cli_commands": [
            {
                "description": "List CloudWatch dashboards",
                "command": "aws cloudwatch list-dashboards"
            },
            {
                "description": "List log groups",
                "command": "aws logs describe-log-groups --query 'logGroups[*].logGroupName'"
            },
            {
                "description": "Check X-Ray traces",
                "command": "aws xray get-trace-summaries --start-time $(date -d '1 hour ago' +%s) --end-time $(date +%s)"
            }
        ],
        "console_steps": [
            "Go to CloudWatch → Dashboards",
            "Check CloudWatch → Log groups for application logs",
            "Review X-Ray → Service map for distributed tracing",
            "Verify CloudWatch → Alarms are configured"
        ],
        "evidence_to_collect": [
            "List of CloudWatch dashboards",
            "Log retention policies",
            "X-Ray service map screenshot",
            "Alarm configurations"
        ],
        "if_yes_means": "You have visibility into your systems and can detect/diagnose issues quickly.",
        "if_no_means": "You lack visibility. Implement comprehensive monitoring strategy.",
        "recommendations": [
            "Create CloudWatch dashboards for key metrics",
            "Enable detailed monitoring for EC2",
            "Implement X-Ray for distributed tracing",
            "Set up CloudWatch Alarms for critical metrics"
        ],
        "related_services": ["CloudWatch", "X-Ray", "CloudTrail"],
        "risk_level": "HIGH",
        "estimated_effort": "Medium (1-2 weeks for comprehensive setup)"
    }
}

# Try to import and merge extended knowledge base
try:
    from waf_knowledge_base_extended import EXTENDED_WAF_KNOWLEDGE_BASE
    WAF_QUESTION_KNOWLEDGE_BASE.update(EXTENDED_WAF_KNOWLEDGE_BASE)
    print(f"✅ Extended knowledge base loaded: {len(EXTENDED_WAF_KNOWLEDGE_BASE)} additional questions")
except ImportError:
    pass  # Extended knowledge base not available


# ============================================================================
# AI HELPER CLASS
# ============================================================================

class WAFAIQuestionHelper:
    """
    AI-powered helper for WAF questions.
    Provides explanations, verification steps, and recommendations.
    """
    
    def __init__(self, provider: AIProvider = AIProvider.MOCK, api_key: str = None):
        self.provider = provider
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if provider == AIProvider.ANTHROPIC and ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
        elif provider == AIProvider.OPENAI and OPENAI_AVAILABLE and self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def get_question_help(
        self, 
        question_id: str,
        question_text: str,
        description: str = "",
        best_practices: List[str] = None,
        detection_services: List[str] = None,
        context: Dict = None
    ) -> QuestionHelp:
        """
        Get AI-powered help for a WAF question.
        
        Args:
            question_id: The WAF question ID (e.g., "SEC-IAM-01")
            question_text: The actual question text
            description: Additional description
            best_practices: List of best practices
            detection_services: AWS services that can detect this
            context: Additional context about the user's environment
            
        Returns:
            QuestionHelp object with comprehensive guidance
        """
        
        # First check knowledge base for pre-built help
        if question_id in WAF_QUESTION_KNOWLEDGE_BASE:
            kb_entry = WAF_QUESTION_KNOWLEDGE_BASE[question_id]
            return QuestionHelp(
                question_id=question_id,
                simple_explanation=kb_entry["simple_explanation"],
                what_it_means=kb_entry["what_it_means"],
                why_it_matters=kb_entry["why_it_matters"],
                how_to_check=kb_entry["how_to_check"],
                aws_cli_commands=kb_entry["aws_cli_commands"],
                console_steps=kb_entry["console_steps"],
                evidence_to_collect=kb_entry["evidence_to_collect"],
                if_yes_means=kb_entry["if_yes_means"],
                if_no_means=kb_entry["if_no_means"],
                recommendations=kb_entry["recommendations"],
                related_services=kb_entry["related_services"],
                risk_level=kb_entry["risk_level"],
                estimated_effort=kb_entry["estimated_effort"]
            )
        
        # Generate help using AI if available
        if self.provider != AIProvider.MOCK and self.client:
            return self._generate_ai_help(
                question_id, question_text, description, 
                best_practices, detection_services, context
            )
        
        # Fallback to generic help
        return self._generate_generic_help(
            question_id, question_text, description,
            best_practices, detection_services
        )
    
    def _generate_ai_help(
        self,
        question_id: str,
        question_text: str,
        description: str,
        best_practices: List[str],
        detection_services: List[str],
        context: Dict
    ) -> QuestionHelp:
        """Generate help using AI provider"""
        
        prompt = f"""You are an AWS Well-Architected Framework expert. Help a user understand and answer this WAF question.

Question ID: {question_id}
Question: {question_text}
Description: {description}
Best Practices: {json.dumps(best_practices or [])}
Related AWS Services: {json.dumps(detection_services or [])}
User Context: {json.dumps(context or {})}

Provide a JSON response with:
{{
    "simple_explanation": "ELI5 version of what this question is really asking",
    "what_it_means": "What this question means for their AWS environment",
    "why_it_matters": "Business impact and risk if not addressed",
    "how_to_check": ["Step 1", "Step 2", "Step 3"],
    "aws_cli_commands": [
        {{"description": "What this command does", "command": "aws command here"}}
    ],
    "console_steps": ["Go to X", "Click Y", "Check Z"],
    "evidence_to_collect": ["Document 1", "Screenshot 2"],
    "if_yes_means": "What answering Yes indicates",
    "if_no_means": "What answering No indicates and risks",
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "related_services": ["Service1", "Service2"],
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "estimated_effort": "Time estimate to implement"
}}

Be specific to AWS services and provide actionable guidance."""

        try:
            if self.provider == AIProvider.ANTHROPIC:
                response = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
            elif self.provider == AIProvider.OPENAI:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000
                )
                content = response.choices[0].message.content
            else:
                return self._generate_generic_help(
                    question_id, question_text, description,
                    best_practices, detection_services
                )
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            
            return QuestionHelp(
                question_id=question_id,
                simple_explanation=data.get("simple_explanation", ""),
                what_it_means=data.get("what_it_means", ""),
                why_it_matters=data.get("why_it_matters", ""),
                how_to_check=data.get("how_to_check", []),
                aws_cli_commands=data.get("aws_cli_commands", []),
                console_steps=data.get("console_steps", []),
                evidence_to_collect=data.get("evidence_to_collect", []),
                if_yes_means=data.get("if_yes_means", ""),
                if_no_means=data.get("if_no_means", ""),
                recommendations=data.get("recommendations", []),
                related_services=data.get("related_services", detection_services or []),
                risk_level=data.get("risk_level", "MEDIUM"),
                estimated_effort=data.get("estimated_effort", "Variable")
            )
            
        except Exception as e:
            print(f"AI generation failed: {e}")
            return self._generate_generic_help(
                question_id, question_text, description,
                best_practices, detection_services
            )
    
    def _generate_generic_help(
        self,
        question_id: str,
        question_text: str,
        description: str,
        best_practices: List[str],
        detection_services: List[str]
    ) -> QuestionHelp:
        """Generate generic help without AI"""
        
        # Determine pillar from question ID
        pillar = "general"
        risk = "MEDIUM"
        if question_id.startswith("SEC"):
            pillar = "security"
            risk = "HIGH"
        elif question_id.startswith("REL"):
            pillar = "reliability"
            risk = "HIGH"
        elif question_id.startswith("PERF"):
            pillar = "performance"
            risk = "MEDIUM"
        elif question_id.startswith("COST"):
            pillar = "cost"
            risk = "MEDIUM"
        elif question_id.startswith("OPS"):
            pillar = "operational"
            risk = "MEDIUM"
        elif question_id.startswith("SUS"):
            pillar = "sustainability"
            risk = "LOW"
        
        # Generate CLI commands based on detection services
        cli_commands = []
        for service in (detection_services or []):
            if service == "CloudWatch":
                cli_commands.append({
                    "description": "List CloudWatch alarms",
                    "command": "aws cloudwatch describe-alarms --state-value ALARM"
                })
            elif service == "IAM":
                cli_commands.append({
                    "description": "List IAM users",
                    "command": "aws iam list-users"
                })
            elif service == "S3":
                cli_commands.append({
                    "description": "List S3 buckets",
                    "command": "aws s3 ls"
                })
            elif service == "RDS":
                cli_commands.append({
                    "description": "Describe RDS instances",
                    "command": "aws rds describe-db-instances"
                })
            elif service == "EC2":
                cli_commands.append({
                    "description": "Describe EC2 instances",
                    "command": "aws ec2 describe-instances"
                })
        
        if not cli_commands:
            cli_commands.append({
                "description": "This question may require manual verification",
                "command": "# Review AWS Console or documentation"
            })
        
        return QuestionHelp(
            question_id=question_id,
            simple_explanation=f"This question asks: {question_text}",
            what_it_means=description or f"Evaluate your {pillar} practices for this area.",
            why_it_matters=f"This is a {risk} priority item in the {pillar} pillar of the Well-Architected Framework.",
            how_to_check=[
                f"Review your current {pillar} configuration",
                "Check relevant AWS services in the console",
                "Verify best practices are implemented"
            ] + (best_practices[:3] if best_practices else []),
            aws_cli_commands=cli_commands,
            console_steps=[
                f"Navigate to AWS Console",
                f"Go to relevant service ({', '.join(detection_services[:3]) if detection_services else 'varies'})",
                "Review current configuration against best practices"
            ],
            evidence_to_collect=[
                "Configuration screenshots",
                "Policy documents",
                "Architecture diagrams"
            ],
            if_yes_means="You are following this best practice.",
            if_no_means="Consider implementing this best practice to improve your architecture.",
            recommendations=best_practices[:5] if best_practices else [
                "Review AWS Well-Architected Framework documentation",
                "Consider AWS best practices for this area",
                f"Evaluate your {pillar} posture"
            ],
            related_services=detection_services or [],
            risk_level=risk,
            estimated_effort="Variable - depends on current state"
        )
    
    def get_quick_tips(self, question_id: str) -> List[str]:
        """Get quick tips for a question"""
        
        if question_id in WAF_QUESTION_KNOWLEDGE_BASE:
            entry = WAF_QUESTION_KNOWLEDGE_BASE[question_id]
            return [
                f"💡 {entry['simple_explanation']}",
                f"⚠️ Risk Level: {entry['risk_level']}",
                f"⏱️ Effort: {entry['estimated_effort']}",
                f"🔧 Key Services: {', '.join(entry['related_services'][:3])}"
            ]
        
        return [
            "💡 Review AWS documentation for this question",
            "⚠️ Consider the impact on your workload",
            "🔧 Check related AWS services"
        ]
    
    def to_dict(self, help_obj: QuestionHelp) -> Dict:
        """Convert QuestionHelp to dictionary for JSON serialization"""
        return {
            "question_id": help_obj.question_id,
            "simple_explanation": help_obj.simple_explanation,
            "what_it_means": help_obj.what_it_means,
            "why_it_matters": help_obj.why_it_matters,
            "how_to_check": help_obj.how_to_check,
            "aws_cli_commands": help_obj.aws_cli_commands,
            "console_steps": help_obj.console_steps,
            "evidence_to_collect": help_obj.evidence_to_collect,
            "if_yes_means": help_obj.if_yes_means,
            "if_no_means": help_obj.if_no_means,
            "recommendations": help_obj.recommendations,
            "related_services": help_obj.related_services,
            "risk_level": help_obj.risk_level,
            "estimated_effort": help_obj.estimated_effort
        }


# ============================================================================
# STREAMLIT COMPONENT
# ============================================================================

def render_question_help_streamlit(question_id: str, question_text: str, description: str = "", 
                                   best_practices: List[str] = None, detection_services: List[str] = None):
    """
    Render AI question help in Streamlit.
    Call this from your WAF assessment page.
    """
    import streamlit as st
    
    helper = WAFAIQuestionHelper(provider=AIProvider.MOCK)
    
    with st.expander("🤖 AI Help - Click to understand this question better", expanded=False):
        help_data = helper.get_question_help(
            question_id=question_id,
            question_text=question_text,
            description=description,
            best_practices=best_practices,
            detection_services=detection_services
        )
        
        # Simple Explanation
        st.markdown(f"### 💡 In Simple Terms")
        st.info(help_data.simple_explanation)
        
        # Why It Matters
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 📌 What This Means")
            st.write(help_data.what_it_means)
        with col2:
            st.markdown("#### ⚠️ Why It Matters")
            st.write(help_data.why_it_matters)
        
        # Risk Badge
        risk_colors = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
        st.markdown(f"**Risk Level:** {risk_colors.get(help_data.risk_level, '⚪')} {help_data.risk_level} | **Effort:** {help_data.estimated_effort}")
        
        # How to Check
        st.markdown("#### 🔍 How to Check")
        for step in help_data.how_to_check:
            st.markdown(f"- {step}")
        
        # AWS CLI Commands
        if help_data.aws_cli_commands:
            st.markdown("#### 💻 AWS CLI Commands")
            for cmd in help_data.aws_cli_commands:
                st.markdown(f"**{cmd['description']}**")
                st.code(cmd['command'], language="bash")
        
        # Console Steps
        st.markdown("#### 🖥️ AWS Console Steps")
        for i, step in enumerate(help_data.console_steps, 1):
            st.markdown(f"{i}. {step}")
        
        # Answer Implications
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"**If YES:** {help_data.if_yes_means}")
        with col2:
            st.warning(f"**If NO:** {help_data.if_no_means}")
        
        # Recommendations
        st.markdown("#### 💡 Recommendations")
        for rec in help_data.recommendations:
            st.markdown(f"- {rec}")
        
        # Related Services
        if help_data.related_services:
            st.markdown(f"**Related AWS Services:** {', '.join(help_data.related_services)}")


# ============================================================================
# FASTAPI ENDPOINTS (FOR REACT)
# ============================================================================

def create_fastapi_router():
    """Create FastAPI router for WAF question help"""
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/api/waf-help", tags=["WAF Question Help"])
    
    class QuestionHelpRequest(BaseModel):
        question_id: str
        question_text: str
        description: str = ""
        best_practices: List[str] = []
        detection_services: List[str] = []
        context: Dict = {}
    
    class QuickTipsRequest(BaseModel):
        question_id: str
    
    helper = WAFAIQuestionHelper(provider=AIProvider.MOCK)
    
    @router.post("/get-help")
    async def get_question_help(request: QuestionHelpRequest):
        """Get AI-powered help for a WAF question"""
        try:
            help_data = helper.get_question_help(
                question_id=request.question_id,
                question_text=request.question_text,
                description=request.description,
                best_practices=request.best_practices,
                detection_services=request.detection_services,
                context=request.context
            )
            return helper.to_dict(help_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/quick-tips")
    async def get_quick_tips(request: QuickTipsRequest):
        """Get quick tips for a question"""
        tips = helper.get_quick_tips(request.question_id)
        return {"question_id": request.question_id, "tips": tips}
    
    @router.get("/knowledge-base")
    async def get_knowledge_base():
        """Get all pre-built question help"""
        return {
            "questions": list(WAF_QUESTION_KNOWLEDGE_BASE.keys()),
            "count": len(WAF_QUESTION_KNOWLEDGE_BASE)
        }
    
    @router.get("/knowledge-base/{question_id}")
    async def get_knowledge_base_entry(question_id: str):
        """Get specific knowledge base entry"""
        if question_id in WAF_QUESTION_KNOWLEDGE_BASE:
            return WAF_QUESTION_KNOWLEDGE_BASE[question_id]
        raise HTTPException(status_code=404, detail="Question not in knowledge base")
    
    return router


# ============================================================================
# CLI TESTING
# ============================================================================

if __name__ == "__main__":
    # Test the helper
    helper = WAFAIQuestionHelper(provider=AIProvider.MOCK)
    
    # Test with knowledge base question
    print("=" * 60)
    print("Testing SEC-IAM-01 (from knowledge base)")
    print("=" * 60)
    
    help_data = helper.get_question_help(
        question_id="SEC-IAM-01",
        question_text="How do you manage identities for people and machines?",
        description="Securely manage identities for your workload",
        best_practices=["Use IAM Roles", "Avoid long-term credentials"],
        detection_services=["IAM", "STS"]
    )
    
    print(f"\n📌 Simple Explanation: {help_data.simple_explanation}")
    print(f"\n⚠️ Risk Level: {help_data.risk_level}")
    print(f"\n🔧 Related Services: {', '.join(help_data.related_services)}")
    print(f"\n💻 CLI Commands:")
    for cmd in help_data.aws_cli_commands[:2]:
        print(f"  - {cmd['description']}: {cmd['command']}")
    
    # Test with generic question
    print("\n" + "=" * 60)
    print("Testing OPS-CUSTOM-99 (generic)")
    print("=" * 60)
    
    help_data2 = helper.get_question_help(
        question_id="OPS-CUSTOM-99",
        question_text="How do you manage operational events?",
        description="Handle operational events effectively",
        best_practices=["Use runbooks", "Automate responses"],
        detection_services=["CloudWatch", "SNS"]
    )
    
    print(f"\n📌 Simple Explanation: {help_data2.simple_explanation}")
    print(f"\n⚠️ Risk Level: {help_data2.risk_level}")
    
    print("\n✅ WAF AI Question Helper working correctly!")
