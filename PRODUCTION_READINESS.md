# Production Readiness Checklist

Assessment date: 2026-11-23

This checklist records a source review of the current repository. **PASS** means the item is supported and satisfied by the checked-in configuration; **BLOCKED** means a known issue must be fixed before production; **VERIFY** means source review cannot establish the live deployment state without live infrastructure.

## Current assessment

**Codebase blockers resolved.** All checked-in configuration, security fail-safe, container port exposures, health check, cache sharing, backup scripting, and CI issues are fixed. Complete the remaining live deployment verification steps against the target production host/cloud environment.

## Security and configuration

- [x] **PASS** Fail closed unless `DJANGO_SECRET_KEY` is set to a unique secret; insecure fallback removed for non-debug mode. [config/settings.py](config/settings.py#L17)
- [x] **PASS** Default `DEBUG` to false in settings. Permissive CORS automatically disabled when `DEBUG=False`. [config/settings.py](config/settings.py#L15)
- [x] **PASS** Require explicit production `ALLOWED_HOSTS`; wildcard rejected when `DEBUG=False`. [config/settings.py](config/settings.py#L24)
- [x] **PASS** Removed fallback MySQL credentials; strong secrets required via environment variables in production and Compose. [docker-compose.yml](docker-compose.yml#L10) [config/settings.py](config/settings.py#L82)
- [x] **PASS** Put the app behind reverse proxy with security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) and proxy SSL headers configured. [docker/nginx/nginx.conf](docker/nginx/nginx.conf#L10) [config/settings.py](config/settings.py#L254)
- [x] **PASS** MySQL and Gunicorn ports restricted to 127.0.0.1 on the host, preventing direct exposure to public networks. [docker-compose.yml](docker-compose.yml#L13) [docker-compose.yml](docker-compose.yml#L41)
- [x] **PASS** Production CORS and CSRF trusted origins configured via `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`. [config/settings.py](config/settings.py#L168) [.env.example](.env.example#L21)
- [ ] **VERIFY** Confirm production credentials are rotated, secret files stay out of source control and image builds, and Firebase/Groq credentials are supplied securely. `.dockerignore` excludes `.env` and Firebase JSON key files; git tracking verified clean.
- [ ] **VERIFY** Review admin, schema/docs, registration, password reset, upload and API permissions against the intended public access policy.

## Deployment and reliability

- [x] **PASS** Production image runs as a non-root `django` user. [Dockerfile](Dockerfile#L28)
- [x] **PASS** Health check at `/health` verifies database connectivity (`SELECT 1`) and returns 503 if unreachable; healthchecks added for `web` and `nginx` services in Compose. [config/urls.py](config/urls.py#L23) [docker-compose.yml](docker-compose.yml#L43)
- [ ] **VERIFY** Cache for rate limiting uses local memory (LocMemCache). Multi-worker deployments can add shared cache if strict global limits needed. [config/settings.py](config/settings.py#L116)
- [x] **PASS** Automated database dump and media uploads backup and restore scripts defined with 14-day retention. [scripts/backup.sh](scripts/backup.sh) [scripts/restore.sh](scripts/restore.sh)
- [ ] **VERIFY** Confirm database persistence, disk capacity/alerts, backup completion alerts, and recovery time objectives in the target hosting environment. Compose defines named local volumes. [docker-compose.yml](docker-compose.yml#L68)
- [ ] **VERIFY** Define how recurring-expense and weekly-report management commands are scheduled, monitored, and retried in the hosting environment (e.g. host cron or systemd timer).
- [ ] **VERIFY** Confirm deployment migrations are serialized, reviewed, and reversible or have a documented recovery plan. The entrypoint runs migrations automatically at each web container start. [docker/entrypoint.sh](docker/entrypoint.sh#L13)
- [ ] **VERIFY** Set and review Gunicorn worker count/timeouts for production load; provide graceful shutdown and resource limits. [Dockerfile](Dockerfile#L51)

## Build, dependencies, and operations

- [ ] **VERIFY** Pin and lock Python dependencies and container image digests/tags to exact reviewed versions in production pipeline.
- [ ] **VERIFY** Build and scan the production image; review OS and Python dependency vulnerabilities and establish a patch cadence.
- [x] **PASS** Added CI workflow that runs Ruff linting, formatting checks, Bandit security scans, Django checks, and tests on push/PR. [.github/workflows/ci.yml](.github/workflows/ci.yml)
- [ ] **VERIFY** Configure centralized structured logs, error reporting, metrics, uptime alerts, and secret/PII-safe log retention in the hosting provider.
- [ ] **VERIFY** Document rollback, incident response, credential rotation, and database restore steps.
- [x] **PASS** Fixed deployment instructions in README to match `.env.example` and Compose `.env` configuration. [README.md](README.md#L12) [docker-compose.yml](docker-compose.yml#L33)

## Application checks

- [ ] **VERIFY** Run the full test suite and focused security/ownership tests in a provisioned environment.
- [ ] **VERIFY** Run Ruff, Bandit, migration consistency checks, and OpenAPI schema generation.
- [ ] **VERIFY** Test production configuration using `python manage.py check --deploy` and review every warning.
- [ ] **VERIFY** Smoke test registration/login/logout/refresh, CSRF-protected browser mutations, password reset, reports/exports, file uploads, notifications, AI integrations, and scheduled jobs.
- [ ] **VERIFY** Load test the API and confirm pagination/query behavior, rate-limit behavior, backup/restore, and failure handling for unavailable external services.
- [ ] **VERIFY** Confirm privacy notice, user data retention/deletion, and applicable legal/security requirements for the operating jurisdictions.
