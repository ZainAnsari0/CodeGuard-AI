# ── Build Stage ─────────────────────────────────────────────
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

# ── Production Stage ───────────────────────────────────────
FROM nginx:alpine

ARG NGINX_ENV=dev

# Copy the appropriate nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf.dev
COPY nginx.prod.conf /etc/nginx/conf.d/default.conf.prod

# Select config based on environment
RUN if [ "$NGINX_ENV" = "prod" ]; then \
      cp /etc/nginx/conf.d/default.conf.prod /etc/nginx/conf.d/default.conf; \
    else \
      cp /etc/nginx/conf.d/default.conf.dev /etc/nginx/conf.d/default.conf; \
    fi && \
    rm -f /etc/nginx/conf.d/default.conf.dev /etc/nginx/conf.d/default.conf.prod

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --spider -q http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]