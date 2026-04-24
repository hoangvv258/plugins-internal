# AWS Infrastructure Templates & Sample Code

---

# Part 1: Complete CDK Infrastructure Templates

## 1.1 Full Stack CDK Project Structure
```
infrastructure/
├── bin/
│   └── app.ts                    # CDK app entry
├── lib/
│   ├── stacks/
│   │   ├── network-stack.ts      # VPC, subnets, endpoints
│   │   ├── database-stack.ts     # Aurora, ElastiCache, RDS Proxy
│   │   ├── compute-stack.ts      # ECS Fargate, Lambda
│   │   ├── api-stack.ts          # API Gateway, ALB, WAF
│   │   ├── messaging-stack.ts    # SQS, SNS, EventBridge
│   │   ├── auth-stack.ts         # Cognito
│   │   ├── monitoring-stack.ts   # Dashboards, alarms
│   │   └── pipeline-stack.ts     # CI/CD pipeline
│   ├── constructs/
│   │   ├── fargate-service.ts    # Reusable ECS service
│   │   ├── lambda-api.ts         # Lambda + API GW pattern
│   │   └── secure-bucket.ts      # Encrypted S3
│   └── config/
│       └── environments.ts       # Per-env config
├── cdk.json
├── package.json
└── tsconfig.json
```

## 1.2 Network Stack (VPC)
```typescript
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export interface NetworkStackProps extends cdk.StackProps {
  cidr: string;
  maxAzs: number;
  natGateways: number;
}

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;
  public readonly appSecurityGroup: ec2.SecurityGroup;
  public readonly dbSecurityGroup: ec2.SecurityGroup;
  public readonly cacheSecurityGroup: ec2.SecurityGroup;
  public readonly lambdaSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: NetworkStackProps) {
    super(scope, id, props);

    // VPC with 3-tier subnet architecture
    this.vpc = new ec2.Vpc(this, 'VPC', {
      ipAddresses: ec2.IpAddresses.cidr(props.cidr),
      maxAzs: props.maxAzs,
      natGateways: props.natGateways,
      subnetConfiguration: [
        { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
        { name: 'App', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 20 },
        { name: 'Data', subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 },
      ],
    });

    // VPC Flow Logs
    this.vpc.addFlowLog('FlowLogs', {
      destination: ec2.FlowLogDestination.toCloudWatchLogs(),
      trafficType: ec2.FlowLogTrafficType.REJECT,
    });

    // Gateway Endpoints (FREE)
    this.vpc.addGatewayEndpoint('S3', { service: ec2.GatewayVpcEndpointAwsService.S3 });
    this.vpc.addGatewayEndpoint('DynamoDB', { service: ec2.GatewayVpcEndpointAwsService.DYNAMODB });

    // Interface Endpoints (for private subnet access to AWS services)
    const interfaceEndpoints = [
      { id: 'SecretsManager', service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER },
      { id: 'SQS', service: ec2.InterfaceVpcEndpointAwsService.SQS },
      { id: 'SNS', service: ec2.InterfaceVpcEndpointAwsService.SNS },
      { id: 'ECR', service: ec2.InterfaceVpcEndpointAwsService.ECR },
      { id: 'ECRDocker', service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER },
      { id: 'Logs', service: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS },
      { id: 'StepFunctions', service: ec2.InterfaceVpcEndpointAwsService.STEP_FUNCTIONS },
    ];
    for (const ep of interfaceEndpoints) {
      this.vpc.addInterfaceEndpoint(ep.id, {
        service: ep.service,
        subnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      });
    }

    // Security Groups — layered
    this.appSecurityGroup = new ec2.SecurityGroup(this, 'AppSG', {
      vpc: this.vpc,
      description: 'Application tier (ECS tasks)',
      allowAllOutbound: true,
    });

    this.dbSecurityGroup = new ec2.SecurityGroup(this, 'DBSG', {
      vpc: this.vpc,
      description: 'Database tier (Aurora)',
      allowAllOutbound: false,
    });
    this.dbSecurityGroup.addIngressRule(this.appSecurityGroup, ec2.Port.tcp(5432), 'App → DB');

    this.cacheSecurityGroup = new ec2.SecurityGroup(this, 'CacheSG', {
      vpc: this.vpc,
      description: 'Cache tier (ElastiCache)',
      allowAllOutbound: false,
    });
    this.cacheSecurityGroup.addIngressRule(this.appSecurityGroup, ec2.Port.tcp(6379), 'App → Cache');

    this.lambdaSecurityGroup = new ec2.SecurityGroup(this, 'LambdaSG', {
      vpc: this.vpc,
      description: 'Lambda functions',
      allowAllOutbound: true,
    });
    this.dbSecurityGroup.addIngressRule(this.lambdaSecurityGroup, ec2.Port.tcp(5432), 'Lambda → DB');
    this.cacheSecurityGroup.addIngressRule(this.lambdaSecurityGroup, ec2.Port.tcp(6379), 'Lambda → Cache');
  }
}
```

## 1.3 Database Stack
```typescript
import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';

export interface DatabaseStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
  dbSecurityGroup: ec2.SecurityGroup;
  cacheSecurityGroup: ec2.SecurityGroup;
  appSecurityGroup: ec2.SecurityGroup;
  lambdaSecurityGroup: ec2.SecurityGroup;
  auroraMinCapacity: number;
  auroraMaxCapacity: number;
}

export class DatabaseStack extends cdk.Stack {
  public readonly cluster: rds.DatabaseCluster;
  public readonly proxy: rds.DatabaseProxy;
  public readonly dbSecret: secretsmanager.ISecret;

  constructor(scope: cdk.App, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    // Aurora Serverless v2
    this.cluster = new rds.DatabaseCluster(this, 'Aurora', {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_16_1,
      }),
      serverlessV2MinCapacity: props.auroraMinCapacity,
      serverlessV2MaxCapacity: props.auroraMaxCapacity,
      writer: rds.ClusterInstance.serverlessV2('writer'),
      readers: [
        rds.ClusterInstance.serverlessV2('reader', {
          scaleWithWriter: true,
        }),
      ],
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [props.dbSecurityGroup],
      defaultDatabaseName: 'appdb',
      backup: {
        retention: cdk.Duration.days(30),
        preferredWindow: '03:00-04:00',
      },
      storageEncrypted: true,
      deletionProtection: true,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    this.dbSecret = this.cluster.secret!;

    // RDS Proxy (for Lambda connections)
    this.proxy = this.cluster.addProxy('RDSProxy', {
      secrets: [this.dbSecret],
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.dbSecurityGroup],
      requireTLS: true,
      iamAuth: true,
      maxConnectionsPercent: 90,
      maxIdleConnectionsPercent: 50,
      borrowTimeout: cdk.Duration.seconds(120),
    });

    // ElastiCache Redis
    const cacheSubnetGroup = new elasticache.CfnSubnetGroup(this, 'CacheSubnetGroup', {
      description: 'Cache subnet group',
      subnetIds: props.vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      }).subnetIds,
    });

    new elasticache.CfnReplicationGroup(this, 'Redis', {
      replicationGroupDescription: 'App cache cluster',
      engine: 'redis',
      cacheNodeType: 'cache.r7g.large',
      numNodeGroups: 1,
      replicasPerNodeGroup: 1,
      automaticFailoverEnabled: true,
      multiAzEnabled: true,
      transitEncryptionEnabled: true,
      atRestEncryptionEnabled: true,
      cacheSubnetGroupName: cacheSubnetGroup.ref,
      securityGroupIds: [props.cacheSecurityGroup.securityGroupId],
    });

    // Outputs
    new cdk.CfnOutput(this, 'ProxyEndpoint', { value: this.proxy.endpoint });
    new cdk.CfnOutput(this, 'ClusterEndpoint', { value: this.cluster.clusterEndpoint.hostname });
    new cdk.CfnOutput(this, 'SecretArn', { value: this.dbSecret.secretArn });
  }
}
```

## 1.4 Compute Stack (Lambda + ECS)
```typescript
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecsPatterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as apigw from 'aws-cdk-lib/aws-apigatewayv2';

export interface ComputeStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
  appSecurityGroup: ec2.SecurityGroup;
  lambdaSecurityGroup: ec2.SecurityGroup;
  dbProxy: rds.DatabaseProxy;
  lambdaMemory: number;
  ecsDesiredCount: number;
  ecsMaxCount: number;
}

export class ComputeStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props: ComputeStackProps) {
    super(scope, id, props);

    // ===== DynamoDB Table =====
    const ordersTable = new dynamodb.Table(this, 'OrdersTable', {
      tableName: 'Orders',
      partitionKey: { name: 'PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'SK', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      pointInTimeRecovery: true,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    ordersTable.addGlobalSecondaryIndex({
      indexName: 'GSI1',
      partitionKey: { name: 'GSI1PK', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'GSI1SK', type: dynamodb.AttributeType.STRING },
    });

    // ===== Lambda Functions =====
    const getOrderFn = new lambda.Function(this, 'GetOrder', {
      runtime: lambda.Runtime.JAVA_21,
      handler: 'com.example.GetOrderHandler::handleRequest',
      code: lambda.Code.fromAsset('app/target/order-service.jar'),
      memorySize: props.lambdaMemory,
      timeout: cdk.Duration.seconds(30),
      architecture: lambda.Architecture.ARM_64,
      snapStart: lambda.SnapStartConf.ON_PUBLISHED_VERSIONS,
      tracing: lambda.Tracing.ACTIVE,
      environment: {
        TABLE_NAME: ordersTable.tableName,
        DB_PROXY_ENDPOINT: props.dbProxy.endpoint,
        POWERTOOLS_SERVICE_NAME: 'order-service',
        POWERTOOLS_LOG_LEVEL: 'INFO',
      },
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.lambdaSecurityGroup],
    });

    ordersTable.grantReadData(getOrderFn);
    props.dbProxy.grantConnect(getOrderFn, 'app_user');

    // ===== ECS Fargate Service =====
    const cluster = new ecs.Cluster(this, 'Cluster', {
      vpc: props.vpc,
      containerInsights: true,
    });

    const fargateService = new ecsPatterns.ApplicationLoadBalancedFargateService(this, 'WebService', {
      cluster,
      desiredCount: props.ecsDesiredCount,
      taskImageOptions: {
        image: ecs.ContainerImage.fromAsset('app/'),
        containerPort: 8080,
        environment: {
          SPRING_PROFILES_ACTIVE: 'aws',
          DB_PROXY_ENDPOINT: props.dbProxy.endpoint,
        },
        secrets: {
          DB_PASSWORD: ecs.Secret.fromSecretsManager(
            props.dbProxy.secret!, 'password'
          ),
        },
      },
      cpu: 512,
      memoryLimitMiB: 1024,
      publicLoadBalancer: true,
      taskSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
      securityGroups: [props.appSecurityGroup],
      healthCheck: {
        command: ['CMD-SHELL', 'curl -f http://localhost:8080/actuator/health || exit 1'],
        interval: cdk.Duration.seconds(30),
        timeout: cdk.Duration.seconds(5),
        retries: 3,
      },
      circuitBreaker: { rollback: true },
    });

    // Auto Scaling
    const scaling = fargateService.service.autoScaleTaskCount({
      minCapacity: props.ecsDesiredCount,
      maxCapacity: props.ecsMaxCount,
    });
    scaling.scaleOnCpuUtilization('CpuScaling', { targetUtilizationPercent: 70 });
    scaling.scaleOnRequestCount('RequestScaling', {
      requestsPerTarget: 1000,
      targetGroup: fargateService.targetGroup,
    });

    props.dbProxy.grantConnect(fargateService.taskDefinition.taskRole, 'app_user');
  }
}
```

---

# Part 2: Sample Spring Boot + Lambda Project

## 2.1 Project Structure
```
order-service/
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/com/example/order/
│   │   │   ├── OrderApplication.java          # Spring Boot entry + Lambda beans
│   │   │   ├── config/
│   │   │   │   ├── AwsConfig.java             # AWS clients config
│   │   │   │   └── DatabaseConfig.java        # DataSource config
│   │   │   ├── domain/
│   │   │   │   ├── Order.java                 # Entity
│   │   │   │   └── OrderStatus.java           # Enum
│   │   │   ├── repository/
│   │   │   │   ├── OrderRepository.java       # Interface
│   │   │   │   └── DynamoDbOrderRepository.java
│   │   │   ├── service/
│   │   │   │   └── OrderService.java          # Business logic
│   │   │   └── handler/
│   │   │       ├── GetOrderHandler.java       # Lambda handler
│   │   │       └── CreateOrderHandler.java
│   │   └── resources/
│   │       ├── application.yml
│   │       └── application-aws.yml
│   └── test/
│       └── java/com/example/order/
│           ├── service/OrderServiceTest.java
│           └── handler/GetOrderHandlerIT.java
├── template.yaml                              # SAM template
└── Dockerfile                                 # For ECS deployment
```

## 2.2 Core Application Code

### pom.xml (Key Dependencies)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>order-service</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.0</version>
    </parent>

    <properties>
        <java.version>21</java.version>
        <spring-cloud-function.version>4.1.0</spring-cloud-function.version>
        <aws-sdk.version>2.25.0</aws-sdk.version>
        <powertools.version>1.18.0</powertools.version>
    </properties>

    <dependencies>
        <!-- Spring Cloud Function (Lambda adapter) -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-function-adapter-aws</artifactId>
            <version>${spring-cloud-function.version}</version>
        </dependency>

        <!-- AWS SDK v2 -->
        <dependency>
            <groupId>software.amazon.awssdk</groupId>
            <artifactId>dynamodb-enhanced</artifactId>
            <version>${aws-sdk.version}</version>
        </dependency>
        <dependency>
            <groupId>software.amazon.awssdk</groupId>
            <artifactId>rds</artifactId>
            <version>${aws-sdk.version}</version>
        </dependency>

        <!-- Lambda Powertools -->
        <dependency>
            <groupId>software.amazon.lambda</groupId>
            <artifactId>powertools-tracing</artifactId>
            <version>${powertools.version}</version>
        </dependency>
        <dependency>
            <groupId>software.amazon.lambda</groupId>
            <artifactId>powertools-logging</artifactId>
            <version>${powertools.version}</version>
        </dependency>
        <dependency>
            <groupId>software.amazon.lambda</groupId>
            <artifactId>powertools-metrics</artifactId>
            <version>${powertools.version}</version>
        </dependency>

        <!-- Lambda Events -->
        <dependency>
            <groupId>com.amazonaws</groupId>
            <artifactId>aws-lambda-java-events</artifactId>
            <version>3.14.0</version>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>localstack</artifactId>
            <version>1.19.0</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <mainClass>com.example.order.OrderApplication</mainClass>
                    <!-- Thin JAR for Lambda (smaller package) -->
                    <layers><enabled>true</enabled></layers>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
```

### OrderApplication.java
```java
package com.example.order;

import com.amazonaws.services.lambda.runtime.events.*;
import com.example.order.service.OrderService;
import com.example.order.domain.Order;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.util.Map;
import java.util.function.Function;

@SpringBootApplication(exclude = {
    org.springframework.boot.autoconfigure.web.servlet.WebMvcAutoConfiguration.class,
})
public class OrderApplication {

    public static void main(String[] args) {
        SpringApplication.run(OrderApplication.class, args);
    }

    private static final ObjectMapper mapper = new ObjectMapper();

    @Bean
    public Function<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> getOrder(
            OrderService orderService) {
        return request -> {
            try {
                String orderId = request.getPathParameters().get("id");
                Order order = orderService.getOrder(orderId);

                if (order == null) {
                    return response(404, Map.of("error", "Order not found"));
                }
                return response(200, order);
            } catch (Exception e) {
                return response(500, Map.of("error", "Internal server error"));
            }
        };
    }

    @Bean
    public Function<APIGatewayProxyRequestEvent, APIGatewayProxyResponseEvent> createOrder(
            OrderService orderService) {
        return request -> {
            try {
                Order order = mapper.readValue(request.getBody(), Order.class);
                Order created = orderService.createOrder(order);
                return response(201, created);
            } catch (IllegalArgumentException e) {
                return response(400, Map.of("error", e.getMessage()));
            } catch (Exception e) {
                return response(500, Map.of("error", "Internal server error"));
            }
        };
    }

    private static APIGatewayProxyResponseEvent response(int status, Object body) {
        try {
            return new APIGatewayProxyResponseEvent()
                .withStatusCode(status)
                .withHeaders(Map.of(
                    "Content-Type", "application/json",
                    "X-Request-Id", java.util.UUID.randomUUID().toString()
                ))
                .withBody(mapper.writeValueAsString(body));
        } catch (Exception e) {
            return new APIGatewayProxyResponseEvent()
                .withStatusCode(500)
                .withBody("{\"error\":\"Serialization error\"}");
        }
    }
}
```

### OrderService.java
```java
package com.example.order.service;

import com.example.order.domain.Order;
import com.example.order.domain.OrderStatus;
import com.example.order.repository.OrderRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import software.amazon.lambda.powertools.tracing.Tracing;

import java.time.Instant;
import java.util.UUID;

public class OrderService {
    private static final Logger log = LoggerFactory.getLogger(OrderService.class);
    private final OrderRepository repository;

    public OrderService(OrderRepository repository) {
        this.repository = repository;
    }

    @Tracing
    public Order getOrder(String orderId) {
        log.info("Fetching order: {}", orderId);
        return repository.findById(orderId);
    }

    @Tracing
    public Order createOrder(Order order) {
        if (order.getItems() == null || order.getItems().isEmpty()) {
            throw new IllegalArgumentException("Order must have at least one item");
        }

        order.setOrderId(UUID.randomUUID().toString());
        order.setStatus(OrderStatus.PENDING);
        order.setCreatedAt(Instant.now());

        log.info("Creating order: {}", order.getOrderId());
        repository.save(order);
        return order;
    }
}
```

### DynamoDbOrderRepository.java
```java
package com.example.order.repository;

import com.example.order.domain.Order;
import software.amazon.awssdk.enhanced.dynamodb.*;
import software.amazon.awssdk.enhanced.dynamodb.model.*;
import software.amazon.lambda.powertools.tracing.Tracing;

public class DynamoDbOrderRepository implements OrderRepository {
    private final DynamoDbTable<Order> table;

    public DynamoDbOrderRepository(DynamoDbEnhancedClient enhancedClient, String tableName) {
        this.table = enhancedClient.table(tableName, TableSchema.fromBean(Order.class));
    }

    @Tracing(segmentName = "DynamoDB GetItem")
    @Override
    public Order findById(String orderId) {
        return table.getItem(Key.builder()
            .partitionValue("ORDER#" + orderId)
            .sortValue("METADATA")
            .build());
    }

    @Tracing(segmentName = "DynamoDB PutItem")
    @Override
    public void save(Order order) {
        table.putItem(order);
    }
}
```

## 2.3 SAM Template
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: Order Service — Lambda + API Gateway

Globals:
  Function:
    Runtime: java21
    MemorySize: 1769
    Timeout: 30
    Architectures: [arm64]
    SnapStart:
      ApplyOn: PublishedVersions
    Tracing: Active
    Environment:
      Variables:
        TABLE_NAME: !Ref OrdersTable
        POWERTOOLS_SERVICE_NAME: order-service
        POWERTOOLS_LOG_LEVEL: INFO

Parameters:
  Stage:
    Type: String
    Default: dev
    AllowedValues: [dev, staging, prod]

Resources:
  # API Gateway (HTTP API)
  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: !Ref Stage
      CorsConfiguration:
        AllowOrigins:
          - '*'
        AllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
        AllowHeaders:
          - Content-Type
          - Authorization

  # Lambda Functions
  GetOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: org.springframework.cloud.function.adapter.aws.FunctionInvoker::handleRequest
      CodeUri: target/order-service-1.0.0.jar
      AutoPublishAlias: live
      DeploymentPreference:
        Type: Canary10Percent5Minutes
        Alarms:
          - !Ref GetOrderErrorAlarm
      Environment:
        Variables:
          SPRING_CLOUD_FUNCTION_DEFINITION: getOrder
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref OrdersTable
      Events:
        GetOrder:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /orders/{id}
            Method: get

  CreateOrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: org.springframework.cloud.function.adapter.aws.FunctionInvoker::handleRequest
      CodeUri: target/order-service-1.0.0.jar
      AutoPublishAlias: live
      Environment:
        Variables:
          SPRING_CLOUD_FUNCTION_DEFINITION: createOrder
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref OrdersTable
      Events:
        CreateOrder:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /orders
            Method: post

  # DynamoDB Table
  OrdersTable:
    Type: AWS::DynamoDB::Table
    DeletionPolicy: Retain
    Properties:
      TableName: !Sub "${Stage}-Orders"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
        - AttributeName: GSI1PK
          AttributeType: S
        - AttributeName: GSI1SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      GlobalSecondaryIndexes:
        - IndexName: GSI1
          KeySchema:
            - AttributeName: GSI1PK
              KeyType: HASH
            - AttributeName: GSI1SK
              KeyType: RANGE
          Projection:
            ProjectionType: ALL
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      SSESpecification:
        SSEEnabled: true

  # Alarms
  GetOrderErrorAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub "${Stage}-GetOrder-Errors"
      MetricName: Errors
      Namespace: AWS/Lambda
      Dimensions:
        - Name: FunctionName
          Value: !Ref GetOrderFunction
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 2
      Threshold: 5
      ComparisonOperator: GreaterThanThreshold

Outputs:
  ApiUrl:
    Value: !Sub "https://${HttpApi}.execute-api.${AWS::Region}.amazonaws.com/${Stage}"
  GetOrderFunction:
    Value: !Ref GetOrderFunction
```

## 2.4 Dockerfile (for ECS deployment)
```dockerfile
# Multi-stage build
FROM maven:3.9-amazoncorretto-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src/ src/
RUN mvn clean package -DskipTests

# Runtime
FROM amazoncorretto:21-alpine
WORKDIR /app

# Security: non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

COPY --from=build /app/target/order-service-1.0.0.jar app.jar

# Spring Boot optimizations
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

## 2.5 application.yml
```yaml
spring:
  application:
    name: order-service
  cloud:
    function:
      definition: getOrder;createOrder
  jackson:
    serialization:
      write-dates-as-timestamps: false
    default-property-inclusion: non_null

logging:
  level:
    root: INFO
    com.example: DEBUG
  pattern:
    console: '{"timestamp":"%d","level":"%p","logger":"%c","message":"%m","traceId":"%X{traceId}"}%n'

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: always

---
# AWS profile
spring:
  config:
    activate:
      on-profile: aws
  datasource:
    url: jdbc:postgresql://${DB_PROXY_ENDPOINT:localhost}:5432/appdb
    hikari:
      maximum-pool-size: 2
      minimum-idle: 0
      idle-timeout: 60000
      connection-timeout: 5000
```
