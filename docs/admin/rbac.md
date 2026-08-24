# Role-Based Access Control (RBAC)

SkillSwap Arena maintains a strict two-tier role model at the platform level while keeping teaching and learning capabilities contextual.

---

## 1. Platform Roles

| Role | Target Audience | Permissions & Route Access |
| :--- | :--- | :--- |
| **`USER`** | Students & Mentors | Access to student portal (`/dashboard`, `/sessions`, `/mentor`, `/wallet`, `/profile`). Zero access to `/admin/*`. |
| **`ADMIN`** | Platform Operators | Full access to student portal AND authoritative access to `/admin/*` operations, audit logs, moderation, and diagnostics. |

---

## 2. Capability Separation: Mentors vs Learners

```
              ┌──────────────────────────────────────────────┐
              │           Platform User (role: USER)         │
              └──────────────────────┬───────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐
    │     Can Teach (Mentor)   │             │   Can Learn (Learner)   │
    │  • Verified Skills Only │             │  • Any Desired Skill    │
    │  • Receives 1 Coin / Hr │             │  • Pays 1 Coin / Hr     │
    │  • Configures Slots     │             │  • Advances Roadmap     │
    └─────────────────────────┘             └─────────────────────────┘
```

- Mentor and Learner are **NOT** database roles.
- The same account acts as a **Mentor** in skills where they have completed a verification test, and as a **Learner** in skills where they are pursuing a Learning Journey.
