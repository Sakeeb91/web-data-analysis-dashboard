# Phase 1 Change Log - Demo to Production

Date: 2025-09-15

This log documents the concrete changes applied to complete and harden Phase 1 (Core) of the demo-to-production checklist.

## Summary
- Implemented bcrypt-based password hashing for authentication.
- Added robots.txt compliance to scraping pipeline.
- Enabled User-Agent rotation with a robust fallback pool.
- Introduced simple per-domain rate limiting for scraping.
- Strengthened production scraping route configuration to use the above safeguards.
- Upgraded start script to install full production dependencies, install Playwright browsers, and run DB migrations.

## Files Changed

- `web-analysis-dashboard/app_production.py`
  - Switched password hashing from Werkzeug to `bcrypt` for `User.set_password` and `User.check_password`.
  - Enabled scraper safeguards in the production `/api/scrape` path: `respect_robots`, `rotate_user_agent`, and `rate_limit_interval`.

- `web-analysis-dashboard/scraper/base_scraper.py`
  - Added robots.txt checks via `urllib.robotparser` and a small cache.
  - Added per-domain rate limiting for both requests and Playwright code paths.
  - Added User-Agent rotation using `fake-useragent` when available, with a safe fallback UA pool.
  - Wired UA rotation and rate limiting into both `requests` and `playwright` flows.

- `web-analysis-dashboard/start_production.sh`
  - Installs dependencies from `requirements_production.txt` (fallback to explicit list if absent).
  - Installs Playwright browsers (`python -m playwright install`) and OS deps where supported.
  - Uses Flask-Migrate: initializes migrations if needed, runs `flask db migrate`/`flask db upgrade`, then ensures tables with `db.create_all()` as a safety net.

## Rationale
- Authentication now matches the documented production posture (bcrypt with adjustable rounds via `BCRYPT_LOG_ROUNDS`).
- Scraping respects site policies and reduces detection/rate issues via robots compliance, UA rotation, and throttling.
- Start script guarantees “real” functionality by installing ML and Playwright dependencies and applying DB migrations.

## Follow-ups (Optional)
- Add a migration directory to version control after first `flask db migrate` creates it.
- Extend scraper with per-domain concurrency limits and structured retry/backoff policies.
- Add logs/metrics around robots denials and throttling events.

