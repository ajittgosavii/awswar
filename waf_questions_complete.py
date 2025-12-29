"""
Complete AWS Well-Architected Framework Questions Database
205 Questions across all 6 pillars
"""

from enum import Enum

class WAFPillar(Enum):
    OPERATIONAL_EXCELLENCE = "Operational Excellence"
    SECURITY = "Security"
    RELIABILITY = "Reliability"
    PERFORMANCE_EFFICIENCY = "Performance Efficiency"
    COST_OPTIMIZATION = "Cost Optimization"
    SUSTAINABILITY = "Sustainability"

# ============================================================================
# COMPLETE WAF QUESTIONS DATABASE - 205 QUESTIONS
# ============================================================================

WAF_QUESTIONS_COMPLETE = {
    # ========================================================================
    # OPERATIONAL EXCELLENCE - 35 Questions
    # ========================================================================
    WAFPillar.OPERATIONAL_EXCELLENCE: [
        # Organization (OPS-ORG) - 8 questions
        {
            "id": "OPS-ORG-01",
            "question": "How do you determine what your priorities are?",
            "description": "Everyone needs to understand their part in enabling business success. Have shared goals in order to set priorities for resources.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Evaluate external customer needs",
                "Evaluate internal customer needs",
                "Evaluate governance requirements",
                "Evaluate compliance requirements",
                "Evaluate threat landscape"
            ]
        },
        {
            "id": "OPS-ORG-02",
            "question": "How do you structure your organization to support your business outcomes?",
            "description": "Your teams must understand their part in achieving business outcomes.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Resources have identified owners",
                "Processes and procedures have identified owners",
                "Operations activities have identified owners responsible",
                "Team members know what they are responsible for",
                "Mechanisms exist to identify responsibility and ownership"
            ]
        },
        {
            "id": "OPS-ORG-03",
            "question": "How does your organizational culture support your business outcomes?",
            "description": "Provide support for your team members so that they can be more effective.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Executive sponsorship",
                "Team members are empowered to take action",
                "Escalation is encouraged",
                "Communications are timely, clear, and actionable",
                "Experimentation is encouraged"
            ]
        },
        {
            "id": "OPS-ORG-04",
            "question": "How do you design your workload to be observable?",
            "description": "Design your workload so that it provides the information necessary for you to understand its internal state.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "X-Ray", "CloudTrail"],
            "best_practices": [
                "Implement application telemetry",
                "Implement user activity telemetry",
                "Implement dependency telemetry",
                "Implement distributed tracing"
            ]
        },
        {
            "id": "OPS-ORG-05",
            "question": "How do you reduce defects, ease remediation, and improve flow into production?",
            "description": "Adopt approaches that improve flow of changes into production and enable refactoring.",
            "scan_detectable": True,
            "detection_services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "best_practices": [
                "Use version control",
                "Test and validate changes",
                "Use configuration management systems",
                "Use build and deployment management systems",
                "Perform patch management"
            ]
        },
        {
            "id": "OPS-ORG-06",
            "question": "How do you mitigate deployment risks?",
            "description": "Adopt approaches that provide fast feedback on quality and enable rapid recovery from changes.",
            "scan_detectable": True,
            "detection_services": ["CodeDeploy", "CloudFormation", "Elastic Beanstalk"],
            "best_practices": [
                "Plan for unsuccessful changes",
                "Test and validate changes",
                "Use deployment management systems",
                "Test using limited deployments",
                "Automate testing and rollback"
            ]
        },
        {
            "id": "OPS-ORG-07",
            "question": "How do you know that you are ready to support a workload?",
            "description": "Evaluate the operational readiness of your workload, processes and procedures, and personnel.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Ensure personnel capability",
                "Ensure consistent review of operational readiness",
                "Use runbooks to perform procedures",
                "Use playbooks to investigate issues",
                "Make informed decisions to deploy systems"
            ]
        },
        {
            "id": "OPS-ORG-08",
            "question": "How do you evaluate your management and governance requirements?",
            "description": "Evaluate management priorities and internal governance requirements.",
            "scan_detectable": True,
            "detection_services": ["Organizations", "Control Tower", "Service Catalog"],
            "best_practices": [
                "Use AWS Organizations for multi-account management",
                "Implement tagging strategies",
                "Use AWS Control Tower for governance",
                "Define service control policies"
            ]
        },
        # Prepare (OPS-PREP) - 10 questions
        {
            "id": "OPS-PREP-01",
            "question": "How do you design your workload so that you can understand its state?",
            "description": "Design your workload so that it provides the information necessary across all components.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "X-Ray", "CloudTrail"],
            "best_practices": [
                "Implement application telemetry",
                "Generate log telemetry",
                "Generate metrics telemetry",
                "Generate trace telemetry",
                "Analyze workload telemetry"
            ]
        },
        {
            "id": "OPS-PREP-02",
            "question": "How do you instrument your workload to capture operational events?",
            "description": "Instrument workload to emit information about internal state, status, and business outcomes.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "EventBridge", "SNS"],
            "best_practices": [
                "Capture operational events",
                "Create custom CloudWatch metrics",
                "Use AWS X-Ray for tracing",
                "Implement structured logging"
            ]
        },
        {
            "id": "OPS-PREP-03",
            "question": "How do you utilize workload observability in your organization?",
            "description": "Understand the current state of your workload and use that to respond to events.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "CloudWatch Dashboards", "Managed Grafana"],
            "best_practices": [
                "Create dashboards",
                "Configure alerting",
                "Use AIOps capabilities",
                "Implement event management"
            ]
        },
        {
            "id": "OPS-PREP-04",
            "question": "How do you prepare for operational events and incidents?",
            "description": "Prepare for operational events and incidents through procedures and testing.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Create runbooks for common operations",
                "Create playbooks for incident response",
                "Practice incident management",
                "Conduct game days"
            ]
        },
        {
            "id": "OPS-PREP-05",
            "question": "How do you manage your infrastructure as code?",
            "description": "Use infrastructure as code to provision and manage your cloud resources.",
            "scan_detectable": True,
            "detection_services": ["CloudFormation", "CDK", "Terraform"],
            "best_practices": [
                "Use CloudFormation or CDK",
                "Store templates in version control",
                "Use change sets before deployment",
                "Implement drift detection"
            ]
        },
        {
            "id": "OPS-PREP-06",
            "question": "How do you implement logging and monitoring?",
            "description": "Implement comprehensive logging and monitoring for your workloads.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch Logs", "CloudTrail", "VPC Flow Logs"],
            "best_practices": [
                "Centralize log collection",
                "Enable CloudTrail in all regions",
                "Enable VPC Flow Logs",
                "Set up log retention policies"
            ]
        },
        {
            "id": "OPS-PREP-07",
            "question": "How do you prepare your team for operations?",
            "description": "Ensure your team has the skills and knowledge to operate your workloads.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Document operating procedures",
                "Conduct training sessions",
                "Define escalation procedures",
                "Establish on-call rotations"
            ]
        },
        {
            "id": "OPS-PREP-08",
            "question": "How do you manage configuration in your workload?",
            "description": "Manage configuration consistently across your environments.",
            "scan_detectable": True,
            "detection_services": ["Systems Manager", "AppConfig", "Secrets Manager"],
            "best_practices": [
                "Use AWS Systems Manager Parameter Store",
                "Use AWS AppConfig for application configuration",
                "Separate configuration from code",
                "Implement configuration validation"
            ]
        },
        {
            "id": "OPS-PREP-09",
            "question": "How do you implement tagging for your resources?",
            "description": "Implement a consistent tagging strategy for cost allocation and operations.",
            "scan_detectable": True,
            "detection_services": ["Tag Editor", "Config", "Resource Groups"],
            "best_practices": [
                "Define a tagging strategy",
                "Enforce tagging with policies",
                "Use tags for cost allocation",
                "Use tags for automation"
            ]
        },
        {
            "id": "OPS-PREP-10",
            "question": "How do you ensure patch management for your workloads?",
            "description": "Keep your systems patched and up to date.",
            "scan_detectable": True,
            "detection_services": ["Systems Manager", "Patch Manager", "Inspector"],
            "best_practices": [
                "Use AWS Systems Manager Patch Manager",
                "Define patch baselines",
                "Schedule maintenance windows",
                "Test patches before deployment"
            ]
        },
        # Operate (OPS-OPER) - 10 questions
        {
            "id": "OPS-OPER-01",
            "question": "How do you understand the health of your workload?",
            "description": "Define, capture, and analyze workload metrics to gain visibility.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "Health Dashboard", "Trusted Advisor"],
            "best_practices": [
                "Identify key performance indicators",
                "Define workload metrics",
                "Collect and analyze metrics",
                "Establish workload baselines",
                "Learn expected patterns of activity"
            ]
        },
        {
            "id": "OPS-OPER-02",
            "question": "How do you understand the health of your operations?",
            "description": "Define, capture, and analyze operations metrics to gain visibility.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "Service Health Dashboard"],
            "best_practices": [
                "Identify key operational indicators",
                "Implement operational health dashboards",
                "Monitor AWS service health",
                "Track operational metrics"
            ]
        },
        {
            "id": "OPS-OPER-03",
            "question": "How do you manage workload and operations events?",
            "description": "Prepare and validate procedures for responding to events.",
            "scan_detectable": True,
            "detection_services": ["EventBridge", "SNS", "CloudWatch Alarms"],
            "best_practices": [
                "Use runbooks for known events",
                "Use playbooks for unknown events",
                "Prioritize events based on impact",
                "Define escalation paths"
            ]
        },
        {
            "id": "OPS-OPER-04",
            "question": "How do you respond to unplanned operational events?",
            "description": "Have processes to respond to unplanned operational events and incidents.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Establish incident management process",
                "Define communication plans",
                "Conduct post-incident analysis",
                "Document lessons learned"
            ]
        },
        {
            "id": "OPS-OPER-05",
            "question": "How do you implement automated alarming and notification?",
            "description": "Use automated alarming to detect and respond to operational issues.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch Alarms", "SNS", "EventBridge"],
            "best_practices": [
                "Create CloudWatch alarms for key metrics",
                "Configure SNS notifications",
                "Use composite alarms",
                "Implement anomaly detection"
            ]
        },
        {
            "id": "OPS-OPER-06",
            "question": "How do you automate operations?",
            "description": "Use automation to perform operations tasks consistently.",
            "scan_detectable": True,
            "detection_services": ["Systems Manager", "Lambda", "Step Functions"],
            "best_practices": [
                "Automate runbook execution",
                "Use Systems Manager Automation",
                "Implement self-healing capabilities",
                "Automate scaling operations"
            ]
        },
        {
            "id": "OPS-OPER-07",
            "question": "How do you manage your deployment pipeline?",
            "description": "Use automated deployment pipelines for consistent deployments.",
            "scan_detectable": True,
            "detection_services": ["CodePipeline", "CodeBuild", "CodeDeploy"],
            "best_practices": [
                "Implement CI/CD pipelines",
                "Use automated testing",
                "Implement deployment gates",
                "Enable rollback capabilities"
            ]
        },
        {
            "id": "OPS-OPER-08",
            "question": "How do you manage your container operations?",
            "description": "Manage container workloads effectively.",
            "scan_detectable": True,
            "detection_services": ["ECS", "EKS", "ECR"],
            "best_practices": [
                "Use managed container services",
                "Implement container image scanning",
                "Use container orchestration",
                "Monitor container health"
            ]
        },
        {
            "id": "OPS-OPER-09",
            "question": "How do you manage serverless operations?",
            "description": "Manage serverless workloads effectively.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "API Gateway", "Step Functions"],
            "best_practices": [
                "Monitor Lambda performance",
                "Implement error handling",
                "Use X-Ray for tracing",
                "Optimize function configuration"
            ]
        },
        {
            "id": "OPS-OPER-10",
            "question": "How do you perform capacity planning?",
            "description": "Plan for capacity to meet demand.",
            "scan_detectable": True,
            "detection_services": ["Compute Optimizer", "Cost Explorer", "Auto Scaling"],
            "best_practices": [
                "Analyze historical usage patterns",
                "Use AWS Compute Optimizer",
                "Implement auto scaling",
                "Plan for peak demand"
            ]
        },
        # Evolve (OPS-EVOLVE) - 7 questions
        {
            "id": "OPS-EVOLVE-01",
            "question": "How do you learn, share, and improve?",
            "description": "Regularly provide time for analysis, learning, and improvements.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Conduct post-incident reviews",
                "Share lessons learned",
                "Dedicate time for improvement",
                "Implement feedback loops"
            ]
        },
        {
            "id": "OPS-EVOLVE-02",
            "question": "How do you conduct post-incident analysis?",
            "description": "Learn from incidents and implement improvements.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Document incident timeline",
                "Identify root causes",
                "Define corrective actions",
                "Track improvement implementation"
            ]
        },
        {
            "id": "OPS-EVOLVE-03",
            "question": "How do you evolve your operations?",
            "description": "Continuously improve your operations based on lessons learned.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Review operational metrics regularly",
                "Identify improvement opportunities",
                "Prioritize improvements",
                "Measure improvement impact"
            ]
        },
        {
            "id": "OPS-EVOLVE-04",
            "question": "How do you implement continuous improvement?",
            "description": "Make continuous improvement part of your culture.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Establish improvement processes",
                "Encourage experimentation",
                "Measure and track improvements",
                "Celebrate successes"
            ]
        },
        {
            "id": "OPS-EVOLVE-05",
            "question": "How do you keep your runbooks and playbooks current?",
            "description": "Maintain operational documentation.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Review documentation regularly",
                "Update after incidents",
                "Version control documentation",
                "Test procedures periodically"
            ]
        },
        {
            "id": "OPS-EVOLVE-06",
            "question": "How do you evaluate new AWS services and features?",
            "description": "Stay current with AWS innovations.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Monitor AWS announcements",
                "Evaluate new services for your workload",
                "Conduct proof of concepts",
                "Plan migrations to new services"
            ]
        },
        {
            "id": "OPS-EVOLVE-07",
            "question": "How do you optimize your operational processes?",
            "description": "Continuously optimize operational efficiency.",
            "scan_detectable": True,
            "detection_services": ["Trusted Advisor", "Well-Architected Tool"],
            "best_practices": [
                "Use AWS Trusted Advisor",
                "Conduct Well-Architected reviews",
                "Benchmark against best practices",
                "Automate manual processes"
            ]
        }
    ],
    
    # ========================================================================
    # SECURITY - 45 Questions
    # ========================================================================
    WAFPillar.SECURITY: [
        # Identity and Access Management (SEC-IAM) - 12 questions
        {
            "id": "SEC-IAM-01",
            "question": "How do you securely operate your workload?",
            "description": "Operating workloads securely includes establishing security practices and protecting against unauthorized access.",
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
            "id": "SEC-IAM-02",
            "question": "How do you manage identities for people and machines?",
            "description": "Strong identity foundation ensures only authorized identities access resources.",
            "scan_detectable": True,
            "detection_services": ["IAM", "Organizations", "IAM Identity Center"],
            "best_practices": [
                "Use IAM Identity Center for workforce identities",
                "Use IAM roles for applications",
                "Implement least privilege access",
                "Regularly review and remove unused permissions"
            ]
        },
        {
            "id": "SEC-IAM-03",
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
            "id": "SEC-IAM-04",
            "question": "How do you secure the AWS account root user?",
            "description": "Protect the root user with strong controls.",
            "scan_detectable": True,
            "detection_services": ["IAM", "Security Hub"],
            "best_practices": [
                "Enable MFA on root account",
                "Don't use root for daily tasks",
                "Remove root access keys",
                "Monitor root account usage"
            ]
        },
        {
            "id": "SEC-IAM-05",
            "question": "How do you enforce MFA?",
            "description": "Require multi-factor authentication for all human users.",
            "scan_detectable": True,
            "detection_services": ["IAM", "IAM Identity Center"],
            "best_practices": [
                "Enable MFA for all IAM users",
                "Use hardware MFA for privileged users",
                "Enforce MFA in IAM policies",
                "Monitor MFA compliance"
            ]
        },
        {
            "id": "SEC-IAM-06",
            "question": "How do you manage IAM policies?",
            "description": "Create and manage IAM policies effectively.",
            "scan_detectable": True,
            "detection_services": ["IAM", "IAM Access Analyzer", "Config"],
            "best_practices": [
                "Use managed policies where possible",
                "Apply least privilege principle",
                "Use policy conditions",
                "Regularly review policies"
            ]
        },
        {
            "id": "SEC-IAM-07",
            "question": "How do you manage cross-account access?",
            "description": "Securely manage access across AWS accounts.",
            "scan_detectable": True,
            "detection_services": ["IAM", "Organizations", "Resource Access Manager"],
            "best_practices": [
                "Use IAM roles for cross-account access",
                "Implement external ID for third parties",
                "Use AWS Organizations SCPs",
                "Audit cross-account access"
            ]
        },
        {
            "id": "SEC-IAM-08",
            "question": "How do you manage service-linked roles?",
            "description": "Understand and manage service-linked roles.",
            "scan_detectable": True,
            "detection_services": ["IAM"],
            "best_practices": [
                "Understand service-linked role permissions",
                "Monitor service-linked role usage",
                "Review service-linked role policies",
                "Document service-linked roles"
            ]
        },
        {
            "id": "SEC-IAM-09",
            "question": "How do you implement identity federation?",
            "description": "Federate identities from external identity providers.",
            "scan_detectable": True,
            "detection_services": ["IAM Identity Center", "Cognito", "IAM"],
            "best_practices": [
                "Use SAML 2.0 or OIDC federation",
                "Implement just-in-time provisioning",
                "Map external groups to IAM roles",
                "Audit federated access"
            ]
        },
        {
            "id": "SEC-IAM-10",
            "question": "How do you manage temporary credentials?",
            "description": "Use temporary credentials instead of long-term credentials.",
            "scan_detectable": True,
            "detection_services": ["IAM", "STS"],
            "best_practices": [
                "Use IAM roles instead of IAM users",
                "Rotate credentials regularly",
                "Set appropriate session durations",
                "Monitor credential usage"
            ]
        },
        {
            "id": "SEC-IAM-11",
            "question": "How do you manage service accounts?",
            "description": "Securely manage identities for services and applications.",
            "scan_detectable": True,
            "detection_services": ["IAM", "Secrets Manager"],
            "best_practices": [
                "Use IAM roles for EC2",
                "Use IRSA for EKS",
                "Use task roles for ECS",
                "Avoid long-term credentials"
            ]
        },
        {
            "id": "SEC-IAM-12",
            "question": "How do you analyze and validate IAM policies?",
            "description": "Validate IAM policies before deployment.",
            "scan_detectable": True,
            "detection_services": ["IAM Access Analyzer", "IAM Policy Simulator"],
            "best_practices": [
                "Use IAM Access Analyzer",
                "Use IAM Policy Simulator",
                "Validate policies in CI/CD",
                "Review policy findings regularly"
            ]
        },
        # Detection (SEC-DET) - 10 questions
        {
            "id": "SEC-DET-01",
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
            "id": "SEC-DET-02",
            "question": "How do you enable AWS CloudTrail?",
            "description": "Enable CloudTrail for API activity logging.",
            "scan_detectable": True,
            "detection_services": ["CloudTrail"],
            "best_practices": [
                "Enable CloudTrail in all regions",
                "Enable CloudTrail log file validation",
                "Store logs in secure S3 bucket",
                "Enable CloudTrail Insights"
            ]
        },
        {
            "id": "SEC-DET-03",
            "question": "How do you use Amazon GuardDuty?",
            "description": "Enable GuardDuty for threat detection.",
            "scan_detectable": True,
            "detection_services": ["GuardDuty"],
            "best_practices": [
                "Enable GuardDuty in all accounts",
                "Enable all protection plans",
                "Configure findings export",
                "Integrate with Security Hub"
            ]
        },
        {
            "id": "SEC-DET-04",
            "question": "How do you use AWS Security Hub?",
            "description": "Aggregate and prioritize security findings.",
            "scan_detectable": True,
            "detection_services": ["Security Hub"],
            "best_practices": [
                "Enable Security Hub in all accounts",
                "Enable security standards",
                "Configure custom insights",
                "Automate remediation"
            ]
        },
        {
            "id": "SEC-DET-05",
            "question": "How do you implement centralized logging?",
            "description": "Centralize logs for analysis and retention.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch Logs", "S3", "OpenSearch"],
            "best_practices": [
                "Use centralized logging account",
                "Aggregate logs from all accounts",
                "Implement log retention policies",
                "Enable log analysis capabilities"
            ]
        },
        {
            "id": "SEC-DET-06",
            "question": "How do you monitor for security anomalies?",
            "description": "Detect anomalous behavior in your environment.",
            "scan_detectable": True,
            "detection_services": ["GuardDuty", "CloudWatch Anomaly Detection", "Macie"],
            "best_practices": [
                "Enable GuardDuty anomaly detection",
                "Use CloudWatch anomaly detection",
                "Enable Macie for data discovery",
                "Implement SIEM integration"
            ]
        },
        {
            "id": "SEC-DET-07",
            "question": "How do you respond to security findings?",
            "description": "Implement automated response to security findings.",
            "scan_detectable": True,
            "detection_services": ["Security Hub", "EventBridge", "Lambda"],
            "best_practices": [
                "Automate finding remediation",
                "Define response playbooks",
                "Implement finding notifications",
                "Track finding resolution"
            ]
        },
        {
            "id": "SEC-DET-08",
            "question": "How do you use AWS Config for compliance?",
            "description": "Use AWS Config rules for compliance monitoring.",
            "scan_detectable": True,
            "detection_services": ["Config"],
            "best_practices": [
                "Enable AWS Config in all accounts",
                "Deploy conformance packs",
                "Implement auto-remediation",
                "Track compliance over time"
            ]
        },
        {
            "id": "SEC-DET-09",
            "question": "How do you implement vulnerability management?",
            "description": "Identify and remediate vulnerabilities.",
            "scan_detectable": True,
            "detection_services": ["Inspector", "ECR", "Systems Manager"],
            "best_practices": [
                "Enable Amazon Inspector",
                "Scan container images",
                "Use Systems Manager Patch Manager",
                "Track vulnerability remediation"
            ]
        },
        {
            "id": "SEC-DET-10",
            "question": "How do you implement security monitoring dashboards?",
            "description": "Visualize security posture.",
            "scan_detectable": True,
            "detection_services": ["Security Hub", "CloudWatch", "QuickSight"],
            "best_practices": [
                "Create Security Hub dashboards",
                "Track security metrics",
                "Implement executive reporting",
                "Monitor security KPIs"
            ]
        },
        # Infrastructure Protection (SEC-INFRA) - 10 questions
        {
            "id": "SEC-INFRA-01",
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
            "id": "SEC-INFRA-02",
            "question": "How do you implement VPC security?",
            "description": "Secure your VPC infrastructure.",
            "scan_detectable": True,
            "detection_services": ["VPC", "Security Groups", "NACLs"],
            "best_practices": [
                "Use security groups effectively",
                "Implement network ACLs",
                "Enable VPC Flow Logs",
                "Use VPC endpoints"
            ]
        },
        {
            "id": "SEC-INFRA-03",
            "question": "How do you implement security groups?",
            "description": "Configure security groups for least privilege access.",
            "scan_detectable": True,
            "detection_services": ["EC2", "VPC"],
            "best_practices": [
                "Follow least privilege principle",
                "Avoid 0.0.0.0/0 rules",
                "Use security group references",
                "Document security group rules"
            ]
        },
        {
            "id": "SEC-INFRA-04",
            "question": "How do you use AWS WAF?",
            "description": "Protect web applications with AWS WAF.",
            "scan_detectable": True,
            "detection_services": ["WAF", "CloudFront", "ALB"],
            "best_practices": [
                "Enable AWS managed rules",
                "Implement rate limiting",
                "Block known bad actors",
                "Monitor WAF metrics"
            ]
        },
        {
            "id": "SEC-INFRA-05",
            "question": "How do you protect against DDoS attacks?",
            "description": "Implement DDoS protection.",
            "scan_detectable": True,
            "detection_services": ["Shield", "CloudFront", "Route 53"],
            "best_practices": [
                "Enable AWS Shield",
                "Use CloudFront for edge protection",
                "Implement rate limiting",
                "Plan for attack response"
            ]
        },
        {
            "id": "SEC-INFRA-06",
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
            "id": "SEC-INFRA-07",
            "question": "How do you implement endpoint protection?",
            "description": "Protect EC2 instances and endpoints.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Systems Manager", "Inspector"],
            "best_practices": [
                "Use IMDSv2",
                "Implement endpoint detection",
                "Enable detailed monitoring",
                "Use Systems Manager for management"
            ]
        },
        {
            "id": "SEC-INFRA-08",
            "question": "How do you secure your container infrastructure?",
            "description": "Secure container workloads.",
            "scan_detectable": True,
            "detection_services": ["ECS", "EKS", "ECR", "Inspector"],
            "best_practices": [
                "Scan container images",
                "Use minimal base images",
                "Implement pod security",
                "Enable container insights"
            ]
        },
        {
            "id": "SEC-INFRA-09",
            "question": "How do you secure serverless workloads?",
            "description": "Secure Lambda functions and serverless applications.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "API Gateway"],
            "best_practices": [
                "Use least privilege execution roles",
                "Enable VPC connectivity when needed",
                "Implement input validation",
                "Monitor function behavior"
            ]
        },
        {
            "id": "SEC-INFRA-10",
            "question": "How do you implement network segmentation?",
            "description": "Segment your network for security.",
            "scan_detectable": True,
            "detection_services": ["VPC", "Transit Gateway", "Network Firewall"],
            "best_practices": [
                "Use multiple VPCs",
                "Implement subnet tiers",
                "Use Transit Gateway for connectivity",
                "Enable Network Firewall"
            ]
        },
        # Data Protection (SEC-DATA) - 10 questions
        {
            "id": "SEC-DATA-01",
            "question": "How do you classify your data?",
            "description": "Classification provides a way to categorize data based on criticality.",
            "scan_detectable": True,
            "detection_services": ["Macie"],
            "best_practices": [
                "Identify data within your workload",
                "Define data protection controls",
                "Automate identification and classification",
                "Define data lifecycle management"
            ]
        },
        {
            "id": "SEC-DATA-02",
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
            "id": "SEC-DATA-03",
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
            "id": "SEC-DATA-04",
            "question": "How do you manage encryption keys?",
            "description": "Manage encryption keys securely with AWS KMS.",
            "scan_detectable": True,
            "detection_services": ["KMS", "CloudHSM"],
            "best_practices": [
                "Use AWS KMS for key management",
                "Implement key rotation",
                "Define key policies",
                "Use separate keys for different data"
            ]
        },
        {
            "id": "SEC-DATA-05",
            "question": "How do you manage secrets?",
            "description": "Securely store and manage secrets.",
            "scan_detectable": True,
            "detection_services": ["Secrets Manager", "Parameter Store"],
            "best_practices": [
                "Use Secrets Manager for credentials",
                "Enable automatic rotation",
                "Audit secret access",
                "Never hardcode secrets"
            ]
        },
        {
            "id": "SEC-DATA-06",
            "question": "How do you implement S3 security?",
            "description": "Secure your S3 buckets.",
            "scan_detectable": True,
            "detection_services": ["S3", "Macie", "IAM Access Analyzer"],
            "best_practices": [
                "Block public access",
                "Enable server-side encryption",
                "Use bucket policies",
                "Enable versioning and logging"
            ]
        },
        {
            "id": "SEC-DATA-07",
            "question": "How do you implement database security?",
            "description": "Secure your database instances.",
            "scan_detectable": True,
            "detection_services": ["RDS", "DynamoDB", "Aurora"],
            "best_practices": [
                "Enable encryption at rest",
                "Use SSL/TLS connections",
                "Implement IAM authentication",
                "Enable audit logging"
            ]
        },
        {
            "id": "SEC-DATA-08",
            "question": "How do you implement data backup and recovery?",
            "description": "Implement backup strategies for data protection.",
            "scan_detectable": True,
            "detection_services": ["Backup", "S3", "RDS"],
            "best_practices": [
                "Enable automated backups",
                "Use AWS Backup",
                "Implement cross-region backups",
                "Test recovery procedures"
            ]
        },
        {
            "id": "SEC-DATA-09",
            "question": "How do you implement data retention?",
            "description": "Implement data lifecycle management.",
            "scan_detectable": True,
            "detection_services": ["S3", "Glacier", "DynamoDB"],
            "best_practices": [
                "Define retention policies",
                "Use S3 Lifecycle rules",
                "Implement data archiving",
                "Automate data deletion"
            ]
        },
        {
            "id": "SEC-DATA-10",
            "question": "How do you protect sensitive data?",
            "description": "Implement additional controls for sensitive data.",
            "scan_detectable": True,
            "detection_services": ["Macie", "KMS", "CloudHSM"],
            "best_practices": [
                "Use Amazon Macie for discovery",
                "Implement data masking",
                "Enable encryption with CMKs",
                "Implement access logging"
            ]
        },
        # Incident Response (SEC-IR) - 3 questions
        {
            "id": "SEC-IR-01",
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
        },
        {
            "id": "SEC-IR-02",
            "question": "How do you prepare for incident response?",
            "description": "Prepare your organization for security incidents.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Define incident response plan",
                "Conduct tabletop exercises",
                "Prepare forensic environment",
                "Define communication procedures"
            ]
        },
        {
            "id": "SEC-IR-03",
            "question": "How do you automate incident response?",
            "description": "Automate response actions.",
            "scan_detectable": True,
            "detection_services": ["EventBridge", "Lambda", "Step Functions"],
            "best_practices": [
                "Automate containment actions",
                "Implement automated notification",
                "Use Step Functions for orchestration",
                "Document automated responses"
            ]
        }
    ],

    # ========================================================================
    # RELIABILITY - 35 Questions
    # ========================================================================
    WAFPillar.RELIABILITY: [
        # Foundations (REL-FOUND) - 10 questions
        {
            "id": "REL-FOUND-01",
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
            "id": "REL-FOUND-02",
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
            "id": "REL-FOUND-03",
            "question": "How do you implement multi-AZ deployments?",
            "description": "Deploy across multiple Availability Zones for high availability.",
            "scan_detectable": True,
            "detection_services": ["EC2", "RDS", "ELB"],
            "best_practices": [
                "Deploy to multiple AZs",
                "Use managed multi-AZ services",
                "Implement cross-AZ load balancing",
                "Test AZ failover"
            ]
        },
        {
            "id": "REL-FOUND-04",
            "question": "How do you implement multi-region strategies?",
            "description": "Plan for multi-region deployments.",
            "scan_detectable": True,
            "detection_services": ["Route 53", "S3", "DynamoDB"],
            "best_practices": [
                "Define multi-region architecture",
                "Implement data replication",
                "Use Route 53 for DNS failover",
                "Test regional failover"
            ]
        },
        {
            "id": "REL-FOUND-05",
            "question": "How do you manage AWS accounts and organizational structure?",
            "description": "Organize AWS accounts for reliability.",
            "scan_detectable": True,
            "detection_services": ["Organizations", "Control Tower"],
            "best_practices": [
                "Use multiple accounts",
                "Implement account vending",
                "Define organizational structure",
                "Manage accounts centrally"
            ]
        },
        {
            "id": "REL-FOUND-06",
            "question": "How do you manage your AWS quotas?",
            "description": "Monitor and manage service quotas.",
            "scan_detectable": True,
            "detection_services": ["Service Quotas", "CloudWatch"],
            "best_practices": [
                "Monitor quota usage",
                "Request quota increases proactively",
                "Implement quota alarms",
                "Plan for quota limits"
            ]
        },
        {
            "id": "REL-FOUND-07",
            "question": "How do you implement VPC design for reliability?",
            "description": "Design VPCs for high availability.",
            "scan_detectable": True,
            "detection_services": ["VPC"],
            "best_practices": [
                "Use multiple subnets per AZ",
                "Plan IP address space",
                "Implement VPC peering or Transit Gateway",
                "Use VPC endpoints"
            ]
        },
        {
            "id": "REL-FOUND-08",
            "question": "How do you implement DNS reliability?",
            "description": "Ensure DNS is highly available.",
            "scan_detectable": True,
            "detection_services": ["Route 53"],
            "best_practices": [
                "Use Route 53 for DNS",
                "Implement health checks",
                "Use DNS failover",
                "Configure appropriate TTLs"
            ]
        },
        {
            "id": "REL-FOUND-09",
            "question": "How do you implement network connectivity?",
            "description": "Ensure reliable network connectivity.",
            "scan_detectable": True,
            "detection_services": ["Direct Connect", "VPN", "Transit Gateway"],
            "best_practices": [
                "Use redundant connections",
                "Implement multiple VPN tunnels",
                "Use Direct Connect with backup",
                "Monitor network connectivity"
            ]
        },
        {
            "id": "REL-FOUND-10",
            "question": "How do you manage IP addresses?",
            "description": "Plan and manage IP address allocation.",
            "scan_detectable": True,
            "detection_services": ["VPC", "IPAM"],
            "best_practices": [
                "Use AWS IPAM",
                "Plan for growth",
                "Avoid IP conflicts",
                "Document IP allocations"
            ]
        },
        # Workload Architecture (REL-ARCH) - 10 questions
        {
            "id": "REL-ARCH-01",
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
            "id": "REL-ARCH-02",
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
            "id": "REL-ARCH-03",
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
            "id": "REL-ARCH-04",
            "question": "How do you implement load balancing?",
            "description": "Distribute load across resources.",
            "scan_detectable": True,
            "detection_services": ["ELB", "ALB", "NLB"],
            "best_practices": [
                "Use Application Load Balancer",
                "Implement health checks",
                "Use cross-zone load balancing",
                "Configure connection draining"
            ]
        },
        {
            "id": "REL-ARCH-05",
            "question": "How do you implement auto scaling?",
            "description": "Scale resources automatically based on demand.",
            "scan_detectable": True,
            "detection_services": ["Auto Scaling", "ECS", "EKS"],
            "best_practices": [
                "Define scaling policies",
                "Use target tracking scaling",
                "Implement predictive scaling",
                "Test scaling behavior"
            ]
        },
        {
            "id": "REL-ARCH-06",
            "question": "How do you implement circuit breaker patterns?",
            "description": "Prevent cascading failures.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Implement circuit breakers",
                "Use bulkhead patterns",
                "Implement timeouts",
                "Handle partial failures"
            ]
        },
        {
            "id": "REL-ARCH-07",
            "question": "How do you implement queue-based architectures?",
            "description": "Decouple components with queues.",
            "scan_detectable": True,
            "detection_services": ["SQS", "SNS", "EventBridge"],
            "best_practices": [
                "Use SQS for decoupling",
                "Implement dead letter queues",
                "Handle message failures",
                "Monitor queue depth"
            ]
        },
        {
            "id": "REL-ARCH-08",
            "question": "How do you implement event-driven architectures?",
            "description": "Build event-driven systems.",
            "scan_detectable": True,
            "detection_services": ["EventBridge", "SNS", "Lambda"],
            "best_practices": [
                "Use EventBridge for events",
                "Implement event replay",
                "Handle event failures",
                "Design for idempotency"
            ]
        },
        {
            "id": "REL-ARCH-09",
            "question": "How do you implement caching?",
            "description": "Use caching to improve reliability and performance.",
            "scan_detectable": True,
            "detection_services": ["ElastiCache", "CloudFront", "DAX"],
            "best_practices": [
                "Implement caching layers",
                "Use ElastiCache for in-memory caching",
                "Use CloudFront for edge caching",
                "Implement cache invalidation"
            ]
        },
        {
            "id": "REL-ARCH-10",
            "question": "How do you implement database reliability?",
            "description": "Design databases for high availability.",
            "scan_detectable": True,
            "detection_services": ["RDS", "Aurora", "DynamoDB"],
            "best_practices": [
                "Use Multi-AZ deployments",
                "Implement read replicas",
                "Use Aurora for high availability",
                "Enable automated backups"
            ]
        },
        # Change Management (REL-CHANGE) - 8 questions
        {
            "id": "REL-CHANGE-01",
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
            "id": "REL-CHANGE-02",
            "question": "How do you design your workload to adapt to changes in demand?",
            "description": "Scale resources to maintain availability during demand changes.",
            "scan_detectable": True,
            "detection_services": ["Auto Scaling", "ECS", "Lambda"],
            "best_practices": [
                "Use automation when obtaining or scaling resources",
                "Obtain resources upon detection of impairment",
                "Obtain resources upon detection of more demand"
            ]
        },
        {
            "id": "REL-CHANGE-03",
            "question": "How do you implement change management?",
            "description": "Control changes to prevent failures.",
            "scan_detectable": True,
            "detection_services": ["CloudFormation", "CodePipeline", "Config"],
            "best_practices": [
                "Use infrastructure as code",
                "Implement change control process",
                "Test changes before deployment",
                "Enable change tracking"
            ]
        },
        {
            "id": "REL-CHANGE-04",
            "question": "How do you deploy changes?",
            "description": "Deploy changes safely.",
            "scan_detectable": True,
            "detection_services": ["CodeDeploy", "CodePipeline"],
            "best_practices": [
                "Use blue/green deployments",
                "Use canary deployments",
                "Implement feature flags",
                "Enable quick rollback"
            ]
        },
        {
            "id": "REL-CHANGE-05",
            "question": "How do you test reliability?",
            "description": "Test for reliability.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Implement chaos engineering",
                "Conduct game days",
                "Test failure scenarios",
                "Validate recovery procedures"
            ]
        },
        {
            "id": "REL-CHANGE-06",
            "question": "How do you manage configuration changes?",
            "description": "Manage configuration consistently.",
            "scan_detectable": True,
            "detection_services": ["Config", "Systems Manager", "AppConfig"],
            "best_practices": [
                "Use AWS Config rules",
                "Implement configuration validation",
                "Track configuration changes",
                "Automate configuration management"
            ]
        },
        {
            "id": "REL-CHANGE-07",
            "question": "How do you test your disaster recovery procedures?",
            "description": "Validate disaster recovery.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Define RTO and RPO",
                "Document DR procedures",
                "Conduct DR tests regularly",
                "Measure recovery metrics"
            ]
        },
        {
            "id": "REL-CHANGE-08",
            "question": "How do you manage maintenance windows?",
            "description": "Plan and execute maintenance.",
            "scan_detectable": True,
            "detection_services": ["Systems Manager", "RDS"],
            "best_practices": [
                "Define maintenance windows",
                "Communicate maintenance schedule",
                "Minimize maintenance impact",
                "Automate maintenance tasks"
            ]
        },
        # Failure Management (REL-FAIL) - 7 questions
        {
            "id": "REL-FAIL-01",
            "question": "How do you back up data?",
            "description": "Back up data, applications, and configuration to meet RTO and RPO.",
            "scan_detectable": True,
            "detection_services": ["Backup", "S3", "RDS", "DynamoDB"],
            "best_practices": [
                "Identify all data that needs backup",
                "Automate backups",
                "Perform periodic recovery testing",
                "Secure and encrypt backups"
            ]
        },
        {
            "id": "REL-FAIL-02",
            "question": "How do you implement fault isolation?",
            "description": "Isolate failures to limit impact.",
            "scan_detectable": True,
            "detection_services": ["VPC", "Organizations"],
            "best_practices": [
                "Use multiple Availability Zones",
                "Use multiple AWS Regions",
                "Implement bulkhead patterns",
                "Use shuffle sharding"
            ]
        },
        {
            "id": "REL-FAIL-03",
            "question": "How do you design for recovery?",
            "description": "Plan for recovery from failures.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Define recovery objectives",
                "Design for automatic recovery",
                "Test recovery procedures",
                "Document recovery runbooks"
            ]
        },
        {
            "id": "REL-FAIL-04",
            "question": "How do you implement disaster recovery?",
            "description": "Implement disaster recovery strategies.",
            "scan_detectable": True,
            "detection_services": ["Backup", "DRS", "S3"],
            "best_practices": [
                "Define DR strategy",
                "Implement cross-region replication",
                "Use AWS Elastic Disaster Recovery",
                "Test DR procedures"
            ]
        },
        {
            "id": "REL-FAIL-05",
            "question": "How do you test failure scenarios?",
            "description": "Test how your workload handles failures.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Implement chaos engineering",
                "Test component failures",
                "Test dependency failures",
                "Measure blast radius"
            ]
        },
        {
            "id": "REL-FAIL-06",
            "question": "How do you implement automated recovery?",
            "description": "Automate recovery from failures.",
            "scan_detectable": True,
            "detection_services": ["Auto Scaling", "Lambda", "Systems Manager"],
            "best_practices": [
                "Use health checks",
                "Implement auto-healing",
                "Automate failover",
                "Use self-healing infrastructure"
            ]
        },
        {
            "id": "REL-FAIL-07",
            "question": "How do you manage incidents?",
            "description": "Manage incidents effectively.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Define incident process",
                "Implement incident tracking",
                "Conduct post-incident reviews",
                "Learn from incidents"
            ]
        }
    ],

    # ========================================================================
    # PERFORMANCE EFFICIENCY - 30 Questions
    # ========================================================================
    WAFPillar.PERFORMANCE_EFFICIENCY: [
        # Selection (PERF-SEL) - 12 questions
        {
            "id": "PERF-SEL-01",
            "question": "How do you select the best performing architecture?",
            "description": "Use data to select the best performing architecture.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Understand available services and resources",
                "Define a process for architectural choices",
                "Factor in cost requirements",
                "Use benchmarking"
            ]
        },
        {
            "id": "PERF-SEL-02",
            "question": "How do you select your compute solution?",
            "description": "Select compute resources that meet your requirements.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Lambda", "ECS", "Compute Optimizer"],
            "best_practices": [
                "Evaluate available compute options",
                "Use appropriate instance types",
                "Consider serverless options",
                "Right-size compute resources"
            ]
        },
        {
            "id": "PERF-SEL-03",
            "question": "How do you select your storage solution?",
            "description": "Select storage resources that meet your requirements.",
            "scan_detectable": True,
            "detection_services": ["S3", "EBS", "EFS", "FSx"],
            "best_practices": [
                "Understand storage characteristics",
                "Match storage to access patterns",
                "Use appropriate storage tiers",
                "Optimize storage configuration"
            ]
        },
        {
            "id": "PERF-SEL-04",
            "question": "How do you select your database solution?",
            "description": "Select database resources that meet your requirements.",
            "scan_detectable": True,
            "detection_services": ["RDS", "DynamoDB", "Aurora", "ElastiCache"],
            "best_practices": [
                "Understand data characteristics",
                "Choose appropriate database type",
                "Optimize database configuration",
                "Use caching where appropriate"
            ]
        },
        {
            "id": "PERF-SEL-05",
            "question": "How do you select your network solution?",
            "description": "Select network resources that meet your requirements.",
            "scan_detectable": True,
            "detection_services": ["VPC", "CloudFront", "Global Accelerator"],
            "best_practices": [
                "Understand network requirements",
                "Use appropriate network services",
                "Optimize network configuration",
                "Use edge locations"
            ]
        },
        {
            "id": "PERF-SEL-06",
            "question": "How do you optimize EC2 instance selection?",
            "description": "Choose optimal EC2 instances.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Compute Optimizer"],
            "best_practices": [
                "Use current generation instances",
                "Match instance type to workload",
                "Use Graviton processors where suitable",
                "Consider spot instances"
            ]
        },
        {
            "id": "PERF-SEL-07",
            "question": "How do you optimize container performance?",
            "description": "Optimize container resource allocation.",
            "scan_detectable": True,
            "detection_services": ["ECS", "EKS", "Fargate"],
            "best_practices": [
                "Right-size container resources",
                "Use Fargate for serverless containers",
                "Optimize container images",
                "Implement horizontal scaling"
            ]
        },
        {
            "id": "PERF-SEL-08",
            "question": "How do you optimize Lambda performance?",
            "description": "Optimize Lambda function performance.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "X-Ray"],
            "best_practices": [
                "Optimize memory allocation",
                "Minimize cold starts",
                "Use provisioned concurrency",
                "Optimize function code"
            ]
        },
        {
            "id": "PERF-SEL-09",
            "question": "How do you optimize EBS performance?",
            "description": "Optimize EBS volume performance.",
            "scan_detectable": True,
            "detection_services": ["EBS"],
            "best_practices": [
                "Choose appropriate volume type",
                "Use gp3 for flexibility",
                "Use io2 for high IOPS",
                "Monitor volume performance"
            ]
        },
        {
            "id": "PERF-SEL-10",
            "question": "How do you optimize S3 performance?",
            "description": "Optimize S3 performance for your workload.",
            "scan_detectable": True,
            "detection_services": ["S3"],
            "best_practices": [
                "Use S3 Transfer Acceleration",
                "Use multipart uploads",
                "Optimize object key naming",
                "Use S3 Intelligent Tiering"
            ]
        },
        {
            "id": "PERF-SEL-11",
            "question": "How do you optimize database performance?",
            "description": "Optimize database queries and configuration.",
            "scan_detectable": True,
            "detection_services": ["RDS", "Performance Insights"],
            "best_practices": [
                "Use RDS Performance Insights",
                "Implement query optimization",
                "Use appropriate indexes",
                "Configure database parameters"
            ]
        },
        {
            "id": "PERF-SEL-12",
            "question": "How do you implement caching for performance?",
            "description": "Use caching to improve performance.",
            "scan_detectable": True,
            "detection_services": ["ElastiCache", "CloudFront", "DAX"],
            "best_practices": [
                "Identify caching opportunities",
                "Use ElastiCache for data caching",
                "Use CloudFront for content caching",
                "Implement cache invalidation strategies"
            ]
        },
        # Review (PERF-REV) - 6 questions
        {
            "id": "PERF-REV-01",
            "question": "How do you review your architecture for performance?",
            "description": "Regularly review your architecture.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Conduct regular reviews",
                "Benchmark against targets",
                "Use AWS Well-Architected Tool",
                "Review new services"
            ]
        },
        {
            "id": "PERF-REV-02",
            "question": "How do you use load testing?",
            "description": "Test performance under load.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Implement load testing",
                "Test at expected scale",
                "Test failure scenarios",
                "Use realistic test data"
            ]
        },
        {
            "id": "PERF-REV-03",
            "question": "How do you use performance benchmarks?",
            "description": "Benchmark to understand performance.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Define performance baselines",
                "Compare against benchmarks",
                "Track performance trends",
                "Act on benchmark results"
            ]
        },
        {
            "id": "PERF-REV-04",
            "question": "How do you evaluate new services?",
            "description": "Evaluate new AWS services for performance improvements.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Stay informed about new services",
                "Evaluate services for your workload",
                "Conduct proof of concepts",
                "Plan migrations"
            ]
        },
        {
            "id": "PERF-REV-05",
            "question": "How do you optimize over time?",
            "description": "Continuously optimize performance.",
            "scan_detectable": True,
            "detection_services": ["Compute Optimizer", "Trusted Advisor"],
            "best_practices": [
                "Review optimization recommendations",
                "Implement improvements",
                "Measure impact",
                "Continue optimization cycle"
            ]
        },
        {
            "id": "PERF-REV-06",
            "question": "How do you manage technical debt?",
            "description": "Address performance-related technical debt.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Track technical debt",
                "Prioritize improvements",
                "Allocate time for optimization",
                "Measure debt reduction"
            ]
        },
        # Monitoring (PERF-MON) - 8 questions
        {
            "id": "PERF-MON-01",
            "question": "How do you monitor your resources?",
            "description": "Monitor resources to ensure they perform as expected.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "X-Ray"],
            "best_practices": [
                "Record performance-related metrics",
                "Analyze metrics when events occur",
                "Establish baselines",
                "Define and monitor alarms"
            ]
        },
        {
            "id": "PERF-MON-02",
            "question": "How do you monitor application performance?",
            "description": "Monitor application-level performance.",
            "scan_detectable": True,
            "detection_services": ["X-Ray", "CloudWatch", "Application Insights"],
            "best_practices": [
                "Implement application tracing",
                "Monitor application metrics",
                "Use real user monitoring",
                "Implement synthetic monitoring"
            ]
        },
        {
            "id": "PERF-MON-03",
            "question": "How do you implement distributed tracing?",
            "description": "Trace requests across services.",
            "scan_detectable": True,
            "detection_services": ["X-Ray"],
            "best_practices": [
                "Enable AWS X-Ray",
                "Instrument all services",
                "Analyze trace data",
                "Identify bottlenecks"
            ]
        },
        {
            "id": "PERF-MON-04",
            "question": "How do you set up performance alarms?",
            "description": "Alert on performance issues.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch"],
            "best_practices": [
                "Define performance thresholds",
                "Create CloudWatch alarms",
                "Use anomaly detection",
                "Implement notification workflows"
            ]
        },
        {
            "id": "PERF-MON-05",
            "question": "How do you create performance dashboards?",
            "description": "Visualize performance metrics.",
            "scan_detectable": True,
            "detection_services": ["CloudWatch", "Managed Grafana"],
            "best_practices": [
                "Create CloudWatch dashboards",
                "Display key metrics",
                "Share dashboards with teams",
                "Update dashboards regularly"
            ]
        },
        {
            "id": "PERF-MON-06",
            "question": "How do you monitor network performance?",
            "description": "Monitor network-level performance.",
            "scan_detectable": True,
            "detection_services": ["VPC", "CloudWatch"],
            "best_practices": [
                "Monitor network throughput",
                "Track latency metrics",
                "Use VPC Flow Logs",
                "Analyze network patterns"
            ]
        },
        {
            "id": "PERF-MON-07",
            "question": "How do you monitor storage performance?",
            "description": "Monitor storage performance.",
            "scan_detectable": True,
            "detection_services": ["EBS", "S3", "CloudWatch"],
            "best_practices": [
                "Monitor IOPS and throughput",
                "Track latency",
                "Set up volume alerts",
                "Analyze storage patterns"
            ]
        },
        {
            "id": "PERF-MON-08",
            "question": "How do you monitor database performance?",
            "description": "Monitor database performance.",
            "scan_detectable": True,
            "detection_services": ["RDS", "Performance Insights"],
            "best_practices": [
                "Use Performance Insights",
                "Monitor query performance",
                "Track connection metrics",
                "Set up database alerts"
            ]
        },
        # Tradeoffs (PERF-TRADE) - 4 questions
        {
            "id": "PERF-TRADE-01",
            "question": "How do you use tradeoffs to improve performance?",
            "description": "Understand and make tradeoffs.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Understand tradeoff impacts",
                "Consider consistency vs. availability",
                "Balance cost vs. performance",
                "Document tradeoff decisions"
            ]
        },
        {
            "id": "PERF-TRADE-02",
            "question": "How do you use caching strategically?",
            "description": "Use caching to trade storage for speed.",
            "scan_detectable": True,
            "detection_services": ["CloudFront", "ElastiCache"],
            "best_practices": [
                "Cache at multiple layers",
                "Define cache policies",
                "Handle cache invalidation",
                "Monitor cache effectiveness"
            ]
        },
        {
            "id": "PERF-TRADE-03",
            "question": "How do you use read replicas?",
            "description": "Use replicas to scale reads.",
            "scan_detectable": True,
            "detection_services": ["RDS", "Aurora", "DynamoDB"],
            "best_practices": [
                "Implement read replicas",
                "Route read traffic",
                "Monitor replica lag",
                "Plan for failover"
            ]
        },
        {
            "id": "PERF-TRADE-04",
            "question": "How do you use edge services?",
            "description": "Use edge services for better performance.",
            "scan_detectable": True,
            "detection_services": ["CloudFront", "Global Accelerator", "Lambda@Edge"],
            "best_practices": [
                "Use CloudFront for content",
                "Use Global Accelerator for applications",
                "Implement Lambda@Edge",
                "Monitor edge performance"
            ]
        }
    ],

    # ========================================================================
    # COST OPTIMIZATION - 30 Questions
    # ========================================================================
    WAFPillar.COST_OPTIMIZATION: [
        # Cloud Financial Management (COST-CFM) - 8 questions
        {
            "id": "COST-CFM-01",
            "question": "How do you implement cloud financial management?",
            "description": "Implement cloud financial management capabilities.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Establish a cloud center of excellence",
                "Establish a partnership between finance and technology",
                "Establish cloud budgets and forecasts",
                "Implement cost awareness in your processes"
            ]
        },
        {
            "id": "COST-CFM-02",
            "question": "How do you govern usage?",
            "description": "Govern cloud usage to control costs.",
            "scan_detectable": True,
            "detection_services": ["Organizations", "Budgets", "Control Tower"],
            "best_practices": [
                "Develop policies based on organization requirements",
                "Implement goals and targets",
                "Implement an account structure",
                "Implement controls"
            ]
        },
        {
            "id": "COST-CFM-03",
            "question": "How do you track costs?",
            "description": "Track and report on costs.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Cost and Usage Report"],
            "best_practices": [
                "Configure detailed cost tracking",
                "Use Cost Explorer",
                "Enable Cost and Usage Report",
                "Implement cost allocation tags"
            ]
        },
        {
            "id": "COST-CFM-04",
            "question": "How do you allocate costs?",
            "description": "Allocate costs to business units.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Cost and Usage Report"],
            "best_practices": [
                "Define cost allocation strategy",
                "Use cost allocation tags",
                "Implement chargeback or showback",
                "Track costs by business unit"
            ]
        },
        {
            "id": "COST-CFM-05",
            "question": "How do you set up AWS Budgets?",
            "description": "Use budgets to track and control costs.",
            "scan_detectable": True,
            "detection_services": ["Budgets"],
            "best_practices": [
                "Create cost budgets",
                "Create usage budgets",
                "Set up budget alerts",
                "Use budget actions"
            ]
        },
        {
            "id": "COST-CFM-06",
            "question": "How do you forecast costs?",
            "description": "Forecast future costs.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer"],
            "best_practices": [
                "Use Cost Explorer forecasting",
                "Consider growth patterns",
                "Plan for committed usage",
                "Update forecasts regularly"
            ]
        },
        {
            "id": "COST-CFM-07",
            "question": "How do you implement tagging for cost allocation?",
            "description": "Use tags for cost tracking.",
            "scan_detectable": True,
            "detection_services": ["Tag Editor", "Config"],
            "best_practices": [
                "Define tagging strategy",
                "Activate cost allocation tags",
                "Enforce tagging with policies",
                "Report on tagged resources"
            ]
        },
        {
            "id": "COST-CFM-08",
            "question": "How do you educate teams on cost management?",
            "description": "Build cost awareness in teams.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Train teams on cost management",
                "Share cost reports",
                "Establish cost review meetings",
                "Recognize cost optimization efforts"
            ]
        },
        # Expenditure Awareness (COST-AWARE) - 8 questions
        {
            "id": "COST-AWARE-01",
            "question": "How do you monitor your costs?",
            "description": "Monitor and analyze costs.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "CloudWatch"],
            "best_practices": [
                "Review costs regularly",
                "Identify cost drivers",
                "Track cost trends",
                "Analyze cost anomalies"
            ]
        },
        {
            "id": "COST-AWARE-02",
            "question": "How do you identify cost anomalies?",
            "description": "Detect unexpected cost changes.",
            "scan_detectable": True,
            "detection_services": ["Cost Anomaly Detection"],
            "best_practices": [
                "Enable Cost Anomaly Detection",
                "Configure anomaly monitors",
                "Set up notifications",
                "Investigate anomalies promptly"
            ]
        },
        {
            "id": "COST-AWARE-03",
            "question": "How do you use AWS Cost Explorer?",
            "description": "Analyze costs with Cost Explorer.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer"],
            "best_practices": [
                "Review daily/monthly costs",
                "Analyze by service",
                "Analyze by tag",
                "Export reports"
            ]
        },
        {
            "id": "COST-AWARE-04",
            "question": "How do you use Cost and Usage Reports?",
            "description": "Enable detailed cost reporting.",
            "scan_detectable": True,
            "detection_services": ["Cost and Usage Report"],
            "best_practices": [
                "Enable CUR",
                "Store in S3",
                "Analyze with Athena",
                "Visualize with QuickSight"
            ]
        },
        {
            "id": "COST-AWARE-05",
            "question": "How do you track resource-level costs?",
            "description": "Track costs at the resource level.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Cost and Usage Report"],
            "best_practices": [
                "Enable resource-level data",
                "Tag all resources",
                "Analyze by resource",
                "Identify costly resources"
            ]
        },
        {
            "id": "COST-AWARE-06",
            "question": "How do you communicate cost information?",
            "description": "Share cost information with stakeholders.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Create cost dashboards",
                "Share regular reports",
                "Conduct cost reviews",
                "Communicate optimization opportunities"
            ]
        },
        {
            "id": "COST-AWARE-07",
            "question": "How do you analyze cost by environment?",
            "description": "Track costs by environment (dev, test, prod).",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer"],
            "best_practices": [
                "Tag by environment",
                "Compare environment costs",
                "Optimize non-production environments",
                "Implement scheduling"
            ]
        },
        {
            "id": "COST-AWARE-08",
            "question": "How do you analyze cost by application?",
            "description": "Track costs by application.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Application Cost Profiler"],
            "best_practices": [
                "Tag by application",
                "Use Application Cost Profiler",
                "Calculate unit costs",
                "Compare application costs"
            ]
        },
        # Cost-Effective Resources (COST-RES) - 8 questions
        {
            "id": "COST-RES-01",
            "question": "How do you select cost-effective resources?",
            "description": "Select the most cost-effective resources.",
            "scan_detectable": True,
            "detection_services": ["Compute Optimizer", "Cost Explorer"],
            "best_practices": [
                "Select appropriate resource type",
                "Select appropriate resource size",
                "Consider pricing model",
                "Use cost optimization tools"
            ]
        },
        {
            "id": "COST-RES-02",
            "question": "How do you use Reserved Instances?",
            "description": "Use commitment discounts.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer"],
            "best_practices": [
                "Analyze usage patterns",
                "Purchase Reserved Instances",
                "Monitor RI coverage",
                "Modify RIs as needed"
            ]
        },
        {
            "id": "COST-RES-03",
            "question": "How do you use Savings Plans?",
            "description": "Use Savings Plans for compute.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer"],
            "best_practices": [
                "Analyze compute usage",
                "Choose appropriate Savings Plan",
                "Monitor Savings Plan coverage",
                "Optimize Savings Plan usage"
            ]
        },
        {
            "id": "COST-RES-04",
            "question": "How do you use Spot Instances?",
            "description": "Use Spot Instances for flexible workloads.",
            "scan_detectable": True,
            "detection_services": ["EC2", "ECS", "EKS"],
            "best_practices": [
                "Identify Spot-suitable workloads",
                "Use Spot Instances",
                "Handle Spot interruptions",
                "Diversify instance types"
            ]
        },
        {
            "id": "COST-RES-05",
            "question": "How do you right-size resources?",
            "description": "Optimize resource sizes.",
            "scan_detectable": True,
            "detection_services": ["Compute Optimizer", "Cost Explorer"],
            "best_practices": [
                "Analyze resource utilization",
                "Use Compute Optimizer",
                "Right-size underutilized resources",
                "Monitor after changes"
            ]
        },
        {
            "id": "COST-RES-06",
            "question": "How do you manage idle resources?",
            "description": "Identify and manage unused resources.",
            "scan_detectable": True,
            "detection_services": ["Trusted Advisor", "Cost Explorer"],
            "best_practices": [
                "Identify idle resources",
                "Terminate unused resources",
                "Implement scheduling",
                "Use automation"
            ]
        },
        {
            "id": "COST-RES-07",
            "question": "How do you optimize storage costs?",
            "description": "Optimize storage for cost.",
            "scan_detectable": True,
            "detection_services": ["S3", "EBS"],
            "best_practices": [
                "Use appropriate storage tiers",
                "Implement lifecycle policies",
                "Delete unnecessary data",
                "Use S3 Intelligent Tiering"
            ]
        },
        {
            "id": "COST-RES-08",
            "question": "How do you optimize data transfer costs?",
            "description": "Minimize data transfer costs.",
            "scan_detectable": True,
            "detection_services": ["CloudFront", "VPC"],
            "best_practices": [
                "Use VPC endpoints",
                "Use CloudFront",
                "Optimize architecture",
                "Monitor transfer costs"
            ]
        },
        # Manage Demand (COST-DEMAND) - 3 questions
        {
            "id": "COST-DEMAND-01",
            "question": "How do you manage demand?",
            "description": "Manage demand to optimize costs.",
            "scan_detectable": True,
            "detection_services": ["Auto Scaling", "Lambda"],
            "best_practices": [
                "Implement auto scaling",
                "Use serverless",
                "Schedule resources",
                "Buffer demand"
            ]
        },
        {
            "id": "COST-DEMAND-02",
            "question": "How do you implement scheduling?",
            "description": "Schedule resources to match demand.",
            "scan_detectable": True,
            "detection_services": ["Instance Scheduler", "Lambda"],
            "best_practices": [
                "Use Instance Scheduler",
                "Schedule non-production resources",
                "Implement start/stop automation",
                "Track scheduling savings"
            ]
        },
        {
            "id": "COST-DEMAND-03",
            "question": "How do you use serverless for cost optimization?",
            "description": "Use serverless for variable demand.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "Fargate", "Aurora Serverless"],
            "best_practices": [
                "Evaluate serverless options",
                "Use Lambda for variable workloads",
                "Use Fargate for containers",
                "Use Aurora Serverless"
            ]
        },
        # Optimize Over Time (COST-OPT) - 3 questions
        {
            "id": "COST-OPT-01",
            "question": "How do you evaluate new services?",
            "description": "Evaluate new services for cost optimization.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Stay informed about new services",
                "Evaluate cost impact",
                "Conduct proof of concepts",
                "Plan migrations"
            ]
        },
        {
            "id": "COST-OPT-02",
            "question": "How do you review and analyze costs?",
            "description": "Regularly review costs for optimization.",
            "scan_detectable": True,
            "detection_services": ["Cost Explorer", "Trusted Advisor"],
            "best_practices": [
                "Conduct regular cost reviews",
                "Use Trusted Advisor",
                "Analyze optimization opportunities",
                "Implement improvements"
            ]
        },
        {
            "id": "COST-OPT-03",
            "question": "How do you keep your workload cost-efficient?",
            "description": "Maintain cost efficiency over time.",
            "scan_detectable": True,
            "detection_services": ["Compute Optimizer", "Cost Explorer"],
            "best_practices": [
                "Review recommendations regularly",
                "Monitor new pricing options",
                "Update commitments",
                "Continue optimization cycle"
            ]
        }
    ],

    # ========================================================================
    # SUSTAINABILITY - 20 Questions
    # ========================================================================
    WAFPillar.SUSTAINABILITY: [
        # Region Selection (SUS-REG) - 3 questions
        {
            "id": "SUS-REG-01",
            "question": "How do you select AWS Regions to support sustainability goals?",
            "description": "Choose regions that align with sustainability goals.",
            "scan_detectable": True,
            "detection_services": ["EC2", "S3"],
            "best_practices": [
                "Choose Regions near renewable energy",
                "Choose Regions near users",
                "Evaluate Region carbon footprint",
                "Use Region selector tools"
            ]
        },
        {
            "id": "SUS-REG-02",
            "question": "How do you minimize data transfer across regions?",
            "description": "Reduce cross-region data transfer.",
            "scan_detectable": True,
            "detection_services": ["CloudFront", "S3"],
            "best_practices": [
                "Use edge locations",
                "Implement caching",
                "Optimize data placement",
                "Monitor data transfer"
            ]
        },
        {
            "id": "SUS-REG-03",
            "question": "How do you optimize for renewable energy regions?",
            "description": "Prioritize regions with renewable energy.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Review AWS sustainability data",
                "Consider region energy sources",
                "Balance sustainability and performance",
                "Track sustainability metrics"
            ]
        },
        # User Behavior (SUS-USER) - 3 questions
        {
            "id": "SUS-USER-01",
            "question": "How do you align user behavior with sustainability goals?",
            "description": "Influence user behavior for sustainability.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Provide sustainability information to users",
                "Implement sustainable defaults",
                "Allow users to choose sustainable options",
                "Measure and report sustainability metrics"
            ]
        },
        {
            "id": "SUS-USER-02",
            "question": "How do you optimize user experience for sustainability?",
            "description": "Balance user experience and sustainability.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Implement efficient user interfaces",
                "Optimize data transfer to users",
                "Use progressive loading",
                "Cache content effectively"
            ]
        },
        {
            "id": "SUS-USER-03",
            "question": "How do you minimize unnecessary user traffic?",
            "description": "Reduce wasteful user interactions.",
            "scan_detectable": True,
            "detection_services": ["CloudFront", "API Gateway"],
            "best_practices": [
                "Implement effective caching",
                "Optimize API responses",
                "Reduce polling",
                "Use efficient protocols"
            ]
        },
        # Software & Architecture (SUS-SOFT) - 4 questions
        {
            "id": "SUS-SOFT-01",
            "question": "How do you optimize software for sustainability?",
            "description": "Write efficient code for sustainability.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Optimize algorithms",
                "Use efficient programming languages",
                "Implement lazy loading",
                "Minimize resource usage"
            ]
        },
        {
            "id": "SUS-SOFT-02",
            "question": "How do you design architecture for sustainability?",
            "description": "Design sustainable architectures.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "Fargate"],
            "best_practices": [
                "Use serverless where appropriate",
                "Implement efficient scaling",
                "Optimize resource allocation",
                "Use managed services"
            ]
        },
        {
            "id": "SUS-SOFT-03",
            "question": "How do you implement efficient patterns?",
            "description": "Use efficient architectural patterns.",
            "scan_detectable": True,
            "detection_services": ["SQS", "EventBridge"],
            "best_practices": [
                "Use asynchronous processing",
                "Implement queuing",
                "Use event-driven patterns",
                "Optimize batch processing"
            ]
        },
        {
            "id": "SUS-SOFT-04",
            "question": "How do you optimize managed services usage?",
            "description": "Leverage managed services for efficiency.",
            "scan_detectable": True,
            "detection_services": ["RDS", "DynamoDB", "Aurora"],
            "best_practices": [
                "Use managed databases",
                "Use managed compute",
                "Use serverless services",
                "Leverage AWS optimization"
            ]
        },
        # Data (SUS-DATA) - 4 questions
        {
            "id": "SUS-DATA-01",
            "question": "How do you optimize data storage for sustainability?",
            "description": "Implement sustainable data storage.",
            "scan_detectable": True,
            "detection_services": ["S3", "EBS", "Glacier"],
            "best_practices": [
                "Use appropriate storage classes",
                "Implement lifecycle policies",
                "Remove unnecessary data",
                "Optimize data formats"
            ]
        },
        {
            "id": "SUS-DATA-02",
            "question": "How do you minimize data movement?",
            "description": "Reduce unnecessary data transfers.",
            "scan_detectable": True,
            "detection_services": ["S3", "CloudFront"],
            "best_practices": [
                "Compute near data",
                "Use edge locations",
                "Implement data caching",
                "Optimize data locality"
            ]
        },
        {
            "id": "SUS-DATA-03",
            "question": "How do you implement data lifecycle management?",
            "description": "Manage data throughout its lifecycle.",
            "scan_detectable": True,
            "detection_services": ["S3", "Glacier"],
            "best_practices": [
                "Define retention policies",
                "Automate lifecycle transitions",
                "Delete unnecessary data",
                "Archive cold data"
            ]
        },
        {
            "id": "SUS-DATA-04",
            "question": "How do you take advantage of data access patterns?",
            "description": "Optimize based on access patterns.",
            "scan_detectable": True,
            "detection_services": ["S3", "EBS", "RDS"],
            "best_practices": [
                "Implement data classification",
                "Use tiered storage",
                "Optimize for access patterns",
                "Use lifecycle policies"
            ]
        },
        # Hardware & Services (SUS-HARD) - 4 questions
        {
            "id": "SUS-HARD-01",
            "question": "How do you select efficient hardware?",
            "description": "Choose efficient hardware options.",
            "scan_detectable": True,
            "detection_services": ["EC2", "Graviton"],
            "best_practices": [
                "Use Graviton processors",
                "Select efficient instance types",
                "Use current generation hardware",
                "Right-size instances"
            ]
        },
        {
            "id": "SUS-HARD-02",
            "question": "How do you maximize hardware utilization?",
            "description": "Improve hardware utilization.",
            "scan_detectable": True,
            "detection_services": ["Auto Scaling", "Compute Optimizer"],
            "best_practices": [
                "Use auto scaling",
                "Right-size resources",
                "Consolidate workloads",
                "Monitor utilization"
            ]
        },
        {
            "id": "SUS-HARD-03",
            "question": "How do you use managed services for sustainability?",
            "description": "Leverage managed services efficiency.",
            "scan_detectable": True,
            "detection_services": ["Lambda", "Fargate", "RDS"],
            "best_practices": [
                "Use serverless services",
                "Use managed containers",
                "Use managed databases",
                "Leverage shared infrastructure"
            ]
        },
        {
            "id": "SUS-HARD-04",
            "question": "How do you optimize accelerator usage?",
            "description": "Use accelerators efficiently.",
            "scan_detectable": True,
            "detection_services": ["EC2", "SageMaker"],
            "best_practices": [
                "Use GPUs only when needed",
                "Optimize ML inference",
                "Share accelerator resources",
                "Use Inferentia for inference"
            ]
        },
        # Development (SUS-DEV) - 2 questions
        {
            "id": "SUS-DEV-01",
            "question": "How do you incorporate sustainability into your development process?",
            "description": "Build sustainability into development.",
            "scan_detectable": False,
            "detection_services": [],
            "best_practices": [
                "Include sustainability in reviews",
                "Measure development efficiency",
                "Optimize development environments",
                "Reduce build waste"
            ]
        },
        {
            "id": "SUS-DEV-02",
            "question": "How do you minimize development environment impact?",
            "description": "Optimize development environments.",
            "scan_detectable": True,
            "detection_services": ["Cloud9", "CodeBuild"],
            "best_practices": [
                "Use Cloud IDE",
                "Schedule dev environments",
                "Share development resources",
                "Optimize CI/CD pipelines"
            ]
        }
    ]
}

def get_questions_count():
    """Return total count of questions"""
    total = sum(len(questions) for questions in WAF_QUESTIONS_COMPLETE.values())
    return total

def get_pillar_counts():
    """Return question counts by pillar"""
    return {pillar.value: len(questions) for pillar, questions in WAF_QUESTIONS_COMPLETE.items()}

# ============================================================================
# ADDITIONAL QUESTIONS TO REACH 205+
# ============================================================================

# Add more Security questions
WAF_QUESTIONS_COMPLETE[WAFPillar.SECURITY].extend([
    {
        "id": "SEC-DET-11",
        "question": "How do you implement security information and event management (SIEM)?",
        "description": "Integrate security data for comprehensive analysis.",
        "scan_detectable": True,
        "detection_services": ["Security Hub", "CloudWatch", "OpenSearch"],
        "best_practices": [
            "Aggregate security logs",
            "Implement correlation rules",
            "Enable threat intelligence",
            "Automate incident creation"
        ]
    },
    {
        "id": "SEC-INFRA-11",
        "question": "How do you implement zero trust network architecture?",
        "description": "Implement zero trust principles.",
        "scan_detectable": True,
        "detection_services": ["IAM", "VPC", "Private Link"],
        "best_practices": [
            "Verify every request",
            "Use least privilege access",
            "Implement micro-segmentation",
            "Enable continuous monitoring"
        ]
    }
])

# Add more Reliability questions
WAF_QUESTIONS_COMPLETE[WAFPillar.RELIABILITY].extend([
    {
        "id": "REL-ARCH-11",
        "question": "How do you implement service mesh for reliability?",
        "description": "Use service mesh for microservices reliability.",
        "scan_detectable": True,
        "detection_services": ["App Mesh", "EKS"],
        "best_practices": [
            "Implement service discovery",
            "Enable circuit breaking",
            "Implement retries and timeouts",
            "Enable observability"
        ]
    },
    {
        "id": "REL-CHANGE-09",
        "question": "How do you implement GitOps for infrastructure?",
        "description": "Use GitOps for infrastructure management.",
        "scan_detectable": True,
        "detection_services": ["CodePipeline", "CloudFormation"],
        "best_practices": [
            "Store infrastructure as code in Git",
            "Use pull-based deployments",
            "Enable drift detection",
            "Implement approval workflows"
        ]
    }
])

# Add more Cost Optimization questions
WAF_QUESTIONS_COMPLETE[WAFPillar.COST_OPTIMIZATION].extend([
    {
        "id": "COST-RES-09",
        "question": "How do you optimize container costs?",
        "description": "Optimize costs for container workloads.",
        "scan_detectable": True,
        "detection_services": ["ECS", "EKS", "Fargate"],
        "best_practices": [
            "Right-size container resources",
            "Use Spot for Fargate",
            "Implement cluster autoscaling",
            "Use AWS Graviton"
        ]
    },
    {
        "id": "COST-RES-10",
        "question": "How do you optimize serverless costs?",
        "description": "Optimize Lambda and serverless costs.",
        "scan_detectable": True,
        "detection_services": ["Lambda", "API Gateway"],
        "best_practices": [
            "Optimize memory allocation",
            "Use provisioned concurrency wisely",
            "Implement request batching",
            "Monitor and optimize duration"
        ]
    }
])

# Add more Performance Efficiency questions
WAF_QUESTIONS_COMPLETE[WAFPillar.PERFORMANCE_EFFICIENCY].extend([
    {
        "id": "PERF-SEL-13",
        "question": "How do you optimize machine learning workloads?",
        "description": "Optimize ML and AI workloads for performance.",
        "scan_detectable": True,
        "detection_services": ["SageMaker", "EC2"],
        "best_practices": [
            "Use appropriate instance types",
            "Use AWS Inferentia for inference",
            "Implement model optimization",
            "Use SageMaker managed endpoints"
        ]
    },
    {
        "id": "PERF-TRADE-05",
        "question": "How do you implement geo-distributed architectures?",
        "description": "Optimize performance across geographic regions.",
        "scan_detectable": True,
        "detection_services": ["Route 53", "Global Accelerator", "CloudFront"],
        "best_practices": [
            "Use Global Accelerator",
            "Implement geographic routing",
            "Use regional endpoints",
            "Cache at edge locations"
        ]
    }
])

# Add more Operational Excellence questions
WAF_QUESTIONS_COMPLETE[WAFPillar.OPERATIONAL_EXCELLENCE].extend([
    {
        "id": "OPS-PREP-11",
        "question": "How do you implement AIOps capabilities?",
        "description": "Use AI/ML for operations optimization.",
        "scan_detectable": True,
        "detection_services": ["DevOps Guru", "CloudWatch"],
        "best_practices": [
            "Enable Amazon DevOps Guru",
            "Use anomaly detection",
            "Implement predictive insights",
            "Automate remediation"
        ]
    },
    {
        "id": "OPS-OPER-11",
        "question": "How do you implement chaos engineering?",
        "description": "Use chaos engineering to improve resilience.",
        "scan_detectable": True,
        "detection_services": ["FIS"],
        "best_practices": [
            "Use AWS Fault Injection Simulator",
            "Start with small experiments",
            "Monitor during experiments",
            "Document learnings"
        ]
    }
])