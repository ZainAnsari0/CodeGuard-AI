# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Multi-Stage Production Backend Dockerfile
# ═══════════════════════════════════════════════════════════════════
# Build stages:
#   1. builder  — Install Python deps with wheels
#   2. runtime  — Minimal image with only what's needed
# ═══════════════════════════════════════════════════════════════════

# ── Stage 1: Build dependencies ──────────────────────────────────
FROM python:3.11-slim AS builder

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements and build wheels for faster rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Install only runtime system dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libmagic1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1000 appgroup \
    && useradd -m -u 1000 -g appgroup appuser

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code
COPY . .

# Ensure proper ownership
RUN chown -R appuser:appgroup /app

# Create upload directory with proper permissions
RUN mkdir -p /tmp/codeguard_uploads && chown appuser:appgroup /tmp/codeguard_uploads

# Security: Run as non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Expose application port
EXPOSE 8000

# Production uvicorn command with optimized settings
# --workers: Auto-scale based on CPU (override with UVICORN_WORKERS env var)
# --loop uvloop: High-performance event loop
# --http httptools: Fast HTTP parser
CMD uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers ${UVICORN_WORKERS:-4} \
    --loop uvloop \
    --http httptools \
    --timeout-keep-alive 5 \
    --access-log \
    --log-level info