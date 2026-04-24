# AWS Migration Project — SA Study Guide

> Dành cho SA mới vào dự án migration: Java→Serverless, Struts→Spring, Low-code trên AWS.
> Tài liệu này cover full-stack AWS services cần thiết, cách build đúng, và best practices.

---

## Table of Contents

1. [Part 1: Serverless Core](#part-1-serverless-core)
2. [Part 2: Container & Database](#part-2-container--database)
3. [Part 3: Networking & Security](#part-3-networking--security)
4. [Part 4: CI/CD & Infrastructure as Code](#part-4-cicd--infrastructure-as-code)
5. [Part 5: Migration Methodology](#part-5-migration-methodology)
6. [Part 6: Cost Optimization](#part-6-cost-optimization)
7. [Quick Reference Cards](#quick-reference-cards)

---

# Part 1: Serverless Core

## 1.1 AWS Lambda

### What Is It?
Serverless compute — chạy code mà không cần quản lý server. Pay per invocation + duration.

### Key Specs (2026)
| Spec | Limit |
|------|-------|
| Memory | 128 MB – 10,240 MB |
| Timeout | Max 15 minutes |
| Package size | 50 MB zip / 250 MB unzipped / 10 GB container |
| Concurrency | 1,000 default (có thể tăng) |
| Runtimes | Java 17/21, Python 3.12, Node.js 20, .NET 8, Go, Ruby |
| Architectures | x86_64, arm64 (Graviton — 20% rẻ hơn) |

### When to Use
- Event-driven processing (API calls, S3 events, SQS messages)
- Short-lived tasks (<15 min)
- Variable/unpredictable traffic
- Microservices and API backends

### When NOT to Use
- Long-running processes (>15 min) → ECS Fargate
- Consistent high-throughput → ECS/EC2
- WebSocket connections → ECS or AppRunner
- Large memory (>10 GB) → ECS/EC2

### Java on Lambda — Critical Knowledge

#### Cold Start Problem
Java có cold start 3-10 giây (do JVM startup + class loading). Solutions:

| Solution | Cold Start | Effort | Cost |
|----------|-----------|--------|------|
| **SnapStart** | ~90% reduction (<1s) | Low | Free cho Java managed runtimes |
| **GraalVM Native** | ~95% reduction (<200ms) | High | Free |
| **Provisioned Concurrency** | 100% eliminated | Low | $$$ |
| **Reduce dependencies** | ~40-60% | Medium | Free |
| **ARM64 (Graviton)** | ~10-20% faster | Low | 20% cheaper |

#### SnapStart (Recommended cho Java)
```yaml
# SAM template
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      Runtime: java21
      SnapStart:
        ApplyOn: PublishedVersions
      AutoPublishAlias: live
```

#### Spring Cloud Function on Lambda
```java
@SpringBootApplication
public class Application {
    @Bean
    public Function<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> handleRequest() {
        return request -> {
            // Business logic
            return new APIGatewayProxyResponseEvent()
                .withStatusCode(200)
                .withBody("{\"message\": \"Hello\"}");
        };
    }
}
```

### Lambda Best Practices
```
✅ DO:
- Initialize connections outside handler (reuse across invocations)
- Use environment variables for config
- Enable SnapStart for Java
- Use Powertools for logging/tracing/metrics
- Set appropriate timeout (not max 15 min)
- Use ARM64 for 20% cost savings
- Package only needed dependencies

❌ DON'T:
- Chain Lambda→Lambda synchronously (use Step Functions)
- Store state in /tmp across invocations
- Use for processes >15 min
- Ignore connection pooling (use RDS Proxy)
- Package entire framework if only using 2 classes
```

### Pricing Model
- **Free Tier**: 1M requests + 400K GB-seconds/month
- **Requests**: $0.20 per 1M requests
- **Duration**: $0.0000166667 per GB-second (x86)
- **ARM64**: 20% cheaper than x86
- **SnapStart**: Free cho Java managed runtimes (có phí cho custom runtimes)

---

## 1.2 Amazon API Gateway

### What Is It?
Managed API service — tạo REST, HTTP, và WebSocket APIs. Handles authentication, throttling, caching.

### REST API vs HTTP API

| Feature | REST API | HTTP API |
|---------|----------|----------|
| Price | $3.50/million | $1.00/million |
| Latency | Higher | Lower (~60% less) |
| Auth | IAM, Cognito, Lambda, API Key | IAM, Cognito, JWT |
| Caching | Built-in | ❌ |
| Request validation | ✅ | ❌ |
| Usage plans | ✅ | ❌ |
| WebSocket | Separate type | ❌ |
| **Recommendation** | Full-featured APIs | Most APIs (cheaper, faster) |

### When to Use HTTP API (Default Choice)
- Simple API proxy to Lambda
- JWT authentication sufficient
- Don't need caching or request validation
- Cost-sensitive

### When to Use REST API
- Need caching at API layer
- Need request/response validation models
- Need API keys and usage plans
- Need request transformation

### Example: HTTP API + Lambda
```yaml
# SAM template
Resources:
  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: com.example.Handler::handleRequest
      Runtime: java21
      Events:
        GetUsers:
          Type: HttpApi
          Properties:
            Path: /users/{id}
            Method: get
```

---

## 1.3 AWS Step Functions

### What Is It?
Visual workflow orchestrator — kết nối Lambda functions, AWS services thành workflows có state management, error handling, retry.

### When to Use
- Replace synchronous Lambda chains
- Long-running workflows (up to 1 year)
- Orchestrate multiple microservices
- Replace Java batch jobs
- Saga pattern for distributed transactions
- Human approval workflows

### Standard vs Express

| Feature | Standard | Express |
|---------|----------|---------|
| Duration | Up to 1 year | Up to 5 minutes |
| Price | Per state transition | Per execution + duration |
| Execution | Exactly-once | At-least-once |
| Use case | Long-running, orchestration | High-volume, short |

### Common Patterns

#### ETL Workflow
```json
{
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:extract",
      "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 3, "BackoffRate": 2}],
      "Next": "Transform"
    },
    "Transform": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:transform",
      "Next": "LoadChoice"
    },
    "LoadChoice": {
      "Type": "Choice",
      "Choices": [
        {"Variable": "$.recordCount", "NumericGreaterThan": 0, "Next": "Load"}
      ],
      "Default": "NoDataFound"
    },
    "Load": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:load",
      "End": true
    },
    "NoDataFound": {
      "Type": "Succeed"
    }
  }
}
```

#### Saga Pattern (Distributed Transactions)
```
Start → BookHotel → BookFlight → ChargePayment → Success
                                       ↓ (fail)
                              CancelFlight → CancelHotel → Fail
```

### Step Functions vs Direct Lambda Invocation

| Pattern | Use |
|---------|-----|
| Lambda → Lambda (sync) | ❌ Never |
| Step Functions | ✅ Orchestration, workflows |
| SQS → Lambda | ✅ Decoupled async |
| EventBridge → Lambda | ✅ Event-driven routing |
| SNS → Lambda | ✅ Fan-out |

---

## 1.4 Amazon DynamoDB

### What Is It?
Fully managed NoSQL database — single-digit millisecond latency, unlimited scale.

### Key Concepts
- **Table**: Collection of items (like rows)
- **Item**: JSON document (up to 400 KB)
- **Partition Key (PK)**: Unique identifier for data distribution
- **Sort Key (SK)**: Secondary sort within partition
- **GSI**: Global Secondary Index — query on different attributes
- **LSI**: Local Secondary Index — same PK, different SK

### Capacity Modes

| Mode | Pricing | Use Case |
|------|---------|----------|
| On-Demand | Per read/write | Variable traffic, new apps |
| Provisioned | Per RCU/WCU | Predictable traffic |

**Recommendation**: Start On-Demand → Switch Provisioned when patterns are stable

### Single-Table Design (Advanced)
```
PK              SK              Data
USER#123        PROFILE         {name, email, ...}
USER#123        ORDER#001       {total, date, ...}
USER#123        ORDER#002       {total, date, ...}
ORDER#001       ITEM#A          {product, qty, ...}
ORDER#001       ITEM#B          {product, qty, ...}
```

### When to Use DynamoDB
- Simple key-value or document access
- High throughput, low latency
- Known access patterns
- Session storage, user profiles, shopping carts

### When NOT to Use
- Complex queries, JOINs → Aurora PostgreSQL
- Ad-hoc queries → Aurora or Redshift
- Unknown access patterns → Aurora
- Relational data with complex relationships → Aurora

### DynamoDB Best Practices
- Design for access patterns FIRST, not data model
- Use composite keys (PK + SK) for hierarchical data
- Use GSI overloading (reuse GSI for different queries)
- Enable TTL for auto-expiring temporary data
- Use DynamoDB Streams for CDC (Change Data Capture)
- Keep items small (<400 KB, ideally <4 KB)

---

## 1.5 Amazon SQS (Simple Queue Service)

### What Is It?
Managed message queue — decouple services, buffer requests.

### Standard vs FIFO

| Feature | Standard | FIFO |
|---------|----------|------|
| Throughput | Unlimited | 3,000 msg/sec (with batching) |
| Order | Best-effort | Guaranteed FIFO |
| Delivery | At-least-once | Exactly-once |
| Use case | Most workloads | Order-critical |

### Common Pattern: SQS + Lambda
```yaml
Resources:
  ProcessFunction:
    Type: AWS::Serverless::Function
    Properties:
      Events:
        SQSEvent:
          Type: SQS
          Properties:
            Queue: !GetAtt MyQueue.Arn
            BatchSize: 10
            MaximumBatchingWindowInSeconds: 5
```

### Dead Letter Queue (DLQ)
```yaml
MyQueue:
  Type: AWS::SQS::Queue
  Properties:
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt MyDLQ.Arn
      maxReceiveCount: 3  # Retry 3 times, then send to DLQ
```

---

## 1.6 Amazon SNS (Simple Notification Service)

### What Is It?
Managed pub/sub messaging — fan-out messages to multiple subscribers.

### Use Cases
- Fan-out: 1 message → N subscribers (Lambda, SQS, HTTP, email, SMS)
- Event notifications (S3, CloudWatch, etc.)
- Mobile push notifications

### SNS + SQS Fan-Out Pattern
```
Producer → SNS Topic → SQS Queue 1 → Lambda (Analytics)
                      → SQS Queue 2 → Lambda (Billing)
                      → SQS Queue 3 → Lambda (Notification)
```

---

## 1.7 Amazon EventBridge

### What Is It?
Serverless event bus — route events between AWS services, SaaS, custom apps.

### When to Use EventBridge vs SNS

| Feature | EventBridge | SNS |
|---------|------------|-----|
| Event filtering | Content-based rules | ❌ |
| Schema registry | ✅ | ❌ |
| Event archiving | ✅ | ❌ |
| Event replay | ✅ | ❌ |
| Targets | 20+ AWS services | Lambda, SQS, HTTP, etc. |
| **Recommendation** | New event-driven apps | Simple fan-out |

### EventBridge Rule Example
```json
{
  "source": ["com.myapp.orders"],
  "detail-type": ["OrderCreated"],
  "detail": {
    "total": [{"numeric": [">", 1000]}]
  }
}
```

---

## 1.8 Amazon S3

### What Is It?
Object storage — unlimited storage, 99.999999999% durability.

### Storage Classes

| Class | Use Case | Cost |
|-------|----------|------|
| S3 Standard | Frequent access | $$$ |
| S3 Intelligent-Tiering | Unknown/changing patterns | Auto-optimized |
| S3 Standard-IA | Infrequent access | $$ |
| S3 One Zone-IA | Non-critical infrequent | $ |
| S3 Glacier Instant | Archive, instant access | $ |
| S3 Glacier Flexible | Archive, 1-12 hours | ¢ |
| S3 Glacier Deep Archive | Long-term archive | ¢¢ |

### S3 Best Practices for Migration
- Use S3 Transfer Acceleration for large uploads
- Enable versioning for data protection
- Configure lifecycle rules for cost optimization
- Use S3 Event Notifications → Lambda for event-driven processing
- Enable server-side encryption (SSE-S3 or SSE-KMS)

---

# Part 2: Container & Database

## 2.1 Amazon ECS (Elastic Container Service) + Fargate

### What Is It?
Managed container orchestration. Fargate = serverless containers (no EC2 to manage).

### ECS vs EKS

| Feature | ECS + Fargate | EKS |
|---------|--------------|-----|
| Complexity | Low | High |
| Learning curve | Easy | Steep (Kubernetes) |
| Portability | AWS-specific | Multi-cloud |
| Use case | Most workloads | K8s expertise, multi-cloud |
| **Recommendation** | Default choice | Only if you need K8s |

### When to Use ECS Fargate
- Long-running services (>15 min)
- Consistent traffic patterns
- Need more than 10 GB memory
- WebSocket connections
- Lift-and-shift containers (replatform)

### ECS Fargate Architecture
```
ALB → Target Group → ECS Service (Fargate)
                      ├── Task 1 (Container)
                      ├── Task 2 (Container)
                      └── Task 3 (Container, auto-scaled)
```

### Task Definition (Key Concepts)
```json
{
  "family": "my-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "account.dkr.ecr.region.amazonaws.com/my-app:latest",
      "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/my-app",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/actuator/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Fargate CPU/Memory Combinations

| CPU (vCPU) | Memory (GB) |
|-----------|-------------|
| 0.25 | 0.5, 1, 2 |
| 0.5 | 1, 2, 3, 4 |
| 1 | 2, 3, 4, 5, 6, 7, 8 |
| 2 | 4–16 (1 GB increments) |
| 4 | 8–30 (1 GB increments) |
| 8 | 16–60 (4 GB increments) |
| 16 | 32–120 (8 GB increments) |

### Auto Scaling for ECS
```yaml
ScalingTarget:
  Type: AWS::ApplicationAutoScaling::ScalableTarget
  Properties:
    MaxCapacity: 10
    MinCapacity: 2
    ResourceId: !Sub "service/${Cluster}/${Service.Name}"
    ScalableDimension: ecs:service:DesiredCount

ScalingPolicy:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyType: TargetTrackingScaling
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 70
      PredefinedMetricSpecification:
        PredefinedMetricType: ECSServiceAverageCPUUtilization
```

---

## 2.2 Amazon Aurora

### What Is It?
MySQL/PostgreSQL-compatible relational database. 5x throughput of standard MySQL, 3x of PostgreSQL.

### Aurora vs RDS

| Feature | Aurora | RDS |
|---------|--------|-----|
| Performance | 5x MySQL, 3x PostgreSQL | Standard |
| Storage | Auto-scales to 128 TB | Manual provisioning |
| Replicas | Up to 15 (auto-failover) | Up to 5 |
| Serverless | Aurora Serverless v2 | ❌ |
| Global | Aurora Global Database | ❌ |
| **Recommendation** | Production workloads | Simple/dev workloads |

### Aurora Serverless v2
- Auto-scales from 0.5 to 128 ACU (Aurora Capacity Units)
- Scales in seconds, not minutes
- Pay for what you use
- Best for: Variable workloads, development, new applications

### Migration from Oracle to Aurora
1. Use **AWS Schema Conversion Tool (SCT)** — Convert schemas, stored procedures
2. Use **AWS Database Migration Service (DMS)** — Continuous data replication
3. **Strategy**: Oracle → Aurora PostgreSQL (most compatible)

### Aurora Best Practices
- Use Aurora Serverless v2 for variable workloads
- Enable **RDS Proxy** for Lambda connections (connection pooling)
- Multi-AZ by default (6 copies across 3 AZs)
- Use reader endpoints for read-heavy workloads
- Enable Performance Insights for monitoring

### RDS Proxy (Critical for Lambda + Aurora)
```
Lambda Function → RDS Proxy → Aurora
                  (pools 100s of connections into few DB connections)
```
Without RDS Proxy, each Lambda invocation opens a new DB connection, exhausting the database connection limit.

---

## 2.3 Amazon ElastiCache

### What Is It?
Managed Redis or Memcached — in-memory caching.

### Redis vs Memcached

| Feature | Redis | Memcached |
|---------|-------|-----------|
| Data structures | Rich (strings, lists, sets, sorted sets, hashes) | Simple key-value |
| Persistence | ✅ | ❌ |
| Replication | Multi-AZ, read replicas | ❌ |
| Pub/Sub | ✅ | ❌ |
| **Recommendation** | Default choice | Simple caching only |

### Use Cases
- Session store (replace Java HttpSession)
- Database query cache
- API response cache
- Rate limiting
- Leaderboards (sorted sets)

---

## 2.4 Amazon ECR (Elastic Container Registry)

### What Is It?
Managed Docker container registry — store, manage, deploy container images.

### Key Features
- Lifecycle policies (auto-delete old images)
- Image vulnerability scanning
- Cross-region/cross-account replication
- OCI artifact support

---

# Part 3: Networking & Security

## 3.1 Amazon VPC (Virtual Private Cloud)

### What Is It?
Isolated network on AWS — you control IP ranges, subnets, route tables, gateways.

### Standard VPC Architecture for Migration
```
VPC (10.0.0.0/16)
├── Public Subnet A (10.0.1.0/24)    → ALB, NAT Gateway
├── Public Subnet B (10.0.2.0/24)    → ALB, NAT Gateway
├── Private Subnet A (10.0.10.0/24)  → ECS Tasks, Lambda
├── Private Subnet B (10.0.11.0/24)  → ECS Tasks, Lambda
├── Data Subnet A (10.0.20.0/24)     → Aurora, ElastiCache
└── Data Subnet B (10.0.21.0/24)     → Aurora, ElastiCache

Internet Gateway → Public subnets
NAT Gateway → Private subnets (outbound internet)
No internet → Data subnets (database isolation)
```

### Key Components

| Component | Purpose |
|-----------|---------|
| Internet Gateway | Inbound/outbound internet for public subnets |
| NAT Gateway | Outbound-only internet for private subnets |
| Route Table | Controls traffic routing |
| Security Group | Stateful firewall (instance-level) |
| NACL | Stateless firewall (subnet-level) |
| VPC Endpoints | Private access to AWS services (no internet) |

### Security Group Best Practices
```
ALB Security Group:
  Inbound: 80, 443 from 0.0.0.0/0
  Outbound: All

App Security Group:
  Inbound: 8080 from ALB SG only
  Outbound: All

DB Security Group:
  Inbound: 5432 from App SG only
  Outbound: None needed
```

### VPC Endpoints (Cost Saver)
```yaml
# Gateway Endpoint (free) — S3, DynamoDB
S3Endpoint:
  Type: AWS::EC2::VPCEndpoint
  Properties:
    ServiceName: com.amazonaws.us-east-1.s3
    VpcId: !Ref VPC
    RouteTableIds: [!Ref PrivateRouteTable]

# Interface Endpoint (paid) — All other services
SecretsManagerEndpoint:
  Type: AWS::EC2::VPCEndpoint
  Properties:
    ServiceName: com.amazonaws.us-east-1.secretsmanager
    VpcId: !Ref VPC
    SubnetIds: [!Ref PrivateSubnetA, !Ref PrivateSubnetB]
    PrivateDnsEnabled: true
```

---

## 3.2 AWS IAM (Identity and Access Management)

### What Is It?
Authentication and authorization for AWS. Controls who can do what.

### Key Principles
1. **Least Privilege**: Only grant permissions needed
2. **Use Roles, not Users**: For services and applications
3. **No Long-term Credentials**: Never use access keys in code
4. **MFA Everywhere**: Especially for console access

### IAM Role for Lambda
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:123456789:table/MyTable"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Common IAM Patterns

| Pattern | Implementation |
|---------|---------------|
| Lambda → DynamoDB | IAM Role with DynamoDB permissions |
| Lambda → Aurora | IAM Role + RDS Proxy IAM auth |
| Lambda → S3 | IAM Role with S3 permissions |
| Lambda → Secrets Manager | IAM Role + GetSecretValue |
| ECS Task → AWS Services | Task Execution Role + Task Role |

---

## 3.3 AWS KMS (Key Management Service)

### What Is It?
Managed encryption keys — encrypt data at rest and in transit.

### Encryption Types
- **SSE-S3**: S3-managed keys (default, free)
- **SSE-KMS**: KMS-managed keys (audit trail via CloudTrail)
- **SSE-C**: Customer-provided keys

### Best Practice
- Enable encryption for ALL data at rest (S3, RDS, DynamoDB, EBS)
- Use KMS for sensitive data (audit requirements)
- TLS 1.2+ for all data in transit

---

## 3.4 AWS WAF (Web Application Firewall)

### What Is It?
Web application firewall — protect APIs from common attacks.

### Deploy on
- CloudFront (CDN)
- ALB (Application Load Balancer)
- API Gateway

### Common Rules
- AWS Managed Rules (OWASP Top 10, SQL injection, XSS)
- Rate limiting (prevent DDoS)
- IP whitelist/blacklist
- Geo-restriction

---

## 3.5 Amazon Cognito

### What Is It?
User authentication and authorization — sign-up, sign-in, MFA, social login.

### User Pool vs Identity Pool

| Feature | User Pool | Identity Pool |
|---------|-----------|---------------|
| Purpose | Authentication (who you are) | Authorization (what you can access) |
| Provides | JWT tokens | AWS credentials |
| Use case | Sign-up/sign-in | Access AWS services from frontend |

### When to Use
- Replace custom authentication code
- Replace LDAP/Active Directory (or federate)
- Social login (Google, Facebook, Apple)
- MFA enforcement
- API Gateway JWT authorization

---

## 3.6 AWS Secrets Manager

### What Is It?
Managed secret storage — store and rotate database credentials, API keys, tokens.

### Key Features
- Automatic rotation (Lambda-based)
- Encrypted with KMS
- Cross-account access
- Versioning

### Usage in Lambda
```java
// Java
SecretsManagerClient client = SecretsManagerClient.create();
GetSecretValueResponse response = client.getSecretValue(
    GetSecretValueRequest.builder().secretId("prod/db/credentials").build()
);
String secret = response.secretString();
// Parse JSON: {"username": "admin", "password": "..."}
```

### Best Practice
- **Never** store secrets in environment variables, code, or config files
- Use Secrets Manager for all credentials
- Enable automatic rotation
- Cache secrets in Lambda (initialize outside handler)

---

# Part 4: CI/CD & Infrastructure as Code

## 4.1 AWS CDK (Cloud Development Kit)

### What Is It?
Infrastructure as Code using familiar programming languages (TypeScript, Python, Java).

### CDK vs CloudFormation vs Terraform

| Feature | CDK | CloudFormation | Terraform |
|---------|-----|---------------|-----------|
| Language | TypeScript, Python, Java | YAML/JSON | HCL |
| Abstraction | High (constructs) | Low (resources) | Medium |
| Learning curve | Moderate | Steep | Moderate |
| Multi-cloud | ❌ | ❌ | ✅ |
| **Recommendation** | AWS-focused teams | Legacy/compliance | Multi-cloud |

### CDK Example: Lambda + API Gateway
```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigw from 'aws-cdk-lib/aws-apigateway';

export class MyStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    const fn = new lambda.Function(this, 'Handler', {
      runtime: lambda.Runtime.JAVA_21,
      handler: 'com.example.Handler::handleRequest',
      code: lambda.Code.fromAsset('target/app.jar'),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(30),
      architecture: lambda.Architecture.ARM_64,
      snapStart: lambda.SnapStartConf.ON_PUBLISHED_VERSIONS,
    });

    new apigw.LambdaRestApi(this, 'Api', { handler: fn });
  }
}
```

### CDK Commands
```bash
cdk init app --language typescript  # Create project
cdk synth                           # Generate CloudFormation
cdk diff                            # Preview changes
cdk deploy                          # Deploy to AWS
cdk destroy                         # Tear down
```

---

## 4.2 AWS SAM (Serverless Application Model)

### What Is It?
CloudFormation extension for serverless — simpler syntax for Lambda, API Gateway, DynamoDB.

### SAM Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: java21
    MemorySize: 512
    Timeout: 30
    Architectures: [arm64]
    SnapStart:
      ApplyOn: PublishedVersions
    Environment:
      Variables:
        TABLE_NAME: !Ref UsersTable

Resources:
  GetUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: com.example.GetUserHandler::handleRequest
      CodeUri: target/
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref UsersTable
      Events:
        GetUser:
          Type: HttpApi
          Properties:
            Path: /users/{id}
            Method: get

  UsersTable:
    Type: AWS::Serverless::SimpleTable
    Properties:
      PrimaryKey:
        Name: userId
        Type: String
```

### SAM CLI Commands
```bash
sam init                    # Create project from template
sam build                   # Build artifacts
sam local invoke            # Test locally
sam local start-api         # Local API Gateway
sam deploy --guided         # Deploy (first time)
sam deploy                  # Deploy (subsequent)
sam logs -n GetUserFunction # View logs
```

---

## 4.3 CI/CD Pipeline

### Recommended CI/CD Architecture
```
GitHub/CodeCommit → CodePipeline → CodeBuild → Deploy (SAM/CDK)
                                      ↓
                                   Test Stage
                                      ↓
                              Manual Approval (prod)
                                      ↓
                              Deploy to Production
```

### CodeBuild buildspec.yml
```yaml
version: 0.2
phases:
  install:
    runtime-versions:
      java: corretto21
  build:
    commands:
      - mvn clean package -DskipTests
      - sam build
  post_build:
    commands:
      - sam deploy --no-confirm-changeset --no-fail-on-empty-changeset
artifacts:
  files:
    - '**/*'
```

### GitHub Actions Alternative
```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'corretto'
      - run: mvn clean package
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-deploy
          aws-region: us-east-1
      - uses: aws-actions/setup-sam@v2
      - run: sam build && sam deploy
```

---

# Part 5: Migration Methodology

## 5.1 AWS Migration Framework (6R)

```
┌─────────────────────────────────────────────────────────────┐
│                    6R DECISION TREE                          │
│                                                             │
│  Is the app still needed?                                   │
│  ├── No → RETIRE                                            │
│  └── Yes                                                    │
│      ├── Is there a SaaS replacement?                       │
│      │   └── Yes, better fit → REPURCHASE                   │
│      ├── Is it ready for cloud? Low risk?                   │
│      │   └── Yes → REHOST (Lift & Shift)                    │
│      ├── Can we use managed services with small changes?    │
│      │   └── Yes → REPLATFORM (Lift & Reshape)              │
│      ├── Is it strategic? Worth investing in?               │
│      │   └── Yes → REFACTOR (Re-architect)                  │
│      └── Too complex? Compliance blocker?                   │
│          └── Yes → RETAIN (Keep on-prem)                    │
└─────────────────────────────────────────────────────────────┘
```

## 5.2 Migration cho dự án hiện tại

### Java → Serverless
```
Phase 1: Assess (2-4 weeks)
  → Inventory all Java apps
  → Map dependencies
  → Score migration readiness
  → Choose 6R per component

Phase 2: Foundation (2-4 weeks)
  → Set up AWS accounts (multi-account)
  → Configure VPC, IAM, security baseline
  → Set up CI/CD pipeline
  → Set up monitoring (CloudWatch, X-Ray)

Phase 3: Pilot (4-8 weeks)
  → Pick 1 simple app (quick win)
  → Migrate using strangler fig
  → Validate performance, cost
  → Document lessons learned

Phase 4: Migrate Waves (ongoing)
  → Wave 1: Easy apps (2-3 apps)
  → Wave 2: Medium complexity
  → Wave 3: Complex apps
  → Each wave: Build → Test → Deploy → Monitor → Optimize

Phase 5: Optimize (ongoing)
  → Right-size resources
  → Enable Savings Plans
  → Optimize cold starts
  → Automate operations
```

### Struts → Spring Migration
```
Step 1: Spring Boot project setup (alongside Struts)
Step 2: Migrate service layer (framework-independent)
Step 3: Convert Actions → Controllers (incrementally)
Step 4: Migrate views (JSP → Thymeleaf or REST API)
Step 5: Migrate security (custom → Spring Security)
Step 6: Remove Struts dependencies
Step 7: Containerize Spring Boot → Deploy to ECS/Lambda
```

### Low-Code/WebPerformer Migration
```
Step 1: Inventory screens, workflows, data models
Step 2: Extract and document business logic
Step 3: Choose target (custom dev vs alternative low-code vs SaaS)
Step 4: Redesign on target platform
Step 5: Parallel run and validate
Step 6: Cutover
```

---

# Part 6: Cost Optimization

## 6.1 Cost Saving Strategies

| Strategy | Savings | When |
|----------|---------|------|
| ARM64 / Graviton | 20% | Lambda, Fargate, EC2 |
| Savings Plans (1yr/3yr) | 17-72% | Stable workloads |
| Spot Instances | 60-90% | Batch processing, CI/CD |
| Aurora Serverless v2 | Variable | Unpredictable DB traffic |
| Lambda SnapStart | Indirect (less provisioned concurrency) | Java Lambda |
| HTTP API vs REST API | 70% | Most APIs |
| DynamoDB On-Demand → Provisioned | 30-70% | Stable access patterns |
| S3 Intelligent-Tiering | Automatic | Unknown access patterns |
| NAT Gateway → VPC Endpoints | 50%+ | High-volume S3/DynamoDB |
| Right-sizing | 10-40% | All compute |

## 6.2 Cost Monitoring
- **AWS Cost Explorer**: Visual cost analysis
- **AWS Budgets**: Alert when costs exceed threshold
- **Compute Optimizer**: Right-sizing recommendations
- **Cost Allocation Tags**: Tag all resources for cost tracking

---

# Quick Reference Cards

## Decision Matrix: Where to Run Your Java App?

| Current State | Target | AWS Service |
|---------------|--------|-------------|
| Stateless REST API, <15 min | Serverless | Lambda + API Gateway |
| Stateless REST API, consistent load | Container | ECS Fargate + ALB |
| Stateful web app (sessions) | Container | ECS Fargate + ElastiCache |
| Batch job, <15 min | Serverless | Step Functions + Lambda |
| Batch job, >15 min | Container | ECS Fargate (scheduled) or AWS Batch |
| Message consumer | Serverless | Lambda + SQS |
| WebSocket server | Container | ECS Fargate + ALB |

## Database Decision Matrix

| Need | Service |
|------|---------|
| Relational, complex queries, transactions | Aurora PostgreSQL |
| Key-value, high throughput, simple queries | DynamoDB |
| Session store, caching | ElastiCache Redis |
| Full-text search | OpenSearch |
| Time-series | Timestream |
| Graph database | Neptune |

## Authentication Decision Matrix

| Scenario | Solution |
|----------|----------|
| New app, need user management | Cognito User Pool |
| Existing LDAP/AD | Cognito + SAML federation |
| Service-to-service auth | IAM Roles |
| API key management | API Gateway API Keys |
| JWT validation only | API Gateway JWT Authorizer |

## Monitoring Essentials

| What | Service | Setup |
|------|---------|-------|
| Logs | CloudWatch Logs | Structured JSON (Powertools) |
| Metrics | CloudWatch Metrics | Custom metrics + dashboards |
| Traces | AWS X-Ray | Enable in Lambda/ECS |
| Alerts | CloudWatch Alarms | Error rate, latency P99, 5xx |
| Cost | AWS Budgets | Monthly threshold alerts |

---

> **Next Steps for SA:**
> 1. Get AWS Certified Solutions Architect - Associate (SAA-C03)
> 2. Practice with AWS Free Tier
> 3. Build a sample migration PoC
> 4. Review AWS Well-Architected Framework
> 5. Study AWS Prescriptive Guidance for migration patterns
