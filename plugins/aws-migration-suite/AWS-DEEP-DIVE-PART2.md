# AWS Deep Dive — ECS Fargate, Aurora + RDS Proxy

---

# Deep Dive 4: ECS Fargate + ALB

## 4.1 Complete Architecture

```
                    ┌─── Route 53 (DNS) ───┐
                    │                       │
               CloudFront (CDN, optional)
                    │
                AWS WAF
                    │
              ┌─────┴─────┐
              │    ALB     │  (Public Subnets)
              │ Port 443   │
              └─────┬─────┘
                    │ Target Group (health checks)
         ┌──────────┼──────────┐
    ┌────┴────┐ ┌───┴───┐ ┌───┴───┐
    │ Task 1  │ │Task 2 │ │Task 3 │  (Private Subnets)
    │Container│ │       │ │       │
    └────┬────┘ └───┬───┘ └───┬───┘
         │          │         │
    ┌────┴──────────┴─────────┴────┐
    │  Aurora Cluster / ElastiCache │  (Data Subnets)
    └──────────────────────────────┘
```

## 4.2 Deployment Strategies

### Rolling Deployment (Default)
```yaml
# ECS Service
DeploymentConfiguration:
  MinimumHealthyPercent: 100  # Keep all old tasks running
  MaximumPercent: 200         # Double capacity during deploy
  DeploymentCircuitBreaker:
    Enable: true
    Rollback: true            # Auto-rollback on failure
```

### Blue/Green Deployment (CodeDeploy)
```yaml
# Complete Blue/Green setup
Resources:
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      DeploymentController:
        Type: CODE_DEPLOY
      LoadBalancers:
        - TargetGroupArn: !Ref BlueTargetGroup
          ContainerName: app
          ContainerPort: 8080

  CodeDeployApplication:
    Type: AWS::CodeDeploy::Application
    Properties:
      ComputePlatform: ECS

  DeploymentGroup:
    Type: AWS::CodeDeploy::DeploymentGroup
    Properties:
      DeploymentConfigName: CodeDeployDefault.ECSAllAtOnce  # or ECSCanary10Percent5Minutes
      ECSServices:
        - ClusterName: !Ref Cluster
          ServiceName: !GetAtt ECSService.Name
      LoadBalancerInfo:
        TargetGroupPairInfoList:
          - TargetGroups:
              - Name: !GetAtt BlueTargetGroup.TargetGroupName
              - Name: !GetAtt GreenTargetGroup.TargetGroupName
            ProdTrafficRoute:
              ListenerArns:
                - !Ref ALBListener
            TestTrafficRoute:
              ListenerArns:
                - !Ref TestListener
      AutoRollbackConfiguration:
        Enabled: true
        Events:
          - DEPLOYMENT_FAILURE
          - DEPLOYMENT_STOP_ON_ALARM
      AlarmConfiguration:
        Alarms:
          - Name: !Ref HighErrorRateAlarm
        Enabled: true
```

### Canary Deployment Options
```
CodeDeployDefault.ECSLinear10PercentEvery1Minutes
  → 10% traffic shift every 1 min (gradual)

CodeDeployDefault.ECSCanary10Percent5Minutes
  → 10% traffic → wait 5 min → 100% (fast validation)

CodeDeployDefault.ECSCanary10Percent15Minutes
  → 10% traffic → wait 15 min → 100% (safer)

CodeDeployDefault.ECSAllAtOnce
  → 100% immediately (fastest, riskiest)
```

## 4.3 Service Connect (Service Mesh)

### What Is It?
ECS-native service mesh — service discovery + load balancing + observability without sidecar complexity.

```yaml
# ECS Service with Service Connect
Service:
  Type: AWS::ECS::Service
  Properties:
    ServiceConnectConfiguration:
      Enabled: true
      Namespace: production
      Services:
        - PortName: http
          DiscoveryName: order-service
          ClientAliases:
            - Port: 8080
              DnsName: order-service
```

```
# Call other services using DNS name
http://order-service:8080/api/orders
http://payment-service:8080/api/payments
```

## 4.4 Logging & Monitoring

### Structured Logging (Spring Boot)
```json
{
  "timestamp": "2024-01-20T10:15:30.123Z",
  "level": "INFO",
  "logger": "com.example.OrderService",
  "message": "Order processed",
  "orderId": "ord-123",
  "userId": "usr-456",
  "duration": 245,
  "traceId": "1-abc-def"
}
```

### CloudWatch Container Insights
```yaml
# Enable Container Insights on cluster
Cluster:
  Type: AWS::ECS::Cluster
  Properties:
    ClusterSettings:
      - Name: containerInsights
        Value: enabled
```

### Auto Scaling Policies
```yaml
# Target Tracking — CPU
CPUScaling:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyType: TargetTrackingScaling
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 70
      PredefinedMetricSpecification:
        PredefinedMetricType: ECSServiceAverageCPUUtilization
      ScaleInCooldown: 300
      ScaleOutCooldown: 60

# Target Tracking — Request Count
RequestScaling:
  Type: AWS::ApplicationAutoScaling::ScalingPolicy
  Properties:
    PolicyType: TargetTrackingScaling
    TargetTrackingScalingPolicyConfiguration:
      TargetValue: 1000  # requests per target
      PredefinedMetricSpecification:
        PredefinedMetricType: ALBRequestCountPerTarget
        ResourceLabel: !Sub "${ALB.FullName}/${TargetGroup.FullName}"
```

## 4.5 Secrets Management in ECS

```yaml
# Task Definition — reference Secrets Manager
ContainerDefinitions:
  - Name: app
    Secrets:
      - Name: DB_PASSWORD
        ValueFrom: arn:aws:secretsmanager:us-east-1:123456:secret:prod/db-AbCdEf
      - Name: API_KEY
        ValueFrom: arn:aws:ssm:us-east-1:123456:parameter/prod/api-key
    Environment:
      - Name: DB_HOST
        Value: !GetAtt AuroraCluster.Endpoint.Address
      - Name: DB_NAME
        Value: mydb
```

## 4.6 Health Checks — Layered Strategy

```
Layer 1: Container Health Check (Docker HEALTHCHECK)
  → "Is the container process running?"
  → CMD: curl -f http://localhost:8080/actuator/health

Layer 2: ALB Target Group Health Check
  → "Is the service responding to HTTP?"
  → Path: /actuator/health
  → Interval: 15s, Threshold: 3, Timeout: 5s

Layer 3: ECS Service Health
  → "Are enough tasks healthy?"
  → Minimum healthy percent + deployment circuit breaker

Layer 4: Route 53 Health Check (multi-region)
  → "Is the regional endpoint healthy?"
  → Failover to secondary region
```

---

# Deep Dive 5: Aurora + RDS Proxy

## 5.1 Aurora Architecture

```
                    ┌───────────────────┐
                    │  Cluster Endpoint │ (Writer)
                    │  port 5432        │
                    └────────┬──────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
         │ Storage │  │ Storage │  │ Storage │
         │  Copy 1 │  │  Copy 2 │  │  Copy 3 │
         │  (AZ-a) │  │  (AZ-b) │  │  (AZ-c) │
         └─────────┘  └─────────┘  └─────────┘
              ↑              ↑              ↑
    Writer Instance   Reader Instance  Reader Instance
    (Primary)         (auto-failover)  (read scaling)
                             │
                    ┌────────┴──────────┐
                    │ Reader Endpoint   │ (Load balanced)
                    │ port 5432         │
                    └───────────────────┘
```

### Storage: 6 copies across 3 AZs
- Tolerates loss of 2 copies for writes
- Tolerates loss of 3 copies for reads
- Self-healing with peer-to-peer replication

## 5.2 Aurora Serverless v2

### Configuration
```yaml
AuroraCluster:
  Type: AWS::RDS::DBCluster
  Properties:
    Engine: aurora-postgresql
    EngineVersion: '16.1'
    ServerlessV2ScalingConfiguration:
      MinCapacity: 0.5    # Minimum ACU (Aurora Capacity Units)
      MaxCapacity: 128     # Maximum ACU
    MasterUsername: !Sub '{{resolve:secretsmanager:${DBSecret}:SecretString:username}}'
    MasterUserPassword: !Sub '{{resolve:secretsmanager:${DBSecret}:SecretString:password}}'
    VpcSecurityGroupIds:
      - !Ref DBSecurityGroup
    DBSubnetGroupName: !Ref DBSubnetGroup

AuroraInstance:
  Type: AWS::RDS::DBInstance
  Properties:
    DBClusterIdentifier: !Ref AuroraCluster
    DBInstanceClass: db.serverless
    Engine: aurora-postgresql
```

### ACU Scaling
```
1 ACU ≈ 2 GB memory
0.5 ACU = minimum (1 GB memory) — good for dev/idle
128 ACU = maximum (256 GB memory) — production peak

Scaling: Increments of 0.5 ACU, scales in seconds

Cost: ~$0.12/ACU-hour (on-demand, us-east-1)
  0.5 ACU idle: ~$0.06/hr = ~$43/month
  8 ACU active: ~$0.96/hr
  32 ACU peak:  ~$3.84/hr
```

## 5.3 RDS Proxy (Critical for Lambda)

### The Problem
```
Without RDS Proxy:
  1000 concurrent Lambda invocations
  = 1000 database connections
  = Database overwhelmed (max_connections ≈ 500-5000)
  = Connection errors, timeouts

With RDS Proxy:
  1000 concurrent Lambda invocations
  → RDS Proxy pools to ~50 actual connections
  → Database happy
```

### Setup
```yaml
RDSProxy:
  Type: AWS::RDS::DBProxy
  Properties:
    DBProxyName: my-app-proxy
    EngineFamily: POSTGRESQL
    Auth:
      - AuthScheme: SECRETS
        SecretArn: !Ref DBSecret
        IAMAuth: REQUIRED  # Use IAM auth instead of password
    RoleArn: !GetAtt ProxyRole.Arn
    VpcSubnetIds:
      - !Ref PrivateSubnetA
      - !Ref PrivateSubnetB
    VpcSecurityGroupIds:
      - !Ref ProxySecurityGroup

ProxyTargetGroup:
  Type: AWS::RDS::DBProxyTargetGroup
  Properties:
    DBProxyName: !Ref RDSProxy
    DBClusterIdentifiers:
      - !Ref AuroraCluster
    TargetGroupName: default
    ConnectionPoolConfigurationInfo:
      MaxConnectionsPercent: 90
      MaxIdleConnectionsPercent: 50
      ConnectionBorrowTimeout: 120
```

### Lambda → RDS Proxy (IAM Auth)
```java
// Generate IAM auth token (no password!)
RdsUtilities rdsUtilities = RdsClient.create().utilities();
String authToken = rdsUtilities.generateAuthenticationToken(
    GenerateAuthenticationTokenRequest.builder()
        .hostname(System.getenv("DB_PROXY_ENDPOINT"))
        .port(5432)
        .username(System.getenv("DB_USERNAME"))
        .build()
);

// Connect with auth token
Properties props = new Properties();
props.setProperty("user", System.getenv("DB_USERNAME"));
props.setProperty("password", authToken);
props.setProperty("ssl", "true");
props.setProperty("sslmode", "require");

Connection conn = DriverManager.getConnection(
    "jdbc:postgresql://" + System.getenv("DB_PROXY_ENDPOINT") + ":5432/mydb",
    props
);
```

### Spring Boot + RDS Proxy
```yaml
# application.yml
spring:
  datasource:
    url: jdbc:postgresql://${DB_PROXY_ENDPOINT}:5432/mydb
    username: ${DB_USERNAME}
    hikari:
      maximum-pool-size: 2         # Lambda: keep small!
      minimum-idle: 0
      idle-timeout: 60000
      connection-timeout: 5000
      max-lifetime: 900000         # 15 min (before Lambda reuse timeout)
```

## 5.4 Oracle to Aurora PostgreSQL Migration

### Phase 1: Schema Conversion (AWS SCT)
```
Oracle                     → Aurora PostgreSQL
──────────────────────────────────────────────
NUMBER                     → NUMERIC / BIGINT / INTEGER
VARCHAR2(N)                → VARCHAR(N)
DATE                       → TIMESTAMP
CLOB                       → TEXT
BLOB                       → BYTEA
SEQUENCE                   → SERIAL / BIGSERIAL / IDENTITY
NVL(a, b)                  → COALESCE(a, b)
SYSDATE                    → CURRENT_TIMESTAMP
ROWNUM                     → ROW_NUMBER() OVER() / LIMIT
DECODE()                   → CASE WHEN
CONNECT BY                 → WITH RECURSIVE (CTE)
DBMS_OUTPUT                → RAISE NOTICE
PL/SQL Package             → Schema + Functions
Materialized View          → Materialized View (similar)
```

### Phase 2: Data Migration (AWS DMS)
```
Source (Oracle) → DMS Replication Instance → Target (Aurora PostgreSQL)
  ├── Full Load (initial)
  ├── CDC (Change Data Capture) — ongoing
  └── Validation (row-by-row comparison)

DMS Task Types:
1. Full load only — migrate existing data
2. Full load + CDC — migrate + keep in sync
3. CDC only — replicate ongoing changes
```

### Phase 3: Application Changes
```
JDBC Driver:   ojdbc → postgresql
Connection:    oracle:thin:@host:1521:SID → postgresql://host:5432/db
SQL Syntax:    Fix Oracle-specific SQL (SCT helps identify)
Stored Procs:  Convert PL/SQL → PL/pgSQL (SCT auto-converts ~80%)
Sequences:     Oracle SEQ.NEXTVAL → PostgreSQL NEXTVAL('seq')
Pagination:    ROWNUM → LIMIT/OFFSET or keyset pagination
```

## 5.5 Aurora Monitoring

### Key Metrics to Watch
```
CPU Utilization        — Target: <70% average
Database Connections   — Watch for exhaustion
Read/Write IOPS       — Capacity planning
Replication Lag        — Reader freshness (<100ms ideal)
Deadlocks              — Application design issue
Buffer Cache Hit Ratio — Target: >99%
Free Local Storage     — Temp space for queries
Serverless ACU         — Actual vs max capacity
```

### Performance Insights
```
Top SQL:           Identify slow queries
Wait Events:       CPU, IO, Lock contention
Database Load:     vCPU usage over time
Host Metrics:      Memory, network, storage
```

---

# ECS vs Lambda Decision Deep Dive

## Detailed Comparison

| Dimension | Lambda | ECS Fargate |
|-----------|--------|-------------|
| **Max execution** | 15 min | Unlimited |
| **Max memory** | 10 GB | 120 GB |
| **Cold start** | 0.5-10s (Java) | 30-60s (task startup) |
| **Warm start** | <1ms | N/A (always warm) |
| **Scaling speed** | Instant (ms) | Slow (minutes) |
| **Scale to zero** | ✅ (no cost idle) | ❌ (min 1 task) |
| **Min cost (idle)** | $0/month | ~$15/month (0.25 vCPU) |
| **Networking** | VPC optional | VPC always |
| **Persistent storage** | ❌ (only /tmp) | EFS, EBS volumes |
| **GPU** | ❌ | ✅ |
| **WebSocket** | Limited (via API GW) | ✅ native |
| **Container image** | Up to 10 GB | Unlimited |
| **Deployment** | Per function | Per service |
| **Port binding** | ❌ | Any port |

## Cost Crossover Point
```
At ~3M requests/month with 500ms avg duration, 1 GB memory:

Lambda:  3M × $0.20/M + (3M × 0.5s × 1GB × $0.0000166667) = $25.60
Fargate: 1 task × 0.5 vCPU × $0.04048/hr × 730hr + 1GB × $0.004445/hr × 730hr = $32.79

Lambda wins for low-medium traffic.
Fargate wins at consistent high traffic (>5-10M requests/month).
```
