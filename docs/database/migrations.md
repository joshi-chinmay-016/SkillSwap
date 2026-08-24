# Database Migrations (Alembic)

SkillSwap Arena uses **Alembic** for deterministic, version-controlled database schema migrations.

---

## 1. Migration History & Lineage

The current migration head is **`m10a1_phase8_rbac_and_admin`**.

```
56e76cde8818_create_core_tables
  └── ecd85fa68d90_create_sessions_table
        └── 84a1d9bcfcce_add_wallet_system
              └── ...
                    └── k10a1_phase4_session_intelligence
                          └── l10a1_phase5_session_realtime
                                └── l10a2_phase7_oauth_identities
                                      └── m10a1_phase8_rbac_and_admin (HEAD)
```

### Key Milestones in Schema Lineage
- `56e76cde8818`: Initial core tables (`users`, `profiles`, `skills`, `user_skills`).
- `ecd85fa68d90`: Peer learning sessions schema.
- `84a1d9bcfcce`: Wallet & transaction ledger.
- `f10a1_skill_verification`: Assessment rubrics and skill verification status tracking.
- `k10a1_phase4_session_intelligence`: Structured session intelligence and collaborative notes.
- `l10a2_phase7_oauth_identities`: Third-party Google & GitHub OAuth account linking.
- `m10a1_phase8_rbac_and_admin`: Authoritative RBAC (`users.role`, `users.is_active`), `admin_audit_logs`, and `reports`.

---

## 2. Running Migrations

### Local Environment
```bash
cd backend
# Apply all pending migrations to the database
alembic upgrade head

# Rollback the last migration
alembic downgrade -1

# View current database version
alembic current
```

### In Docker Compose / Production
Database migrations execute automatically as part of container initialization or via the dedicated Cloud Run migration job:

```bash
# In Docker Compose
docker compose run --rm backend alembic upgrade head

# On Google Cloud Platform
gcloud run jobs execute skillswap-db-migration --region=us-central1 --wait
```

---

## 3. Creating New Migrations

To generate a new schema migration:

```bash
cd backend
# Generate auto-migration from SQLAlchemy model changes
alembic revision --autogenerate -m "describe_schema_change"

# Always inspect the generated script in alembic/versions/ before committing!
```

---

## 4. Zero-Downtime Migration Guidelines

1. **Add Columns as Nullable First**: When introducing a new required column, add it as nullable, backfill data, and then apply `nullable=False` in a subsequent revision.
2. **Never Rename Columns In-Place**: Use an additive approach (add new column, sync writes, drop old column) to prevent breaking live backend instances during rolling updates.
3. **Index Creation**: Add large indexes concurrently in production to avoid table lock contention.
