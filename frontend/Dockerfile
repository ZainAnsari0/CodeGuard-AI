# ═══════════════════════════════════════════════════════════════════
# CodeGuard AI — Multi-Stage Production Frontend Dockerfile
# ═══════════════════════════════════════════════════════════════════
# Build stages:
#   1. builder  — npm install + vite build (generates static assets)
#   2. runtime  — nginx with built assets, minimal footprint
# ═══════════════════════════════════════════════════════════════════

# ── Stage 1: Build React application ─────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies first for Docker layer caching
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY . .

# Build-time environment variables (use .env.production at build time)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Stage 2: Nginx runtime ───────────────────────────────────────
FROM nginx:alpine AS runtime

ARG NGINX_ENV=prod

# Remove default nginx configs
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy nginx configs
COPY nginx.conf /etc/nginx/conf.d/default.conf.dev
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf.prod

# Select config based on environment
RUN if [ "$NGINX_ENV" = "prod" ]; then \
      cp /etc/nginx/conf.d/default.conf.prod /etc/nginx/conf.d/default.conf; \
    else \
      cp /etc/nginx/conf.d/default.conf.dev /etc/nginx/conf.d/default.conf; \
    fi && \
    rm -f /etc/nginx/conf.d/default.conf.dev /etc/nginx/conf.d/default.conf.prod

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Add health check endpoint for nginx
RUN echo '{"status":"healthy"}' > /usr/share/nginx/html/health.json && \
    printf 'server {\n  listen 8080;\n  location /health { \n    alias /usr/share/nginx/html/health.json;\n    default_type application/json;\n  }\n}\n' > /etc/nginx/conf.d/health.conf

# Create log directory
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]