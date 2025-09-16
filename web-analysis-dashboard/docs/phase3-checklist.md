# Phase 3 – Production (Week 5–6)

Scope: Cloud deployment, HTTPS, performance optimization, error tracking.

## Deployment
- [ ] Container image publishing to registry (GHCR)
- [ ] Production compose with TLS proxy (Caddy) and env files
- [ ] Health checks + readiness
- [ ] Deployment runbook and env examples

## HTTPS
- [ ] Caddy reverse proxy with automatic TLS (Let's Encrypt)
- [ ] HSTS, security headers (Talisman already active)
- [ ] Optional custom domain + email for ACME

## Performance
- [ ] Flask-Limiter backed by Redis storage
- [ ] Response caching (Flask-Caching + Redis) for aggregated endpoints
- [ ] Pagination + index audit (documented)

## Reliability/Observability
- [ ] Sentry DSN + traces sample rate
- [ ] Flower deployed for Celery (already available)
- [ ] Dashboard /health extended (already done)

## Acceptance
- [ ] Deployed behind HTTPS with valid certs
- [ ] Aggregated endpoints cached and rate limited via Redis
- [ ] Image published to GHCR on push to main
- [ ] Error reporting visible in Sentry

