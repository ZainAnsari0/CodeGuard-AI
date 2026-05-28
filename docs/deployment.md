# CodeGuard AI — Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2+
- Domain name (for production TLS)
- 4GB+ RAM, 2+ CPU cores
- Linux host (tested on Ubuntu 22.04)

## Quick Start

### Development

```bash
# Clone and configure
git clone <repo-url> && cd FYP
cp .env.example .env
# Edit .env with your API keys

# Generate JWT keys
bash backend/scripts/setup-tls.sh self-signed

# Start services
docker compose up -d

# Run database migrations
docker exec codeguard_api alembic upgrade head

# Verify
curl http://localhost:8000/health
curl http://localhost:3000/
```

### Production

```bash
# 1. Configure environment
cp .env.production .env.production.local
# Edit ALL CHANGE_ME placeholders with strong passwords

# 2. Generate TLS certificates
# For local/self-signed:
bash backend/scripts/setup-tls.sh self-signed
# For production with a domain:
DOMAIN=codeguard.example.com bash backend/scripts/setup-tls.sh production

# 3. Deploy
bash backend/scripts/deploy.sh production

# 4. Verify
curl -f https://localhost/health
```

## Architecture

```
                    ┌─────────────┐
                    │   Internet   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   Nginx (FE)  │  :80/:443
                    │  TLS + Static │
                    └──────┬───────┘
                           │ /api/
                    ┌──────▼───────┐
                    │  FastAPI API  │  :8000
                    │  + /metrics   │
                    └──────┬───────┘
                     ┌─────┼──────┐
                ┌────▼─┐ ┌─▼────┐ │
                │Redis │ │PG DB │ │
                └──────┘ └──────┘ │
                    ┌──────▼──────┐
                    │    Celery    │
                    │  + Beat      │
                    └─────────────┘
```

### Networks (Production)

| Network    | Services                              | Purpose          |
|------------|---------------------------------------|------------------|
| `public`   | frontend, grafana                    | Internet-facing  |
| `backend`  | frontend, api, celery, celery-beat, prometheus, grafana | Service mesh |
| `data`     | api, celery, celery-beat, postgres, redis  | Data layer  |
| `monitoring` | prometheus, grafana                | Metrics          |

### Volumes

| Volume             | Service    | Purpose              |
|--------------------|-----------|----------------------|
| `postgres_data`    | postgres  | Persistent DB data   |
| `redis_data`      | redis     | Persistent cache      |
| `prometheus_data` | prometheus| Metrics storage       |
| `grafana_data`     | grafana   | Dashboard storage     |

## Environment Variables

### Required (Production)

| Variable              | Description                          | Default                     |
|-----------------------|--------------------------------------|-----------------------------|
| `POSTGRES_PASSWORD`   | Database password                    | **CHANGE_ME**               |
| `JWT_ALGORITHM`       | JWT algorithm (HS256 or RS256)       | RS256                       |
| `ALLOWED_HOSTS`       | Comma-separated allowed hosts        | localhost,127.0.0.1         |
| `CORS_ORIGINS`        | Comma-separated CORS origins         | https://codeguard.example.com|
| `OPENAI_API_KEY`      | OpenAI API key                       |                             |
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password            | **CHANGE_ME**               |

### Optional

| Variable                | Description                    | Default                      |
|-------------------------|--------------------------------|------------------------------|
| `DEBUG`                 | Enable debug mode              | false                        |
| `RATE_LIMIT_REQUESTS`   | Max requests per window        | 60                           |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window (s)       | 60                           |
| `GROQ_API_KEY`          | Groq API key                   |                              |
| `OLLAMA_URL`            | Ollama endpoint                | http://host.docker.internal:11434 |

## Monitoring

### Accessing Dashboards

- **Grafana**: http://localhost:3001 (admin / password from .env.production)
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/metrics

### Key Metrics

| Metric                     | Alert Threshold         |
|----------------------------|-------------------------|
| 5xx Error Rate             | > 5% for 5 minutes      |
| p95 Latency                | > 2s for 5 minutes       |
| Scan Queue Backlog         | > 50 pending for 10 min  |
| Memory Usage               | > 85% for 10 minutes     |
| Disk Space                 | < 10% remaining          |

## Backup & Restore

### Create Backup

```bash
bash backend/scripts/backup-db.sh
```

Backups are stored in `backups/` directory. Default retention: 7 backups.

### Restore from Backup

```bash
bash backend/scripts/restore-db.sh backups/codeguard_codeguard_20260528_020000.sql.gz
```

### Automated Daily Backups (Crontab)

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/FYP/backend/scripts/backup-db.sh >> /var/log/codeguard-backup.log 2>&1
```

## TLS Certificates

### Generate Self-Signed (Development)

```bash
bash backend/scripts/setup-tls.sh self-signed
```

### Request Let's Encrypt (Production)

```bash
DOMAIN=codeguard.example.com bash backend/scripts/setup-tls.sh production
```

### Renew Let's Encrypt Certificates

```bash
bash backend/scripts/renew-tls.sh
```

### Auto-Renewal (Crontab)

```bash
# Renew at 3 AM on the 1st of each month
0 3 1 * * /path/to/FYP/backend/scripts/renew-tls.sh >> /var/log/tls-renewal.log 2>&1
```

## Troubleshooting

### Services won't start

```bash
# Check service status
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs api
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs celery

# Restart specific service
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart api
```

### Database connection errors

```bash
# Check PostgreSQL is healthy
docker exec codeguard_postgres pg_isready

# Check connection from API
docker exec codeguard_api python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
```

### High memory usage

```bash
# Check container resource usage
docker stats --no-stream

# Increase memory limits in docker-compose.prod.yml
# deploy.resources.limits.memory: 1G -> 2G
```

### Reset everything

```bash
# Stop all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# WARNING: This removes all data volumes
docker compose -f docker-compose.yml -f docker-compose.prod.yml down -v
```