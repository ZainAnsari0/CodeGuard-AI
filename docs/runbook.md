# CodeGuard AI — Operations Runbook

## Service Health

### Check All Services

```bash
# Check API health
curl -f http://localhost:8000/health

# Check API readiness
curl -f http://localhost:8000/ready

# Check process status
sudo systemctl status codeguard-api
sudo systemctl status codeguard-celery
```

### Individual Health Checks

```bash
# API health
curl -f http://localhost:8000/health

# Frontend health (production, via nginx)
curl -f https://localhost/health

# PostgreSQL
psql -h localhost -U codeguard_user -d codeguard -c "SELECT 1;"

# Redis
redis-cli -h localhost ping

# Workspace health (checks temp directory is writable)
curl -f http://localhost:8000/api/v1/scanner/workspace-health
```

## Restarting Services

### Restart Single Service

```bash
# API
sudo systemctl restart codeguard-api

# Celery worker
sudo systemctl restart codeguard-celery

# Celery beat (scheduler)
sudo systemctl restart codeguard-celery-beat

# Frontend (nginx)
sudo systemctl reload nginx
```

### Restart All Services

```bash
sudo systemctl restart codeguard-api codeguard-celery codeguard-celery-beat nginx
```

## Viewing Logs

```bash
# API logs
sudo journalctl -u codeguard-api -f

# Celery worker logs
sudo journalctl -u codeguard-celery -f

# Celery beat logs
sudo journalctl -u codeguard-celery-beat -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Last 100 lines
sudo journalctl -u codeguard-api -n 100
```

## Database Operations

### Connect to PostgreSQL

```bash
psql -h localhost -U codeguard_user -d codeguard
```

### Backup

```bash
bash deploy/db-backup.sh
```

### Restore

```bash
bash deploy/db-restore.sh backups/codeguard_codeguard_20260528_020000.sql.gz
```

### Run Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### Check Migration Status

```bash
cd backend
source venv/bin/activate
alembic current
```

## Scaling Workers

### Increase Celery Concurrency

Edit the celery service configuration:

```bash
sudo systemctl edit codeguard-celery
```

Add or modify:

```ini
[Service]
ExecStart=/opt/codeguard/backend/venv/bin/celery -A app.tasks.celery_app worker --loglevel=info --concurrency=8
```

Then restart:

```bash
sudo systemctl restart codeguard-celery
```

## Monitoring

### Grafana Dashboard

Access at: http://localhost:3001 (or your configured Grafana URL)

Default credentials (from .env.production):
- Username: admin
- Password: (from GRAFANA_ADMIN_PASSWORD, if configured)

### Prometheus Metrics

Access at: http://localhost:9090

Key queries:
- Request rate: `rate(http_requests_total[5m])`
- p95 latency: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
- Active scans: `codeguard_active_scans`
- Workspace disk usage: `codeguard_workspace_disk_bytes`

## Common Incidents

### API Returns 502/503

1. Check if API process is running: `sudo systemctl status codeguard-api`
2. Check API logs: `sudo journalctl -u codeguard-api -n 50`
3. Check database connectivity: `psql -h localhost -U codeguard_user -d codeguard -c "SELECT 1;"`
4. Restart API: `sudo systemctl restart codeguard-api`

### High Memory Usage

1. Check resource usage: `top -o %MEM | head -20`
2. Identify the process with high usage
3. Check for memory leaks in logs
4. Restart the affected service
5. If persistent, increase system resources or reduce MAX_CONCURRENT_SCANS

### Celery Queue Backlog

1. Check Celery logs: `sudo journalctl -u codeguard-celery -n 100`
2. Check active tasks in Redis: `redis-cli LLEN celery`
3. Increase worker concurrency (see Scaling Workers above)
4. Check for stuck scan processes

### Database Connection Pool Exhaustion

1. Check active connections: `psql -h localhost -U codeguard_user -d codeguard -c "SELECT count(*) FROM pg_stat_activity;"`
2. Check max connections: `psql -h localhost -U codeguard_user -d codeguard -c "SHOW max_connections;"`
3. Restart API to reset connection pool: `sudo systemctl restart codeguard-api`

### TLS Certificate Expiry

1. Check cert expiry: `openssl x509 -in certs/fullchain.pem -noout -dates`
2. Renew (Let's Encrypt): `bash deploy/cert-manager.sh renew`
3. Self-signed (dev): `bash backend/scripts/setup-tls.sh self-signed`

### Stale Workspace Cleanup

If temporary workspaces accumulate:

```bash
# Check workspace disk usage
du -sh /tmp/codeguard_uploads/

# Clean stale workspaces (older than 1 hour)
make clean-workspaces
```

## Rollback a Deployment

```bash
bash deploy/deploy.sh --rollback
```

Or manually:

```bash
# Find the previous tag
git tag --sort=-version:refname | head -5

# Checkout and deploy
git checkout <previous-tag>
bash deploy/deploy.sh
```