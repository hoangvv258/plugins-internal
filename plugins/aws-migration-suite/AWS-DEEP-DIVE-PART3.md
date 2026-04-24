# AWS Deep Dive — VPC + Security, CI/CD Pipeline

---

# Deep Dive 6: VPC + Security Architecture

## 6.1 Multi-Account Strategy

### AWS Organizations Structure
```
Management Account (root)
├── Security OU
│   ├── Log Archive Account      (CloudTrail, Config, centralized logs)
│   └── Security Tooling Account (GuardDuty, Security Hub, Inspector)
├── Infrastructure OU
│   ├── Network Hub Account      (Transit Gateway, DNS, shared VPCs)
│   └── Shared Services Account  (CI/CD, container registry, artifacts)
├── Workloads OU
│   ├── Development Account      (dev environment)
│   ├── Staging Account          (staging/UAT)
│   └── Production Account       (production)
└── Sandbox OU
    └── Sandbox Account          (experimentation)
```

### Why Multi-Account?
- **Blast radius**: Mistake in dev won't affect prod
- **Billing**: Clear cost allocation per environment
- **Security**: Separate IAM boundaries per environment
- **Compliance**: Isolate regulated workloads
- **Service limits**: Each account has its own limits

### Minimum for Migration Project
```
Account 1: Shared Services (CI/CD, ECR, shared infra)
Account 2: Development
Account 3: Production

Use AWS Control Tower for automated setup.
```

## 6.2 Production VPC Design

### Complete VPC with CDK
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;

  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    this.vpc = new ec2.Vpc(this, 'ProductionVPC', {
      ipAddresses: ec2.IpAddresses.cidr('10.0.0.0/16'),
      maxAzs: 3,
      natGateways: 2, // 2 for HA, 1 for cost saving
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,   // /24 = 254 IPs per subnet
        },
        {
          name: 'Application',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 20,   // /20 = 4094 IPs (for ECS tasks, Lambda)
        },
        {
          name: 'Database',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,   // /24 = 254 IPs (database instances)
        },
      ],
    });

    // VPC Flow Logs (security audit)
    this.vpc.addFlowLog('FlowLogs', {
      destination: ec2.FlowLogDestination.toCloudWatchLogs(),
      trafficType: ec2.FlowLogTrafficType.ALL,
    });
  }
}
```

### Subnet Sizing Guide
```
/16 = 65,534 IPs  (VPC)
/20 = 4,094 IPs   (Application subnets — room for many tasks)
/24 = 254 IPs     (Public, Database — fewer resources)
/28 = 14 IPs      (Minimum for NAT Gateway, VPN endpoints)

Rule: Always use larger subnets than you think you need.
      IP addresses within a VPC are free.
```

## 6.3 Network Segmentation

### Security Groups (Layered)
```
Internet → [ALB SG] → [App SG] → [DB SG]
                                → [Cache SG]

ALB Security Group:
  Inbound:
    - TCP 443 from 0.0.0.0/0 (HTTPS)
    - TCP 80 from 0.0.0.0/0  (HTTP → redirect to HTTPS)
  Outbound:
    - TCP 8080 to App SG

App Security Group (ECS Tasks):
  Inbound:
    - TCP 8080 from ALB SG only
  Outbound:
    - TCP 5432 to DB SG (PostgreSQL)
    - TCP 6379 to Cache SG (Redis)
    - TCP 443  to 0.0.0.0/0 (AWS APIs via NAT/VPC Endpoints)

DB Security Group:
  Inbound:
    - TCP 5432 from App SG only
  Outbound: (none — database doesn't initiate connections)

Cache Security Group:
  Inbound:
    - TCP 6379 from App SG only
  Outbound: (none)

Lambda Security Group:
  Inbound: (none — Lambda initiates connections)
  Outbound:
    - TCP 5432 to DB SG (via RDS Proxy)
    - TCP 443  to 0.0.0.0/0 (AWS APIs)
```

## 6.4 VPC Endpoints (Cost & Security)

### Why VPC Endpoints?
```
Without VPC Endpoints:
  Lambda/ECS → NAT Gateway → Internet → S3/DynamoDB/etc.
  Cost: $0.045/GB data processing (NAT Gateway)

With VPC Gateway Endpoint (S3, DynamoDB):
  Lambda/ECS → Gateway Endpoint → S3/DynamoDB
  Cost: FREE

With VPC Interface Endpoint (other services):
  Lambda/ECS → Interface Endpoint → SecretsManager/SQS/etc.
  Cost: ~$7.20/month per endpoint + $0.01/GB

SAVINGS: If processing 1 TB/month through NAT:
  NAT Gateway: $45/month data + $32/month hourly = $77/month
  VPC Gateway: $0 (S3/DynamoDB traffic)
```

### Essential VPC Endpoints
```yaml
# CDK setup
// Gateway Endpoints (FREE)
vpc.addGatewayEndpoint('S3Endpoint', {
  service: ec2.GatewayVpcEndpointAwsService.S3,
});
vpc.addGatewayEndpoint('DynamoDBEndpoint', {
  service: ec2.GatewayVpcEndpointAwsService.DYNAMODB,
});

// Interface Endpoints (paid, but avoid NAT + improve security)
vpc.addInterfaceEndpoint('SecretsManagerEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
});
vpc.addInterfaceEndpoint('SQSEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.SQS,
});
vpc.addInterfaceEndpoint('ECREndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.ECR,
});
vpc.addInterfaceEndpoint('ECRDockerEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
});
vpc.addInterfaceEndpoint('CloudWatchLogsEndpoint', {
  service: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
});
```

## 6.5 AWS PrivateLink

### What Is It?
Expose your service privately to other VPCs/accounts without internet, VPC peering, or Transit Gateway.

```
Account A (Service Provider):
  NLB → ECS Service

Account B (Consumer):
  VPC Endpoint → PrivateLink → NLB → ECS Service

Traffic stays on AWS backbone. No internet exposure.
```

### Use Cases
- SaaS integration (private API access)
- Cross-account microservices
- Partner API exposure

## 6.6 Transit Gateway (Multi-VPC)

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Dev VPC │  │Stage VPC│  │Prod VPC │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┼────────────┘
                  │
         ┌───────┴───────┐
         │Transit Gateway │
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │ Shared VPC    │ (NAT, DNS, Egress)
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │   Internet    │
         └───────────────┘

Routing:
- Dev ↔ Shared ✅
- Stage ↔ Shared ✅
- Prod ↔ Shared ✅
- Dev ↔ Prod ❌ (isolated by route table)
```

## 6.7 IAM Advanced Patterns

### Service Control Policies (SCPs)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRegionsExceptApproved",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": ["us-east-1", "ap-northeast-1"]
        }
      }
    },
    {
      "Sid": "RequireIMDSv2",
      "Effect": "Deny",
      "Action": "ec2:RunInstances",
      "Resource": "arn:aws:ec2:*:*:instance/*",
      "Condition": {
        "StringNotEquals": {
          "ec2:MetadataHttpTokens": "required"
        }
      }
    }
  ]
}
```

### Permission Boundary
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "dynamodb:*",
        "s3:*",
        "sqs:*",
        "sns:*",
        "logs:*",
        "xray:*",
        "cloudwatch:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "iam:CreateUser",
        "iam:CreateRole",
        "organizations:*",
        "account:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### Cross-Account Access
```json
// Account A (Resource Account) — Trust Policy on Role
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::ACCOUNT_B:root"
    },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": {
        "sts:ExternalId": "unique-external-id"
      }
    }
  }]
}

// Account B (Caller) — Lambda assumes role in Account A
StsClient stsClient = StsClient.create();
AssumeRoleResponse creds = stsClient.assumeRole(AssumeRoleRequest.builder()
    .roleArn("arn:aws:iam::ACCOUNT_A:role/CrossAccountRole")
    .roleSessionName("lambda-session")
    .externalId("unique-external-id")
    .build());
```

## 6.8 WAF Rules for Migration Project

### Managed Rule Groups
```yaml
WebACL:
  Type: AWS::WAFv2::WebACL
  Properties:
    DefaultAction:
      Allow: {}
    Rules:
      # OWASP Top 10 protection
      - Name: AWSManagedRulesCommonRuleSet
        Priority: 1
        OverrideAction:
          None: {}
        Statement:
          ManagedRuleGroupStatement:
            VendorName: AWS
            Name: AWSManagedRulesCommonRuleSet
        VisibilityConfig:
          SampledRequestsEnabled: true
          CloudWatchMetricsEnabled: true
          MetricName: CommonRules

      # SQL Injection protection
      - Name: AWSManagedRulesSQLiRuleSet
        Priority: 2
        OverrideAction:
          None: {}
        Statement:
          ManagedRuleGroupStatement:
            VendorName: AWS
            Name: AWSManagedRulesSQLiRuleSet

      # Rate limiting
      - Name: RateLimitRule
        Priority: 3
        Action:
          Block: {}
        Statement:
          RateBasedStatement:
            Limit: 2000      # requests per 5-minute window per IP
            AggregateKeyType: IP

      # Block known bad IPs
      - Name: AWSManagedRulesAmazonIpReputationList
        Priority: 4
        OverrideAction:
          None: {}
        Statement:
          ManagedRuleGroupStatement:
            VendorName: AWS
            Name: AWSManagedRulesAmazonIpReputationList
```

## 6.9 Cognito + API Gateway Integration

### User Pool Setup
```yaml
UserPool:
  Type: AWS::Cognito::UserPool
  Properties:
    UserPoolName: migration-app-users
    AutoVerifiedAttributes:
      - email
    MfaConfiguration: OPTIONAL
    EnabledMfas:
      - SOFTWARE_TOKEN_MFA
    Policies:
      PasswordPolicy:
        MinimumLength: 12
        RequireUppercase: true
        RequireLowercase: true
        RequireNumbers: true
        RequireSymbols: true
    Schema:
      - Name: email
        Required: true
        Mutable: true
      - Name: role
        AttributeDataType: String
        Mutable: true

UserPoolClient:
  Type: AWS::Cognito::UserPoolClient
  Properties:
    UserPoolId: !Ref UserPool
    GenerateSecret: false
    ExplicitAuthFlows:
      - ALLOW_USER_SRP_AUTH
      - ALLOW_REFRESH_TOKEN_AUTH
    AccessTokenValidity: 60        # 60 minutes
    RefreshTokenValidity: 30       # 30 days
    PreventUserExistenceErrors: ENABLED
```

### API Gateway JWT Authorizer (HTTP API)
```yaml
HttpApi:
  Type: AWS::Serverless::HttpApi
  Properties:
    Auth:
      DefaultAuthorizer: CognitoAuthorizer
      Authorizers:
        CognitoAuthorizer:
          AuthorizationScopes:
            - openid
            - email
          IdentitySource: $request.header.Authorization
          JwtConfiguration:
            issuer: !Sub "https://cognito-idp.${AWS::Region}.amazonaws.com/${UserPool}"
            audience:
              - !Ref UserPoolClient
```

---

# Deep Dive 7: CI/CD Pipeline

## 7.1 Complete CDK Pipeline

### Pipeline Architecture
```
GitHub Push → CodePipeline → 
  Source Stage → 
  Build Stage (CodeBuild) →
    Unit Tests → Integration Tests → Build Artifacts →
  Deploy Dev →
    Smoke Tests →
  Deploy Staging →
    Load Tests → Manual Approval →
  Deploy Production →
    Canary Deployment → Monitor → Full rollout
```

### CDK Pipelines (Self-Mutating)
```typescript
import * as cdk from 'aws-cdk-lib';
import { CodePipeline, CodePipelineSource, ShellStep } from 'aws-cdk-lib/pipelines';

export class PipelineStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string) {
    super(scope, id);

    const pipeline = new CodePipeline(this, 'Pipeline', {
      pipelineName: 'MigrationAppPipeline',
      synth: new ShellStep('Synth', {
        input: CodePipelineSource.gitHub('org/repo', 'main', {
          authentication: cdk.SecretValue.secretsManager('github-token'),
        }),
        commands: [
          'npm ci',
          'cd app && mvn clean package',
          'cd .. && npx cdk synth',
        ],
        primaryOutputDirectory: 'cdk.out',
      }),
      // Self-mutating: pipeline updates itself when CDK code changes
      selfMutation: true,
    });

    // Dev stage
    const dev = pipeline.addStage(new AppStage(this, 'Dev', {
      env: { account: '111111111111', region: 'us-east-1' },
    }));
    dev.addPost(new ShellStep('SmokeTest', {
      commands: [
        'curl -f https://dev-api.example.com/health',
      ],
    }));

    // Staging stage
    const staging = pipeline.addStage(new AppStage(this, 'Staging', {
      env: { account: '222222222222', region: 'us-east-1' },
    }));
    staging.addPost(new ShellStep('IntegrationTest', {
      commands: [
        'npm run test:integration -- --env staging',
      ],
    }));

    // Production stage (with manual approval)
    const prod = pipeline.addStage(new AppStage(this, 'Production', {
      env: { account: '333333333333', region: 'us-east-1' },
    }));
    prod.addPre(new cdk.pipelines.ManualApprovalStep('PromoteToProd', {
      comment: 'Review staging metrics before deploying to production',
    }));
  }
}

// Application stage — deployed to each environment
class AppStage extends cdk.Stage {
  constructor(scope: cdk.App, id: string, props: cdk.StageProps) {
    super(scope, id, props);

    new VpcStack(this, 'Network');
    new DatabaseStack(this, 'Database');
    new AppStack(this, 'Application');
  }
}
```

## 7.2 Multi-Environment Configuration

### CDK Context for Environment Config
```typescript
// cdk.json
{
  "context": {
    "environments": {
      "dev": {
        "vpcCidr": "10.1.0.0/16",
        "natGateways": 1,
        "auroraMinCapacity": 0.5,
        "auroraMaxCapacity": 4,
        "ecsDesiredCount": 1,
        "ecsMaxCount": 4,
        "lambdaMemory": 512,
        "enableWaf": false,
        "domain": "dev-api.example.com"
      },
      "staging": {
        "vpcCidr": "10.2.0.0/16",
        "natGateways": 2,
        "auroraMinCapacity": 2,
        "auroraMaxCapacity": 16,
        "ecsDesiredCount": 2,
        "ecsMaxCount": 10,
        "lambdaMemory": 1024,
        "enableWaf": true,
        "domain": "staging-api.example.com"
      },
      "production": {
        "vpcCidr": "10.3.0.0/16",
        "natGateways": 3,
        "auroraMinCapacity": 4,
        "auroraMaxCapacity": 64,
        "ecsDesiredCount": 3,
        "ecsMaxCount": 50,
        "lambdaMemory": 1769,
        "enableWaf": true,
        "domain": "api.example.com"
      }
    }
  }
}
```

## 7.3 Testing Strategies

### Test Pyramid for Serverless
```
                    ╱╲
                   ╱  ╲
                  ╱ E2E ╲        (Few, slow, expensive)
                 ╱────────╲      API tests against real endpoints
                ╱Integration╲    (Medium)
               ╱──────────────╲  Lambda + DynamoDB Local
              ╱   Unit Tests    ╲ (Many, fast, cheap)
             ╱────────────────────╲ Business logic only
            ╱   Static Analysis    ╲
           ╱────────────────────────╲ Linting, type checking
```

### Unit Tests (JUnit 5)
```java
@Test
void shouldProcessOrder() {
    // Given
    OrderService service = new OrderService(mockRepository, mockEventPublisher);
    Order order = new Order("ord-001", "usr-001", BigDecimal.valueOf(99.99));
    
    // When
    OrderResult result = service.processOrder(order);
    
    // Then
    assertEquals(OrderStatus.CONFIRMED, result.getStatus());
    verify(mockRepository).save(order);
    verify(mockEventPublisher).publish(any(OrderConfirmedEvent.class));
}
```

### Integration Tests (Testcontainers + LocalStack)
```java
@Testcontainers
class OrderHandlerIntegrationTest {
    
    @Container
    static LocalStackContainer localstack = new LocalStackContainer(
            DockerImageName.parse("localstack/localstack:3.0"))
        .withServices(Service.DYNAMODB, Service.SQS);
    
    @BeforeAll
    static void setup() {
        DynamoDbClient dynamoDb = DynamoDbClient.builder()
            .endpointOverride(localstack.getEndpointOverride(Service.DYNAMODB))
            .build();
        
        dynamoDb.createTable(CreateTableRequest.builder()
            .tableName("Orders")
            .keySchema(
                KeySchemaElement.builder().attributeName("PK").keyType(KeyType.HASH).build(),
                KeySchemaElement.builder().attributeName("SK").keyType(KeyType.RANGE).build()
            )
            .attributeDefinitions(
                AttributeDefinition.builder().attributeName("PK").attributeType(ScalarAttributeType.S).build(),
                AttributeDefinition.builder().attributeName("SK").attributeType(ScalarAttributeType.S).build()
            )
            .billingMode(BillingMode.PAY_PER_REQUEST)
            .build());
    }
    
    @Test
    void shouldSaveOrderToDynamoDB() {
        // Full integration test with real DynamoDB
        OrderHandler handler = new OrderHandler(localstack.getEndpoint());
        APIGatewayProxyRequestEvent request = createRequest("{\"item\": \"test\"}");
        
        APIGatewayProxyResponseEvent response = handler.handleRequest(request, mockContext);
        
        assertEquals(201, response.getStatusCode());
    }
}
```

### SAM Local Testing
```bash
# Invoke single function with event
sam local invoke GetOrderFunction -e events/get-order.json

# Start local API Gateway
sam local start-api --warm-containers EAGER

# Run integration tests against local
sam local start-api &
curl http://localhost:3000/orders/ord-001
```

## 7.4 Monitoring & Observability

### CloudWatch Dashboard (CDK)
```typescript
const dashboard = new cloudwatch.Dashboard(this, 'ServiceDashboard', {
  dashboardName: 'migration-app-prod',
});

// Lambda metrics
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'Lambda Invocations & Errors',
    left: [fn.metricInvocations()],
    right: [fn.metricErrors()],
  }),
  new cloudwatch.GraphWidget({
    title: 'Lambda Duration (P50, P90, P99)',
    left: [
      fn.metricDuration({ statistic: 'p50' }),
      fn.metricDuration({ statistic: 'p90' }),
      fn.metricDuration({ statistic: 'p99' }),
    ],
  }),
);

// ALB metrics
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'ALB Request Count & Response Time',
    left: [alb.metricRequestCount()],
    right: [alb.metricTargetResponseTime()],
  }),
);

// Alarms
new cloudwatch.Alarm(this, 'HighErrorRate', {
  metric: fn.metricErrors({ period: cdk.Duration.minutes(5) }),
  threshold: 10,
  evaluationPeriods: 2,
  alarmDescription: 'Lambda error rate too high',
  actionsEnabled: true,
  alarmActions: [snsTopic],
});

new cloudwatch.Alarm(this, 'HighLatency', {
  metric: fn.metricDuration({
    statistic: 'p99',
    period: cdk.Duration.minutes(5),
  }),
  threshold: 3000, // 3 seconds
  evaluationPeriods: 3,
  alarmDescription: 'P99 latency above 3s',
  actionsEnabled: true,
  alarmActions: [snsTopic],
});
```

### X-Ray Tracing
```
Client → API Gateway → Lambda → DynamoDB
         [trace]       [trace]  [trace]

Full request trace with:
- Latency per service
- Error identification
- Cold start detection
- Bottleneck analysis
```

## 7.5 Rollback Strategies

### Lambda with Aliases and Weights
```yaml
# Gradual traffic shifting
AutoPublishAlias: live
DeploymentPreference:
  Type: Canary10Percent5Minutes  # 10% for 5 min, then 100%
  Alarms:
    - !Ref HighErrorAlarm
    - !Ref HighLatencyAlarm
  Hooks:
    PreTraffic: !Ref PreTrafficTestFunction
    PostTraffic: !Ref PostTrafficTestFunction
```

### ECS with CodeDeploy
```
Blue/Green: Old tasks stay running while new tasks start
  → Traffic shifts to new tasks
  → If alarm fires → automatic rollback to old tasks
  → Old tasks terminated after successful deployment
```

### Database Rollback Strategy
```
Forward-Compatible Migrations:
  1. Add new column (nullable)       ← v2 code can handle both
  2. Deploy code that writes to both ← works with v1 and v2 schema
  3. Backfill data                   ← populate new column
  4. Deploy code that reads new      ← uses new column
  5. Drop old column                 ← cleanup (much later)

NEVER:
  - Drop columns in same deployment as code change
  - Rename columns directly
  - Change column types without migration
```

---

# Appendix: AWS CLI Quick Reference

## Most Used Commands

```bash
# Lambda
aws lambda invoke --function-name my-func output.json
aws lambda list-functions --query 'Functions[].FunctionName'
aws lambda update-function-code --function-name my-func --zip-file fileb://deploy.zip

# ECS
aws ecs list-services --cluster my-cluster
aws ecs describe-services --cluster my-cluster --services my-service
aws ecs update-service --cluster my-cluster --service my-service --force-new-deployment

# DynamoDB
aws dynamodb scan --table-name MyTable --max-items 10
aws dynamodb get-item --table-name MyTable --key '{"PK":{"S":"USER#001"},"SK":{"S":"PROFILE"}}'
aws dynamodb query --table-name MyTable --key-condition-expression "PK = :pk" --expression-attribute-values '{":pk":{"S":"USER#001"}}'

# CloudWatch Logs
aws logs tail /aws/lambda/my-func --follow
aws logs filter-log-events --log-group-name /aws/lambda/my-func --filter-pattern "ERROR"

# Secrets Manager
aws secretsmanager get-secret-value --secret-id prod/db/credentials
aws secretsmanager create-secret --name prod/db/credentials --secret-string '{"username":"admin","password":"..."}'

# S3
aws s3 sync ./build s3://my-bucket/artifacts/
aws s3 cp s3://my-bucket/data.csv ./data.csv

# SSM Parameter Store
aws ssm get-parameter --name /prod/config/api-url --with-decryption
aws ssm put-parameter --name /prod/config/api-url --value "https://api.example.com" --type SecureString

# CloudFormation / CDK
aws cloudformation describe-stacks --stack-name my-stack --query 'Stacks[0].Outputs'
aws cloudformation list-stack-resources --stack-name my-stack
```

---

# Appendix: Study Path & Certifications

## Recommended Learning Order

```
Week 1-2: Foundation
  □ AWS Cloud Practitioner concepts
  □ VPC, IAM, S3 basics
  □ Set up AWS Free Tier account
  □ Deploy first Lambda function

Week 3-4: Serverless
  □ Lambda + API Gateway hands-on
  □ DynamoDB data modeling
  □ SQS, SNS, EventBridge
  □ Step Functions workflow
  □ SAM CLI local development

Week 5-6: Containers & Database
  □ Docker basics → ECS Fargate
  □ Aurora PostgreSQL setup
  □ RDS Proxy configuration
  □ ElastiCache Redis basics

Week 7-8: Production Readiness
  □ CI/CD with CDK Pipelines
  □ Monitoring (CloudWatch, X-Ray)
  □ Security (WAF, Cognito, KMS)
  □ Cost optimization strategies

Week 9-10: Migration Practice
  □ Sample Struts → Spring Boot migration
  □ Deploy to Lambda with SnapStart
  □ Database migration with DMS
  □ Full pipeline deployment

Certification Path:
  1. AWS Solutions Architect Associate (SAA-C03) — start here
  2. AWS Developer Associate (DVA-C02) — hands-on coding
  3. AWS DevOps Professional (DOP-C02) — CI/CD mastery
```

## Essential Resources
```
Official:
- AWS Well-Architected Framework: https://aws.amazon.com/architecture/well-architected/
- AWS Prescriptive Guidance: https://aws.amazon.com/prescriptive-guidance/
- AWS Architecture Center: https://aws.amazon.com/architecture/
- AWS Samples GitHub: https://github.com/aws-samples
- Serverless Land: https://serverlessland.com

Hands-on:
- AWS Workshop Studio: https://workshops.aws
- AWS Skill Builder: https://skillbuilder.aws
- Serverless Patterns: https://serverlessland.com/patterns

Community:
- AWS re:Invent videos (YouTube)
- The Burning Monk blog (Lambda expert)
- AWS Heroes blog posts
```
