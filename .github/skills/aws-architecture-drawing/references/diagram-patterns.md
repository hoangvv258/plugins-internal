# Common AWS Architecture Diagram Patterns

Reference patterns for frequently requested AWS architecture diagrams.

## Pattern 1: Basic VPC with Public/Private Subnets

```
AWS Cloud
└── Region
    └── VPC (10.0.0.0/16)
        ├── Availability Zone 1
        │   ├── Public Subnet (10.0.1.0/24)
        │   │   ├── NAT Gateway
        │   │   └── Bastion Host (EC2)
        │   └── Private Subnet (10.0.2.0/24)
        │       └── Application Server (EC2)
        └── Availability Zone 2
            ├── Public Subnet (10.0.3.0/24)
            │   └── NAT Gateway
            └── Private Subnet (10.0.4.0/24)
                └── Application Server (EC2)
```

**Groups**: AWS Cloud → Region → VPC → AZ → Subnets
**Services**: EC2, NAT Gateway, Internet Gateway
**Connectors**: Internet → IGW → Public Subnet → NAT → Private Subnet

## Pattern 2: Three-Tier Web Application

```
Users → CloudFront → ALB
                      ├── Web Tier (Public Subnet)
                      │   └── Auto Scaling Group
                      │       └── EC2 Instances
                      ├── App Tier (Private Subnet)
                      │   └── Auto Scaling Group
                      │       └── EC2 Instances
                      └── Data Tier (Private Subnet)
                          ├── Amazon RDS (Primary)
                          └── Amazon RDS (Standby)
```

**Groups**: AWS Cloud → VPC → AZ × 2 → Public/Private Subnets → Auto Scaling Groups
**Services**: CloudFront, ALB, EC2, RDS
**Connectors**: User → CloudFront → ALB → Web → App → DB

## Pattern 3: Serverless API

```
Client → API Gateway → Lambda → DynamoDB
                    └── Lambda → S3
                    └── Lambda → SQS → Lambda → SNS
```

**Groups**: AWS Cloud (flat, no VPC needed for serverless)
**Services**: API Gateway, Lambda, DynamoDB, S3, SQS, SNS
**Connectors**: Simple left-to-right flow arrows

## Pattern 4: Microservices with ECS/EKS

```
AWS Cloud
└── VPC
    ├── Public Subnet
    │   ├── Application Load Balancer
    │   └── NAT Gateway
    └── Private Subnet
        └── ECS Cluster / EKS Cluster
            ├── Service A (Fargate Tasks)
            ├── Service B (Fargate Tasks)
            └── Service C (Fargate Tasks)
        ├── Amazon RDS
        ├── Amazon ElastiCache
        └── Amazon SQS
```

**Groups**: AWS Cloud → VPC → Subnets → ECS/EKS Cluster
**Services**: ALB, ECS/EKS, Fargate, RDS, ElastiCache, SQS, ECR
**Connectors**: ALB → Services → Databases/Queues

## Pattern 5: Data Analytics Pipeline

```
Data Sources → Kinesis Data Streams → Kinesis Data Firehose → S3 (Data Lake)
                                                                    ↓
                                                              AWS Glue (ETL)
                                                                    ↓
                                                              Amazon Athena
                                                                    ↓
                                                              Amazon QuickSight
```

**Groups**: AWS Cloud (flat layout)
**Services**: Kinesis, Firehose, S3, Glue, Athena, QuickSight, Redshift
**Connectors**: Left-to-right data flow with branching

## Pattern 6: CI/CD Pipeline

```
Developer → CodeCommit → CodeBuild → CodeDeploy → EC2/ECS/Lambda
                ↓
           CodePipeline (orchestration)
                ↓
           CloudFormation (infrastructure)
```

**Groups**: AWS Cloud, optional VPC for deployment targets
**Services**: CodeCommit, CodeBuild, CodeDeploy, CodePipeline, CloudFormation
**Connectors**: Pipeline flow left-to-right

## Pattern 7: Multi-Account Organization

```
AWS Organizations
├── Management Account
│   └── AWS Control Tower
├── Security Account
│   ├── GuardDuty
│   ├── Security Hub
│   └── CloudTrail (org-level)
├── Shared Services Account
│   ├── Transit Gateway
│   ├── Directory Service
│   └── DNS (Route 53)
└── Workload Accounts
    ├── Production Account
    │   └── VPC → Application
    └── Staging Account
        └── VPC → Application
```

**Groups**: AWS Account × N (each with #E7157B pink border)
**Services**: Organizations, Control Tower, GuardDuty, Transit Gateway
**Connectors**: Account-to-account via Transit Gateway

## Pattern 8: Event-Driven Architecture

```
Event Sources → EventBridge → Rules
                                ├── Lambda → DynamoDB
                                ├── Step Functions → (workflow)
                                ├── SQS → Lambda → SNS
                                └── Kinesis Data Firehose → S3
```

**Groups**: AWS Cloud (flat)
**Services**: EventBridge, Lambda, Step Functions, SQS, SNS, DynamoDB, S3, Kinesis
**Connectors**: Fan-out from EventBridge to multiple targets

## Pattern 9: Machine Learning Pipeline

```
Data Sources → S3 (Raw Data Lake)
                    ↓
              AWS Glue (ETL)
                    ↓
              S3 (Processed Data)
                    ↓
              SageMaker (Training)
                    ↓
              SageMaker (Endpoint)
                    ↓
              API Gateway → Lambda → SageMaker Endpoint
```

**Groups**: AWS Cloud → VPC (for SageMaker endpoints)
**Services**: S3, Glue, SageMaker, API Gateway, Lambda, CloudWatch
**Connectors**: Top-to-bottom pipeline flow

## Pattern 10: Disaster Recovery (Pilot Light)

```
Primary Region                    DR Region
├── VPC                           ├── VPC (pilot light)
│   ├── EC2 (active)             │   ├── EC2 (stopped)
│   ├── RDS (primary)            │   ├── RDS (read replica)
│   └── S3 (primary)             │   └── S3 (cross-region repl.)
└── Route 53 ──failover──────────└── Route 53
```

**Groups**: AWS Cloud × 2 (side-by-side regions), VPC in each
**Services**: EC2, RDS, S3, Route 53, CloudWatch
**Connectors**: Cross-region replication arrows (dashed), Route 53 failover

## Pattern 11: IoT Architecture

```
IoT Devices → IoT Core → IoT Rules Engine
                              ├── Lambda → DynamoDB
                              ├── Kinesis → S3 (raw)
                              └── IoT Analytics → QuickSight
              IoT Device Shadow
              IoT Greengrass (edge)
```

**Groups**: AWS Cloud, IoT Greengrass (edge devices)
**Services**: IoT Core, Lambda, DynamoDB, Kinesis, S3, QuickSight
**Connectors**: Device → Cloud flows, edge processing

## Pattern 12: Static Website with CDN

```
Users → Route 53 → CloudFront → S3 (static website)
                         ↓
                   API Gateway → Lambda → DynamoDB
                         ↓
                   WAF (security)
```

**Groups**: AWS Cloud (simple, flat)
**Services**: Route 53, CloudFront, S3, API Gateway, Lambda, DynamoDB, WAF
**Connectors**: Left-to-right user request flow

## Layout Guidelines

### Horizontal Flow (Default)
- Left-to-right for data/request flow
- Users/Internet on left, databases/storage on right
- Best for: API flows, data pipelines, CI/CD

### Vertical Flow
- Top-to-bottom for hierarchical architectures
- Internet/users at top, data storage at bottom
- Best for: VPC diagrams, 3-tier architectures

### Spacing Recommendations
- Between service icons: ~1.5 inches
- Between groups: ≥ 0.3 inches
- Icon to group border: ≥ 0.2 inches
- Title area: top 1.1 inches reserved
- Footer area: bottom 0.6 inches reserved
- Usable diagram area: ~12.8 × 5.8 inches
