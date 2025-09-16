# Phase 2 Change Log – Essential

Date: 2025-09-15

This log captures the concrete changes to deliver Phase 2 essentials: API security, background jobs, Docker, and monitoring.

## Security & API
- Rate limiting via Flask-Limiter (default `RATE_LIMIT`, per-endpoint overrides).
- Security headers via Talisman (CSP configured; HTTPS enforcement off for local dev).
- CSRF protection enabled for forms; CSRF token added to login and register templates.
- API keys:
  - New model `APIKey` (stored as bcrypt hashes; not plaintext).
  - App CLI command `flask create_api_key` prints a one-time token and stores its hash.
  - Endpoints allow either logged-in session or `X-API-Key`/`api_key` with constant-time bcrypt comparison.
- Input validation: Marshmallow schema for scrape/task enqueue payloads.

## Background Jobs
- Celery worker/beat scaffolded; task `scrape_and_analyze` added.
- Task endpoints: `/api/tasks/scrape` (enqueue) and `/api/tasks/<id>/status` (poll).
- Optional hourly schedule via `SCHEDULE_SCRAPE_URL` env.
- Flower UI added at port 5555 in `docker-compose`.

## Monitoring & Health
- Optional Sentry bootstrap (`SENTRY_DSN`).
- Enhanced `/api/health`: checks DB, Redis, and Celery worker reachability.

## Migrations
- Flask-Migrate is configured. Run migrations after pulling these changes:
  ```bash
  export FLASK_APP=app_production.py
  flask db migrate -m "add api_keys table"
  flask db upgrade
  ```
  Note: `db.create_all()` remains as a safety net to create missing tables locally.

## Files Affected
- `app_production.py`: limiter, Talisman, CSRF, API key auth, input validation, task endpoints, enhanced health, CLI command `create_api_key`.
- `database/models.py`: new `APIKey` model.
- `database/__init__.py`: export `APIKey`.
- `templates/login.html`, `templates/register.html`: CSRF tokens.
- `requirements_production.txt`: Flask-Limiter, flask-talisman, marshmallow, flower, sentry-sdk.
- `celery_app.py`: optional beat schedule from env.
- `docker-compose.yml`: Flower service.

