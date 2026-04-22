---
name: aws-serverless-guide
description: This skill should be used when the user asks to "build serverless on AWS", "use AWS Lambda", "design with API Gateway", "create Step Functions workflow", "use DynamoDB", "configure EventBridge", "set up SQS or SNS", or mentions AWS serverless architecture, Lambda cold starts, SAM, CDK, or serverless best practices.
version: 1.0.0
---

# AWS Serverless Guide Skill

Build serverless applications on AWS using Lambda, API Gateway, Step Functions, DynamoDB, and supporting services.

## Core Serverless Services

### AWS Lambda
- **Runtime:** Java 17/21, Python 3.12, Node.js 20, .NET 8, Go, Ruby, Custom
- **Memory:** 128 MB – 10,240 MB (CPU scales proportionally)
- **Timeout:** Max 15 minutes
- **Concurrency:** 1,000 default (requestable increase)
- **Package:** 50 MB zipped, 250 MB unzipped, 10 GB container image
- **SnapStart:** Java cold start reduction (~90% faster, Java 11+)

### Lambda Best Practices
```
✅ DO:
- Keep functions focused (single responsibility)
- Initialize outside handler (connection pooling, SDK clients)
- Use environment variables for configuration
- Enable SnapStart for Java functions
- Use Powertools for structured logging, tracing, metrics
- Set appropriate timeout and memory

❌ DON'T:
- Chain Lambda calls synchronously (use Step Functions)
- Store state in /tmp across invocations
- Use Lambda for long-running processes (>15min → ECS)
- Ignore cold start impact for latency-sensitive APIs
- Package unused dependencies
```

### API Gateway Patterns

| Pattern | Type | Use Case |
|---------|------|----------|
| REST API | Regional/Edge | Full REST with models, validation, caching |
| HTTP API | Regional | Simple proxy, JWT auth, lower cost |
| WebSocket | Regional | Real-time bidirectional communication |

### Step Functions (Workflow Orchestration)
```json
{
  "Comment": "ETL Workflow",
  "StartAt": "Extract",
  "States": {
    "Extract": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:extract",
      "Next": "Transform",
      "Retry": [{"ErrorEquals": ["States.ALL"], "MaxAttempts": 3}]
    },
    "Transform": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:transform",
      "Next": "Load"
    },
    "Load": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:load",
      "End": true
    }
  }
}
```

**Step Functions vs Lambda Chaining:**
- Use Step Functions for orchestration (sequential, parallel, branching)
- Use SQS/SNS for decoupled event-driven processing
- Never call Lambda from Lambda synchronously

### DynamoDB Patterns
- **Single-table design** — One table for multiple entity types
- **GSI overloading** — Reuse indexes for different access patterns
- **TTL** — Auto-expire items for temporary data
- **Streams** — CDC for event-driven processing
- **On-demand vs Provisioned** — Start on-demand, switch when patterns stable

### Event-Driven Architecture

```
EventBridge Rules → Lambda (process)
                  → SQS (buffer) → Lambda (batch process)
                  → Step Functions (orchestrate)
                  → SNS → Multiple subscribers
```

## Infrastructure as Code

### AWS SAM (Serverless Application Model)
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: java21
    MemorySize: 512
    Timeout: 30
    SnapStart:
      ApplyOn: PublishedVersions

Resources:
  GetUserFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: com.example.GetUserHandler::handleRequest
      Events:
        GetUser:
          Type: Api
          Properties:
            Path: /users/{id}
            Method: get
```

### AWS CDK (TypeScript)
```typescript
const fn = new lambda.Function(this, 'GetUser', {
  runtime: lambda.Runtime.JAVA_21,
  handler: 'com.example.GetUserHandler::handleRequest',
  code: lambda.Code.fromAsset('target/app.jar'),
  memorySize: 512,
  timeout: Duration.seconds(30),
});

const api = new apigateway.RestApi(this, 'UserApi');
api.root.addResource('users').addResource('{id}')
  .addMethod('GET', new apigateway.LambdaIntegration(fn));
```

## Cost Optimization

| Strategy | Savings | Effort |
|----------|---------|--------|
| Right-size memory | 10-40% | Low |
| ARM64 (Graviton) | 20% | Low |
| Provisioned Concurrency (scheduled) | Variable | Medium |
| Reserved Concurrency | Control costs | Low |
| DynamoDB on-demand → provisioned | 30-70% | Medium |
| API Gateway HTTP API vs REST | 70% | Low |

## Monitoring & Observability

- **CloudWatch Logs** — Function logs (structured JSON with Powertools)
- **X-Ray** — Distributed tracing across services
- **CloudWatch Metrics** — Invocations, errors, duration, throttles
- **CloudWatch Alarms** — Error rate, duration P99, throttle alerts
- **Powertools** — Structured logging, tracing, metrics (Java/Python/TS)
