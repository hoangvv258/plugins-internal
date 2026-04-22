# AWS Migration Suite Plugin v1.0

A comprehensive Claude Code plugin for **full-lifecycle AWS migration** — from assessment to optimization, covering Java→Serverless, Struts→Spring, and low-code/WebPerformer migrations.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     MIGRATION LIFECYCLE                       │
├────────────┬──────────────┬──────────────┬──────────────────┤
│  ASSESS    │   STRATEGY   │   DESIGN     │   MIGRATE        │
│            │              │              │                   │
│ • Inventory│ • 6R Mapping │ • Target     │ • Java→Serverless│
│ • Deps     │ • Roadmap    │   Architecture│ • Struts→Spring │
│ • Scoring  │ • Cost/Risk  │ • IaC        │ • Low-code       │
│ • Waves    │ • Timeline   │ • Security   │ • Data migration │
├────────────┴──────────────┴──────────────┴──────────────────┤
│                     AWS TARGET PLATFORM                      │
│  Lambda │ ECS Fargate │ API Gateway │ Aurora │ DynamoDB      │
│  Step Functions │ SQS │ EventBridge │ S3 │ CloudFront       │
├─────────────────────────────────────────────────────────────┤
│                     GOVERNANCE                               │
│  Well-Architected Framework │ Security │ Cost Optimization   │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Migration Types Supported

### Java → AWS Serverless
- Spring Boot → Lambda (Spring Cloud Function)
- Java monolith → Lambda + Step Functions (strangler fig)
- Cold start optimization (SnapStart, GraalVM, Provisioned Concurrency)
- Batch processing → Step Functions + Lambda

### Struts → Spring Boot
- Struts 1.x/2.x → Spring MVC/Spring Boot
- Action → Controller, ActionForm → DTO, Interceptor → HandlerInterceptor
- JSP + Struts tags → Thymeleaf (or REST API)
- Incremental coexistence migration strategy

### Low-Code / WebPerformer
- Business logic extraction and documentation
- Decision matrix: Custom dev vs alternative low-code vs SaaS
- WebPerformer components → Spring Boot / React equivalents
- Data model and workflow migration

## 🚀 Quick Start

1. Install the plugin in Claude Code
2. Use `/assess-application` to evaluate migration readiness
3. Use `/migration-strategy` to create a comprehensive strategy
4. Use `/design-architecture` to design the target AWS architecture
5. Use `/java-to-serverless` for Java→Lambda migration guidance
6. Use `/struts-to-spring` for Struts→Spring conversion patterns
7. Use `/migration-checklist` for a complete migration checklist

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/assess-application` | Assess app for migration readiness (inventory, deps, scoring) |
| `/migration-strategy` | Generate migration strategy (6R, roadmap, cost, risk) |
| `/design-architecture` | Design target AWS architecture with IaC templates |
| `/java-to-serverless` | Java→AWS Serverless migration guide with code examples |
| `/struts-to-spring` | Struts→Spring Boot migration with component mapping |
| `/migration-checklist` | Pre/during/post migration checklist |

## 🤖 Agents

| Agent | Expertise |
|-------|-----------|
| `migration-assessor` | Application assessment, dependency mapping, readiness scoring |
| `migration-strategist` | 6R strategy, roadmap, cost analysis, risk management |
| `architecture-designer` | AWS target architecture, service selection, Well-Architected |
| `java-serverless-engineer` | Java→Lambda, Spring Cloud Function, SnapStart, strangler fig |
| `struts-spring-migrator` | Struts→Spring conversion, component mapping, incremental migration |
| `lowcode-migration-advisor` | WebPerformer, low-code extraction, platform evaluation |

## 📚 Skills

| Skill | Coverage |
|-------|----------|
| `migration-assessment` | Assessment frameworks, scoring models, discovery tools |
| `aws-serverless-guide` | Lambda, API Gateway, Step Functions, DynamoDB, SAM/CDK |
| `java-modernization` | Monolith decomposition, DDD, containerization, Java upgrades |
| `struts-to-spring` | Component mapping, code conversion, security migration |
| `aws-well-architected` | 6 pillars checklists, architecture review, anti-patterns |

## 📦 Plugin Structure

```
aws-migration-suite/
├── .claude-plugin/
│   └── plugin.json
├── agents/
│   ├── migration-assessor.md
│   ├── migration-strategist.md
│   ├── architecture-designer.md
│   ├── java-serverless-engineer.md
│   ├── struts-spring-migrator.md
│   └── lowcode-migration-advisor.md
├── commands/
│   ├── assess-application.md
│   ├── migration-strategy.md
│   ├── design-architecture.md
│   ├── java-to-serverless.md
│   ├── struts-to-spring.md
│   └── migration-checklist.md
├── skills/
│   ├── migration-assessment/
│   │   └── SKILL.md
│   ├── aws-serverless-guide/
│   │   └── SKILL.md
│   ├── java-modernization/
│   │   └── SKILL.md
│   ├── struts-to-spring/
│   │   └── SKILL.md
│   └── aws-well-architected/
│       └── SKILL.md
└── README.md
```
