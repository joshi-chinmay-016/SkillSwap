# Redis Architecture & Distributed Coordination

SkillSwap Arena relies on **Redis 7.0+** for real-time Pub/Sub message distribution, participant presence tracking, and distributed rate limiting.

---

## 1. Key Namespaces & Structures

| Namespace / Key Pattern | Type | TTL | Purpose |
| :--- | :--- | :--- | :--- |
| `session:presence:{session_id}:{user_id}` | String | 60s | Active presence heartbeat in peer workspace. |
| `channel:session:{session_id}` | Pub/Sub Channel | N/A | Real-time collaborative note sync across backend nodes. |
| `channel:notifications` | Pub/Sub Channel | N/A | User notification event stream for instant UI toasts. |
| `ratelimit:{ip}:{endpoint}` | String (Counter) | 60s | Atomic token bucket rate limiting. |

---

## 2. Pub/Sub Multi-Worker Flow

```
[ Backend Worker Node A ]                         [ Backend Worker Node B ]
         │                                                 │
         │  1. Learner creates note in Session 42          │  Mentor is connected to Node B
         ▼                                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Redis 7 Pub/Sub                          │
│               Channel: channel:session:42                        │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 │  2. Delivers event to Node B
                                 ▼
                     Forwards to Mentor Browser
```
