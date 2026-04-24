---
description: Design target AWS architecture for migrated applications — service selection, diagrams, IaC templates
---

Design a target architecture on AWS for the specified application or workload.

Cover the following aspects:

1. **Requirements Analysis**
   - Functional requirements (what the app does)
   - Non-functional requirements (performance, availability, scalability)
   - Compliance requirements (data residency, encryption, audit)
   - Budget constraints

2. **Architecture Design**
   - Architecture diagram (ASCII art or Mermaid format)
   - AWS service selection with justification for each choice
   - Network design (VPC, subnets, security groups)
   - Data flow diagram

3. **Compute Layer**
   - Lambda vs ECS Fargate vs EC2 decision
   - Container strategy (if applicable)
   - Auto-scaling configuration

4. **Data Layer**
   - Database selection (Aurora, DynamoDB, ElastiCache)
   - Storage strategy (S3, EFS, EBS)
   - Caching strategy
   - Backup and retention policies

5. **Integration Layer**
   - API Gateway configuration
   - Messaging (SQS, SNS, EventBridge)
   - Service-to-service communication patterns

6. **Security Design**
   - IAM roles and policies (least privilege)
   - Network security (VPC, security groups, WAF)
   - Encryption (KMS, TLS)
   - Authentication (Cognito, IAM)

7. **Observability**
   - Logging strategy (CloudWatch Logs)
   - Metrics and dashboards
   - Tracing (X-Ray)
   - Alerting rules

8. **Infrastructure as Code**
   - CDK or SAM template skeleton
   - CI/CD pipeline design
   - Environment strategy (dev/staging/prod)

9. **Cost Estimate**
   - Monthly cost breakdown by service
   - Cost optimization recommendations

10. **Well-Architected Review**
    - Validation against all 6 pillars
    - Identified risks and mitigations

$ARGUMENTS
