# API Overview & Catalog

The SkillSwap Arena backend exposes RESTful endpoints and WebSocket streams documented interactively via OpenAPI (Swagger UI) at `/docs` and ReDoc at `/redoc`.

---

## 1. API Route Groups

| Domain | Base Path | Key Endpoints | Auth Level | Role Required |
| :--- | :--- | :--- | :--- | :--- |
| **Authentication** | `/auth` | `POST /register`, `POST /login`, `GET /me`, `/oauth/*` | Public / Bearer | `Any` / `None` |
| **Profiles & Capabilities** | `/profiles` | `GET /me`, `PUT /me`, `GET /me/capabilities`, `GET /{id}` | Bearer JWT | `USER` or `ADMIN` |
| **Skills & Verification** | `/skills`, `/verification` | `GET /skills`, `POST /verification/claim`, `POST /verification/test` | Bearer JWT | `USER` or `ADMIN` |
| **Peer Sessions** | `/sessions` | `POST /`, `GET /me`, `GET /upcoming`, `POST /{id}/cancel` | Bearer JWT | `USER` or `ADMIN` |
| **Live Workspace** | `/learning-sessions` | `GET /{id}/workspace`, `POST /{id}/notes`, `POST /{id}/topics` | Bearer JWT | Participant |
| **Learning Journeys** | `/journeys` | `POST /`, `GET /me`, `PUT /{id}/milestones` | Bearer JWT | `USER` or `ADMIN` |
| **AI Mentor (RAG)** | `/ai`, `/documents` | `POST /query`, `POST /documents/upload`, `GET /documents` | Bearer JWT | `USER` or `ADMIN` |
| **Session Intelligence** | `/session-intelligence` | `POST /{session_id}/synthesize`, `GET /{session_id}` | Bearer JWT | Participant |
| **Platform Administration** | `/admin` | `GET /dashboard`, `GET /users`, `POST /users/{id}/suspend`, `/audit-logs` | Bearer JWT | `ADMIN` Only |
| **System Diagnostics** | `/health`, `/metrics` | `GET /health`, `GET /health/redis`, `GET /metrics` | Public / Scraper | `None` |
| **Real-time WebSockets** | `/ws` | `WSS /ws/{user_id}` | JWT Handshake | `USER` or `ADMIN` |

---

## 2. Interactive Swagger UI
When running the backend server locally, explore the live OpenAPI interactive documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
