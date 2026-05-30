# FastAPI Backend Setup & Deployment Guide
## Production-Ready SEO Platform API

---

## ✅ WHAT'S INCLUDED

The new `api.py` is a **production-grade FastAPI application** that:

✅ Integrates all 5 Python modules (PageAuditor, HumanizationValidator, LLMService, etc.)
✅ Includes PostgreSQL database with 3 tables (ContentMetadata, AuditLog, LLMUsageLog)
✅ Has comprehensive error handling with Sentry integration
✅ Includes health checks, status monitoring, and metrics collection
✅ Implements rate limiting via LLM service (60 calls/min)
✅ Tracks costs and enforces $100/day LLM spending cap
✅ Exports data to CSV for analysis
✅ Follows production best practices (async/await, dependency injection, logging)

---

## 📋 QUICK START

### 1. Install Dependencies

```bash
# Core FastAPI stack
pip install fastapi uvicorn sqlalchemy pydantic psycopg2-binary

# Monitoring & Error Tracking
pip install sentry-sdk datadog

# LLM & Utilities
pip install openai redis

# Optional but recommended
pip install python-json-logger python-dotenv
```

**Or use requirements file:**
```bash
# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.0
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
psycopg2-binary==2.9.9
sentry-sdk==1.38.0
datadog==0.48.0
openai==1.3.0
redis==5.0.0
python-dotenv==1.0.0
EOF

pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create `.env` file:

```bash
# Core
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/seo_platform

# LLM
OPENAI_API_KEY=sk-...
LLM_DAILY_COST_LIMIT=100.0
LLM_MAX_CALLS_PER_MINUTE=60

# Redis
REDIS_URL=redis://localhost:6379/0

# Monitoring (optional)
SENTRY_DSN=https://[key]@sentry.io/[project]
DATADOG_API_KEY=
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# API
HOST=0.0.0.0
PORT=8000
WORKERS=4
CORS_ORIGINS=http://localhost:3000,http://localhost:5000
```

### 3. Start the API

```bash
# Development (with auto-reload)
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Production (4 workers)
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4

# With logging to file
uvicorn api:app --host 0.0.0.0 --port 8000 --log-config logging.json
```

### 4. Verify It Works

```bash
# Health check
curl http://localhost:8000/health

# Status
curl http://localhost:8000/status

# API docs (development only)
# Open: http://localhost:8000/docs
```

---

## 🔌 API ENDPOINTS

### Health & Status

**GET `/health`** - System health check
```bash
curl http://localhost:8000/health
# Returns: {status, timestamp, uptime_seconds, checks{database, redis, llm, memory, disk}}
```

**GET `/status`** - API status and metrics
```bash
curl http://localhost:8000/status
# Returns: {status, environment, uptime_seconds, llm_service{daily_spend, daily_limit, rate_limited, queue_depth}}
```

### Content Generation

**POST `/api/v1/generate-metadata`** - Generate SEO metadata
```bash
curl -X POST http://localhost:8000/api/v1/generate-metadata \
  -H "Content-Type: application/json" \
  -d '{
    "page_type": "blog",
    "primary_keyword": "machine learning tutorial",
    "secondary_keywords": "AI, Python, data science",
    "user_id": "user123"
  }'

# Returns: {
#   title: "...",
#   meta_description: "...",
#   h1: "...",
#   h2_headers: [...],
#   h3_headers: [...],
#   content_paragraphs: [...],
#   cta_lines: [...],
#   humanization_score: 85.5,
#   humanization_grade: "A",
#   metadata_id: 1
# }
```

**POST `/api/v1/audit-page`** - Audit HTML page for SEO issues
```bash
curl -X POST http://localhost:8000/api/v1/audit-page \
  -H "Content-Type: application/json" \
  -d '{
    "html_content": "<html><h1>Machine Learning 101</h1>...</html>",
    "primary_keyword": "machine learning",
    "user_id": "user123"
  }'

# Returns: {
#   h1_visibility_score: 100,
#   h1_visible: true,
#   semantic_validation: {...},
#   image_alt_quality: {...},
#   keyword_density: {...},
#   overall_audit_grade: "A+",
#   recommendations: [...]
# }
```

### Data Export

**GET `/api/v1/export/csv`** - Export metadata history as CSV
```bash
curl "http://localhost:8000/api/v1/export/csv?user_id=user123&start_date=2024-01-01" \
  -o metadata-export.csv

# Returns downloadable CSV with columns:
# ID, Page Type, Primary Keyword, Title, Meta Description, H1, Humanization Score, Created At
```

### Monitoring

**GET `/api/v1/metrics`** - Get platform metrics
```bash
curl "http://localhost:8000/api/v1/metrics?time_range=24h"
```

**GET `/api/v1/llm-stats`** - Get LLM usage statistics
```bash
curl http://localhost:8000/api/v1/llm-stats
# Returns: {
#   stats: {daily_spend, daily_limit, rate_limited, queue_depth},
#   recent_usage: [...]
# }
```

### Admin

**POST `/api/v1/admin/reset-daily-spend`** - Reset LLM daily spend counter
```bash
curl -X POST http://localhost:8000/api/v1/admin/reset-daily-spend
```

---

## 🗄️ DATABASE SETUP

### Prerequisites
- PostgreSQL 12+
- psycopg2-binary Python driver

### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE seo_platform;
CREATE USER seo_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE seo_platform TO seo_user;
\q
```

### Update Connection String

```bash
# In .env file:
DATABASE_URL=postgresql://seo_user:secure_password@localhost:5432/seo_platform
```

### Tables (Created Automatically)

The API automatically creates these tables on startup:

**content_metadata** - Stores generated SEO content
```sql
- id (primary key)
- user_id (indexed)
- page_type
- primary_keyword
- secondary_keywords
- title
- meta_description
- h1, h2_headers, h3_headers (JSON)
- content_paragraphs, cta_lines (JSON)
- humanization_score
- audit_results (JSON)
- created_at, updated_at (indexed)
```

**audit_logs** - Tracks all API calls
```sql
- id (primary key)
- user_id (indexed)
- endpoint
- method
- status_code
- response_time_ms
- error_message
- created_at (indexed)
```

**llm_usage_logs** - Tracks LLM costs
```sql
- id (primary key)
- user_id (indexed)
- model
- input_tokens, output_tokens
- cost
- daily_total_cost
- created_at (indexed)
```

### Query Examples

```bash
# Connect to database
psql -U seo_user -d seo_platform

# View recent metadata
SELECT id, page_type, primary_keyword, title, humanization_score, created_at 
FROM content_metadata 
ORDER BY created_at DESC LIMIT 10;

# Check daily LLM spend
SELECT SUM(cost) as daily_spend FROM llm_usage_logs 
WHERE DATE(created_at) = CURRENT_DATE;

# Monitor API performance
SELECT endpoint, AVG(response_time_ms) as avg_time, COUNT(*) as calls
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY endpoint;
```

---

## 📡 REDIS SETUP (For Rate Limiting & Queueing)

### Install Redis

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

### Update Connection

```bash
# In .env file:
REDIS_URL=redis://localhost:6379/0

# For Docker:
REDIS_URL=redis://redis:6379/0
```

### Verify Redis

```bash
redis-cli
> PING
# Should return: PONG

> INFO
# Check Redis status

> EXIT
```

---

## 🔍 MONITORING SETUP

### Sentry Integration (Error Tracking)

1. **Create Sentry Account**
   - Go to: https://sentry.io
   - Create new project → Select "FastAPI"
   - Get your DSN

2. **Update .env**
   ```bash
   SENTRY_DSN=https://[key]@sentry.io/[project_id]
   ```

3. **Verify**
   - Trigger test error: `curl http://localhost:8000/test-error` (if endpoint exists)
   - Check Sentry dashboard for incoming errors

### Datadog Integration (Metrics & Dashboards)

1. **Get API Key**
   - Go to: https://app.datadoghq.com
   - Settings → API Keys → Copy API key

2. **Update .env**
   ```bash
   DATADOG_API_KEY=your_api_key_here
   ```

3. **Verify Metrics**
   ```bash
   # Check that metrics are flowing
   curl http://localhost:8000/api/v1/metrics
   ```

### Slack Alerts

1. **Create Webhook**
   - Go to Slack workspace
   - Apps → Create New App → From scratch
   - Incoming Webhooks → Add New Webhook
   - Copy webhook URL

2. **Update .env**
   ```bash
   SLACK_WEBHOOK=https://hooks.slack.com/services/...
   ```

---

## 🚀 PRODUCTION DEPLOYMENT

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build and run:
```bash
docker build -t seo-api:1.0.0 .
docker run -d \
  --name seo-api \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db:5432/seo_platform" \
  -e REDIS_URL="redis://redis:6379/0" \
  -e OPENAI_API_KEY="sk-..." \
  seo-api:1.0.0
```

### Kubernetes Deployment

Create `deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: seo-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: seo-api
  template:
    metadata:
      labels:
        app: seo-api
    spec:
      containers:
      - name: api
        image: seo-api:1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: seo-secrets
              key: database_url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: seo-secrets
              key: openai_api_key
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 500m
            memory: 1Gi
```

Deploy:
```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs -f deployment/seo-api
```

### Reverse Proxy (Nginx)

```nginx
upstream seo_api {
    server localhost:8000;
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    listen 80;
    server_name api.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
    limit_req zone=api_limit burst=20 nodelay;

    # Proxy to FastAPI
    location / {
        proxy_pass http://seo_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }
}
```

---

## 🧪 TESTING

### Unit Tests

Create `test_api.py`:
```python
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]

def test_generate_metadata():
    response = client.post("/api/v1/generate-metadata", json={
        "page_type": "blog",
        "primary_keyword": "python programming",
    })
    assert response.status_code == 200
    assert "title" in response.json()
    assert "humanization_score" in response.json()

def test_invalid_page_type():
    response = client.post("/api/v1/generate-metadata", json={
        "page_type": "invalid_type",
        "primary_keyword": "test",
    })
    assert response.status_code == 422  # Validation error
```

Run tests:
```bash
pip install pytest
pytest test_api.py -v
```

### Load Testing

Create `load_test.py` using Locust:
```python
from locust import HttpUser, task, between

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health")

    @task
    def generate_metadata(self):
        self.client.post("/api/v1/generate-metadata", json={
            "page_type": "blog",
            "primary_keyword": "machine learning",
        })
```

Run load test:
```bash
pip install locust
locust -f load_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

---

## 📊 MONITORING DASHBOARDS

### Datadog Dashboard

Key metrics to track:
- **Latency**: P50, P95, P99 response times
- **Error Rate**: % of 5xx errors
- **Throughput**: Requests per second
- **LLM Cost**: Daily spend vs $100 limit
- **Database Connections**: Active/idle/overflow
- **Redis Queue**: Job queue depth

### CloudWatch Logs

Search examples:
```
# Find slow requests
response_time_ms > 5000

# Find errors
status_code >= 500

# Find LLM costs
"daily_spend" > 50

# Find rate limit hits
"rate_limited"
```

---

## 🐛 TROUBLESHOOTING

### Common Issues

**Issue: "Connection refused" on database**
```
Error: could not translate host name "localhost" to address
Solution: Update DATABASE_URL, ensure PostgreSQL is running
```

**Issue: LLM service not initializing**
```
Error: RobustLLMService import failed
Solution: Check OPENAI_API_KEY env var, run: pip install openai redis
```

**Issue: API starts but endpoints return 500 errors**
```
Check logs: tail -f api.log
Look for: module import errors, database connection issues, Redis unavailable
```

**Issue: Slow response times**
```
Check: SELECT * FROM pg_stat_statements WHERE mean_exec_time > 1000;
Kill slow queries: SELECT pg_terminate_backend(pid) FROM ...
Increase pool_size in database config
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Install all Python dependencies
- [ ] Create PostgreSQL database and user
- [ ] Start Redis server
- [ ] Create `.env` file with all variables
- [ ] Run `python api.py` to test startup
- [ ] Hit `/health` endpoint to verify
- [ ] Run test_api.py to verify endpoints
- [ ] Setup Sentry and Datadog (optional)
- [ ] Setup monitoring dashboards
- [ ] Run load testing (500 users, 10 min)
- [ ] Verify error handling and logging
- [ ] Document API for frontend team
- [ ] Deploy to staging environment
- [ ] Perform production readiness gate testing
- [ ] Execute canary deployment (72-hour rollout)
- [ ] Monitor in production

---

## 📚 NEXT STEPS

1. **Frontend Integration**
   - Update HTML to call API endpoints instead of local code
   - Connect to `/api/v1/generate-metadata` and `/api/v1/audit-page`
   - Display results from API responses

2. **Testing**
   - Run production readiness gate tests (PRODUCTION_READINESS_GATES.md)
   - Load testing: 500 concurrent users
   - Security testing: OWASP Top 10 vulnerabilities

3. **Deployment**
   - Follow CANARY_DEPLOYMENT.md (72-hour progressive rollout)
   - Monitor using MONITORING_OBSERVABILITY_CONFIG.md
   - Use INCIDENT_RESPONSE_PROCEDURES.md for emergencies

---

## 📞 SUPPORT

For questions:
1. Check FastAPI docs: https://fastapi.tiangolo.com
2. Review Python module docstrings in page_auditor.py, llm_service.py, etc.
3. Check logs: `tail -f api.log`
4. Run health check: `curl http://localhost:8000/health`

---

**Status:** ✅ READY FOR DEPLOYMENT

**Last Updated:** May 12, 2024

**Version:** 1.0.0 (Production-Ready)
