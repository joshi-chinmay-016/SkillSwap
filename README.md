<div align="center">

# ⚡ SkillSwap Arena

### **Enterprise Peer-to-Peer Skill Exchange, AI Mentorship & Production Platform**

*Transforming peer education through real-time skill matching, structured peer learning sessions, reputation-backed feedback, an integrated AI Mentor RAG knowledge engine, authoritative RBAC platform management, and GCP production architecture.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Google Cloud](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![Prometheus](https://img.shields.io/badge/Prometheus-Metrics-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

<br />

[Architecture](#-system-architecture) • [RBAC & Capabilities](#-rbac--capability-model) • [Admin Console](#-platform-administration-console) • [Observability](#-observability--metrics) • [Quick Start](#-quick-start) • [GCP Deployment](#-gcp-production-migration) • [CI/CD Pipeline](#-cicd-pipeline)

</div>

---

## 📌 Executive Summary

**SkillSwap Arena** is an enterprise-grade SaaS platform engineered for collaborative peer-to-peer education and AI-augmented mentorship. Built with a decoupled **Router → Service → Repository** backend pattern and a responsive React 18 SPA frontend, SkillSwap Arena enables students to exchange real-world skills through scheduled peer sessions while leveraging an integrated **AI Mentor** RAG knowledge engine and a comprehensive **Platform Administration & Observability Suite**.

---

## 🏛️ System Architecture

```mermaid
graph TD
    Client["React 18 Frontend / SPA"] -->|HTTPS / REST API| Nginx["Nginx Reverse Proxy & Load Balancer"]
    Client -->|WSS / WebSockets| Nginx
    
    subgraph Infrastructure ["Production Platform Layer"]
        Nginx -->|Proxy HTTP & /metrics| Backend["FastAPI Backend (Non-root, Multi-stage)"]
        Nginx -->|Proxy /ws/ (Upgrade)| Backend
        Prometheus["Prometheus Server"] -->|Scrape /metrics| Backend
        Grafana["Grafana Dashboards"] -->|Query| Prometheus
    end

    subgraph Storage ["Persistent & Coordination Services"]
        Backend --> DB[("PostgreSQL 16 (Alembic Managed)")]
        Backend --> Redis[("Redis 7 (Pub/Sub & Distributed State)")]
        Backend --> Secrets[("GCP Secret Manager")]
    end
```

---

## 🛡️ RBAC & Capability Model

SkillSwap Arena maintains a strict separation between **Platform Authorization** and **Contextual Teaching/Learning Capabilities**:

### 1. Platform Authorization (RBAC)
* `USER`: Standard platform member. Can book sessions, participate in peer learning, take skill verification tests, manage their wallet, and interact with the AI Mentor.
* `ADMIN`: Platform operator. Grants access to the dedicated `/admin/*` console, user suspensions, role updates, test verification reviews, administrative session cancellations with automated refunds, and system health diagnostics.

### 2. Contextual Capabilities (Per-User / Per-Session)
* **Mentor and Learner are NOT rigid RBAC roles.**
* Any user account has contextual capabilities:
  - `Can Learn`: Any skill the user desires to acquire.
  - `Can Teach`: Skills where the user has successfully taken a verification assessment (`status = "VERIFIED"`).
* In **Session A**, User X acts as the **Mentor** and User Y is the **Learner**.
* In **Session B**, User X acts as the **Learner** and User Z is the **Mentor**.
* The platform dynamically enforces capabilities per session context.

---

## 🖥️ Platform Administration Console

The dedicated `/admin` frontend platform provides 10 real-time operational views:

1. **Platform Dashboard (`/admin`)**: Real-time KPI matrix, Three.js ambient background visualizer, live service health pulse, and recent audit logs.
2. **User Management (`/admin/users`)**: Search, role filtering, suspension/reactivation with mandatory audit justification, and contextual capability inspection.
3. **Platform Skills (`/admin/skills`)**: Skill catalog oversight, verified mentor statistics, learner demand counts, and skill creation/editing.
4. **Mentor Verifications (`/admin/verification`)**: Candidate test review queue, score inspector, approval with optional grade override, and rejection reasons.
5. **Session Oversight (`/admin/sessions`)**: Live session monitoring, filtering by lifecycle status, and administrative cancellation with automated coin refunding.
6. **Moderation & Reports (`/admin/reports`)**: User report triage, resolution workflows, and dismissals.
7. **Wallet & Economy (`/admin/wallet`)**: Circulating coin supply, transaction stream, and audited balance adjustments.
8. **Analytics & Growth (`/admin/analytics`)**: Live Recharts visualizations derived from database aggregations (top skills, session distribution, completion rates).
9. **System Diagnostics (`/admin/system`)**: Live PostgreSQL query ping latency, Redis ping latency, uptime counter, and release environment details.
10. **Append-Only Audit Trail (`/admin/audit-logs`)**: Tamper-resistant log stream recording every administrative action, operator identity, target ID, explanation, IP address, and JSON metadata.

---

## 📊 Observability & Metrics

SkillSwap Arena is instrumented for Prometheus scraping and structured distributed tracing:

* **Prometheus Endpoint**: `GET /metrics` returns standard Prometheus text format with low-cardinality labels:
  - `http_requests_total` (method, handler, status_code)
  - `http_request_duration_seconds` (histogram with p50, p90, p95, p99 latency buckets)
  - `websocket_connections_active` (gauge of live active WebSocket connections)
  - `sessions_total` (counter of lifecycle transitions)
  - `auth_attempts_total` (counter of login attempts)
  - `booking_operations_total` (counter of booking operations)
* **Request Tracing**: `X-Request-ID` is assigned (or preserved) for every HTTP request and logged in structured format (`request_id="...", duration_ms=...`).
* **Health Endpoints**:
  - `GET /health`: Core application and dependency status summary.
  - `GET /health/redis`: Real-time Redis latency and coordination check.
* **Grafana Dashboards**: Pre-provisioned dashboards in `docker/production/grafana/provisioning/` for instant operational visibility.

---

## 🚀 Quick Start (Local Production Docker)

Launch the complete local production topology (FastAPI, React SPA, PostgreSQL 16, Redis 7, Prometheus, Grafana) with a single command:

```bash
# 1. Clone the repository
git clone https://github.com/joshi-chinmay-016/SkillSwap.git
cd SkillSwap

# 2. Configure environment variables (or use defaults)
cp .env.example .env

# 3. Launch Docker Compose stack
docker compose up --build -d
```

### Access Platform Services
* **Web Application**: `http://localhost:5173`
* **Admin Console**: `http://localhost:5173/admin`
* **Backend API Documentation**: `http://localhost:8000/docs`
* **Prometheus Metrics**: `http://localhost:8000/metrics`
* **Prometheus UI**: `http://localhost:9090`
* **Grafana Dashboards**: `http://localhost:3001` (user: `admin`, password: `admin`)

---

## ☁️ GCP Production Migration

SkillSwap Arena is architected for zero-serverless-friction deployment to **Google Cloud Platform (GCP)**:

### 1. Automated Deployment Script
```bash
# Make script executable and deploy to your GCP project
chmod +x deploy/gcp/deploy.sh deploy/gcp/setup-secrets.sh

# 1. Initialize Secret Manager
./deploy/gcp/setup-secrets.sh YOUR_GCP_PROJECT_ID

# 2. Build, migrate, and deploy to Cloud Run
./deploy/gcp/deploy.sh YOUR_GCP_PROJECT_ID us-central1
```

### 2. Infrastructure as Code (Terraform)
```bash
cd deploy/gcp/terraform
terraform init
terraform plan -var="project_id=YOUR_GCP_PROJECT_ID"
terraform apply -var="project_id=YOUR_GCP_PROJECT_ID"
```

### GCP Architecture Components
* **Cloud Run**: Serverless container execution for FastAPI Backend (1 vCPU, 1Gi, auto-scales 1–10 instances) and React Frontend Nginx (0.5 vCPU, 256Mi).
* **Cloud SQL (PostgreSQL 16)**: Managed private database with automated backups.
* **Memorystore (Redis 7)**: Low-latency caching, rate limiting, and multi-instance WebSocket coordination.
* **Serverless VPC Access Connector**: Secure private network bridge between Cloud Run, Cloud SQL, and Redis.
* **Secret Manager**: Secure runtime injection for JWT keys, database credentials, and OAuth tokens.

---

## 🔄 CI/CD Pipeline

Automated GitHub Actions workflow (`.github/workflows/ci-cd.yml`) executes on every push and pull request:

1. **Backend Validation**: Python 3.12 environment, dependency installation, bytecode validation, Alembic migrations against live PostgreSQL service container, and full Pytest execution.
2. **Frontend Validation**: Node.js 20 environment, dependency installation, and Vite production bundle compilation.
3. **Security & Secret Scans**: Automated credential leak detection and package security audits.
4. **Docker Image Builds**: Multi-stage build reproducibility checks for both backend and frontend images with GitHub Actions caching.

---

## 🧪 Testing & Verification

Run the comprehensive test suite locally:

```bash
cd backend
# Run all Phase 1–8 platform integration tests
pytest tests/test_phase8_*.py tests/test_phase7_*.py tests/test_phase6_*.py tests/test_phase5_*.py tests/test_phase4_*.py tests/test_phase3_*.py tests/test_phase2_*.py -v
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
