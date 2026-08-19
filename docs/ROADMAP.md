# 🗺️ Product Roadmap — SkillSwap Arena

This roadmap outlines the evolution of **SkillSwap Arena** from core peer-learning functionality to advanced AI mentorship capabilities.

---

## 📌 Status & Milestones

### Phase 1: Core Peer-Learning & Skill Matching (Completed)
- [x] User authentication & OAuth2 password flow with JWT security.
- [x] Bidirectional skill catalog (skills to teach / skills to learn).
- [x] Mentor discovery, search, and filtering.
- [x] Time-slot availability scheduling with collision prevention.
- [x] Session request lifecycle (propose, accept, reject, complete, cancel).
- [x] Peer ratings & feedback model reconciliation (`LearningSession` integration).

### Phase 2: AI Mentor & RAG Knowledge Engine (Completed)
- [x] Asynchronous document parsing pipeline (PDF, TXT, Markdown).
- [x] Intelligent text chunking with sentence boundary preservation and 150-char overlap halos.
- [x] Gemini 3072-dimensional vector embedding generation (`gemini-embedding-001`).
- [x] FAISS CPU vector storage index with inner-product cosine similarity.
- [x] Semantic retrieval with candidate overfetching and batch PostgreSQL metadata lookup.
- [x] RAG context quality analysis, token-budget optimization, and grounded answer validation.
- [x] Unified AI Mentor experience (`/mentor`, `/mentor/knowledge`, `/mentor/memory`).

### Phase 3: Real-Time Alerts & Gamification (Completed)
- [x] Authenticated WebSocket notification endpoint (`/ws/{user_id}`).
- [x] Real-time session request alerts and event delivery.
- [x] Reputation scoring algorithm and leaderboard rankings.
- [x] Learning journeys, activity feed, and streak tracking.

### Phase 4: Production Observability & Scale (In Progress / Next Steps)
- [ ] Multi-tenant AWS S3 / Azure Blob cloud storage provider backend.
- [ ] HNSW vector indexing for billion-scale chunk retrieval.
- [ ] Advanced multi-modal document parsing (OCR for handwritten notes & diagrams).
- [ ] Real-time voice mentorship session transcription and AI summary auto-generation.
