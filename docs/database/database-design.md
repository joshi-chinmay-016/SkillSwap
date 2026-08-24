# Database Design & Architecture

SkillSwap Arena uses **PostgreSQL 16** as its primary relational database. The schema is designed for high relational integrity, concurrency safety, auditability, and fast indexed lookups across 37 domain entities.

---

## 1. Database Architecture & Engine Configuration

- **RDBMS Engine**: PostgreSQL 16+
- **ORM / Driver**: SQLAlchemy 2.0 with `psycopg2-binary`
- **Migration Engine**: Alembic (head revision: `m10a1_phase8_rbac_and_admin`)
- **Connection Pooling**: Managed pool (`pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`)

---

## 2. Entity Normalization & Core Domains

The schema is partitioned into 8 cohesive functional domains:

```
1. Identity & Access      -> users, oauth_identities, profiles
2. Skills & Capabilities  -> skills, user_skills, assessments
3. Economy & Coins        -> wallets, wallet_transactions
4. Peer Sessions          -> sessions, feedbacks, session_requests, mentor_availabilities
5. Learning Progress      -> learning_journeys, learning_activities, achievements, badges
6. Session Intelligence   -> session_notes, session_topics, session_action_items, session_intelligences
7. AI Mentor & RAG        -> documents, parsed_documents, chunks, vector_index_entries, mentor_memories
8. Admin & Moderation     -> admin_audit_logs, reports
```

---

## 3. Critical Integrity Constraints & Business Rationale

| Table | Constraint Type | Column(s) | Business Rationale |
| :--- | :--- | :--- | :--- |
| `users` | `UNIQUE` | `email` | Guarantees single account per email address across the platform. |
| `profiles` | `UNIQUE` | `user_id` | Enforces strict 1:1 relationship between user credentials and profile metadata. |
| `wallets` | `UNIQUE` | `user_id` | Guarantees each user has exactly one coin ledger. |
| `wallet_transactions` | `UNIQUE` | `reference_id` | Idempotency key constraint preventing double-spending or duplicate refund execution. |
| `user_skills` | `UNIQUE` | `(user_id, skill_id, type)` | Prevents duplicate claims for the same skill in the same capability mode (`TEACH` vs `LEARN`). |
| `feedbacks` | `UNIQUE` | `(session_id, reviewer_id)` | Prevents ballot stuffing and duplicate reviews for a single completed session. |
| `session_intelligences` | `UNIQUE` | `session_id` | Enforces single synthesized AI intelligence record per peer learning session. |

---

## 4. Indexing Strategy

Indexes are applied deliberately to support frequent query patterns while avoiding write overhead:

- **B-Tree Indexes on Foreign Keys**: Every relational foreign key (`user_id`, `session_id`, `mentor_id`, `learner_id`, `skill_id`) is indexed to accelerate joins.
- **Lookup Indexes**:
  - `users.role` and `users.is_active` (filtered lookups in admin user directory).
  - `sessions.status` and `sessions.scheduled_at` (calendar queries and session state transitions).
  - `admin_audit_logs.action`, `target_type`, `created_at` (audit log filtering and compliance sorting).
  - `user_skills.verification_status` (mentor discovery queries filtering `status = 'VERIFIED'`).

---

## 5. Deletion & Cascade Rules

- **Strict Cascading (`CASCADE`)**:
  - Deleting a `User` cascades to `profiles`, `wallets`, `user_skills`, `notifications`, and `oauth_identities`.
  - Deleting a `Session` cascades to its `session_notes`, `session_topics`, and `session_action_items`.
  - Deleting a `Document` cascades to `parsed_documents` and `chunks`.
- **Restricted / Preservation Rules (`RESTRICT` / Soft Flags)**:
  - `wallet_transactions` are immutable financial audit records.
  - `admin_audit_logs` are strictly append-only and have no cascade deletion triggers.
  - `users.is_active = False` is used for account suspension rather than physical deletion to preserve audit history.
