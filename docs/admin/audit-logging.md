# Append-Only Audit Logging

SkillSwap Arena maintains an immutable, tamper-resistant audit trail in `admin_audit_logs` to ensure complete governance and traceability of all administrative interventions.

---

## 1. Audit Log Schema (`admin_audit_logs`)

```sql
CREATE TABLE admin_audit_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER NOT NULL REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(100),
    reason TEXT NOT NULL,
    ip_address VARCHAR(50),
    metadata_payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

---

## 2. Audited Actions

| Action Code | Target Type | Trigger Description |
| :--- | :--- | :--- |
| **`SUSPEND_USER`** | `USER` | Disables user login and API access (`is_active = False`). |
| **`REACTIVATE_USER`** | `USER` | Restores suspended account access (`is_active = True`). |
| **`UPDATE_USER_ROLE`** | `USER` | Promotes user to `ADMIN` or demotes to `USER`. |
| **`CREATE_SKILL`** | `SKILL` | Adds a new skill category to the platform catalog. |
| **`UPDATE_SKILL`** | `SKILL` | Modifies name, category, or description of a skill. |
| **`APPROVE_VERIFICATION`** | `USER_SKILL` | Approves a mentor skill claim with optional score override. |
| **`REJECT_VERIFICATION`** | `USER_SKILL` | Rejects a mentor skill claim with feedback notes. |
| **`ADMIN_CANCEL_SESSION`** | `SESSION` | Administratively terminates a session and issues coin refund. |
| **`RESOLVE_REPORT`** | `REPORT` | Resolves or dismisses a user moderation complaint. |
| **`ADJUST_WALLET`** | `WALLET` | Credited or debited user coin balance manually. |

---

## 3. Immutability Principles
- Audit log records are strictly **append-only**.
- There are **no API endpoints** or service functions capable of updating or deleting existing audit entries.
- Every entry includes the initiating admin's operator identity, timestamp, explanation reason, and client IP address.
