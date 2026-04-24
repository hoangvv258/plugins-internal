# Production Readiness, Cost Analysis & API Design

---

# Part 1: Production Readiness Checklist

## 1.1 Pre-Launch Checklist

### Infrastructure
```
□ Multi-AZ deployment for all stateful services
□ Aurora: Writer + Reader, multi-AZ, automated backups (30 days)
□ ElastiCache: Multi-AZ with automatic failover
□ ECS: Minimum 2 tasks across 2 AZs
□ Lambda: No single-AZ dependency
□ NAT Gateway: At least 2 (one per AZ) for production
□ VPC: Properly sized subnets with room to grow
```

### Security
```
□ All data encrypted at rest (S3 SSE, RDS encryption, DynamoDB encryption)
□ All data encrypted in transit (TLS 1.2+ everywhere)
□ WAF enabled on ALB and/or API Gateway
□ Security groups follow least-privilege (specific ports, specific sources)
□ No public access to databases or caches
□ IAM roles follow least-privilege
□ Secrets stored in Secrets Manager (NOT env vars)
□ MFA enabled for all IAM users
□ VPC Flow Logs enabled
□ CloudTrail enabled (all regions)
□ No hardcoded credentials anywhere
□ Container images scanned for vulnerabilities
□ Dependency vulnerability scanning (Dependabot/Snyk)
```

### Monitoring & Alerting
```
□ CloudWatch Dashboards created for key metrics
□ Alarms configured:
  □ Lambda error rate > threshold
  □ Lambda duration P99 > threshold
  □ ECS CPU utilization > 80%
  □ ECS task count at maximum (scaling limit)
  □ Aurora CPU > 80%
  □ Aurora connection count approaching limit
  □ DynamoDB throttled reads/writes
  □ SQS DLQ messages > 0
  □ ALB 5xx error rate > 1%
  □ ALB response time P99 > threshold
□ X-Ray tracing enabled
□ Structured JSON logging
□ Log retention policy set (not infinite)
□ PagerDuty/OpsGenie integration for critical alarms
```

### Deployment & Rollback
```
□ CI/CD pipeline tested end-to-end
□ Blue/Green or Canary deployment configured
□ Automatic rollback on alarm trigger
□ Database migration strategy (forward-compatible)
□ Rollback procedure documented and tested
□ Deployment to production requires manual approval
□ Smoke tests run after every deployment
```

### Performance
```
□ Load testing completed (realistic traffic patterns)
□ Auto-scaling policies configured and tested
□ Lambda: Memory right-sized (Lambda Power Tuning)
□ Lambda: SnapStart enabled for Java
□ Lambda: ARM64 architecture selected
□ ECS: CPU/memory right-sized
□ Aurora: Serverless v2 min/max set appropriately
□ DynamoDB: On-demand or provisioned capacity tuned
□ Connection pooling configured (RDS Proxy for Lambda)
□ API Gateway throttling configured
□ CDN (CloudFront) for static assets
```

### Disaster Recovery
```
□ RPO (Recovery Point Objective) defined
□ RTO (Recovery Time Objective) defined
□ Backup strategy documented:
  □ Aurora: Automated backups + manual snapshots
  □ DynamoDB: Point-in-time recovery enabled
  □ S3: Versioning enabled, cross-region replication (if needed)
□ DR plan documented and tested
□ Runbook for common failure scenarios
```

### Cost
```
□ Tagging strategy implemented (Environment, Service, Owner, CostCenter)
□ AWS Budgets configured with alerts
□ Unused resources identified and removed
□ Reserved capacity / Savings Plans evaluated
□ Cost optimization recommendations reviewed (Compute Optimizer)
```

## 1.2 Disaster Recovery Strategies

### DR Tiers

| Strategy | RPO | RTO | Cost |
|----------|-----|-----|------|
| **Backup & Restore** | Hours | Hours | $ (lowest) |
| **Pilot Light** | Minutes | 10-30 min | $$ |
| **Warm Standby** | Seconds | Minutes | $$$ |
| **Active-Active** | Zero | Zero | $$$$ (highest) |

### Recommended for Migration Project
```
Tier 1 (Critical APIs): Warm Standby
  - Aurora Global Database (cross-region)
  - ECS + Lambda deployable in secondary region
  - Route 53 health checks + failover routing
  - RTO: 5-15 minutes

Tier 2 (Background Processing): Pilot Light
  - Infrastructure templates ready (CDK)
  - Data replicated (Aurora, S3 CRR)
  - Deploy on-demand in DR scenario
  - RTO: 30-60 minutes

Tier 3 (Non-critical): Backup & Restore
  - Regular backups stored cross-region
  - Rebuild from IaC templates
  - RTO: 2-4 hours
```

### Runbook Template
```markdown
# Incident: [SERVICE] Outage

## Detection
- Alert: [Alarm name and description]
- Dashboard: [Link to CloudWatch dashboard]

## Assessment (5 min)
1. Check CloudWatch dashboard for affected services
2. Check X-Ray for error traces
3. Check CloudWatch Logs for error messages
4. Determine scope: single function, service, or region

## Response
### If single Lambda function:
1. Check recent deployment → rollback if needed
   `aws lambda update-alias --function-name X --name live --function-version PREV`
2. Check DLQ for failed messages
3. Check downstream dependencies (DynamoDB, Aurora)

### If ECS service:
1. Check ECS events: `aws ecs describe-services --cluster X --services Y`
2. Force new deployment: `aws ecs update-service --cluster X --service Y --force-new-deployment`
3. Check ALB target health
4. Check container logs

### If database:
1. Check Aurora events in RDS console
2. Check replica lag
3. If primary failure: Aurora auto-failover (<30s)
4. If region failure: promote Aurora Global Database secondary

## Recovery Verification
1. Confirm all health checks passing
2. Verify API responses correct
3. Check error rates returned to baseline
4. Monitor for 30 minutes

## Post-Incident
1. Create incident report
2. Root cause analysis
3. Update runbook if needed
```

---

# Part 2: Cost Analysis & TCO Calculator

## 2.1 Monthly Cost Estimates

### Scenario A: Small (Startup / Dev)
```
Traffic: 1M requests/month, 200ms avg duration

Lambda (ARM64, 1024 MB):
  Requests: 1M × $0.20/M = $0.20
  Duration:  1M × 0.2s × 1GB × $0.0000133334 = $2.67
  Total:    $2.87/month

API Gateway (HTTP API):
  Requests: 1M × $1.00/M = $1.00

DynamoDB (On-Demand):
  Read:   1M × $0.25/M = $0.25
  Write:  200K × $1.25/M = $0.25
  Storage: 1 GB × $0.25 = $0.25
  Total:  $0.75/month

Aurora Serverless v2 (0.5 ACU idle, 2 ACU peak):
  Avg 1 ACU × $0.12/hr × 730hr = $87.60/month

VPC:
  NAT Gateway: 1 × $0.045/hr × 730hr + data = ~$40/month

CloudWatch:
  Logs, metrics, alarms: ~$10/month

TOTAL: ~$142/month
```

### Scenario B: Medium (Production)
```
Traffic: 10M requests/month, 300ms avg duration

Lambda (ARM64, 1769 MB):
  Requests: 10M × $0.20/M = $2.00
  Duration:  10M × 0.3s × 1.73GB × $0.0000133334 = $69.16
  Total:    $71.16/month

API Gateway (HTTP API):
  Requests: 10M × $1.00/M = $10.00

DynamoDB (On-Demand):
  Read:   10M × $0.25/M = $2.50
  Write:  2M × $1.25/M = $2.50
  Storage: 20 GB × $0.25 = $5.00
  Total:  $10.00/month

Aurora Serverless v2 (4 ACU avg):
  4 ACU × $0.12/hr × 730hr = $350.40/month

ECS Fargate (2 tasks, 0.5 vCPU, 1 GB):
  2 × (0.5 × $0.04048 + 1 × $0.004445) × 730hr = $36.00/month

ElastiCache (cache.r7g.large, 2 nodes):
  2 × $0.226/hr × 730hr = $329.96/month

VPC:
  NAT Gateway: 2 × $0.045/hr × 730hr + data = ~$80/month

ALB:
  $0.0225/hr × 730hr + LCU charges = ~$25/month

WAF:
  WebACL: $5 + Rules: $4 × 4 = ~$21/month

CloudWatch + X-Ray:
  ~$30/month

TOTAL: ~$963/month
```

### Scenario C: Large (Enterprise Production)
```
Traffic: 100M requests/month

Lambda + ECS mixed:        ~$800/month
API Gateway:               ~$100/month
DynamoDB:                  ~$150/month
Aurora (16 ACU avg):       ~$1,400/month
ElastiCache:               ~$660/month
VPC + NAT:                 ~$200/month
ALB + WAF:                 ~$100/month
Monitoring:                ~$100/month
S3 + data transfer:        ~$50/month

TOTAL: ~$3,560/month

With 1-year Savings Plan:  ~$2,850/month (20% saving)
With 3-year Savings Plan:  ~$2,100/month (41% saving)
```

## 2.2 TCO Comparison: On-Premise vs AWS

### On-Premise (3-year amortized)
```
Hardware:
  4 servers × $15,000 = $60,000
  Network equipment: $10,000
  Storage (SAN): $30,000
  Amortized: $100,000 / 36 = $2,778/month

Software:
  Oracle license: $47,500/processor × 4 = $190,000
  Amortized: $190,000 / 36 = $5,278/month

Operations:
  2 sysadmins (partial): $10,000/month × 0.3 = $3,000/month
  Data center costs: $500/month
  Power, cooling: $300/month

TOTAL On-Premise: ~$11,856/month
```

### AWS (Medium scenario)
```
Compute + Database + Network: ~$963/month
Operational savings:
  - No sysadmin for infrastructure (managed services)
  - No Oracle license (Aurora PostgreSQL)
  - No data center costs
  - Auto-scaling (no over-provisioning)

TOTAL AWS: ~$963/month

SAVINGS: $10,893/month = $130,716/year = ~92% reduction
```

## 2.3 Cost Optimization Strategies

### Immediate Savings (Week 1)
```
1. ARM64 everywhere                     → 20% Lambda, 20% Fargate
2. HTTP API instead of REST API          → 70% API Gateway
3. DynamoDB On-Demand (start)            → No over-provisioning
4. VPC Gateway Endpoints (S3, DynamoDB)  → Free (vs NAT Gateway)
5. Lambda SnapStart (Java)               → Reduce Provisioned Concurrency need
6. Right-size Lambda memory              → Use Power Tuning tool
```

### Medium-term Savings (Month 1-3)
```
1. Compute Savings Plans (1-year)        → 17% Lambda, 20% Fargate
2. DynamoDB switch to Provisioned        → 30-70% when patterns are stable
3. Aurora Serverless v2 tuning           → Set appropriate min/max
4. S3 Intelligent-Tiering               → Auto-optimize storage costs
5. Log retention optimization            → 30 days hot, archive to S3
```

### Long-term Savings (Month 3+)
```
1. Compute Savings Plans (3-year)        → Up to 72% savings
2. Reserved Instances (ElastiCache, RDS) → 30-60%
3. Spot for batch processing             → 60-90%
4. Review unused resources monthly       → Cost Explorer recommendations
5. Multi-region optimization             → Cheaper regions for non-latency-critical
```

---

# Part 3: API Design Best Practices

## 3.1 RESTful API Design

### URL Structure
```
GET    /api/v1/orders              → List orders
POST   /api/v1/orders              → Create order
GET    /api/v1/orders/{id}         → Get order
PUT    /api/v1/orders/{id}         → Update order
DELETE /api/v1/orders/{id}         → Delete order
GET    /api/v1/orders/{id}/items   → List order items
POST   /api/v1/orders/{id}/items   → Add item to order

Rules:
- Nouns, not verbs (orders, not getOrders)
- Plural nouns (orders, not order)
- Lowercase with hyphens (order-items, not orderItems)
- Version in URL (v1)
- Nested resources max 2 levels deep
```

### Request/Response Format
```json
// Success Response
{
  "data": {
    "orderId": "ord-001",
    "status": "CONFIRMED",
    "items": [...],
    "total": 99.99,
    "createdAt": "2024-01-20T10:30:00Z"
  },
  "meta": {
    "requestId": "req-abc-123",
    "timestamp": "2024-01-20T10:30:01Z"
  }
}

// Error Response
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Order must have at least one item",
    "details": [
      {
        "field": "items",
        "message": "Must not be empty"
      }
    ]
  },
  "meta": {
    "requestId": "req-abc-456",
    "timestamp": "2024-01-20T10:30:02Z"
  }
}

// List Response (with pagination)
{
  "data": [...],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 150,
    "totalPages": 8,
    "nextToken": "eyJsYXN0S2V5..."
  }
}
```

### HTTP Status Codes
```
2xx Success:
  200 OK          → GET, PUT (with body)
  201 Created     → POST (with Location header)
  204 No Content  → DELETE, PUT (no body)
  202 Accepted    → Async operation started

4xx Client Error:
  400 Bad Request    → Validation error
  401 Unauthorized   → Missing/invalid auth token
  403 Forbidden      → Valid token, insufficient permissions
  404 Not Found      → Resource doesn't exist
  409 Conflict       → Duplicate/conflicting state
  422 Unprocessable  → Valid JSON, business rule violation
  429 Too Many Requests → Rate limited

5xx Server Error:
  500 Internal Error   → Unexpected server error
  502 Bad Gateway      → Upstream service error
  503 Service Unavailable → Overloaded or maintenance
  504 Gateway Timeout  → Upstream timeout
```

## 3.2 Pagination Patterns

### Cursor-Based (Recommended for DynamoDB)
```json
// Request
GET /api/v1/orders?limit=20&nextToken=eyJsYXN0S2V5...

// Response
{
  "data": [...],
  "pagination": {
    "limit": 20,
    "nextToken": "eyJsYXN0S2V5...",  // null if no more results
    "hasMore": true
  }
}
```

```java
// Lambda handler with DynamoDB pagination
QueryRequest.Builder query = QueryRequest.builder()
    .tableName(tableName)
    .keyConditionExpression("PK = :pk")
    .expressionAttributeValues(Map.of(":pk", s("USER#" + userId)))
    .limit(pageSize);

// If nextToken provided, decode and set as ExclusiveStartKey
if (nextToken != null) {
    Map<String, AttributeValue> startKey = decodeToken(nextToken);
    query.exclusiveStartKey(startKey);
}

QueryResponse result = dynamoDb.query(query.build());

// Encode LastEvaluatedKey as next token
String newToken = result.lastEvaluatedKey().isEmpty() 
    ? null 
    : encodeToken(result.lastEvaluatedKey());
```

### Offset-Based (for Aurora/SQL)
```json
GET /api/v1/orders?page=2&pageSize=20

{
  "data": [...],
  "pagination": {
    "page": 2,
    "pageSize": 20,
    "totalItems": 150,
    "totalPages": 8
  }
}
```

## 3.3 Error Handling

### Centralized Error Handler (Spring)
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(ResourceNotFoundException ex) {
        return ResponseEntity.status(404).body(new ErrorResponse(
            "NOT_FOUND", ex.getMessage()
        ));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(MethodArgumentNotValidException ex) {
        List<FieldError> details = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> new FieldError(e.getField(), e.getDefaultMessage()))
            .toList();
        return ResponseEntity.status(400).body(new ErrorResponse(
            "VALIDATION_ERROR", "Invalid request", details
        ));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGeneral(Exception ex) {
        log.error("Unexpected error", ex);
        return ResponseEntity.status(500).body(new ErrorResponse(
            "INTERNAL_ERROR", "An unexpected error occurred"
        ));
    }
}
```

### Lambda Error Handling Pattern
```java
public APIGatewayProxyResponseEvent handleRequest(
        APIGatewayProxyRequestEvent request, Context context) {
    try {
        // Validate input
        String id = Optional.ofNullable(request.getPathParameters())
            .map(p -> p.get("id"))
            .orElseThrow(() -> new BadRequestException("Missing order ID"));

        // Business logic
        Order order = service.getOrder(id);
        if (order == null) {
            return errorResponse(404, "NOT_FOUND", "Order not found: " + id);
        }
        return successResponse(200, order);

    } catch (BadRequestException e) {
        return errorResponse(400, "BAD_REQUEST", e.getMessage());
    } catch (Exception e) {
        log.error("Unhandled error", e);
        return errorResponse(500, "INTERNAL_ERROR", "Internal server error");
    }
}
```

## 3.4 API Versioning

### Recommended: URL Versioning
```
/api/v1/orders    → Version 1 (current)
/api/v2/orders    → Version 2 (new)

SAM template:
  Events:
    V1GetOrder:
      Type: HttpApi
      Properties:
        Path: /api/v1/orders/{id}
        Method: get
    V2GetOrder:
      Type: HttpApi
      Properties:
        Path: /api/v2/orders/{id}
        Method: get
```

### Version Migration Strategy
```
Phase 1: Deploy v2 alongside v1 (both active)
Phase 2: Communicate deprecation to consumers
Phase 3: Monitor v1 usage decline
Phase 4: Return 301 redirect from v1 → v2
Phase 5: Remove v1 (after grace period)
```

## 3.5 Rate Limiting & Throttling

### API Gateway Throttling
```yaml
HttpApi:
  Type: AWS::Serverless::HttpApi
  Properties:
    DefaultRouteSettings:
      ThrottlingBurstLimit: 100    # Max concurrent requests
      ThrottlingRateLimit: 50      # Requests per second

# Per-route overrides
    RouteSettings:
      "POST /api/v1/orders":
        ThrottlingBurstLimit: 50
        ThrottlingRateLimit: 25
```

### Client-Side Retry with Exponential Backoff
```java
// AWS SDK v2 built-in retry
DynamoDbClient dynamoDb = DynamoDbClient.builder()
    .overrideConfiguration(ClientOverrideConfiguration.builder()
        .retryPolicy(RetryPolicy.builder()
            .numRetries(3)
            .build())
        .build())
    .build();

// Custom retry logic
public <T> T retryWithBackoff(Supplier<T> operation, int maxRetries) {
    for (int i = 0; i <= maxRetries; i++) {
        try {
            return operation.get();
        } catch (ThrottlingException | ServiceUnavailableException e) {
            if (i == maxRetries) throw e;
            long delay = (long) Math.pow(2, i) * 100 + random.nextInt(100);
            Thread.sleep(delay);
        }
    }
    throw new RuntimeException("Exhausted retries");
}
```

## 3.6 API Security Checklist
```
□ HTTPS only (TLS 1.2+)
□ Authentication on all endpoints (Cognito JWT / IAM)
□ Authorization checks (user can only access their own data)
□ Input validation (size limits, format, allowed values)
□ Output sanitization (no sensitive data in responses)
□ Rate limiting (API Gateway throttling)
□ WAF enabled (SQL injection, XSS, rate limiting)
□ CORS configured (specific origins, not *)
□ Request size limits
□ No sensitive data in URLs or query parameters
□ API keys for third-party consumers (usage tracking)
□ Audit logging (CloudTrail + custom logs)
```

---

# Part 4: Monitoring & Alerting Guide

## 4.1 Four Golden Signals

```
1. LATENCY    — How long requests take
   Metrics: P50, P90, P99 duration
   Lambda:  Duration metric
   ECS:     ALB TargetResponseTime

2. TRAFFIC    — How many requests
   Metrics: Requests per second/minute
   Lambda:  Invocations metric
   ECS:     ALB RequestCount

3. ERRORS     — Error rate
   Metrics: Error count, error rate %
   Lambda:  Errors metric, Throttles
   ECS:     ALB HTTPCode_Target_5XX_Count

4. SATURATION — Resource utilization
   Metrics: CPU, memory, connections
   Lambda:  ConcurrentExecutions
   ECS:     CPUUtilization, MemoryUtilization
   Aurora:  DatabaseConnections, CPUUtilization
```

## 4.2 CloudWatch Alarm Configuration

### Critical Alarms (PagerDuty/OpsGenie)
```yaml
# Lambda Error Rate
LambdaErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-lambda-error-rate"
    MetricName: Errors
    Namespace: AWS/Lambda
    Dimensions:
      - Name: FunctionName
        Value: !Ref MyFunction
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 2
    Threshold: 10
    ComparisonOperator: GreaterThanThreshold
    TreatMissingData: notBreaching
    AlarmActions:
      - !Ref CriticalSNSTopic

# ALB 5xx Rate
ALB5xxAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-alb-5xx-rate"
    Metrics:
      - Id: errors
        MetricStat:
          Metric:
            MetricName: HTTPCode_Target_5XX_Count
            Namespace: AWS/ApplicationELB
            Dimensions:
              - Name: LoadBalancer
                Value: !GetAtt ALB.LoadBalancerFullName
          Period: 300
          Stat: Sum
      - Id: total
        MetricStat:
          Metric:
            MetricName: RequestCount
            Namespace: AWS/ApplicationELB
            Dimensions:
              - Name: LoadBalancer
                Value: !GetAtt ALB.LoadBalancerFullName
          Period: 300
          Stat: Sum
      - Id: errorRate
        Expression: "(errors / total) * 100"
        Label: "5xx Error Rate %"
    EvaluationPeriods: 2
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold

# DLQ Messages (Failed Processing)
DLQAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-dlq-messages"
    MetricName: ApproximateNumberOfMessagesVisible
    Namespace: AWS/SQS
    Dimensions:
      - Name: QueueName
        Value: !GetAtt DeadLetterQueue.QueueName
    Statistic: Sum
    Period: 60
    EvaluationPeriods: 1
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold

# Aurora CPU
AuroraCPUAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-aurora-cpu"
    MetricName: CPUUtilization
    Namespace: AWS/RDS
    Dimensions:
      - Name: DBClusterIdentifier
        Value: !Ref AuroraCluster
    Statistic: Average
    Period: 300
    EvaluationPeriods: 3
    Threshold: 80
    ComparisonOperator: GreaterThanThreshold
```

### Warning Alarms (Slack/Email)
```yaml
# Lambda Throttling
ThrottleAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-lambda-throttles"
    MetricName: Throttles
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    Threshold: 5

# Lambda P99 Latency
LatencyAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-lambda-p99-latency"
    MetricName: Duration
    Namespace: AWS/Lambda
    ExtendedStatistic: p99
    Period: 300
    Threshold: 5000  # 5 seconds

# DynamoDB Throttling
DDBThrottleAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: !Sub "${Service}-ddb-throttle"
    MetricName: ReadThrottleEvents
    Namespace: AWS/DynamoDB
    Statistic: Sum
    Period: 300
    Threshold: 10
```

## 4.3 Structured Logging Standards

### Log Format
```json
{
  "timestamp": "2024-01-20T10:15:30.123Z",
  "level": "INFO",
  "service": "order-service",
  "function": "getOrder",
  "requestId": "req-abc-123",
  "traceId": "1-65abc-def123",
  "correlationId": "corr-xyz-789",
  "userId": "usr-456",
  "message": "Order retrieved successfully",
  "orderId": "ord-001",
  "duration": 45,
  "cold_start": false
}
```

### What to Log
```
✅ DO LOG:
  - Request received (with requestId, path, method)
  - Business events (order created, payment processed)
  - Error details (with stack trace for unexpected errors)
  - Performance data (duration, external call latency)
  - Security events (auth failures, suspicious activity)
  - Cold starts (for Lambda)

❌ DON'T LOG:
  - Sensitive data (passwords, tokens, PII)
  - Full request/response bodies (unless debugging)
  - High-cardinality data that explodes log costs
  - Health check requests (noise)
```

---

# Part 5: Security Hardening Guide

## 5.1 Threat Model for Migration App

```
┌──────────────────────────────────────────────┐
│                 THREAT MODEL                  │
├──────────────────────────────────────────────┤
│                                              │
│  Internet → [WAF] → [ALB/APIGW]             │
│  Threats: DDoS, injection, credential stuff  │
│  Controls: WAF rules, rate limiting, HTTPS   │
│                                              │
│  [ALB/APIGW] → [Lambda/ECS]                 │
│  Threats: Unauthorized access, code injection│
│  Controls: JWT auth, input validation, IAM   │
│                                              │
│  [Lambda/ECS] → [Aurora/DynamoDB]            │
│  Threats: SQL injection, data exfiltration   │
│  Controls: Parameterized queries, encryption,│
│            RDS Proxy, VPC isolation           │
│                                              │
│  [Internal] → [AWS Console/API]              │
│  Threats: Privilege escalation, lateral move │
│  Controls: MFA, SCPs, permission boundaries  │
│                                              │
└──────────────────────────────────────────────┘
```

## 5.2 OWASP Top 10 Mitigations on AWS

| # | Vulnerability | AWS Mitigation |
|---|--------------|----------------|
| 1 | Broken Access Control | Cognito + API GW JWT + IAM least privilege |
| 2 | Cryptographic Failures | KMS encryption, TLS 1.2+, Secrets Manager |
| 3 | Injection | WAF SQL/XSS rules, parameterized queries, input validation |
| 4 | Insecure Design | Well-Architected review, threat modeling |
| 5 | Security Misconfiguration | Config Rules, Security Hub, SCPs |
| 6 | Vulnerable Components | ECR image scanning, Dependabot, Inspector |
| 7 | Auth Failures | Cognito MFA, account lockout, token expiry |
| 8 | Data Integrity Failures | Code signing, immutable deployments, CI/CD controls |
| 9 | Logging Failures | CloudTrail, VPC Flow Logs, structured logging |
| 10 | SSRF | Lambda VPC, no public metadata, IMDSv2 |

## 5.3 Security Automation

### AWS Config Rules
```yaml
# Ensure encryption
ConfigRuleEncryption:
  Type: AWS::Config::ConfigRule
  Properties:
    ConfigRuleName: s3-bucket-server-side-encryption-enabled
    Source:
      Owner: AWS
      SourceIdentifier: S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED

# Ensure no public S3
ConfigRulePublicS3:
  Type: AWS::Config::ConfigRule
  Properties:
    ConfigRuleName: s3-bucket-public-read-prohibited
    Source:
      Owner: AWS
      SourceIdentifier: S3_BUCKET_PUBLIC_READ_PROHIBITED

# Ensure RDS encryption
ConfigRuleRDS:
  Type: AWS::Config::ConfigRule
  Properties:
    ConfigRuleName: rds-storage-encrypted
    Source:
      Owner: AWS
      SourceIdentifier: RDS_STORAGE_ENCRYPTED
```

### Security Hub
```
Enable:
  - AWS Foundational Security Best Practices
  - CIS AWS Foundations Benchmark
  - PCI DSS (if needed)

Integrations:
  - GuardDuty (threat detection)
  - Inspector (vulnerability scanning)
  - IAM Access Analyzer (external access)
  - Config (compliance)
```

## 5.4 Dependency Security

### Container Image Scanning
```yaml
# ECR scan on push
ECRRepository:
  Type: AWS::ECR::Repository
  Properties:
    RepositoryName: order-service
    ImageScanningConfiguration:
      ScanOnPush: true
    ImageTagMutability: IMMUTABLE  # Prevent tag overwriting
    LifecyclePolicy:
      LifecyclePolicyText: |
        {
          "rules": [
            {
              "rulePriority": 1,
              "description": "Keep last 10 images",
              "selection": {
                "tagStatus": "any",
                "countType": "imageCountMoreThan",
                "countNumber": 10
              },
              "action": { "type": "expire" }
            }
          ]
        }
```

### Java Dependency Scanning
```xml
<!-- pom.xml -->
<plugin>
    <groupId>org.owasp</groupId>
    <artifactId>dependency-check-maven</artifactId>
    <version>9.0.0</version>
    <configuration>
        <failBuildOnCVSS>7</failBuildOnCVSS>
    </configuration>
</plugin>
```

```bash
# CodeBuild buildspec
phases:
  build:
    commands:
      - mvn org.owasp:dependency-check-maven:check
      - mvn clean package
```
