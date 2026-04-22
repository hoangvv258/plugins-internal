---
name: Migration Strategy
description: Generate a migration strategy document with 6R mapping, roadmap, cost analysis, and risk assessment
---

Create a comprehensive migration strategy document for the given application(s) or system.

Include the following sections:

1. **Executive Summary**
   - Migration scope and objectives
   - Key decisions and recommendations
   - Timeline overview

2. **Current State Assessment**
   - Application portfolio summary
   - Technology stack inventory
   - Current TCO (infrastructure, licensing, operations)

3. **6R Strategy Mapping**
   For each application, recommend one of:
   - **Rehost** — Lift & shift to EC2/ECS
   - **Replatform** — Move to managed services (RDS, ElastiCache)
   - **Refactor** — Re-architect for cloud-native (Lambda, ECS Fargate)
   - **Repurchase** — Replace with SaaS
   - **Retain** — Keep on-premises
   - **Retire** — Decommission

4. **Target Architecture**
   - AWS service mapping for each application
   - Architecture diagram (ASCII or Mermaid)
   - Integration patterns between services

5. **Migration Roadmap**
   - Wave planning with dependencies
   - Milestones and decision gates
   - Timeline with parallel workstreams

6. **Cost Analysis**
   - Current vs target TCO comparison
   - Migration investment (one-time costs)
   - ROI projection (1-year, 3-year, 5-year)

7. **Risk Register**
   - Technical, business, and organizational risks
   - Probability and impact ratings
   - Mitigation strategies for each risk

8. **Team & Resources**
   - Required skills and roles
   - Training needs
   - AWS partner/support recommendations

$ARGUMENTS
