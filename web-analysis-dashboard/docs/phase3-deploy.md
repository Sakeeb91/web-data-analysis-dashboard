# Phase 3 Deployment Runbook

This runbook describes how to deploy the app behind HTTPS with Caddy, and how to enable Redis-backed rate limiting and caching.

## Prerequisites
- A domain name you control, pointing to your server’s public IP (A/AAAA record)
- Docker and Docker Compose installed on the server
- Ports 80 and 443 open

## Environment
Create `web-analysis-dashboard/.env.production` with at least:

```
# Flask
FLASK_ENV=production
SECRET_KEY=change-me

# Database
DATABASE_URL=postgresql://admin:admin123@postgres:5432/web_analysis

# Redis
REDIS_URL=redis://redis:6379/0
RATELIMIT_STORAGE_URL=redis://redis:6379/1
CACHE_REDIS_URL=redis://redis:6379/2
CACHE_DEFAULT_TIMEOUT=60
CACHE_AGGREGATED_TTL=120

# Rate limit
RATE_LIMIT=200/hour

# Caddy
CADDY_DOMAIN=your.domain.com
CADDY_EMAIL=you@example.com

# Optional Monitoring
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.1
```

## Bring Up (Production Compose)
From the `web-analysis-dashboard` folder:

```
docker compose -f docker-compose.prod.yml up -d --build
```

- Caddy will request/renew certs automatically for `CADDY_DOMAIN` via Let’s Encrypt.
- App is served at `https://your.domain.com` (reverse proxy to `app:5000`).

## Health Check
```
curl -I https://your.domain.com/api/health
```

## Create Admin / API Key
```
# Create admin user
docker compose -f docker-compose.prod.yml exec app flask create_admin

# Create API key
docker compose -f docker-compose.prod.yml exec app flask create_api_key
```

## Optional: Publish & Pull Image from GHCR
A GitHub Actions workflow builds and pushes an image to GHCR on pushes to `main`.

- Image: `ghcr.io/<owner>/<repo>:latest`
- To deploy from GHCR instead of building locally, change `docker-compose.prod.yml` `app` service:

```
app:
  image: ghcr.io/<owner>/<repo>:latest
  env_file:
    - .env.production
  depends_on: [postgres, redis]
  expose: ["5000"]
```

Then:
```
docker compose -f docker-compose.prod.yml pull app && \
  docker compose -f docker-compose.prod.yml up -d app
```

## Notes
- Redis-backed rate limiter and caching are enabled via `RATELIMIT_STORAGE_URL` and `CACHE_REDIS_URL`.
- Caddyfile is at `web-analysis-dashboard/Caddyfile`; it sets HSTS and proxies to the app.
- Update DNS before bringing Caddy up so it can obtain a certificate.

