# 📜 Architecture Decision Records (ADR)

This document records the key architectural and design decisions made for **SkillSwap Arena**.

---

## ADR-001: Decoupled Router → Service → Repository Pattern

* **Status**: Accepted
* **Context**: HTTP endpoint handlers were becoming bloated with database queries, authorization checks, and data transformation logic.
* **Decision**: Enforce a strict three-tier architecture:
  * **Router Layer**: Endpoint definition, input validation (Pydantic), and HTTP response serialization.
  * **Service Layer**: Business logic, workflow orchestration, and domain rules.
  * **Repository Layer**: Data persistence, SQLAlchemy ORM queries, and query optimizations.
* **Consequences**: Ensures 100% unit-testability of business logic using mock repositories or SQLite in-memory databases, without requiring live HTTP servers.

---

## ADR-002: FAISS CPU Index with Inner-Product (Cosine) Similarity

* **Status**: Accepted
* **Context**: Vector similarity search requires low-latency retrieval across thousands of document text chunks without incurring cloud vector database subscription overhead or network latencies.
* **Decision**: Adopt FAISS CPU (`faiss.IndexIDMap2(faiss.IndexFlatIP(3072))`) with normalized vectors for exact inner-product (cosine) similarity search.
* **Alternatives Considered**: Pinecone (high recurring cost & external network latency), Pgvector (requires specialized PostgreSQL extension setup).
* **Consequences**: Provides sub-10ms vector search locally; requires atomic file persistence (`.index` and mapping JSON) to guarantee index durability across process restarts.

---

## ADR-003: Gemini 3072-Dimensional Embeddings (`gemini-embedding-001`)

* **Status**: Accepted
* **Context**: Text chunks must be converted into high-density vector representations preserving semantic meaning across diverse subjects (programming, mathematics, language learning).
* **Decision**: Standardize on Google Gemini `gemini-embedding-001` producing 3072-dimensional normalized embeddings.
* **Consequences**: Embeddings capture deep semantic context; dimension validation must be strictly enforced before FAISS insertion and retrieval query execution.

---

## ADR-004: Asynchronous Non-Blocking Document Pipeline

* **Status**: Accepted
* **Context**: Extracting text from multi-page PDFs and computing thousands of vector embeddings per document causes HTTP request timeouts if processed synchronously.
* **Decision**: Execute file extraction, text chunking, and embedding generation inside background task workers after committing file upload metadata.
* **Consequences**: Upload response latency remains under 50ms; status polling APIs (`GET /documents/{id}/status`) allow clients to track asynchronous completion.

---

## ADR-005: Backend-Controlled Citation Attribution

* **Status**: Accepted
* **Context**: Large Language Models frequently fabricate citation numbers or hallucinate non-existent document source references when generating answers.
* **Decision**: Disallow reliance on LLM-generated citations. The backend RAG pipeline explicitly injects retrieved chunk metadata into the context prompt and independently constructs the response `sources` payload from validated retrieved chunks.
* **Consequences**: Guarantees 100% truthful, verifiable source attribution without hallucinated citations.

---

## ADR-006: Unified AI Mentor Architecture (`/mentor...`)

* **Status**: Accepted
* **Context**: Legacy standalone AI chat endpoints existed alongside the primary AI Mentor experience, creating duplicate codebases and fragmented UI.
* **Decision**: Consolidate all AI capability into `/mentor`, `/mentor/knowledge`, and `/mentor/memory`. Redirect legacy `/ai/chat` HTTP routes to `/mentor` for seamless backward compatibility.
* **Consequences**: Eliminates code duplication while maintaining backwards compatibility for old links.
