# CodeGuard AI — Deployment Guide

## Architecture Overview

CodeGuard AI runs as a set of local processes — no Docker containers required.

```
┌──────────────────────────────────────────────────┐
│                 Nginx (Reverse Proxy)              │
│              TLS termination + static files         │
└──────────────────────┬────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                          │
┌─────────┴─────────┐  ┌────────────┴─────────────┐
│  FastAPI Backend   │  │   Celery Workers          │
│  (uvicorn)        │  │   (scan processing)        │
│  Port 8000        │  │                            │
└─────────┬─────────┘  └────────────┬──────────────┘
          │                          │
    ┌─────┴──────┐          ┌──────┴──────┐
    │ PostgreSQL │          │   Redis      │
    │  (Primary  │          │  (Broker +   │
    │   DB)      │          │   Cache)     │
    └────────────┘          └──────────────┘
```

**Key architectural principle:** Scans run via in-process AST analysis — uploaded code is **parsed, never executed**. Temporary workspaces provide filesystem isolation between scans.

---

## Prerequisites

- Python 3.11+
- Node.js 18+ (for JavaScript scanner)
- PostgreSQL 16+
- Redis 7+
- Nginx (production TLS termination)

---

## Local Development Setup

### 1. Clone and Configure

```bash
git clone <repo-url> && cd FYP
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, GROQ_API_KEY, etc.)
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate JWT keys for RS256
bash scripts/setup-tls.sh self-signed

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Celery Worker (separate terminal)

```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app worker --loglevel=info
```

### 4. Celery Beat (optional, for scheduled tasks)

```bash
cd backend
source venv/bin/activate
celery -A app.tasks.celery_app beat --loglevel=info
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Available at http://localhost:5173
```

### 6. Production Frontend Build

```bash
cd frontend
npm run build
# Static files in frontend/dist/
```

---

## Production Deployment

### Environment Variables

Copy `.env.production` and fill in ALL secrets:

```bash
cp .env.production .env.production.local
# Edit ALL CHANGE_ME placeholders
```

**Required in production:**
- `SECRET_KEY` — 32+ character random string
- `JWT_SECRET_KEY` — 32+ character random string (or use RS256 key pair)
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string with password
- `CORS_ORIGINS` — Your production domain(s)

### systemd Service Files

**API Server** (`/etc/systemd/system/codeguard-api.service`):

```ini
[Unit]
Description=CodeGuard AI API Server
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=codeguard
WorkingDirectory=/opt/codeguard/backend
Environment=PATH=/opt/codeguard/backend/venv/bin
ExecStart=/opt/codeguard/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Celery Worker** (`/etc/systemd/system/codeguard-celery.service`):

```ini
[Unit]
Description=CodeGuard AI Celery Worker
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=codeguard
WorkingDirectory=/opt/codeguard/backend
Environment=PATH=/opt/codeguard/backend/venv/bin
ExecStart=/opt/codeguard/backend/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name codeguard.example.com;

    ssl_certificate /etc/letsencrypt/live/codeguard.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/codeguard.example.com/privkey.pem;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;

    # Frontend (static files)
    location / {
        root /opt/codeguard/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
    }

    # Metrics (internal network only)
    location /metrics {
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        proxy_pass http://127.0.0.1:8000;
    }
}

server {
    listen 80;
    server_name codeguard.example.com;
    return 301 https://$host$request_uri;
}
```

---

## Security Model

### Static Analysis Safety

CodeGuard AI performs **static analysis only**. Uploaded code is:

- **Parsed** via AST (Python) or Acorn (JavaScript)
- **Analyzed** for vulnerability patterns
- **Never executed, interpreted, or compiled**

### Temporary Workspace Isolation

Each scan gets an isolated temporary workspace:
- Files stored in `/tmp/codeguard_uploads/{scan_id}/`
- Workspaces deleted after scan completion
- Stale workspaces cleaned up on startup and periodically
- Only vulnerability metadata is persisted to the database

### Production Checklist

- [ ] PostgreSQL configured (not SQLite)
- [ ] Redis password set
- [ ] JWT RS256 key pair generated
- [ ] SECRET_KEY and JWT_SECRET_KEY set (32+ chars)
- [ ] CORS_ORIGINS set to production domains (no localhost)
- [ ] EMAIL_BACKEND set to smtp (not console)
- [ ] TLS certificates configured
- [ ] Nginx security headers enabled
- [ ] File upload limits configured (MAX_FILE_SIZE, ALLOWED_EXTENSIONS)
- [ ] Rate limiting active
- [ ] Prometheus + Grafana monitoring active

---

## Monitoring

### Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### Metrics

- **FastAPI metrics**: Available at `/metrics` (via prometheus-fastapi-instrumentator)
- **PostgreSQL**: Via postgres_exporter
- **Redis**: Via redis_exporter
- **System**: Via node_exporter

### Grafana Dashboard

Import `monitoring/grafana/dashboards/codeguard-overview.json` for:
- Request rate and latency
- Scan queue depth
- AI provider availability
- Database and Redis health
- Error rate by endpoint

---

## Database Management

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Backup
bash scripts/backup-db.sh

# Restore
bash scripts/restore-db.sh
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| API won't start | Check `.env` configuration, verify PostgreSQL and Redis are running |
| Scans stuck in pending | Verify Celery worker is running and connected to Redis |
| JWT errors | Ensure JWT keys are generated and paths configured |
| Upload errors | Check `UPLOAD_DIR` is writable, verify `MAX_FILE_SIZE` |
| AI providers failing | Check API keys in `.env`, verify Ollama is running if configured |
| Node.js scanner | Ensure Node.js 18+ is installed for JavaScript scanning |