# Backend Architecture

The SkillSwap Arena backend is built on **Python 3.12** and **FastAPI 0.115+**, utilizing an asynchronous event loop for concurrent WebSockets, synchronous database connections via SQLAlchemy ORM with managed pooling, and background worker queues.

---

## 1. Directory Structure

```
backend/
├── alembic/                      # Database migrations
│   └── versions/                 # 32 version migration scripts (m10a1 head)
├── app/
│   ├── ai/                       # AI synthesis, RAG retrieval & prompt builders
│   │   ├── providers/            # Google Gemini LLM & Embeddings client
│   │   ├── rag/                  # Document chunking, indexing, and vector search
│   │   └── prompts/              # Isolated, sanitized prompt templates
│   ├── api/                      # 32 FastAPI router modules
│   ├── core/                     # Configuration, security, logging, redis, websocket manager
│   ├── dependencies/             # FastAPI dependency injection (auth guards, DB session)
│   ├── infrastructure/           # Prometheus metrics engine & exporters
│   ├── middleware/               # Correlation ID & request metrics middleware
│   ├── models/                   # 37 SQLAlchemy database models
│   ├── repositories/             # Data access layer abstractions
│   ├── schemas/                  # Pydantic DTO validation schemas
│   ├── scripts/                  # CLI bootstrapping tools (seed_admin.py)
│   └── services/                 # Domain business logic & transaction managers
├── tests/                        # Pytest integration & unit test suite
├── alembic.ini                   # Alembic configuration
├── Dockerfile                    # Production multi-stage Docker build
└── requirements.txt              # Production Python package dependencies
```

---

## 2. Request Handling Pipeline

```
1. Client HTTP/WSS Request
   │
2. CorrelationAndMetricsMiddleware:
   - Injects/extracts X-Request-ID (UUID4)
   - Starts latency stopwatch
   │
3. CORSMiddleware:
   - Validates Origin against configured CORS_ORIGINS
   │
4. FastAPI Dependency Resolution:
   - get_db() -> Yields SQLAlchemy session from pool
   - get_current_user() -> Decodes JWT, rejects suspended accounts (is_active == False)
   - require_admin() -> Asserts user.role == "ADMIN"
   │
5. Router Handler:
   - Parses & validates body with Pydantic Schema
   - Calls Service method
   │
6. Domain Service:
   - Executes business logic & atomic DB commit
   - Triggers Redis Pub/Sub broadcast if real-time event
   - Records AdminAuditLog if administrative operation
   │
7. Response Formatting & Metric Logging:
   - Serializes response DTO
   - Sets X-Request-ID header
   - Records duration in Prometheus histogram
   - Emits structured JSON log line
```

---

## 3. Database Session & Concurrency Management

- **Engine Configuration**: Connection pooling configured with `pool_size=20`, `max_overflow=10`, and `pool_pre_ping=True` to detect stale connections automatically.
- **Transaction Safety**: All mutative operations (such as coin transfers, session lifecycle changes, and user suspensions) execute inside explicit database transaction blocks with deterministic rollback on exception.
- **Async & Threading**: CPU-bound vector indexing and PDF parsing tasks are dispatched to background threads (`FastAPI BackgroundTasks` or executor pools) to prevent blocking the asynchronous event loop.
