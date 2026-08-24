# Component Architecture

SkillSwap Arena is structured around clear module boundaries, strict separation of concerns, and unidirectional data flow. This document details how each layer interacts and how cross-cutting infrastructure concerns are enforced across the codebase.

---

## 1. Architectural Pattern: Router → Service → Repository

The backend codebase adheres to a decoupled 4-tier layer pattern:

```
[ HTTP Request ]
       │
       ▼
┌──────────────┐
│ Router Layer │  --> Endpoint definition, request parsing, Pydantic DTO validation, HTTP status codes
└──────┬───────┘
       │
       ▼
┌───────────────┐
│ Service Layer │  --> Domain business logic, transaction boundaries, capability checks, events
└──────┬────────┘
       │
       ▼
┌──────────────────┐
│ Repository Layer │  --> SQLAlchemy ORM queries, database access abstractions, joins, and filters
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│ Model Layer │  --> Declarative database entities, foreign keys, table indexes, constraints
└─────────────┘
       │
       ▼
 [ PostgreSQL 16 ]
```

### Layer Responsibilities

1. **Router Layer (`backend/app/api/`)**:
   - Accepts incoming HTTP/WebSocket connections.
   - Injects dependencies (e.g. database session `get_db`, authenticated user `get_current_user`, admin guard `require_admin`).
   - Validates input and output schemas with Pydantic (`app/schemas/`).
   - Delegates domain orchestration to the Service layer; contains **zero** direct business or database transaction logic.

2. **Service Layer (`backend/app/services/`)**:
   - Enforces core domain rules (e.g. coin balances, escrow transfers, capability validation, session status transitions).
   - Manages atomic transactions: commits or rolls back database state.
   - Triggers cross-system side effects: Redis Pub/Sub events, AI synthesis jobs, and append-only audit log entries.

3. **Repository Layer (`backend/app/repositories/`)**:
   - Encapsulates raw data persistence queries.
   - Provides clean interfaces for filtering, pagination, locking, and bulk updates.
   - Insulates business logic from database schema specifics.

4. **Model Layer (`backend/app/models/`)**:
   - Defines declarative SQLAlchemy schema models with precise foreign keys, constraints, and indexes.

---

## 2. Cross-Cutting Infrastructure Concerns

```
                                  [ Incoming Request ]
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │ Correlation & Metrics Middleware      │ (Attaches X-Request-ID, observes latency)
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │ CORS & Security Headers Middleware    │ (Restricts origins, injects security headers)
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │ Auth & Active Account Guard           │ (Validates JWT, verifies is_active == True)
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                       ┌───────────────────────────────────────┐
                       │ Role Guard (require_admin)            │ (Restricts /admin/* to role == "ADMIN")
                       └───────────────────┬───────────────────┘
                                           │
                                           ▼
                                    [ Route Handler ]
```

### 1. Request Correlation & Tracing
Every request passes through `CorrelationAndMetricsMiddleware` (`app/middleware/correlation.py`). An `X-Request-ID` is assigned (or preserved) and propagated into all structured logs and the response header.

### 2. Operational Metrics
The middleware increments Prometheus counters (`http_requests_total`) and measures request execution time with low-cardinality route labels (`http_request_duration_seconds`).

### 3. Distributed Caching & Coordination
`RedisClient` (`app/core/redis_client.py`) and `ConnectionManager` (`app/core/websocket_manager.py`) provide multi-worker synchronization, user presence tracking (60-second TTL heartbeats), and atomic token-bucket rate limiting.

### 4. Append-Only Audit Logging
`audit_service.py` records immutable logs in `admin_audit_logs` for all sensitive operations (user suspension, role changes, session cancellations, coin adjustments, and test verifications).
