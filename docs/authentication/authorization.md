# Authorization, RBAC & Capability Model

SkillSwap Arena separates **Platform Authorization** (RBAC) from **Contextual Capabilities** (Teaching & Learning).

---

## 1. Platform Authorization (RBAC)

Platform authorization controls administrative access to system-level operations and configuration:

```
                  ┌──────────────────────┐
                  │    Platform User     │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
    ┌───────────────┐                 ┌───────────────┐
    │  role: "USER" │                 │ role: "ADMIN" │
    └───────┬───────┘                 └───────┬───────┘
            │                                 │
     Standard Student                  Full Platform Access:
     • Book sessions                   • User suspension / reactivation
     • Take skill tests                • Role promotion / demotion
     • Manage wallet                   • Test verification review
     • Engage AI mentor                • Administrative session cancels
                                       • Coin balance adjustments
                                       • Moderation resolution
                                       • System health & diagnostics
                                       • Append-only audit logs
```

### FastAPI Authorization Guards (`app/dependencies/auth_guards.py`)
- `get_current_active_user`: Enforces `is_active == True`. If an account is suspended, immediately aborts with `HTTP 403 Forbidden`.
- `require_admin`: Enforces `user.role == "ADMIN"`. Rejects non-admin users attempting to call `/admin/*` with `HTTP 403 Forbidden`.

---

## 2. Contextual Capabilities: Teaching vs Learning

**"Mentor" and "Learner" are NOT static user roles.** Every user can participate in both modes depending on skill context:

```
[ User Account: Alice (role: "USER") ]
  ├── Verified Skill: Python / Distributed Systems  ──>  Can Teach (Mentor in Session 101)
  └── In-Progress Skill: Cloud Architecture        ──>  Can Learn (Learner in Session 102)
```

### Capability Rules
1. **Learning Capability**: Any user can learn any skill by initializing a Learning Journey or booking a session.
2. **Teaching Capability**: A user can only mentor peers in skills where they have completed a verification assessment (`user_skills.verification_status = 'VERIFIED'`).
3. **Session Context**:
   - In **Session A**, User X is the `mentor` and User Y is the `learner`.
   - In **Session B**, User X is the `learner` and User Z is the `mentor`.
   - The session service dynamically validates capabilities per session context.
