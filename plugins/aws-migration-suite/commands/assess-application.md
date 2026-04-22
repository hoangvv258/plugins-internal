---
name: Assess Application
description: Assess an application for cloud migration readiness — inventory, dependencies, complexity scoring
---

Assess the following application for cloud migration readiness to AWS.

Perform a comprehensive assessment covering:

1. **Application Inventory**
   - Identify technology stack (language, framework, runtime, database)
   - List all components (web, API, batch, integration)
   - Document current infrastructure (servers, OS, middleware)

2. **Dependency Mapping**
   - Map upstream dependencies (who calls this app?)
   - Map downstream dependencies (what does this app call?)
   - Identify data dependencies (shared databases, file systems)
   - Document authentication/SSO dependencies

3. **Complexity Scoring** (rate 1-5 for each)
   - Business Criticality
   - Technical Complexity
   - Data Sensitivity
   - Dependency Depth
   - Cloud Readiness
   - Team Readiness

4. **Risk Identification**
   - Technical risks (compatibility, performance, data)
   - Business risks (downtime, user impact)
   - Organizational risks (skills, capacity)

5. **Recommendation**
   - Recommended 6R strategy (Rehost/Replatform/Refactor/Repurchase/Retain/Retire)
   - Target AWS services
   - Estimated effort (T-shirt size)
   - Suggested migration wave

Provide the assessment in a structured format with clear scoring and actionable recommendations.

$ARGUMENTS
