"""
Extended WAF Question Knowledge Base
=====================================
Pre-built AI help for common WAF questions across all pillars.
This supplements the base knowledge base in waf_ai_question_helper.py
"""

EXTENDED_WAF_KNOWLEDGE_BASE = {
    # ========================================================================
    # SECURITY PILLAR
    # ========================================================================
    
    "SEC-IAM-03": {
        "simple_explanation": "Do you have MFA (Multi-Factor Authentication) enabled for all users, especially those with privileged access?",
        "what_it_means": "MFA adds a second layer of security beyond just passwords - typically a code from a phone app or hardware token.",
        "why_it_matters": "Passwords alone can be stolen, guessed, or phished. MFA significantly reduces the risk of account compromise even if passwords are leaked.",
        "how_to_check": [
            "Check if MFA is enabled for the root account",
            "Verify all IAM users have MFA configured",
            "Review if MFA is required via IAM policies for sensitive operations"
        ],
        "aws_cli_commands": [
            {"description": "Check root account MFA status", "command": "aws iam get-account-summary --query 'SummaryMap.AccountMFAEnabled'"},
            {"description": "List users without MFA", "command": "aws iam generate-credential-report && aws iam get-credential-report --query 'Content' --output text | base64 -d | grep -v ',true,'"},
            {"description": "List MFA devices", "command": "aws iam list-virtual-mfa-devices"}
        ],
        "console_steps": [
            "Go to IAM Console → Dashboard",
            "Check 'Security Status' for root MFA",
            "Go to IAM → Users → Select user → Security credentials",
            "Verify 'Assigned MFA device' shows a device"
        ],
        "evidence_to_collect": [
            "IAM Credential Report showing MFA status",
            "Screenshot of root account MFA enabled",
            "SCP or IAM policy requiring MFA for sensitive actions"
        ],
        "if_yes_means": "Your accounts have an extra layer of protection against unauthorized access.",
        "if_no_means": "Accounts are vulnerable to password-based attacks. Enable MFA immediately, especially for root and admin accounts.",
        "recommendations": [
            "Enable MFA for root account first (highest priority)",
            "Require MFA for all IAM users",
            "Use hardware MFA tokens for highly privileged accounts",
            "Implement MFA condition in IAM policies for sensitive actions"
        ],
        "related_services": ["IAM", "AWS SSO", "Organizations"],
        "risk_level": "CRITICAL",
        "estimated_effort": "Low (1-2 hours for setup)"
    },
    
    "SEC-DATA-01": {
        "simple_explanation": "Is your data encrypted when stored (at rest) in AWS services like S3, RDS, and EBS?",
        "what_it_means": "Encryption at rest means data is scrambled when stored on disk, so even if someone accesses the physical storage, they can't read it.",
        "why_it_matters": "Protects data from unauthorized access if storage media is compromised, stolen, or improperly disposed of. Often required for compliance.",
        "how_to_check": [
            "Verify S3 buckets have default encryption enabled",
            "Check RDS instances have storage encryption",
            "Confirm EBS volumes are encrypted",
            "Review encryption settings for other data stores"
        ],
        "aws_cli_commands": [
            {"description": "Check S3 bucket encryption", "command": "aws s3api get-bucket-encryption --bucket BUCKET_NAME"},
            {"description": "List unencrypted RDS instances", "command": "aws rds describe-db-instances --query 'DBInstances[?StorageEncrypted==`false`].[DBInstanceIdentifier]'"},
            {"description": "List unencrypted EBS volumes", "command": "aws ec2 describe-volumes --query 'Volumes[?Encrypted==`false`].[VolumeId]'"}
        ],
        "console_steps": [
            "S3 Console → Bucket → Properties → Default encryption",
            "RDS Console → Database → Configuration → Encryption",
            "EC2 Console → Volumes → Check Encryption column"
        ],
        "evidence_to_collect": [
            "List of all data stores with encryption status",
            "KMS key policies",
            "AWS Config rules for encryption compliance"
        ],
        "if_yes_means": "Your data is protected even if storage is compromised.",
        "if_no_means": "Unencrypted data could be exposed if storage is accessed improperly.",
        "recommendations": [
            "Enable S3 default encryption for all buckets",
            "Use encrypted RDS instances (enable during creation)",
            "Enable EBS encryption by default in account settings",
            "Use AWS KMS for key management"
        ],
        "related_services": ["KMS", "S3", "RDS", "EBS", "Secrets Manager"],
        "risk_level": "HIGH",
        "estimated_effort": "Medium (existing unencrypted resources may need migration)"
    },
    
    "SEC-NET-01": {
        "simple_explanation": "Are your VPCs and subnets designed to control network access and segment your workloads?",
        "what_it_means": "Network segmentation means separating different parts of your system so that if one part is compromised, attackers can't easily move to others.",
        "why_it_matters": "Limits blast radius of security incidents. Web servers shouldn't be able to directly access your database servers without going through proper channels.",
        "how_to_check": [
            "Review VPC architecture for proper segmentation",
            "Verify public and private subnets are used appropriately",
            "Check security groups for overly permissive rules",
            "Review NACLs for additional controls"
        ],
        "aws_cli_commands": [
            {"description": "List VPCs", "command": "aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock,Tags]'"},
            {"description": "List subnets", "command": "aws ec2 describe-subnets --query 'Subnets[*].[SubnetId,VpcId,CidrBlock,MapPublicIpOnLaunch]'"},
            {"description": "Find overly permissive security groups", "command": "aws ec2 describe-security-groups --query 'SecurityGroups[?IpPermissions[?IpRanges[?CidrIp==`0.0.0.0/0`]]].[GroupId,GroupName]'"}
        ],
        "console_steps": [
            "VPC Console → Your VPCs → Review architecture",
            "Check Subnets → Verify public vs private designation",
            "Security Groups → Look for 0.0.0.0/0 inbound rules",
            "Network ACLs → Review allow/deny rules"
        ],
        "evidence_to_collect": [
            "VPC architecture diagram",
            "Security group rules export",
            "NACL configurations"
        ],
        "if_yes_means": "Your network is properly segmented, limiting attack surface.",
        "if_no_means": "Flat networks allow attackers to move laterally after initial compromise.",
        "recommendations": [
            "Use separate subnets for web, app, and database tiers",
            "Place databases in private subnets",
            "Minimize security group rules to required ports only",
            "Use VPC Flow Logs for monitoring"
        ],
        "related_services": ["VPC", "Security Groups", "NACLs", "AWS Network Firewall"],
        "risk_level": "HIGH",
        "estimated_effort": "High (requires architecture review and potential redesign)"
    },
    
    # ========================================================================
    # RELIABILITY PILLAR
    # ========================================================================
    
    "REL-AVAIL-01": {
        "simple_explanation": "Are your critical resources deployed across multiple Availability Zones (AZs) so they keep running if one data center fails?",
        "what_it_means": "Availability Zones are separate data centers within a region. Deploying across multiple AZs means your app stays up even if one data center has issues.",
        "why_it_matters": "Single points of failure can cause complete outages. Multi-AZ deployment provides resilience against data center-level failures.",
        "how_to_check": [
            "Check if RDS is Multi-AZ enabled",
            "Verify EC2 instances are spread across AZs",
            "Confirm load balancers are cross-zone",
            "Review Auto Scaling group AZ configuration"
        ],
        "aws_cli_commands": [
            {"description": "Check RDS Multi-AZ status", "command": "aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,MultiAZ,AvailabilityZone]'"},
            {"description": "Check EC2 instance distribution", "command": "aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,AvailabilityZone]' --output table"},
            {"description": "Check Auto Scaling group AZs", "command": "aws autoscaling describe-auto-scaling-groups --query 'AutoScalingGroups[*].[AutoScalingGroupName,AvailabilityZones]'"}
        ],
        "console_steps": [
            "RDS Console → Database → Check 'Multi-AZ' in Configuration",
            "EC2 Console → Instances → Check AZ column distribution",
            "EC2 Console → Auto Scaling Groups → Check AZ configuration"
        ],
        "evidence_to_collect": [
            "RDS Multi-AZ configuration screenshots",
            "Auto Scaling group configurations",
            "Architecture diagram showing AZ distribution"
        ],
        "if_yes_means": "Your workload can survive Availability Zone failures with minimal or no impact.",
        "if_no_means": "A single AZ failure could cause complete workload outage.",
        "recommendations": [
            "Enable Multi-AZ for RDS databases",
            "Spread EC2 instances across at least 2 AZs",
            "Use Application Load Balancer with cross-zone enabled",
            "Configure Auto Scaling to use multiple AZs"
        ],
        "related_services": ["RDS", "EC2", "ALB", "Auto Scaling"],
        "risk_level": "HIGH",
        "estimated_effort": "Medium (RDS Multi-AZ is a setting, EC2 may require restructuring)"
    },
    
    "REL-CHANGE-01": {
        "simple_explanation": "Do you test changes in a non-production environment before deploying to production?",
        "what_it_means": "Having separate development, staging, and production environments allows you to catch problems before they affect real users.",
        "why_it_matters": "Changes deployed directly to production without testing can cause outages, data corruption, or security vulnerabilities.",
        "how_to_check": [
            "Verify separate AWS accounts or environments exist for dev/staging/prod",
            "Check if there's a deployment pipeline with approval gates",
            "Review if automated testing runs before production deployment"
        ],
        "aws_cli_commands": [
            {"description": "List CodePipeline pipelines", "command": "aws codepipeline list-pipelines"},
            {"description": "Get pipeline details", "command": "aws codepipeline get-pipeline --name PIPELINE_NAME"},
            {"description": "List Organizations accounts", "command": "aws organizations list-accounts --query 'Accounts[*].[Name,Id]'"}
        ],
        "console_steps": [
            "CodePipeline Console → Check for staging/approval stages",
            "Organizations Console → Verify separate accounts for environments",
            "CloudFormation → Check for environment-specific stacks"
        ],
        "evidence_to_collect": [
            "CI/CD pipeline configurations",
            "Environment architecture diagram",
            "Approval process documentation"
        ],
        "if_yes_means": "Changes are validated before reaching production, reducing risk of outages.",
        "if_no_means": "You're at higher risk of production incidents from untested changes.",
        "recommendations": [
            "Create separate AWS accounts for dev, staging, and production",
            "Implement CI/CD with automated testing",
            "Add manual approval gates for production deployments",
            "Use Infrastructure as Code for consistent environments"
        ],
        "related_services": ["CodePipeline", "CodeBuild", "CodeDeploy", "Organizations"],
        "risk_level": "MEDIUM",
        "estimated_effort": "High (requires pipeline and environment setup)"
    },
    
    # ========================================================================
    # PERFORMANCE EFFICIENCY PILLAR
    # ========================================================================
    
    "PERF-DB-01": {
        "simple_explanation": "Are you using the right database type for your data and access patterns?",
        "what_it_means": "Different databases are optimized for different use cases - relational for structured data, NoSQL for flexible schemas, in-memory for caching.",
        "why_it_matters": "Using the wrong database type leads to poor performance, higher costs, and complex workarounds.",
        "how_to_check": [
            "Review your data model and access patterns",
            "Check if you're using relational DB for non-relational data",
            "Verify caching is implemented for frequent reads",
            "Assess if current database is meeting performance needs"
        ],
        "aws_cli_commands": [
            {"description": "List RDS instances", "command": "aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,Engine,DBInstanceClass]'"},
            {"description": "List DynamoDB tables", "command": "aws dynamodb list-tables"},
            {"description": "List ElastiCache clusters", "command": "aws elasticache describe-cache-clusters --query 'CacheClusters[*].[CacheClusterId,Engine]'"}
        ],
        "console_steps": [
            "Review your application's data requirements",
            "Check RDS Console → Performance Insights for bottlenecks",
            "Consider DynamoDB for key-value or document data",
            "Review if ElastiCache could help with read performance"
        ],
        "evidence_to_collect": [
            "Data model documentation",
            "Database performance metrics",
            "Query patterns analysis"
        ],
        "if_yes_means": "Your databases are well-matched to your data and access patterns.",
        "if_no_means": "Performance issues and unnecessary complexity may result from database mismatch.",
        "recommendations": [
            "Use RDS/Aurora for relational data with complex queries",
            "Use DynamoDB for high-scale key-value access",
            "Implement ElastiCache for frequently accessed data",
            "Consider purpose-built databases (Neptune for graphs, Timestream for time series)"
        ],
        "related_services": ["RDS", "Aurora", "DynamoDB", "ElastiCache", "Neptune"],
        "risk_level": "MEDIUM",
        "estimated_effort": "High (database migration is complex)"
    },
    
    # ========================================================================
    # COST OPTIMIZATION PILLAR
    # ========================================================================
    
    "COST-RI-01": {
        "simple_explanation": "Are you using Reserved Instances or Savings Plans for your predictable, steady-state workloads?",
        "what_it_means": "Reserved Instances and Savings Plans offer up to 72% discount compared to On-Demand pricing in exchange for a 1 or 3 year commitment.",
        "why_it_matters": "Running steady workloads on On-Demand pricing is like paying full price when discounts are available.",
        "how_to_check": [
            "Review Cost Explorer for RI/Savings Plan coverage",
            "Identify steady-state workloads suitable for commitments",
            "Check RI utilization to ensure you're using what you've purchased"
        ],
        "aws_cli_commands": [
            {"description": "List Reserved Instances", "command": "aws ec2 describe-reserved-instances --query 'ReservedInstances[?State==`active`].[ReservedInstancesId,InstanceType,InstanceCount]'"},
            {"description": "Get Savings Plans", "command": "aws savingsplans describe-savings-plans --query 'savingsPlans[*].[savingsPlanId,commitment,savingsPlanType]'"},
            {"description": "Check RI utilization", "command": "aws ce get-reservation-utilization --time-period Start=$(date -d '-30 days' +%Y-%m-%d),End=$(date +%Y-%m-%d)"}
        ],
        "console_steps": [
            "Cost Explorer → Reservations → Utilization report",
            "Cost Explorer → Savings Plans → Utilization report",
            "Cost Explorer → Recommendations for RI/Savings Plans"
        ],
        "evidence_to_collect": [
            "RI/Savings Plan coverage report",
            "Utilization metrics",
            "Cost savings analysis"
        ],
        "if_yes_means": "You're optimizing costs for predictable workloads.",
        "if_no_means": "You may be paying significantly more than necessary for steady-state resources.",
        "recommendations": [
            "Analyze workload patterns to identify steady-state usage",
            "Start with 1-year No Upfront for lower risk",
            "Use Compute Savings Plans for flexibility",
            "Monitor utilization to ensure commitments are used"
        ],
        "related_services": ["Cost Explorer", "Savings Plans", "Reserved Instances"],
        "risk_level": "MEDIUM",
        "estimated_effort": "Low (purchasing is straightforward, analysis takes time)"
    },
    
    "COST-UNUSED-01": {
        "simple_explanation": "Are you identifying and removing unused or idle resources that are costing money?",
        "what_it_means": "Resources like unused EBS volumes, old snapshots, idle EC2 instances, and unattached Elastic IPs cost money even when not being used.",
        "why_it_matters": "Unused resources are pure waste - you're paying for something providing no value.",
        "how_to_check": [
            "Look for unattached EBS volumes",
            "Check for EC2 instances with low CPU utilization",
            "Review old EBS snapshots",
            "Find unattached Elastic IPs"
        ],
        "aws_cli_commands": [
            {"description": "Find unattached EBS volumes", "command": "aws ec2 describe-volumes --query 'Volumes[?State==`available`].[VolumeId,Size,CreateTime]'"},
            {"description": "Find unattached Elastic IPs", "command": "aws ec2 describe-addresses --query 'Addresses[?InstanceId==`null`].[PublicIp,AllocationId]'"},
            {"description": "Find old snapshots", "command": "aws ec2 describe-snapshots --owner-ids self --query 'Snapshots[?StartTime<=`2023-01-01`].[SnapshotId,VolumeSize,StartTime]'"},
            {"description": "Get idle instance recommendations", "command": "aws compute-optimizer get-ec2-instance-recommendations --query 'instanceRecommendations[?finding==`UNDER_PROVISIONED` || finding==`OVER_PROVISIONED`]'"}
        ],
        "console_steps": [
            "EC2 Console → Volumes → Filter by 'available' state",
            "EC2 Console → Elastic IPs → Check for unassociated IPs",
            "EC2 Console → Snapshots → Sort by date, review old ones",
            "Compute Optimizer → Check for idle instances"
        ],
        "evidence_to_collect": [
            "List of unused resources with costs",
            "Compute Optimizer report",
            "Trusted Advisor cost optimization findings"
        ],
        "if_yes_means": "You're actively managing resources and minimizing waste.",
        "if_no_means": "You're likely paying for resources providing no value.",
        "recommendations": [
            "Set up regular reviews to identify unused resources",
            "Use AWS Trusted Advisor for cost optimization checks",
            "Implement lifecycle policies for EBS snapshots",
            "Create alerts for idle resources"
        ],
        "related_services": ["Trusted Advisor", "Compute Optimizer", "Cost Explorer"],
        "risk_level": "LOW",
        "estimated_effort": "Low (cleanup is quick once identified)"
    },
    
    # ========================================================================
    # OPERATIONAL EXCELLENCE PILLAR
    # ========================================================================
    
    "OPS-LOG-01": {
        "simple_explanation": "Are you collecting and centralizing logs from your applications and infrastructure?",
        "what_it_means": "Logs record what's happening in your systems. Centralizing them makes it easier to search, analyze, and troubleshoot issues.",
        "why_it_matters": "Without centralized logging, troubleshooting is slow and you may miss important events or security incidents.",
        "how_to_check": [
            "Verify CloudWatch Logs is receiving logs from applications",
            "Check if VPC Flow Logs are enabled",
            "Confirm CloudTrail is enabled for API logging",
            "Review log retention policies"
        ],
        "aws_cli_commands": [
            {"description": "List CloudWatch Log Groups", "command": "aws logs describe-log-groups --query 'logGroups[*].[logGroupName,retentionInDays]'"},
            {"description": "Check CloudTrail status", "command": "aws cloudtrail describe-trails --query 'trailList[*].[Name,IsMultiRegionTrail,IsLogging]'"},
            {"description": "Check VPC Flow Logs", "command": "aws ec2 describe-flow-logs --query 'FlowLogs[*].[FlowLogId,ResourceId,LogDestination]'"}
        ],
        "console_steps": [
            "CloudWatch Console → Log groups → Review what's being collected",
            "CloudTrail Console → Trails → Verify logging is enabled",
            "VPC Console → Your VPCs → Flow logs tab"
        ],
        "evidence_to_collect": [
            "List of log groups and retention policies",
            "CloudTrail configuration",
            "VPC Flow Logs configuration"
        ],
        "if_yes_means": "You have visibility into system behavior for troubleshooting and security.",
        "if_no_means": "You're flying blind - issues are harder to diagnose and security events may go unnoticed.",
        "recommendations": [
            "Enable CloudWatch Logs for all applications",
            "Enable CloudTrail in all regions",
            "Enable VPC Flow Logs for network visibility",
            "Set appropriate retention policies to balance cost and compliance"
        ],
        "related_services": ["CloudWatch Logs", "CloudTrail", "VPC Flow Logs", "OpenSearch"],
        "risk_level": "HIGH",
        "estimated_effort": "Medium (setup is straightforward, integration takes time)"
    },
    
    "OPS-ALARM-01": {
        "simple_explanation": "Do you have alarms set up to notify you when something goes wrong before users are affected?",
        "what_it_means": "CloudWatch Alarms can automatically notify you (via SNS) when metrics exceed thresholds, like high CPU or error rates.",
        "why_it_matters": "Proactive alerting means you can fix issues before they cause outages or user impact, rather than waiting for complaints.",
        "how_to_check": [
            "Review existing CloudWatch Alarms",
            "Verify alarms exist for critical metrics (CPU, memory, errors, latency)",
            "Check that alarm actions are configured (SNS notifications)",
            "Test that notifications actually reach the right people"
        ],
        "aws_cli_commands": [
            {"description": "List all alarms", "command": "aws cloudwatch describe-alarms --query 'MetricAlarms[*].[AlarmName,StateValue,MetricName]'"},
            {"description": "List alarms in ALARM state", "command": "aws cloudwatch describe-alarms --state-value ALARM"},
            {"description": "Get alarm details", "command": "aws cloudwatch describe-alarms --alarm-names ALARM_NAME"}
        ],
        "console_steps": [
            "CloudWatch Console → Alarms → Review existing alarms",
            "Check 'In alarm' state alarms for current issues",
            "Verify SNS topic subscriptions are correct",
            "Test alarms by temporarily lowering thresholds"
        ],
        "evidence_to_collect": [
            "List of configured alarms",
            "SNS notification configurations",
            "On-call rotation or escalation procedures"
        ],
        "if_yes_means": "You'll be notified of problems quickly, reducing mean time to detection.",
        "if_no_means": "Problems may go unnoticed until users complain or outages occur.",
        "recommendations": [
            "Create alarms for CPU, memory, disk, and error rates",
            "Set up composite alarms for complex conditions",
            "Use anomaly detection for dynamic thresholds",
            "Ensure alarm notifications reach on-call team"
        ],
        "related_services": ["CloudWatch Alarms", "SNS", "EventBridge"],
        "risk_level": "MEDIUM",
        "estimated_effort": "Low (creating alarms is quick)"
    },
    
    # ========================================================================
    # SUSTAINABILITY PILLAR
    # ========================================================================
    
    "SUS-REGION-01": {
        "simple_explanation": "Have you considered deploying in AWS regions that use more renewable energy?",
        "what_it_means": "Different AWS regions have different carbon footprints based on their local power grid mix. Some regions use more renewable energy.",
        "why_it_matters": "Choosing sustainable regions can reduce your workload's carbon footprint without changing your architecture.",
        "how_to_check": [
            "Review which AWS regions your workload uses",
            "Check AWS's sustainability information for each region",
            "Consider if latency requirements allow moving to greener regions"
        ],
        "aws_cli_commands": [
            {"description": "List your resources by region", "command": "for region in $(aws ec2 describe-regions --query 'Regions[*].RegionName' --output text); do echo \"=== $region ===\"; aws ec2 describe-instances --region $region --query 'Reservations[*].Instances[*].InstanceId' 2>/dev/null; done"},
            {"description": "Check Customer Carbon Footprint Tool", "command": "# Available in AWS Billing Console > Cost & Usage Reports > Carbon Footprint"}
        ],
        "console_steps": [
            "Review AWS Carbon Footprint Tool in Billing Console",
            "Check workload distribution across regions",
            "Review AWS sustainability page for region information"
        ],
        "evidence_to_collect": [
            "Current region usage breakdown",
            "Latency requirements analysis",
            "Carbon footprint report from AWS"
        ],
        "if_yes_means": "You're optimizing for environmental sustainability.",
        "if_no_means": "Consider sustainability in future architecture decisions.",
        "recommendations": [
            "Review AWS Customer Carbon Footprint Tool",
            "Consider moving non-latency-sensitive workloads to greener regions",
            "Use AWS's commitment to 100% renewable energy by 2025",
            "Factor sustainability into new architecture decisions"
        ],
        "related_services": ["Customer Carbon Footprint Tool", "AWS Regions"],
        "risk_level": "LOW",
        "estimated_effort": "Variable (depends on migration complexity)"
    },
    
    "SUS-UTIL-01": {
        "simple_explanation": "Are you maximizing resource utilization to avoid wasted compute capacity?",
        "what_it_means": "Running servers at low utilization wastes energy. Right-sizing and using managed services improves efficiency.",
        "why_it_matters": "Under-utilized resources consume power without providing proportional value, increasing environmental impact.",
        "how_to_check": [
            "Review average CPU and memory utilization",
            "Check Compute Optimizer recommendations",
            "Consider if serverless options would be more efficient"
        ],
        "aws_cli_commands": [
            {"description": "Check average CPU utilization", "command": "aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=INSTANCE_ID --start-time $(date -d '7 days ago' -Iseconds) --end-time $(date -Iseconds) --period 86400 --statistics Average"},
            {"description": "Get right-sizing recommendations", "command": "aws compute-optimizer get-ec2-instance-recommendations"}
        ],
        "console_steps": [
            "Compute Optimizer → Review right-sizing recommendations",
            "CloudWatch → EC2 → Per-Instance Metrics → CPUUtilization",
            "Consider Lambda or Fargate for variable workloads"
        ],
        "evidence_to_collect": [
            "Utilization metrics across fleet",
            "Compute Optimizer recommendations",
            "Serverless migration assessment"
        ],
        "if_yes_means": "Your resources are efficiently utilized, minimizing waste.",
        "if_no_means": "Over-provisioned resources waste energy and money.",
        "recommendations": [
            "Right-size instances based on actual utilization",
            "Use Auto Scaling to match capacity to demand",
            "Consider serverless for variable workloads",
            "Use Graviton processors for better performance per watt"
        ],
        "related_services": ["Compute Optimizer", "Lambda", "Fargate", "Auto Scaling"],
        "risk_level": "LOW",
        "estimated_effort": "Medium (analysis and migration)"
    }
}

# Function to merge with base knowledge base
def get_merged_knowledge_base(base_kb: dict) -> dict:
    """Merge base and extended knowledge bases"""
    merged = base_kb.copy()
    merged.update(EXTENDED_WAF_KNOWLEDGE_BASE)
    return merged
