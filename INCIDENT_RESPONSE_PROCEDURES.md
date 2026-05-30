# INCIDENT RESPONSE & DISASTER RECOVERY PROCEDURES
## Production Emergency Playbooks for SEO Platform

---

## INCIDENT SEVERITY LEVELS

| Severity | Definition | Response Time | Example |
|----------|-----------|----------------|---------|
| **P0 - CRITICAL** | Data loss, total service down, security breach | < 15 min | Database corrupted, all servers down, XSS vulnerability exposed |
| **P1 - HIGH** | Major functionality broken, 10%+ users affected | < 1 hour | Metadata generation broken, 50% error rate |
| **P2 - MEDIUM** | Partial functionality issue, <10% users affected | < 4 hours | Search broken, some CTAs not displaying |
| **P3 - LOW** | Minor issue, no user impact | < 24 hours | Typo in UI, slow report generation |

---

## INCIDENT RESPONSE FLOWCHART

```
ALERT TRIGGERED
       ↓
   [DETECT] → Is it real? (Not a false positive)
       ↓ YES
   [TRIAGE] → Severity? (P0/P1/P2/P3)
       ↓
   [ASSESS] → Scope? (How many users? Data loss?)
       ↓
   [DECIDE] → Rollback needed? (Yes/No)
       ↓
   [EXECUTE] → Implement fix or rollback
       ↓
   [VERIFY] → Is issue resolved?
       ↓
   [DOCUMENT] → Incident log + postmortem
       ↓
   [COMMUNICATE] → Notify stakeholders
       ↓
   [PREVENT] → Implement controls to prevent recurrence
```

---

## P0 INCIDENT PROCEDURES (CRITICAL)

### Example P0 Scenarios
- ❌ Database completely down
- ❌ All API endpoints returning 500 errors
- ❌ Data corruption/loss detected
- ❌ Security vulnerability exploited
- ❌ LLM service billing runaway (>$1000/day)
- ❌ Unauthorized data access

### IMMEDIATE ACTIONS (First 5 Minutes)

**Step 1: PAGE ON-CALL ENGINEER (< 1 min)**
```
1. PagerDuty: Send CRITICAL alert
2. Slack #incidents: Post initial alert
3. Call on-call: Voice notification + SMS
4. Zoom bridge: Create incident call (auto-link in Slack)
```

**Step 2: EXECUTIVE NOTIFICATION (< 2 min)**
```
Email: VP Engineering, Product Owner
Subject: "🚨 CRITICAL INCIDENT: [Service Name]"
Body:
  - Severity: P0
  - What's down: [Component]
  - Estimated impact: [Users/% of traffic]
  - ETA to fix: [TBD]
```

**Step 3: ASSESS IMPACT (< 5 min)**
```
Questions to answer:
1. How many users affected? (%)
2. Is data being lost? (YES/NO)
3. Can users still access critical features? (YES/NO)
4. Should we notify public status page? (YES/NO)
```

### DECISION POINT: ROLLBACK OR FIX?

**ROLLBACK if:**
- ✅ Issue is in code deployed in last 2 hours
- ✅ Root cause unclear
- ✅ Fix would take >30 minutes
- ✅ Rollback verified to restore service

**FIX if:**
- ✅ Issue existed before latest deployment
- ✅ Quick fix available (<10 minutes)
- ✅ High confidence fix is safe

### ROLLBACK EXECUTION (< 10 min total)

```bash
# 1. FREEZE TRAFFIC (< 1 min)
kubectl scale deployment api-service --replicas=0

# 2. VERIFY PREVIOUS VERSION GOOD
kubectl rollout history deployment/api-service
# Find last stable version

# 3. ROLLBACK CODE (< 2 min)
kubectl rollout undo deployment/api-service
# or
git checkout HEAD~1
docker build -t api:rollback .
docker push api:rollback
kubectl set image deployment/api-service api=api:rollback

# 4. RESTORE DATABASE (if corrupted) (< 5 min)
# From backup (tested daily)
pg_restore -d seo_platform /backups/latest.sql

# 5. SCALE SERVICES BACK (< 2 min)
kubectl scale deployment/api-service --replicas=10
kubectl rollout status deployment/api-service

# 6. VERIFY SERVICE HEALTHY (< 2 min)
curl https://api.example.com/health
# Expect: {"status": "healthy"}
```

### POST-ROLLBACK (Immediate)

```
Slack #incidents:
"✅ ROLLBACK COMPLETE
- Rolled back to v1.2.3
- Service restored at 12:45 UTC
- Investigating root cause..."

Email stakeholders:
Subject: "Incident Update: Service Restored"
Body: "Service is back online. Root cause analysis in progress."
```

### INVESTIGATION & FIX

```
1. Root cause analysis
   - Review: git diff, deployment logs, metrics spike
   - Question: What changed in last 2 hours?

2. Implement fix
   - Code fix + tests
   - Deploy to staging first
   - Manual testing on staging
   
3. Re-deploy carefully
   - Monitor first 5 minutes closely
   - Gradual rollout (1% → 10% → 100%)
```

---

## P1 INCIDENT PROCEDURES (HIGH)

### Example P1 Scenarios
- ⚠️ Metadata generation broken (50% error rate)
- ⚠️ Page auditor returning incorrect results
- ⚠️ LLM rate limiting not working
- ⚠️ Database queries taking >10 seconds
- ⚠️ Security issue (non-critical)

### RESPONSE TIMELINE

| Time | Action |
|------|--------|
| 0-5 min | Alert → Page engineer → Assess |
| 5-15 min | Decide: Rollback vs Fix |
| 15-30 min | Execute rollback or hotfix |
| 30-60 min | Verify service restored |
| 60+ min | Root cause analysis + fix |

### INVESTIGATION CHECKLIST

```
□ Check error logs (Sentry)
□ Check metrics (Datadog) - look for spikes
□ Check database slow query log
□ Check LLM cost & call volume
□ Review recent code changes (git log)
□ Review recent infrastructure changes
□ Check for external dependency issues (OpenAI down?)
□ Check database replication lag
□ Check disk space / memory
```

### COMMUNICATION TEMPLATE

```
Subject: P1 Incident Update

Severity: HIGH (P1)
Status: Investigating [OPEN/RESOLVED]
Impact: Metadata generation broken (~50% error rate)
Affected Users: ~5000
Duration: 15 minutes so far
ETA to fix: 30 minutes

Latest: Traced to LLM rate limiter not resetting. Fix deployed to staging for testing.

Next: Monitor fix in staging, then canary deploy to 1% production traffic.
```

---

## P2 INCIDENT PROCEDURES (MEDIUM)

### Example P2 Scenarios
- ⚠️ Search feature slow (>5 sec)
- ⚠️ Some CTAs not rendering
- ⚠️ Export CSV feature broken
- ⚠️ One workflow broken (others working)

### RESPONSE TIMELINE

```
Alert → (1 hour) → Investigation → Fix → Verify

For P2: Non-critical, handle during business hours
```

### QUICK TROUBLESHOOTING

1. **Is it cache issue?** Clear cache, retry
2. **Is it database performance?** Check slow queries, analyze
3. **Is it frontend issue?** Check browser console for errors
4. **Is it LLM issue?** Check LLM queue depth and error rate
5. **Is it configuration?** Check environment variables

---

## DISASTER RECOVERY PROCEDURES

### SCENARIO 1: DATABASE CORRUPTION

**Detection:**
- Query returns invalid data
- Foreign key constraint violations
- Data integrity checks failing

**Recovery Steps:**

```bash
# Step 1: Verify corruption scope
psql -d seo_platform -c "SELECT COUNT(*) FROM metadata WHERE created_at IS NULL"
# If returns >0: corruption confirmed

# Step 2: Stop all writes
kubectl scale deployment api-service --replicas=0

# Step 3: Restore from backup
# Backups are taken daily at 2 AM UTC
BACKUP_FILE="/backups/seo_platform_$(date -d yesterday +%Y-%m-%d).sql"
pg_restore --clean --if-exists -d seo_platform $BACKUP_FILE

# Step 4: Run data integrity checks
psql -d seo_platform -f scripts/integrity_checks.sql

# Step 5: Restore service
kubectl scale deployment api-service --replicas=10

# Step 6: Monitor for issues
watch -n 5 'curl https://api.example.com/health'
```

**Time to Recovery:** 30 minutes  
**Data Loss:** Up to 24 hours (from last backup)

---

### SCENARIO 2: DISK SPACE EXHAUSTED

**Detection:**
- Alert: Disk usage >90%
- Errors: "No space left on device"
- Processes: Hanging or crashing

**Recovery Steps:**

```bash
# Step 1: Identify large files
df -h /
du -sh /var/log/*
du -sh /data/*

# Step 2: Clean up logs
rm /var/log/api/*.log.old
rm /var/log/nginx/*.log.1

# Step 3: Clean database temporary tables
psql -d seo_platform -c "VACUUM ANALYZE;"

# Step 4: Archive old data
# Move data older than 90 days to archive storage
SELECT COUNT(*) FROM metadata WHERE created_at < NOW() - INTERVAL '90 days';

# Step 5: Resize disk (if in cloud)
# AWS: Increase volume size + extend partition
```

**Prevention:** Monitor disk weekly, set alerts at 75% full

---

### SCENARIO 3: COMPLETE SERVICE OUTAGE

**Recovery from Complete Outage:**

```
Timeline:
- T+00:00 → Service down, alert triggered
- T+00:05 → Engineers paged
- T+00:15 → Root cause identified
- T+00:30 → Service restored (rollback OR fix deployed)
- T+01:00 → Stabilization monitoring
- T+02:00 → Incident postmortem
```

**Recovery Checklist:**

```
□ Restore database from backup
□ Restore application code from git tag
□ Restart all services (API, Workers, Redis)
□ Verify all health checks passing
□ Monitor error rate & latency for 30 minutes
□ Notify stakeholders: service restored
□ Schedule postmortem meeting
```

---

### SCENARIO 4: DATA BREACH / SECURITY INCIDENT

**Immediate Actions (First 30 Minutes):**

```
1. ISOLATE
   - Take affected service offline
   - Revoke all API keys
   - Change database passwords
   - Block suspicious IPs

2. INVESTIGATE
   - Check access logs for unauthorized access
   - Identify what data was exposed
   - Determine if credentials were leaked
   - Check for backdoors (new users, cron jobs)

3. NOTIFY
   - Call Legal & Security team
   - Call VP Engineering
   - Prepare customer notification email
   - Notify regulatory bodies if required

4. REMEDIATE
   - Patch vulnerability
   - Rotate all secrets
   - Force password reset for all users
   - Deploy security fix
   - Re-enable service with monitoring
```

**Do NOT:**
- ❌ Hide incident or delay disclosure
- ❌ Take service offline longer than necessary
- ❌ Rotate secrets without tracking old ones (for forensics)
- ❌ Delete logs (preserve for investigation)

---

## INCIDENT LOG TEMPLATE

```
INCIDENT LOG

Incident ID: INC-2024-001
Date: 2024-05-12
Severity: P1
Status: RESOLVED

TIMELINE:
- 12:30 UTC: Alert triggered (Error rate 5%)
- 12:35 UTC: On-call engineer acknowledged
- 12:45 UTC: Root cause identified (LLM rate limit stuck)
- 13:00 UTC: Hotfix deployed to production
- 13:05 UTC: Service verified healthy
- 13:10 UTC: Incident declared resolved

IMPACT:
- Duration: 40 minutes
- Users affected: ~5000
- Transactions lost: None (data not written)
- Data loss: No
- Root cause: LLM service returned 429 error, rate limiter failed to reset

ROOT CAUSE ANALYSIS:
- Redis connection dropped during rate limit reset
- No fallback logic to handle connection loss
- Issue: Missing error handling in rate limit check

RESOLUTION:
1. Deployed hotfix to retry Redis operation with exponential backoff
2. Added monitoring for Redis connection health
3. Added alerting for rate limiter failures

PREVENTION:
1. Add circuit breaker for Redis operations
2. Implement fallback to in-memory rate limiting
3. Add tests for Redis failure scenarios
4. Code review for all external service dependencies

FOLLOW-UP TASKS:
□ [ ] Deploy circuit breaker (Due: 2024-05-19)
□ [ ] Add Redis failure tests (Due: 2024-05-15)
□ [ ] Update runbook with Redis troubleshooting (Due: 2024-05-13)
□ [ ] Post-incident review meeting (Done: 2024-05-13)
```

---

## RUNBOOK: COMMON ISSUES

### Issue: High Error Rate (>1%)

**Diagnosis:**
```bash
# Check error types in Sentry
curl https://api.sentry.io/api/0/projects/org/project/events/

# Check database connection health
SELECT count(*) FROM pg_stat_activity;

# Check LLM rate limiting
curl https://api.example.com/metrics | grep llm

# Check error logs
kubectl logs -f deployment/api-service --tail=50
```

**Quick Fixes:**
1. Check if LLM service is returning errors → Wait or restart
2. Check if database is slow → Kill long queries
3. Check if rate limiting is stuck → Restart Redis
4. Check if cache is full → Flush old entries

### Issue: High Latency (P95 > 10s)

**Diagnosis:**
```bash
# Check slow queries
psql -d seo_platform -c "SELECT * FROM pg_stat_statements WHERE mean_exec_time > 1000;"

# Check database connections
SELECT count(*) FROM pg_stat_activity;

# Check LLM queue depth
curl https://api.example.com/metrics | grep queue_depth

# Check resource usage
top -b -n 1 | head -20
```

**Quick Fixes:**
1. Kill slow queries: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE duration > 30s;`
2. Scale database: Add read replicas
3. Reduce LLM timeout: Lower max_wait from 30s to 10s
4. Restart services: Clear memory leaks

### Issue: LLM Service Not Responding

**Diagnosis:**
```bash
# Check OpenAI API status
curl https://status.openai.com/api/v2/incidents.json

# Check LLM service stats
curl https://api.example.com/llm-service/stats

# Check rate limiting
redis-cli GET llm:daily_spend

# Check LLM queue
redis-cli ZCARD llm:queue
```

**Quick Fixes:**
1. Check OpenAI status page (might be their outage)
2. Reset daily spend counter: `redis-cli DEL llm:daily_spend`
3. Clear stuck jobs: `redis-cli DEL llm:queue`
4. Restart LLM service

---

## ON-CALL ROTATION

### Schedule Template

```
Week of May 12:
- Monday-Wednesday: Engineer A (alice@company.com)
- Wednesday-Friday: Engineer B (bob@company.com)
- Friday-Monday: Engineer C (charlie@company.com)

Handoff: Friday 9 AM UTC

On-call Responsibilities:
- Respond to pages within 15 min
- Investigate and triage incidents
- Execute incident response procedures
- Escalate to manager if unsure
- Complete incident log before handoff
```

### On-Call Checklist

```
Starting Your On-Call Shift:
□ Update Slack status: "🚨 On-call: Alice"
□ Verify PagerDuty schedule
□ Test alert delivery (send test alert)
□ Verify phone/SMS settings
□ Review recent incidents
□ Ensure access to all systems

Ending Your On-Call Shift:
□ Handoff to next engineer (call or Slack)
□ Document any ongoing incidents
□ Update Slack status: "No longer on-call"
□ Review and log all incidents
```

---

## COMMUNICATION TEMPLATES

### Initial Alert (Internal)

```
🚨 INCIDENT ALERT - P1

Service: SEO Platform API
Issue: Metadata generation returning 50% errors
Detection Time: 12:30 UTC
Status: INVESTIGATING

Slack link: #incidents
Dashboard: [Datadog link]
Slack: @alice-oncall is investigating
```

### Customer Notification (Major Outage)

```
Subject: Service Disruption - SEO Platform (RESOLVED)

Dear Customers,

We experienced a service disruption affecting the SEO Platform 
from 12:30 UTC to 13:10 UTC on May 12, 2024 (40 minutes).

During this time, metadata generation had elevated error rates 
affecting approximately 5,000 active users.

Root Cause: External API rate limiting issue
Status: RESOLVED - Service is fully operational
Impact: No data loss, all functionality restored

We apologize for the disruption and appreciate your patience.

For questions: support@company.com
Status page: https://status.company.com
```

### Post-Incident Summary

```
INCIDENT POSTMORTEM: INC-2024-001

Executive Summary:
LLM rate limiter failed to reset due to Redis connection loss.

Timeline:
- 12:30: Alert triggered
- 12:45: Root cause identified
- 13:00: Fix deployed
- 13:10: Resolved

Impact: 40 minutes, ~5000 users affected, no data loss

Root Cause: Missing error handling in Redis connection

Prevention: Circuit breaker implementation (in progress)

Meeting: Friday 2 PM UTC - incident review
```

---

## RELATED DOCUMENTS

- PRODUCTION_READINESS_GATES.md
- CANARY_DEPLOYMENT.md
- MONITORING_OBSERVABILITY_CONFIG.md
- DATABASE_POOL.md
