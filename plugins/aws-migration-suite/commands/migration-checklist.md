---
name: Migration Checklist
description: Generate a comprehensive migration checklist with pre-migration, during, and post-migration tasks
---

Generate a comprehensive migration checklist for the specified application or migration wave.

Include checklists for all phases:

## Pre-Migration
- [ ] Application assessment completed and documented
- [ ] Migration strategy (6R) selected and approved
- [ ] Target architecture designed and reviewed
- [ ] Dependencies identified and migration order defined
- [ ] Rollback plan documented and tested
- [ ] Communication plan to stakeholders
- [ ] Training plan for operations team
- [ ] Budget approved and resources allocated
- [ ] AWS accounts and environments provisioned
- [ ] Networking configured (VPC, VPN, Direct Connect)
- [ ] Security baseline applied (IAM, encryption, logging)
- [ ] CI/CD pipeline set up for target environment
- [ ] Monitoring and alerting configured
- [ ] Performance baseline captured on source system
- [ ] Data migration strategy defined
- [ ] Test plan and acceptance criteria documented
- [ ] Compliance requirements verified for target

## During Migration
- [ ] Source system backup taken before migration
- [ ] Data migration started and validated
- [ ] Application deployed to target environment
- [ ] Smoke tests passed
- [ ] Integration tests passed
- [ ] Performance tests match or exceed baseline
- [ ] Security scan completed (no critical findings)
- [ ] DNS/routing cutover plan ready
- [ ] Rollback tested and ready
- [ ] Stakeholders notified of cutover window
- [ ] Cutover executed (DNS switch, load balancer update)
- [ ] Production traffic verified on target
- [ ] Source system monitoring for residual traffic

## Post-Migration
- [ ] Application functioning correctly in production
- [ ] All integrations verified end-to-end
- [ ] Performance meets SLA requirements
- [ ] Monitoring dashboards show healthy metrics
- [ ] Alert rules firing correctly (tested)
- [ ] Operations team trained and handed over
- [ ] Runbooks updated for new environment
- [ ] Source system decommission plan scheduled
- [ ] Cost actuals match estimates (first billing cycle)
- [ ] Well-Architected review completed
- [ ] Lessons learned documented
- [ ] Migration report delivered to stakeholders

Customize this checklist based on the specific application context provided.

$ARGUMENTS
