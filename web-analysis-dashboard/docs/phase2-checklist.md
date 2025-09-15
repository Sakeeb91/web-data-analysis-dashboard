# Phase 2 – Essential (Week 3–4)

This checklist scopes the Essential hardening for Phase 2 per the Demo → Production roadmap.

## Scope
- API security
- Background jobs with Celery
- Docker setup
- Basic monitoring

## Checklist

### API Security
- [ ] Rate limiting per user/IP (e.g., Flask-Limiter or gateway)
- [ ] API key management for programmatic access (key issuance + revocation)
- [ ] Input validation and sanitization on all endpoints
- [ ] Strict CORS configuration for production domains
- [ ] RBAC/authorization checks on sensitive routes
- [ ] CSRF protection for forms/session flows
- [ ] Security headers (HSTS, X-Content-Type-Options, etc.)

### Background Jobs (Celery)
- [ ] Celery app wired with Redis broker and result backend
- [ ] Async scraping and sentiment analysis tasks
- [ ] Scheduled jobs (e.g., APScheduler/Celery Beat) for periodic scraping
- [ ] Task retries, timeouts, and visibility timeouts configured
- [ ] Basic task monitoring (flower or logs/metrics)

### Docker Setup
- [ ] Dockerfile with multi-stage build and non-root user
- [ ] docker-compose extended to include app, worker, beat, redis, postgres
- [ ] Environment variable management with .env files
- [ ] Healthchecks for app/worker containers
- [ ] Production-ready Gunicorn entrypoint for Flask

### Basic Monitoring
- [ ] Error tracking (Sentry or similar) integrated
- [ ] Performance metrics (basic request latency, task durations)
- [ ] Uptime checks and /api/health enhanced with dependency checks
- [ ] Structured logging to stdout (JSON optional)

## Acceptance Criteria
- [ ] Hitting API too fast is throttled and logged
- [ ] A long-running scrape runs via Celery, persists results, and surfaces in UI
- [ ] docker-compose up brings up app+worker+redis+db, app serves via Gunicorn
- [ ] Intentional exception shows in error tracker with trace and user context

## References
- docs/demo-to-production-checklist.md: Phase 2
- docs/phase1-change-log.md

