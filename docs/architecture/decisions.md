# Architecture Decision Records (ADRs)

This document records the foundational architectural decisions, rationale, and engineering trade-offs made in the design and evolution of SkillSwap Arena.

---

## ADR-001: Contextual Capability Model vs Rigid RBAC Roles

* **Date**: Phase 8 Foundation
* **Status**: Accepted
* **Context**: Traditional learning management systems (LMS) bind users into rigid roles (`LEARNER` vs `INSTRUCTOR`). In a collaborative peer exchange, a student skilled in Distributed Systems may want to teach that topic while simultaneously learning Graphic Design.
* **Decision**: Separate **Platform Authorization** (`USER` vs `ADMIN`) from **Domain Capabilities** (`Can Teach Verified Skills` vs `Can Learn`). In Session A, User X is the Mentor; in Session B, User X is the Learner.
* **Trade-offs**:
  - *Pros*: Maximum flexibility, eliminates multi-account friction, matches real-world skill reciprocity.
  - *Cons*: Requires capability checks dynamically per skill and per session rather than static role checks.

---

## ADR-002: Router → Service → Repository Architecture

* **Date**: Phase 1 Core Architecture
* **Status**: Accepted
* **Context**: Fast-growing FastAPI applications frequently suffer from bloated router functions mixing HTTP parsing, business logic, and raw database queries.
* **Decision**: Enforce a strict 4-layer decoupling: Router (presentation) → Service (domain logic & transactions) → Repository (ORM persistence) → Model (database schema).
* **Trade-offs**:
  - *Pros*: High testability, isolated unit tests, clear transaction boundaries, maintainable codebase.
  - *Cons*: Slight boilerplate overhead when creating simple CRUD operations.

---

## ADR-003: Redis Pub/Sub & Presence TTL for Real-Time Scaling

* **Date**: Phase 6 Infrastructure
* **Status**: Accepted
* **Context**: WebSocket connections maintained solely in Python process memory cannot broadcast events across multiple horizontally scaled backend worker nodes.
* **Decision**: Integrate Redis Pub/Sub channels for cross-worker event broadcasting (`channel:session:{id}`) and user presence tracking using expiring keys with 60-second TTL heartbeats.
* **Trade-offs**:
  - *Pros*: Horizontally scalable WebSocket architecture, instant failover, zero in-memory cross-node state.
  - *Cons*: Introduces Redis as a mandatory runtime dependency for live presence and multi-worker events.

---

## ADR-004: Grounded AI Session Intelligence & Anti-Fabrication Fencing

* **Date**: Phase 4 Intelligence
* **Status**: Accepted
* **Context**: LLMs tend to hallucinate or invent discussion topics if session notes are sparse. Additionally, untrusted user-submitted notes could attempt prompt injection attacks.
* **Decision**: Implement strict prompt isolation fences (XML delimiter escaping, explicit "data is not instructions" directives) and a sufficiency guard (> 2 distinct items required). If insufficient notes are captured, the system creates a factual fallback record rather than allowing LLM hallucination.
* **Trade-offs**:
  - *Pros*: Zero AI hallucinations, deterministic output schemas, high prompt injection resistance.
  - *Cons*: Sessions with very minimal note-taking produce a concise fallback summary rather than an expansive generated text.

---

## ADR-005: Cloud Run Serverless Architecture on Google Cloud Platform

* **Date**: Phase 8 Production Migration
* **Status**: Accepted
* **Context**: Production deployment requires high availability, automated scaling, zero server maintenance, and secure private connectivity to managed databases and caches.
* **Decision**: Target GCP Cloud Run with Serverless VPC Access Connectors bridging traffic privately to Cloud SQL (PostgreSQL 16) and Memorystore (Redis 7.0), with secrets managed by GCP Secret Manager.
* **Trade-offs**:
  - *Pros*: Zero container orchestration overhead, scales to zero on idle, native IAM integration, low infrastructure cost.
  - *Cons*: Cold starts on scale-up (mitigated by setting `min-instances: 1` on production services).
