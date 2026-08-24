# Production Docker Architecture

SkillSwap Arena uses multi-stage, non-root Docker builds and Docker Compose for reproducible local development and containerized production deployment.

---

## 1. Container Images Overview

### 1.1 Backend Container (`backend/Dockerfile`)
- **Base Image**: `python:3.12-slim`
- **Builder Stage**: Installs `gcc`, `libpq-dev`, and Python packages into user space (`/root/.local`).
- **Runner Stage**:
  - Copies compiled wheels to unprivileged user `/home/appuser/.local`.
  - Creates dedicated non-root user `appuser` (UID: `10001`, GID: `10001`).
  - Implements container healthcheck: `CMD curl -f http://localhost:8000/health || exit 1`.
  - Starts production server: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`.

### 1.2 Frontend Container (`frontend/Dockerfile`)
- **Base Image**: `node:20-alpine` (builder) → `nginx:alpine-slim` (runner).
- **Builder Stage**: Compiles React SPA using `npm run build`.
- **Runner Stage**: Copies static bundle into `/usr/share/nginx/html` with custom `nginx.conf` for SPA routing fallback (`try_files $uri $uri/ /index.html;`) and security headers.

---

## 2. Docker Compose Topology (`docker-compose.yml`)

The root `docker-compose.yml` provisions the complete local production topology:

```yaml
services:
  postgres:     # PostgreSQL 16 on port 5432 (named volume: postgres_data)
  redis:        # Redis 7.0 on port 6379 (named volume: redis_data)
  backend:      # FastAPI API Server on port 8000
  frontend:     # React Nginx SPA on port 5173
  prometheus:   # Prometheus Scraper on port 9090
  grafana:      # Grafana Dashboards on port 3001
```

### Running the Stack
```bash
# Launch all services in background
docker compose up --build -d

# View real-time logs
docker compose logs -f backend

# Stop stack and preserve volume data
docker compose down
```
