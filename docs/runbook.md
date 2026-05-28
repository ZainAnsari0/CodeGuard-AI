# CodeGuard AI — Operations Runbook

## Service Health

### Check All Services

```bash
docker compose ps
```

### Individual Health Checks

```bash
# API health
curl -f http://localhost:8000/health

# Frontend health (production)
curl -f https://localhost/health

# PostgreSQL
docker exec codeguard_postgres pg_isready -U codeguard_user -d codeguard

# Redis
docker exec codeguard_redis redis-cli ping
```

## Restarting Services

### Restart Single Service

```bash
# Development
docker compose restart api

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart api
```

### Restart All Services

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart
```

### Rebuild and Restart

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api
docker compose logs -f celery
docker compose logs -f frontend

# Last 100 lines
docker compose logs --tail 100 api
```

## Database Operations

### Connect to PostgreSQL

```bash
docker exec -it codeguard_postgres psql -U codeguard_user -d codeguard
```

### Backup

```bash
bash backend/scripts/backup-db.sh
```

### Restore

```bash
bash backend/scripts/restore-db.sh backups/codeguard_codeguard_20260528_020000.sql.gz
```

### Run Migrations

```bash
docker exec codeguard_api alembic upgrade head
```

### Check Migration Status

```bash
docker exec codeguard_api alembic current
```

## Scaling Workers

### Increase Celery Concurrency

Edit `docker-compose.prod.yml` and change the celery worker concurrency:

```yaml
celery:
  command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=8
```

Then restart:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d celery
```

## Monitoring

### Grafana Dashboard

Access at: http://localhost:3001

Default credentials (from .env.production):
- Username: admin
- Password: (from GRAFANA_ADMIN_PASSWORD)

### Prometheus Metrics

Access at: http://localhost:9090

Key queries:
- Request rate: `rate(http_requests_total[5m])`
- p95 latency: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- Error rate: `rate(http_requests_total{status=~"5.."}[5m])`

## Common Incidents

### API Returns 502/503

1. Check if API container is running: `docker compose ps api`
2. Check API logs: `docker compose logs --tail 50 api`
3. Check database connectivity: `docker exec codeguard_postgres pg_isready`
4. Restart API: `docker compose restart api`

### High Memory Usage

1. Check resource usage: `docker stats --no-stream`
2. Identify the container with high usage
3. Check for memory leaks in logs
4. Restart the affected container
5. If persistent, increase memory limit in `docker-compose.prod.yml`

### Celery Queue Backlog

1. Check Celery logs: `docker compose logs --tail 100 celery`
2. Check active tasks in Redis: `docker exec codeguard_redis redis-cli LLEN celery`
3. Increase worker concurrency (see Scaling Workers above)
4. Check if scanner containers are stuck: `docker ps | grep codeguard-scanner`

### Database Connection Pool Exhaustion

1. Check active connections: `docker exec codeguard_postgres psql -U codeguard_user -d codeguard -c "SELECT count(*) FROM pg_stat_activity;"`
2. Check max connections: `docker exec codeguard_postgres psql -U codeguard_user -d codeguard -c "SHOW max_connections;"`
3. Restart API to reset connection pool: `docker compose restart api`

### TLS Certificate Expiry

1. Check cert expiry: `openssl x509 -in certs/tls_cert.pem -noout -dates`
2. Renew: `bash backend/scripts/renew-tls.sh`
3. For self-signed (dev): `bash backend/scripts/setup-tls.sh self-signed`

## Rollback a Deployment

```bash
bash backend/scripts/deploy.sh production --rollback
```

Or manually:

```bash
# Find the previous tag
git tag --sort=-version:refname | head -5

# Checkout and deploy
git checkout <previous-tag>
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```