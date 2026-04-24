---
description: Guide Java application migration to AWS Serverless — Lambda, Spring Cloud Function, SnapStart, Step Functions
---

Help migrate a Java application to AWS Serverless architecture.

Analyze the current Java application and provide:

1. **Current State Analysis**
   - Java version, framework (Spring Boot, Struts, J2EE, plain servlet)
   - Application type (web app, REST API, batch processing, integration)
   - Database and data access (JDBC, JPA/Hibernate, MyBatis)
   - External dependencies and integrations
   - State management (stateless vs stateful)

2. **Migration Approach**
   - Recommended Lambda approach:
     - **Spring Cloud Function** — for Spring Boot apps
     - **AWS Lambda Handler** — for lightweight functions
     - **GraalVM Native Image** — for minimal cold starts
   - Handler design and function granularity
   - Shared vs dedicated Lambda functions

3. **Code Migration**
   - Convert request handling to Lambda handlers
   - Migrate dependency injection
   - Handle database connections (RDS Proxy for Aurora)
   - Replace file system with S3
   - Convert properties/config to environment variables + Secrets Manager

4. **Cold Start Optimization**
   - SnapStart configuration (Java 11+)
   - Dependency reduction strategies
   - Lazy initialization patterns
   - Provisioned Concurrency (when needed)
   - Performance benchmarks

5. **Infrastructure**
   - SAM or CDK template for all resources
   - API Gateway configuration (REST vs HTTP API)
   - Step Functions for batch/workflow migration
   - DynamoDB or Aurora Serverless for data layer

6. **Deployment Pipeline**
   - CI/CD pipeline (CodePipeline or GitHub Actions)
   - Environment management (dev/staging/prod)
   - Canary/blue-green deployment strategy

7. **Testing Strategy**
   - Local testing with SAM CLI
   - Integration testing approach
   - Load testing for cold start validation
   - Rollback procedure

Provide concrete code examples for the migration patterns and a SAM/CDK template.

$ARGUMENTS
