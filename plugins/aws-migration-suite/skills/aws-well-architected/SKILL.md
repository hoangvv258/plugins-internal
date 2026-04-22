---
name: aws-well-architected
description: This skill should be used when the user asks to "apply Well-Architected Framework", "review architecture against AWS pillars", "optimize for reliability or cost", "design for security on AWS", "improve operational excellence", "run Well-Architected review", or mentions AWS WAF pillars, architecture best practices, or migration architecture validation.
version: 1.0.0
---

# AWS Well-Architected Skill

Apply the AWS Well-Architected Framework to validate migration target architectures across all six pillars.

## The Six Pillars

### 1. Operational Excellence

**Design Principles:**
- Perform operations as code (IaC)
- Make frequent, small, reversible changes
- Refine operations procedures frequently
- Anticipate failure
- Learn from all operational events

**Migration Checklist:**
- [ ] Infrastructure as Code (CDK/CloudFormation/Terraform)
- [ ] CI/CD pipeline for automated deployments
- [ ] Structured logging (JSON, correlation IDs)
- [ ] Distributed tracing (X-Ray)
- [ ] CloudWatch dashboards and alarms
- [ ] Runbooks for common operational tasks
- [ ] Post-incident review process

### 2. Security

**Design Principles:**
- Implement a strong identity foundation
- Enable traceability
- Apply security at all layers
- Automate security best practices
- Protect data in transit and at rest
- Prepare for security events

**Migration Checklist:**
- [ ] IAM roles with least privilege (no long-term credentials)
- [ ] VPC with private subnets for backend services
- [ ] Encryption at rest (KMS) and in transit (TLS 1.2+)
- [ ] WAF for public-facing applications
- [ ] Security groups and NACLs properly configured
- [ ] Secrets in Secrets Manager (not env vars or code)
- [ ] CloudTrail enabled for audit logging
- [ ] GuardDuty for threat detection
- [ ] Cognito or IAM for authentication

### 3. Reliability

**Design Principles:**
- Automatically recover from failure
- Test recovery procedures
- Scale horizontally
- Stop guessing capacity
- Manage change through automation

**Migration Checklist:**
- [ ] Multi-AZ deployment for all stateful services
- [ ] Auto-scaling configured (target tracking or step)
- [ ] Health checks at load balancer and application level
- [ ] Circuit breakers for external dependencies
- [ ] Retry with exponential backoff for transient errors
- [ ] Dead letter queues for async processing
- [ ] Backup strategy with tested restore procedure
- [ ] DR plan (RPO/RTO defined, tested)

### 4. Performance Efficiency

**Design Principles:**
- Democratize advanced technologies
- Go global in minutes
- Use serverless architectures
- Experiment more often
- Consider mechanical sympathy

**Migration Checklist:**
- [ ] Right-sized compute (Compute Optimizer recommendations)
- [ ] Caching strategy (ElastiCache, CloudFront, API Gateway cache)
- [ ] Database optimized (read replicas, connection pooling, RDS Proxy)
- [ ] Async processing for non-critical paths (SQS, EventBridge)
- [ ] CDN for static assets (CloudFront)
- [ ] ARM64/Graviton where supported (20% cost savings)
- [ ] Performance baseline established and monitored

### 5. Cost Optimization

**Design Principles:**
- Implement cloud financial management
- Adopt a consumption model
- Measure overall efficiency
- Stop spending money on undifferentiated heavy lifting
- Analyze and attribute expenditure

**Migration Checklist:**
- [ ] Serverless where possible (Lambda, Fargate, DynamoDB on-demand)
- [ ] Savings Plans or Reserved Instances for steady-state
- [ ] Spot Instances for fault-tolerant workloads
- [ ] S3 lifecycle policies for data tiering
- [ ] Right-sizing (Compute Optimizer)
- [ ] Cost allocation tags on all resources
- [ ] Budget alerts configured
- [ ] Unused resource cleanup (EC2, EBS, EIP)

### 6. Sustainability

**Design Principles:**
- Understand your impact
- Establish sustainability goals
- Maximize utilization
- Anticipate and adopt new, more efficient offerings
- Use managed services
- Reduce downstream impact

**Migration Checklist:**
- [ ] Use managed/serverless services (higher utilization)
- [ ] Right-size to reduce waste
- [ ] Use ARM64 processors (more efficient per watt)
- [ ] Optimize data transfer and storage
- [ ] Consider region carbon intensity

## Architecture Review Process

### Pre-Migration Review
1. Review current architecture against pillars
2. Identify gaps and risks
3. Design target architecture addressing gaps
4. Document Architecture Decision Records (ADRs)

### Post-Migration Review
1. Run AWS Well-Architected Tool review
2. Validate all pillar checklists
3. Address High Risk Issues (HRIs) first
4. Schedule quarterly re-reviews

### Architecture Decision Record (ADR) Template
```markdown
## ADR-001: [Decision Title]

**Status:** Accepted / Proposed / Deprecated
**Date:** YYYY-MM-DD
**Context:** Why this decision is needed
**Decision:** What was decided
**Consequences:** Positive and negative impacts
**Alternatives Considered:** Other options evaluated
```

## Common Anti-Patterns in Migration

| Anti-Pattern | Problem | Solution |
|-------------|---------|----------|
| Lift-and-shift everything | No cloud benefits | Evaluate 6R per app |
| Single AZ deployment | Single point of failure | Multi-AZ always |
| Hardcoded credentials | Security vulnerability | Secrets Manager |
| No IaC | Manual drift, no reproducibility | CDK/CloudFormation |
| Over-provisioned EC2 | Wasted cost | Right-size, auto-scale |
| No monitoring | Blind to issues | CloudWatch, X-Ray |
| No backup/DR | Data loss risk | Automated backups, DR plan |
| Public subnets for everything | Exposed attack surface | Private subnets + ALB |
