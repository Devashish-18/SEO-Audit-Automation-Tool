# CANARY DEPLOYMENT PROCEDURE
## Progressive Rollout Strategy for SEO Platform

---

## OVERVIEW

Canary deployment reduces risk by gradually rolling out changes to a subset of users, monitoring for issues before full GA launch.

**Traffic Distribution:**
- Phase 1: 1% → 10% users (Internal + Early Users)
- Phase 2: 50% users (Expanded Testing)  
- Phase 3: 100% users (General Availability)

**Total Duration:** 72 hours (3 days)  
**Rollback Trigger:** Any critical issue → Immediate 100% rollback

---

## PRE-DEPLOYMENT CHECKLIST (Day 0)

### ✅ Requirements (Complete 24 hours before deploy)

- [ ] All P0/P1 bugs resolved
- [ ] Code deployed to staging environment
- [ ] All automated tests passing (unit, integration, security)
- [ ] Performance baseline established (P50, P95, P99 latency)
- [ ] Database migrations tested on staging data
- [ ] Backup of production database verified
- [ ] Incident response team on standby
- [ ] Communication templates prepared
- [ ] Rollback procedures documented and tested
- [ ] Monitoring dashboards configured and tested

### ✅ Team Assignments

```
Role                    Name              Contact
─────────────────────────────────────────────────────────
Deployment Lead         [Name]            [Slack/Phone]
On-Call Engineer        [Name]            [Slack/Phone]
DevOps Lead             [Name]            [Slack/Phone]
Product Owner           [Name]            [Slack/Phone]
Communications Lead     [Name]            [Slack/Phone]
```

### ✅ Deployment Window

**Date:** [DATE]  
**Start Time:** [TIME] UTC  
**Expected Duration:** 30 minutes  
**Maintenance Window:** [TIME] UTC  
**Timezone:** UTC  

---

## PHASE 1: INTERNAL VALIDATION (24 Hours)

### Duration
**Start:** 0:00 UTC  
**End:** 24:00 UTC  
**Team:** Engineering only

### Traffic: 1% of Production Users

### Deployment Steps

1. **Pre-flight (0:00-0:15)**
   ```bash
   # Notify team
   slack: "🚀 Canary Phase 1 starting - 1% traffic"
   
   # Health check
   curl https://api.example.com/health
   > {"status": "OK", "version": "1.0.0"}
   ```

2. **Deploy to 1% Traffic (0:15-0:30)**
   ```bash
   kubectl patch service api-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"CANARY_WEIGHT","value":"1"}]}]}}}}'
   ```

3. **Monitor (0:30-24:00)**
   - Watch error rate every 5 minutes
   - Watch latency (P50, P95, P99)
   - Watch LLM cost tracking
   - Watch database pool health

### Success Criteria (ALL must be ✅)

| Metric | Threshold | Current | Status |
|--------|-----------|---------|--------|
| Error Rate | <0.1% | TBD | [ ] |
| P50 Latency | <2.0s | TBD | [ ] |
| P95 Latency | <5.0s | TBD | [ ] |
| P99 Latency | <10.0s | TBD | [ ] |
| LLM Calls/min | <60 | TBD | [ ] |
| DB Connections | <80% capacity | TBD | [ ] |
| Sentry Errors | <5 new types | TBD | [ ] |
| CPU Usage | <70% | TBD | [ ] |
| Memory Usage | <80% | TBD | [ ] |

### Monitoring Dashboard Links
- Datadog: https://app.datadoghq.com/...
- Sentry: https://sentry.io/...
- CloudWatch: https://console.aws.amazon.com/...

### Decision Point (24:00)

**PASS:** Proceed to Phase 2  
**FAIL:** Automatic rollback; incident review meeting

---

## PHASE 2: EARLY USER EXPANSION (24 Hours)

### Duration
**Start:** 24:00 UTC (Day 1)  
**End:** 48:00 UTC (Day 2)  
**Team:** Engineering + Product

### Traffic: 10% of Production Users

### Deployment Steps

1. **Increase Traffic (24:00-24:15)**
   ```bash
   # Scale to 10%
   kubectl patch service api-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"CANARY_WEIGHT","value":"10"}]}]}}}}'
   
   slack: "📈 Phase 2 starting - scaled to 10% traffic"
   ```

2. **Monitor (24:15-48:00)**
   - Continuous error rate monitoring
   - Latency trending
   - User feedback collection (Slack, emails)
   - LLM cost tracking

### Success Criteria (Same as Phase 1)

| Metric | Threshold | Current | Status |
|--------|-----------|---------|--------|
| Error Rate | <0.1% | TBD | [ ] |
| P95 Latency | <5.0s | TBD | [ ] |
| User Complaints | 0 P0/P1 | TBD | [ ] |
| LLM Cost Trend | $X-$Y/hour | TBD | [ ] |

### User Feedback Collection

**Collect from:**
- Internal beta users (email survey)
- Early adopter customers (Slack)
- Sales team (feature feedback)

**Template:** "Is the new SEO tool working well for you? Any issues?"

### Decision Point (48:00)

**PASS:** Proceed to Phase 3  
**FAIL:** Automatic rollback; incident review meeting  
**CAUTION:** Expand slower if any warnings but no critical failures

---

## PHASE 3: ROLLING DEPLOYMENT (24 Hours)

### Duration
**Start:** 48:00 UTC (Day 2)  
**End:** 72:00 UTC (Day 3)  
**Team:** Full team + On-call rotation

### Traffic: 50% → 100% Progressive Rollout

### Deployment Steps

1. **Phase 3a: 50% Traffic (48:00-60:00)**
   ```bash
   kubectl patch service api-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"CANARY_WEIGHT","value":"50"}]}]}}}}'
   slack: "📊 Phase 3a - scaled to 50% traffic"
   ```

2. **Phase 3b: 100% Traffic (60:00-72:00)**
   ```bash
   kubectl patch service api-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"CANARY_WEIGHT","value":"100"}]}]}}}}'
   slack: "🎉 Phase 3b - 100% GA launch"
   ```

3. **Monitor Continuously**
   - 5-minute check intervals (Phase 3a)
   - 15-minute check intervals (Phase 3b)
   - On-call engineer watching dashboard 24/7

### Success Criteria

**Phase 3a (50%):**
- Error rate remains <0.1%
- P95 latency <5.0s
- No new Sentry error types
- CPU/Memory trending normally

**Phase 3b (100%):**
- Error rate <0.1% sustained
- All metrics stable
- On-call engineer confident in stability
- No customer complaints

### Decision Point (72:00)

**PASS:** Deployment complete; post-deployment review  
**FAIL:** Immediate rollback; incident postmortem

---

## ROLLBACK PROCEDURE

### Automatic Rollback Triggers

```
IF error_rate > 1.0% THEN
  AUTOMATIC_ROLLBACK = TRUE
  ALERT = "CRITICAL"
  ROLLBACK_REASON = "Error rate exceeded 1%"

IF p95_latency > 10s THEN
  AUTOMATIC_ROLLBACK = TRUE
  ALERT = "CRITICAL"
  ROLLBACK_REASON = "P95 latency exceeded threshold"

IF database_connections > 90% THEN
  AUTOMATIC_ROLLBACK = TRUE
  ALERT = "CRITICAL"
  ROLLBACK_REASON = "DB connection pool exhausted"

IF lvm_daily_cost > $120 THEN
  AUTOMATIC_ROLLBACK = TRUE
  ALERT = "CRITICAL"
  ROLLBACK_REASON = "LLM cost exceeded limit"
```

### Manual Rollback (On-Demand)

**Decision:** Deployment Lead + Product Owner  
**Trigger:** Any P0 issue

**Execution:**
```bash
# 1. Stop accepting new requests
kubectl scale deployment api-service --replicas=0

# 2. Restore previous version
git checkout v1.2.3  # Previous stable version
docker build -t api:v1.2.3 .
docker push api:v1.2.3

# 3. Redeploy previous version
kubectl set image deployment/api-service api=api:v1.2.3

# 4. Scale back up
kubectl scale deployment api-service --replicas=10

# 5. Verify health
curl https://api.example.com/health

# 6. Notify team
slack: "🔄 ROLLBACK COMPLETE - Reverted to v1.2.3"
email: "Incident team"
```

**Rollback Time:** < 5 minutes  
**Data Impact:** None (read-only deployment)

---

## INCIDENT RESPONSE

### If Critical Issue Detected

**Step 1: Alert (IMMEDIATE)**
```
✅ Page on-call engineer
✅ Slack #incident channel
✅ Email incident@company.com
```

**Step 2: Assess (< 5 min)**
```
- Severity: P0 | P1 | P2
- Scope: % of users affected
- Data loss: Yes/No
- Escalation needed: Yes/No
```

**Step 3: Decide (< 2 min)**
```
- Rollback now? YES/NO
- Hotfix? YES/NO
- Communicate to customers? YES/NO
```

**Step 4: Execute (< 5 min)**
```
- If Rollback: Execute procedure above
- If Hotfix: Apply patch to canary tier only
- If Both: Rollback first, hotfix while users back on stable
```

**Step 5: Investigate (Post-incident)**
```
- Root cause analysis
- Fix implementation
- Restart deployment (all phases)
```

---

## COMMUNICATION TEMPLATES

### Phase 1 Kick-Off
```
Subject: 🚀 Canary Deployment - Phase 1 Starting

Hi team,

The SEO Platform v2.0 canary deployment is starting:

📅 Date: [DATE]
⏰ Duration: 72 hours (3 phases)
🎯 Goal: Gradually rollout with 100% stability

Phase 1 (24h): 1% traffic, internal users only
Phase 2 (24h): 10% traffic, early users
Phase 3 (24h): 50% → 100% gradual rollout

Monitoring: [Dashboard link]
Contacts: [On-call engineer]

🛑 Rollback triggers configured - auto rollback if error rate >1%
```

### Phase Transition
```
Subject: ✅ Canary Phase 1 Complete - Proceeding to Phase 2

All metrics normal:
✅ Error rate: 0.03% (threshold: <0.1%)
✅ P95 latency: 3.2s (threshold: <5.0s)
✅ No critical issues

Scaling to 10% traffic at [TIME] UTC.
```

### GA Launch Complete
```
Subject: 🎉 SEO Platform v2.0 - GA Launch Complete

The new SEO Platform is now live for 100% of users:

✅ 72-hour canary deployment successful
✅ Zero critical incidents
✅ All systems stable

What's new:
- Advanced page auditor with CSS detection
- Humanization validator for content quality
- Rate-limited LLM integration
- Production-grade infrastructure

Thank you for your patience!
```

### Rollback Notification
```
Subject: 🔄 URGENT: Canary Deployment Rollback

We've rolled back to v1.2.3 due to [REASON]:

Issue: [Brief description]
Impact: [User-facing impact]
Duration: [Expected to be resolved in X hours]

We apologize for the interruption and will provide updates every 30 minutes.

Status page: https://status.example.com
Contact: incident@company.com
```

---

## POST-DEPLOYMENT REVIEW (24 Hours After GA)

### Checklist

- [ ] All metrics stable and within normal ranges
- [ ] No customer support escalations related to deployment
- [ ] No data integrity issues detected
- [ ] Performance meets SLAs
- [ ] All monitoring alerts functioning correctly
- [ ] On-call engineer logs reviewed (no suspicious activity)
- [ ] Capacity trending normal (no runaway resource usage)

### Team Retrospective (48 Hours After GA)

**Attendees:**
- Deployment Lead
- On-Call Engineer
- DevOps Lead
- Product Owner
- 2-3 engineers involved in deployment

**Agenda:**
1. Timeline review (what went well, what could improve)
2. Metrics discussion (performance, errors, cost)
3. User feedback summary
4. Process improvements for next deployment
5. Action items

**Output:**
- Deployment retrospective document
- Process improvements logged as tickets
- Lessons learned recorded for future teams

---

## SUCCESS CRITERIA

**Canary Deployment is SUCCESSFUL if:**

✅ 72-hour rollout completes without rollback  
✅ Zero P0 incidents during deployment  
✅ Error rate <0.1% throughout all phases  
✅ Latency metrics met (P95 <5.0s)  
✅ LLM cost tracking accurate and within budget  
✅ Database performance stable  
✅ No data loss or corruption  
✅ Positive user feedback or neutral (no negative)  
✅ Team confidence in new version  

---

## APPENDIX: MONITORING COMMANDS

```bash
# Watch error rate every 5 seconds
watch -n 5 'curl https://api.example.com/metrics | grep error_rate'

# Watch latency percentiles
watch -n 10 'curl https://api.example.com/metrics | grep latency'

# Watch LLM spending
watch -n 60 'curl https://api.example.com/metrics | grep llm_cost'

# Watch database connections
watch -n 5 'psql -h db.example.com -U admin -d platform -c "SELECT count(*) FROM pg_stat_activity"'

# Watch pod restarts
kubectl get pods --watch

# Watch logs
kubectl logs -f deployment/api-service --tail=100

# Scale canary traffic
kubectl patch service api-service -p '{"spec":{"template":{"spec":{"containers":[{"name":"api","env":[{"name":"CANARY_WEIGHT","value":"X"}]}]}}}}'

# Get current traffic split
kubectl get service api-service -o yaml | grep CANARY_WEIGHT
```

---

## RELATED DOCUMENTS

- PRODUCTION_READINESS_GATES.md
- PHASE_GATING_FRAMEWORK.md
- INCIDENT_RESPONSE_PROCEDURES.md
- MONITORING_OBSERVABILITY_CONFIG.md
