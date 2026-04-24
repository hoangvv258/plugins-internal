# AWS Deep Dive — Lambda + Java, Step Functions, DynamoDB

> Phần deep dive chi tiết cho từng service. Đọc sau khi đã hiểu Study Guide chính.

---

# Deep Dive 1: Lambda + Java

## 1.1 Cold Start Anatomy

```
Cold Start Timeline (Java without SnapStart):
┌──────────────────────────────────────────────────────────────┐
│ Download code │ JVM Init │ Class Loading │ Spring DI │ Handler │
│   ~200ms     │  ~500ms  │   ~1-3s      │  ~1-5s   │ ~50ms   │
└──────────────────────────────────────────────────────────────┘
Total: 3-10 seconds (!)

With SnapStart:
┌──────────────────────────────────────────────────────────────┐
│ Restore snapshot │ Runtime hook │ Handler │
│     ~200ms      │   ~100ms    │  ~50ms  │
└──────────────────────────────────────────────────────────────┘
Total: ~350ms

With GraalVM Native Image:
┌──────────────────────────────────────────────────────────────┐
│ Start binary │ Handler │
│   ~50-150ms  │  ~50ms  │
└──────────────────────────────────────────────────────────────┘
Total: ~100-200ms
```

## 1.2 SnapStart In-Depth

### How It Works
1. Bạn publish function version
2. Lambda initializes function (full cold start)
3. Lambda takes snapshot of initialized memory + disk
4. Subsequent invocations restore from snapshot (not cold start)

### SnapStart Hooks (CRaC)
```java
import org.crac.Context;
import org.crac.Core;
import org.crac.Resource;

public class MyHandler implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent>, Resource {
    
    private DynamoDbClient dynamoDb;
    
    public MyHandler() {
        // Register for CRaC lifecycle
        Core.getGlobalContext().register(this);
        // Initialize during snapshot
        dynamoDb = DynamoDbClient.builder().build();
    }
    
    @Override
    public void beforeCheckpoint(Context<? extends Resource> context) {
        // Called BEFORE snapshot — clean up
        // Close connections that can't be serialized
        // Clear sensitive data from memory
    }
    
    @Override
    public void afterRestore(Context<? extends Resource> context) {
        // Called AFTER restore — re-establish
        // Reconnect to database
        // Refresh credentials
        // Re-seed random number generators (CRITICAL for security)
        dynamoDb = DynamoDbClient.builder().build();
    }
    
    @Override
    public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent request, Context context) {
        // Business logic
    }
}
```

### SnapStart Gotchas
```
⚠️ CRITICAL: Uniqueness and Security
- Random number generators get "frozen" in snapshot
- UUIDs generated before snapshot will be identical across invocations
- ALWAYS re-seed randomness in afterRestore hook

⚠️ Network Connections
- TCP connections become stale after snapshot restore
- AWS SDK v2 handles this automatically
- Custom connections need afterRestore reconnection

⚠️ File-based State
- /tmp contents are included in snapshot
- Don't store secrets in /tmp during init
```

## 1.3 Spring Cloud Function + Lambda

### Project Setup (pom.xml key dependencies)
```xml
<dependencies>
    <!-- Spring Cloud Function -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-function-adapter-aws</artifactId>
    </dependency>
    
    <!-- AWS Lambda Events -->
    <dependency>
        <groupId>com.amazonaws</groupId>
        <artifactId>aws-lambda-java-events</artifactId>
        <version>3.14.0</version>
    </dependency>
    
    <!-- AWS Lambda Powertools -->
    <dependency>
        <groupId>software.amazon.lambda</groupId>
        <artifactId>powertools-tracing</artifactId>
    </dependency>
    <dependency>
        <groupId>software.amazon.lambda</groupId>
        <artifactId>powertools-logging</artifactId>
    </dependency>
    <dependency>
        <groupId>software.amazon.lambda</groupId>
        <artifactId>powertools-metrics</artifactId>
    </dependency>
</dependencies>
```

### Handler Pattern (Function Bean)
```java
@SpringBootApplication
public class OrderApplication {

    @Bean
    public Function<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> getOrder(
            OrderService orderService) {
        return request -> {
            String orderId = request.getPathParameters().get("id");
            Order order = orderService.getOrder(orderId);
            
            return new APIGatewayProxyResponseEvent()
                .withStatusCode(200)
                .withHeaders(Map.of("Content-Type", "application/json"))
                .withBody(new ObjectMapper().writeValueAsString(order));
        };
    }
    
    @Bean
    public Function<SQSEvent, Void> processOrderQueue(OrderProcessor processor) {
        return event -> {
            event.getRecords().forEach(record -> {
                Order order = parse(record.getBody());
                processor.process(order);
            });
            return null;
        };
    }
}
```

### Multi-Function Routing
```yaml
# application.yml
spring:
  cloud:
    function:
      definition: getOrder;processOrderQueue
```

### Reducing Spring Boot Cold Start
```
1. Exclude unused auto-configurations:
   @SpringBootApplication(exclude = {
       DataSourceAutoConfiguration.class,
       WebMvcAutoConfiguration.class,
       SecurityAutoConfiguration.class
   })

2. Use functional bean registration:
   SpringApplication app = new SpringApplication(MyApp.class);
   app.addInitializers(context -> {
       context.registerBean(OrderService.class, () -> new OrderServiceImpl());
   });

3. Avoid component scanning:
   @ComponentScan(basePackages = "com.example.order") // specific package only

4. Use spring-cloud-function-adapter-aws (lightweight)
   NOT spring-boot-starter-web (full servlet container)

5. Enable SnapStart in SAM template
```

## 1.4 AWS Lambda Powertools for Java

### Logging
```java
@Logging(logEvent = true)
@Tracing
@Metrics(namespace = "OrderService", service = "getOrder")
public class GetOrderHandler implements RequestHandler<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> {
    
    private static final Logger log = LogManager.getLogger();
    
    @Override
    public APIGatewayProxyResponseEvent handleRequest(APIGatewayProxyRequestEvent request, Context context) {
        // Structured logging — JSON output
        log.info("Processing order request", Map.of(
            "orderId", request.getPathParameters().get("id"),
            "httpMethod", request.getHttpMethod(),
            "correlationId", request.getHeaders().get("X-Correlation-Id")
        ));
        
        // Add custom metrics
        MetricsLogger metricsLogger = MetricsUtils.metricsLogger();
        metricsLogger.putMetric("OrderProcessed", 1, Unit.COUNT);
        metricsLogger.putMetric("ProcessingTime", duration, Unit.MILLISECONDS);
        
        return response;
    }
}
```

### SAM Template với Powertools
```yaml
Globals:
  Function:
    Runtime: java21
    MemorySize: 1024
    Timeout: 30
    Architectures: [arm64]
    SnapStart:
      ApplyOn: PublishedVersions
    Tracing: Active  # Enable X-Ray
    Environment:
      Variables:
        POWERTOOLS_SERVICE_NAME: order-service
        POWERTOOLS_LOG_LEVEL: INFO
        POWERTOOLS_METRICS_NAMESPACE: OrderService
        LOG_LEVEL: INFO
```

## 1.5 Lambda Performance Tuning

### Memory = CPU
```
128 MB  → ~1/8 vCPU    (very slow)
512 MB  → ~1/3 vCPU
1024 MB → ~0.6 vCPU
1769 MB → 1 full vCPU  (sweet spot for many workloads)
3008 MB → ~2 vCPU
10240 MB → ~6 vCPU
```

### Right-Sizing Strategy
```
1. Start at 1024 MB
2. Deploy and run typical workload
3. Check CloudWatch metrics:
   - Memory Used vs Allocated
   - Duration at different memory levels
4. Use AWS Lambda Power Tuning tool:
   https://github.com/alexcasalboni/aws-lambda-power-tuning
5. Find the "sweet spot" where cost * duration is minimized
```

### Connection Reuse
```java
public class OrderHandler {
    // OUTSIDE handler — reused across invocations
    private static final DynamoDbClient dynamoDb = DynamoDbClient.builder()
        .httpClient(UrlConnectionHttpClient.builder()
            .socketTimeout(Duration.ofSeconds(5))
            .connectionTimeout(Duration.ofSeconds(3))
            .build())
        .build();
    
    private static final ObjectMapper mapper = new ObjectMapper();
    
    // Handler — called per invocation
    public APIGatewayProxyResponseEvent handleRequest(
            APIGatewayProxyRequestEvent request, Context context) {
        // Use shared clients
        dynamoDb.getItem(...);
    }
}
```

---

# Deep Dive 2: Step Functions Patterns

## 2.1 Saga Pattern (Distributed Transactions)

### Problem
Microservices don't share databases → no ACID transactions across services.

### Solution: Orchestration Saga via Step Functions
```json
{
  "Comment": "Order Saga — Book Hotel, Flight, Payment with compensations",
  "StartAt": "BookHotel",
  "States": {
    "BookHotel": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:bookHotel",
      "ResultPath": "$.hotelBooking",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "BookHotelFailed"
      }],
      "Next": "BookFlight"
    },
    "BookFlight": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:bookFlight",
      "ResultPath": "$.flightBooking",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "CancelHotel"
      }],
      "Next": "ProcessPayment"
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:processPayment",
      "ResultPath": "$.payment",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "CancelFlight"
      }],
      "Next": "BookingConfirmed"
    },
    
    "CancelFlight": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:cancelFlight",
      "ResultPath": "$.flightCancellation",
      "Next": "CancelHotel"
    },
    "CancelHotel": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:cancelHotel",
      "ResultPath": "$.hotelCancellation",
      "Next": "BookingFailed"
    },
    
    "BookingConfirmed": {
      "Type": "Succeed"
    },
    "BookHotelFailed": {
      "Type": "Fail",
      "Error": "HotelBookingFailed",
      "Cause": "Could not book hotel"
    },
    "BookingFailed": {
      "Type": "Fail",
      "Error": "BookingFailed",
      "Cause": "Booking saga failed, all compensations executed"
    }
  }
}
```

## 2.2 Parallel Processing (Map State)

### Distributed Map for Large-Scale Processing
```json
{
  "StartAt": "ProcessS3Files",
  "States": {
    "ProcessS3Files": {
      "Type": "Map",
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "DISTRIBUTED",
          "ExecutionType": "STANDARD"
        },
        "StartAt": "ProcessFile",
        "States": {
          "ProcessFile": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:processFile",
            "End": true
          }
        }
      },
      "ItemReader": {
        "Resource": "arn:aws:states:::s3:listObjectsV2",
        "Parameters": {
          "Bucket": "my-data-bucket",
          "Prefix": "input/"
        }
      },
      "MaxConcurrency": 100,
      "End": true
    }
  }
}
```

## 2.3 Human Approval Workflow
```json
{
  "StartAt": "SubmitRequest",
  "States": {
    "SubmitRequest": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:submitRequest",
      "Next": "WaitForApproval"
    },
    "WaitForApproval": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
      "Parameters": {
        "QueueUrl": "https://sqs.../approval-queue",
        "MessageBody": {
          "taskToken.$": "$$.Task.Token",
          "requestDetails.$": "$.request"
        }
      },
      "TimeoutSeconds": 604800,
      "Catch": [{
        "ErrorEquals": ["States.Timeout"],
        "Next": "RequestExpired"
      }],
      "Next": "ApprovalDecision"
    },
    "ApprovalDecision": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.approved",
          "BooleanEquals": true,
          "Next": "ExecuteAction"
        }
      ],
      "Default": "RequestDenied"
    },
    "ExecuteAction": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:...:executeAction",
      "End": true
    },
    "RequestDenied": {
      "Type": "Fail",
      "Error": "RequestDenied"
    },
    "RequestExpired": {
      "Type": "Fail",
      "Error": "RequestExpired"
    }
  }
}
```

## 2.4 Error Handling Patterns

### Retry with Exponential Backoff
```json
{
  "Retry": [
    {
      "ErrorEquals": ["ServiceUnavailableException", "ThrottlingException"],
      "IntervalSeconds": 1,
      "MaxAttempts": 5,
      "BackoffRate": 2.0,
      "JitterStrategy": "FULL"
    },
    {
      "ErrorEquals": ["States.ALL"],
      "IntervalSeconds": 5,
      "MaxAttempts": 2
    }
  ],
  "Catch": [
    {
      "ErrorEquals": ["States.ALL"],
      "ResultPath": "$.error",
      "Next": "HandleError"
    }
  ]
}
```

### Circuit Breaker Pattern
```
Monitor error rate → If > threshold → "Open" state (reject requests)
                   → Wait timeout → "Half-Open" (allow 1 request)
                   → If success → "Closed" (normal)
                   → If fail → "Open" (wait again)
```

## 2.5 Step Functions vs EventBridge Pipes vs Direct Integration

| Pattern | Use |
|---------|-----|
| Step Functions | Multi-step orchestration, saga, human approval |
| EventBridge Pipes | Point-to-point with filtering/transformation |
| SQS → Lambda | Simple async processing |
| EventBridge Rules | Event routing to multiple targets |
| Direct SDK integration | Step Functions can call 200+ AWS APIs directly |

### Direct SDK Integration (no Lambda needed)
```json
{
  "PutItemInDynamoDB": {
    "Type": "Task",
    "Resource": "arn:aws:states:::dynamodb:putItem",
    "Parameters": {
      "TableName": "Orders",
      "Item": {
        "orderId": {"S.$": "$.orderId"},
        "status": {"S": "CONFIRMED"},
        "timestamp": {"S.$": "$$.State.EnteredTime"}
      }
    },
    "Next": "SendNotification"
  },
  "SendNotification": {
    "Type": "Task",
    "Resource": "arn:aws:states:::sns:publish",
    "Parameters": {
      "TopicArn": "arn:aws:sns:...:order-notifications",
      "Message.$": "States.Format('Order {} confirmed', $.orderId)"
    },
    "End": true
  }
}
```

---

# Deep Dive 3: DynamoDB Design

## 3.1 Core Design Philosophy

```
RDBMS Mindset:  "What data do I have?" → Normalize → Query later
DynamoDB Mindset: "What queries do I need?" → Design keys → Store data
```

**Rule #1**: Know ALL your access patterns BEFORE designing tables.

## 3.2 Single-Table Design

### Why Single Table?
- Fewer requests (get related data in 1 query)
- Lower cost (fewer read operations)
- Simpler application (1 table to manage)

### E-commerce Example
```
Access Patterns:
1. Get user profile
2. Get user's orders
3. Get order details
4. Get order items
5. Get all orders by date (admin)
6. Get user's recent orders (last 30 days)

Table Design:
┌──────────────────┬────────────────────┬──────────────────────┐
│ PK               │ SK                 │ Attributes           │
├──────────────────┼────────────────────┼──────────────────────┤
│ USER#u001        │ PROFILE            │ name, email, phone   │
│ USER#u001        │ ORDER#2024-01-15#o1│ total, status        │
│ USER#u001        │ ORDER#2024-01-20#o2│ total, status        │
│ ORDER#o001       │ METADATA           │ userId, total, date  │
│ ORDER#o001       │ ITEM#p001          │ product, qty, price  │
│ ORDER#o001       │ ITEM#p002          │ product, qty, price  │
│ ORDER#o002       │ METADATA           │ userId, total, date  │
│ ORDER#o002       │ ITEM#p003          │ product, qty, price  │
└──────────────────┴────────────────────┴──────────────────────┘

GSI1 (for access pattern 5 — orders by date):
┌──────────────────┬────────────────────┬──────────────────────┐
│ GSI1PK           │ GSI1SK             │                      │
├──────────────────┼────────────────────┼──────────────────────┤
│ ORDER            │ 2024-01-15#o001    │ (order data)         │
│ ORDER            │ 2024-01-20#o002    │ (order data)         │
└──────────────────┴────────────────────┴──────────────────────┘
```

### Query Examples (Java SDK v2)
```java
// Pattern 1: Get user profile
GetItemResponse profile = dynamoDb.getItem(GetItemRequest.builder()
    .tableName("MainTable")
    .key(Map.of(
        "PK", AttributeValue.builder().s("USER#" + userId).build(),
        "SK", AttributeValue.builder().s("PROFILE").build()
    ))
    .build());

// Pattern 2: Get user's orders (all)
QueryResponse orders = dynamoDb.query(QueryRequest.builder()
    .tableName("MainTable")
    .keyConditionExpression("PK = :pk AND begins_with(SK, :sk)")
    .expressionAttributeValues(Map.of(
        ":pk", AttributeValue.builder().s("USER#" + userId).build(),
        ":sk", AttributeValue.builder().s("ORDER#").build()
    ))
    .scanIndexForward(false)  // newest first
    .build());

// Pattern 6: User's orders last 30 days
String thirtyDaysAgo = LocalDate.now().minusDays(30).toString();
QueryResponse recentOrders = dynamoDb.query(QueryRequest.builder()
    .tableName("MainTable")
    .keyConditionExpression("PK = :pk AND SK > :sk")
    .expressionAttributeValues(Map.of(
        ":pk", AttributeValue.builder().s("USER#" + userId).build(),
        ":sk", AttributeValue.builder().s("ORDER#" + thirtyDaysAgo).build()
    ))
    .build());
```

## 3.3 Common DynamoDB Patterns

### Adjacency List (Many-to-Many Relationships)
```
Use Case: Users belong to multiple groups, groups have multiple users

PK              SK              Type      Data
USER#u1         USER#u1         User      {name: "Alice"}
USER#u1         GROUP#g1        Membership {joinedAt: "2024-01"}
USER#u1         GROUP#g2        Membership {joinedAt: "2024-02"}
GROUP#g1        GROUP#g1        Group     {name: "Engineering"}
GROUP#g1        USER#u1         Membership {role: "admin"}
GROUP#g1        USER#u2         Membership {role: "member"}

Query "Alice's groups":    PK = USER#u1, SK begins_with GROUP#
Query "Engineering members": PK = GROUP#g1, SK begins_with USER#
```

### Write Sharding (Hot Partition Prevention)
```
Problem: Global counter updated by millions of requests

Bad:  PK = "GLOBAL_COUNTER" → Hot partition!

Good: PK = "COUNTER#" + random(0-9) → 10 shards
      Read all 10, sum them up
```

### TTL (Auto-Delete Expired Items)
```java
// Set TTL attribute
Map<String, AttributeValue> item = Map.of(
    "PK", s("SESSION#abc123"),
    "SK", s("DATA"),
    "sessionData", s("{...}"),
    "ttl", n(Instant.now().plus(Duration.ofHours(24)).getEpochSecond())
);
```

## 3.4 DynamoDB Streams + CDC (Change Data Capture)
```
DynamoDB Table → DynamoDB Streams → Lambda → 
  ├── Update search index (OpenSearch)
  ├── Sync to analytics (S3/Redshift)
  ├── Notify downstream services (EventBridge)
  └── Audit logging (CloudWatch/S3)
```

```yaml
# SAM Template
Resources:
  StreamProcessor:
    Type: AWS::Serverless::Function
    Properties:
      Events:
        DDBStream:
          Type: DynamoDB
          Properties:
            Stream: !GetAtt MainTable.StreamArn
            StartingPosition: TRIM_HORIZON
            BatchSize: 100
            MaximumBatchingWindowInSeconds: 5
            FilterCriteria:
              Filters:
                - Pattern: '{"eventName": ["INSERT", "MODIFY"]}'
```

## 3.5 SQL to DynamoDB Migration Strategy

```
Step 1: Document ALL SQL queries (SELECT, INSERT, UPDATE, DELETE)
Step 2: Categorize by access pattern
Step 3: Design PK/SK to support each pattern
Step 4: Create GSIs for patterns that can't use PK/SK
Step 5: Decide what stays in SQL (complex joins, reporting)

Common Mapping:
┌─────────────────────┬──────────────────────────────┐
│ SQL Pattern         │ DynamoDB Equivalent          │
├─────────────────────┼──────────────────────────────┤
│ SELECT * WHERE id=X │ GetItem (PK=X)               │
│ SELECT * WHERE fk=Y │ Query (PK=Y, SK begins_with) │
│ SELECT * ORDER BY   │ Query with ScanIndexForward   │
│ SELECT * WHERE a=X  │ GSI with a as PK             │
│   AND b BETWEEN     │   and b as SK                │
│ COUNT(*) GROUP BY   │ ❌ Use analytics service     │
│ JOIN                │ ❌ Denormalize or multi-query │
│ Full-text search    │ ❌ Use OpenSearch             │
└─────────────────────┴──────────────────────────────┘
```

---

# Quick Reference: When to Use What

## Event Processing Decision Tree
```
Event arrives → 
  Need ordering?
    Yes → SQS FIFO → Lambda
    No  → 
      Need fan-out?
        Yes → SNS → SQS → Lambda (per subscriber)
        No  →
          Need content filtering?
            Yes → EventBridge → Lambda
            No  → SQS Standard → Lambda
```

## Async Communication Patterns
```
Pattern 1: Request-Response (sync)
  Client → API Gateway → Lambda → DynamoDB → Response

Pattern 2: Fire-and-Forget (async)
  Client → API Gateway → SQS → Lambda → DynamoDB
  (Client gets 202 Accepted immediately)

Pattern 3: Workflow (multi-step)
  Client → API Gateway → Step Functions → [Lambda₁ → Lambda₂ → Lambda₃]
  (Client polls for result or gets callback)

Pattern 4: Event-Driven (reactive)
  DynamoDB Stream → EventBridge → [Lambda₁, Lambda₂, Lambda₃]
  (Each subscriber processes independently)
```
