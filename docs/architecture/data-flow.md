# Data Flow Architecture

This document describes the critical data flow pathways across SkillSwap Arena: user registration, session booking with coin escrow, live workspace synchronization, and AI session intelligence generation.

---

## 1. Authentication & Registration Flow

```
[ User Browser ]
       │  1. POST /auth/register (email, password, name)
       ▼
[ FastAPI Auth Router ]
       │  2. Hash password with bcrypt (12 rounds)
       ▼
[ PostgreSQL Database ]
       │  3. INSERT users (role="USER", is_active=True)
       │  4. INSERT profiles (credibility_score=5.0)
       │  5. INSERT wallets (balance=5)
       │  6. INSERT wallet_transactions (amount=5, type="WELCOME_BONUS")
       ▼
[ FastAPI Auth Router ]
       │  7. Issue HS256 JWT Token (sub=user_id, role="USER", exp=24h)
       ▼
[ User Browser ] -> Stored in Zustand authStore & navigates to /dashboard
```

---

## 2. Session Booking & Escrow Flow

```
[ Learner Client ]
       │  1. POST /sessions (mentor_id, skill_id, scheduled_at, Idempotency-Key)
       ▼
[ Session Service ]
       │  2. Verify Learner wallet balance >= 1 coin
       │  3. Verify Mentor has 'Can Teach' capability for skill_id (status="VERIFIED")
       │  4. Verify Mentor availability slot
       ▼
[ Database Transaction ]
       │  5. Deduct 1 coin from Learner wallet
       │  6. Record WALLET_TRANSACTION (amount=-1, type="SESSION_PAYMENT")
       │  7. INSERT session (status="scheduled", meeting_link="https://meet.jit.si/...")
       ▼
[ Redis Pub/Sub ]
       │  8. PUBLISH channel:notifications (event="SESSION_BOOKED", target=mentor_id)
       ▼
[ Mentor Client ] -> Receives instant toast notification via WebSocket
```

---

## 3. Real-Time Workspace Synchronization Flow

```
[ Learner Workspace ]                       [ Mentor Workspace ]
         │                                            │
         │  1. Connects to /ws/{learner_id}           │  Connects to /ws/{mentor_id}
         ▼                                            ▼
┌───────────────────────────────────────────────────────────────┐
│              FastAPI WebSocket ConnectionManager              │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                        Redis 7 Pub/Sub                        │
│   Channel: session:{session_id} • Key: presence:{user_id} (60s TTL) │
└───────────────────────────────┬───────────────────────────────┘
                                │
  2. Learner posts a Note       │
     ─────────────────────────> │
                                │ 3. Broadcasts "NOTE_CREATED" event
                                │ ─────────────────────────> Updates Mentor View
```

---

## 4. Grounded AI Session Intelligence Flow

```
[ Session Workspace (Completed) ]
       │  1. Gathers collaborative notes, questions, struggles, topics, action items
       ▼
[ Session Intelligence Service ]
       │  2. XML Delimiter Sanitization & Prompt Isolation Fencing
       │  3. Content Sufficiency Check (> 2 items)
       ▼
[ Google Gemini LLM API ]
       │  4. Strict JSON Schema Extraction (Zero-Fabrication Mode)
       ▼
[ PostgreSQL Database ]
       │  5. INSERT session_intelligences (summary, takeaways, guidance, actions)
       │  6. UPDATE learning_journeys (increment milestone progress percentage)
       │  7. INSERT learning_activities (log heatmap contribution)
       ▼
[ User Dashboard ] -> Renders updated roadmap progress and synthesized intelligence
```
