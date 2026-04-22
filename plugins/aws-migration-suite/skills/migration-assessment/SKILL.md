---
name: migration-assessment
description: This skill should be used when the user asks to "assess an application for migration", "evaluate migration readiness", "score migration complexity", "create migration portfolio", "analyze dependencies", "plan migration waves", or mentions application discovery, migration readiness scoring, or TCO analysis.
version: 1.0.0
---

# Migration Assessment Skill

Assess applications and systems for cloud migration readiness using structured frameworks, scoring models, and AWS discovery tools.

## Assessment Framework

### 6-Dimension Scoring Model

Rate each application on a 1-5 scale across these dimensions:

| Dimension | 1 (Hard) | 3 (Moderate) | 5 (Easy) |
|-----------|----------|--------------|----------|
| **Business Criticality** | Revenue-critical, zero downtime | Important, some tolerance | Internal, flexible SLA |
| **Technical Complexity** | Monolith, custom frameworks | Standard frameworks, some coupling | Microservices, cloud-ready |
| **Data Sensitivity** | PCI/HIPAA regulated | Internal confidential | Public or non-sensitive |
| **Dependency Depth** | 10+ upstream/downstream | 3-9 connections | 0-2 connections |
| **Cloud Readiness** | Stateful, OS-dependent | Some state, portable | 12-factor, containerized |
| **Team Readiness** | No cloud experience | Some AWS knowledge | AWS certified team |

**Migration Difficulty Score** = Average of all dimensions
- 4.0-5.0: Easy migration → Wave 1
- 3.0-3.9: Moderate migration → Wave 2
- 2.0-2.9: Complex migration → Wave 3
- 1.0-1.9: Very complex → Wave 4 or Retain

### Application Inventory Template

```markdown
## Application: [Name]
- **Owner:** [Team/Person]
- **Technology Stack:** [Java 8, Struts 2, Oracle 11g, Tomcat 8]
- **Type:** [Web App / Batch / API / Integration]
- **Users:** [Count and type (internal/external)]
- **Uptime SLA:** [99.9% / 99.5% / Best effort]
- **Data Volume:** [GB/TB, growth rate]
- **Integrations:** [List upstream/downstream systems]
- **Compliance:** [HIPAA / PCI / SOC2 / None]
- **Pain Points:** [Performance, cost, maintainability]
- **Migration Score:** [1-5 average]
- **Recommended Strategy:** [Rehost/Replatform/Refactor/Repurchase/Retain/Retire]
```

### Dependency Mapping

Categories to document:
1. **Data dependencies** — Databases, shared schemas, ETL feeds
2. **Service dependencies** — APIs, SOAP services, message queues
3. **Infrastructure dependencies** — Shared file systems, network, DNS
4. **Authentication dependencies** — LDAP, SSO, certificates
5. **Batch dependencies** — Scheduled jobs, file transfers, reports

### AWS Discovery Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| **Migration Hub** | Central tracking dashboard | Always — single pane of glass |
| **Application Discovery Service** | Agent/agentless server discovery | Automated inventory |
| **Migration Evaluator** | TCO analysis and rightsizing | Cost comparison |
| **CloudEndure / AWS MGN** | Replication-based migration | Rehost assessment |
| **Database Migration Service** | DB schema analysis | Database migration |
| **App2Container** | Containerization analysis | Container migration |

### TCO Analysis Template

```
Current State (Annual):
  Hardware/DC:     $___
  Licensing:       $___
  Operations:      $___
  Maintenance:     $___
  Total Current:   $___

Migration Cost (One-time):
  Assessment:      $___
  Migration labor: $___
  Testing:         $___
  Training:        $___
  Double-running:  $___
  Total Migration: $___

Target State (Annual):
  AWS Services:    $___
  Licensing:       $___
  Operations:      $___
  Maintenance:     $___
  Total Target:    $___

ROI:
  Annual Savings:  $___
  Break-even:      ___ months
  3-Year ROI:      ___%
```

### Wave Planning Criteria

Group applications into waves considering:
1. **Dependencies first** — Foundation services migrate before dependents
2. **Quick wins early** — Easy apps in Wave 1 build confidence
3. **Risk spreading** — Don't put all critical apps in one wave
4. **Team capacity** — Match wave size to team availability
5. **Business calendar** — Avoid migration during peak business periods
