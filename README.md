# ExpenseTracker Backend

Django 5 REST API — expense tracking with JWT auth, MySQL, CORS, rate limiting.

---

## 🐳 Docker Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### 1. Configure environment
```bash
# Copy the template and edit your secrets
cp .env.example .env
```

Key variables in `.env`:
| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | Strong random string (required in production!) |
| `DEBUG` | Set `False` for production (`True` for local development) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames (e.g. `api.yourdomain.com`) |
| `MYSQL_PASSWORD` | MySQL app user password |
| `MYSQL_ROOT_PASSWORD` | MySQL root password |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins for CSRF |

### 2. Start (Production mode — Nginx + Gunicorn + MySQL)
```bash
docker compose up -d --build
```
- API available at **http://localhost** (port 80 via Nginx)
- Django admin at **http://localhost/admin**
- Swagger docs at **http://localhost/api/docs/swagger/**
- Health check at **http://localhost/health**

### 3. Start (Development mode — hot reload, port 8000)
```bash
docker compose -f docker-compose.dev.yml up --build
```
- API available at **http://localhost:8000**
- Source code is mounted — changes reload automatically

---

## 🛠️ Makefile Commands

| Command | Description |
|---|---|
| `make build` | Build production Docker image |
| `make up` | Start all production services (detached) |
| `make down` | Stop all production services |
| `make dev` | Start development mode with hot-reload |
| `make dev-down` | Stop development services |
| `make logs` | Tail Django/Gunicorn logs |
| `make logs-db` | Tail MySQL logs |
| `make shell` | Open bash shell in the web container |
| `make migrate` | Run Django migrations inside container |
| `make createsuperuser` | Create Django admin superuser |
| `make ps` | Show running containers |
| `make clean` | Remove all containers, volumes, and images |

---

## 🏗️ Services Architecture

```
┌─────────────────────────────────────────────────┐
│  Host                                           │
│  :80 ──► Nginx ──► Django/Gunicorn :8000        │
│           │                  │                  │
│           ▼                  ▼                  │
│      /static/           MySQL :3306             │
│      /media/           (persistent volume)      │
└─────────────────────────────────────────────────┘
```

| Service | Image | Port |
|---|---|---|
| `db` | mysql:8.4 | 3307 (host) |
| `web` | custom (python:3.12) | 8000 (internal) |
| `nginx` | nginx:1.27-alpine | 80 (host) |

---

## 📁 Docker File Structure

```
├── Dockerfile                  # Multi-stage production image
├── docker-compose.yml          # Production: Nginx + Gunicorn + MySQL
├── docker-compose.dev.yml      # Development: runserver + MySQL
├── .env.docker                 # Environment variables template
├── .dockerignore               # Files excluded from build context
└── docker/
    ├── entrypoint.sh           # Waits for DB, runs migrate + collectstatic
    ├── nginx/
    │   └── nginx.conf          # Reverse proxy + static file serving
    └── mysql/
        └── init.sql            # DB creation + user grants
```

---

## 🔑 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login (returns JWT cookies) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout + blacklist token |
| GET | `/api/v1/auth/me` | Get current user profile |
| GET/POST | `/api/v1/expenses/` | List / create expenses |
| GET/POST | `/api/v1/budgets/` | List / create budgets |
| GET | `/health` | Health check |
| GET | `/api/docs/swagger/` | Swagger UI |