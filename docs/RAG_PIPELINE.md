# 🧠 AI Mentor & Grounded RAG Pipeline — SkillSwap Arena

The **RAG (Retrieval-Augmented Generation)** engine in SkillSwap Arena allows students to convert study materials (PDFs, Markdown notes, text files) into searchable vector knowledge and receive grounded, accurate guidance from the **AI Mentor**.

---

## 🔄 End-to-End Grounded RAG Query Execution Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as "Student / SPA Client"
    participant API as "RAG Router (POST /rag/query)"
    participant RAG as "RAGService"
    participant Ret as "RetrievalService"
    participant FAISS as "FAISS Vector Store"
    participant DB as "PostgreSQL Database"
    participant LLM as "Gemini API"

    User->>API: Submit Question ("Explain dependency injection in Python")
    API->>RAG: query(db, query, user_id, top_k)
    RAG->>Ret: retrieve(db, request, user_id)
    
    Note over Ret, LLM: 1. Query Vector Generation
    Ret->>LLM: generate_embedding(query) via GeminiEmbeddingProvider
    LLM-->>Ret: 3072-dimensional normalized vector
    
    Note over Ret, FAISS: 2. FAISS Candidate Overfetching
    Ret->>FAISS: search(query_vector, top_k * 4)
    FAISS-->>Ret: FAISS integer IDs + Cosine Similarity Scores
    
    Note over Ret, DB: 3. Single-Query Batch Metadata Resolution & Authorization
    Ret->>DB: JOIN Query (Embeddings -> Chunks -> ParsedDocs -> Docs) WHERE Embedding.id IN (resolved_ids)
    DB-->>Ret: Resolved Metadata + Document Ownership
    
    Note over Ret: 4. Ownership Isolation & Lifecycle Filtering
    Ret->>Ret: Exclude chunks where user_id != current_user.id or document status != READY
    Ret-->>RAG: Filtered & Ranked RetrievedChunk objects
    
    Note over RAG: 5. Context Analysis & Token-Budget Optimization
    RAG->>RAG: Deduplicate >85% overlapping chunks & cap at 2048 tokens
    RAG->>RAG: Construct System & Grounding Prompt
    
    Note over RAG, LLM: 6. Grounded Answer Generation
    RAG->>LLM: Generate Answer with Isolated System Instructions
    LLM-->>RAG: Generated Answer Text
    
    Note over RAG: 7. Groundedness & Source Citation Validation
    RAG->>RAG: Validate Citations against Backend Sources
    RAG-->>API: Grounded Answer + Backend Verified Sources
    API-->>User: 200 OK RAGQueryResponse Payload
```

---

## 🧩 Text Chunking & Overlap Halo Strategy

To prevent context truncation across sentence or paragraph boundaries, text is segmented using `RecursiveChunkStrategy` with a 150-character overlap halo.

```mermaid
graph LR
    subgraph Raw ["Raw Extracted Text Document"]
        P1["Paragraph 1: Core Definitions & Concepts"]
        P2["Paragraph 2: Implementation & Code Examples"]
        P3["Paragraph 3: Best Practices & Summary"]
    end

    P1 -->|Recursive Boundary Splitter| C1["Chunk 1: Tokens 0 - 800"]
    P2 -->|Recursive Boundary Splitter| C2["Chunk 2: Tokens 650 - 1450"]
    P3 -->|Recursive Boundary Splitter| C3["Chunk 3: Tokens 1300 - 2100"]

    subgraph Halo ["Overlap Halo Boundaries"]
        C1 -.->|150-char Halo| C2
        C2 -.->|150-char Halo| C3
    end
```

---

## 🔢 Embedding Generation & Non-Blocking Retry State Machine

Vector embeddings are generated using Gemini `gemini-embedding-001` (3072 dimensions) with automatic background retry handling for transient API rate limits.

```mermaid
stateDiagram-v2
    [*] --> PENDING: Chunk Created
    PENDING --> PROCESSING: Worker Picks Batch
    
    state PROCESSING {
        [*] --> EmbeddingCall: Call Gemini API
        EmbeddingCall --> Success: 200 OK Vector Received
        EmbeddingCall --> FailedTransient: 429 Rate Limit / Timeout
        EmbeddingCall --> FailedFatal: 400 Invalid Input
    }

    Success --> READY: Vector Persisted (Status=READY)
    FailedFatal --> FAILED: Permanently Failed (Failure Count++)
    
    FailedTransient --> AutoRetryPending: Background Daemon Scheduled (30s delay)
    AutoRetryPending --> PROCESSING: Single Retry Pass Executed
    
    READY --> [*]
    FAILED --> [*]
```

---

## 🗄️ FAISS Vector Storage & PostgreSQL ID Mapping Architecture

SkillSwap Arena couples PostgreSQL metadata storage with FAISS CPU vector index performance.

```mermaid
graph TD
    subgraph PG ["PostgreSQL Relational Store (Source of Truth)"]
        emb_id["PostgreSQL Embedding UUID: a1b2c3d4-e5f6-..."]
        chunk_rec["Chunk Text & Section Metadata"]
        doc_rec["Document Name & User Ownership"]
    end

    subgraph SHA ["SHA-256 ID Resolution Engine"]
        sha["SHA-256 Truncation Algorithm"]
        emb_id --> sha
        sha -->|Deterministic Mapping| faiss_id["FAISS Int64 ID: 89437205128394"]
    end

    subgraph Index ["FAISS CPU Vector Index"]
        index["faiss.IndexIDMap2(faiss.IndexFlatIP(3072))"]
        faiss_id -->|Maps to Vector Array| index
    end

    index -->|Search Returns Top Matches| match_id["Matched FAISS Int64 ID"]
    match_id -->|Reverse Map| emb_id
    emb_id -->|Batch JOIN Lookup| chunk_rec
    emb_id -->|Batch JOIN Lookup| doc_rec
```

---

## 🔬 RAG Pipeline Subsystems & Safety Invariants

### 1. Hard Ownership Security Boundary
All vector search results undergo PostgreSQL metadata verification before context assembly. Results where `document.user_id != current_user.id` or `document.status != READY` are strictly dropped. User A can never access User B's knowledge base.

### 2. Untrusted LLM Citations
Large Language Models cannot be trusted to generate accurate citation indices. The RAG pipeline strips LLM-generated bracketed citations and independently constructs the response `sources` list directly from verified retrieved chunk metadata.

### 3. Context Quality Analysis & Optimization Pass
- **Overlap Reduction**: Chunks sharing >85% Jaccard text overlap are pruned to maximize context diversity.
- **Token Capping**: Retrieved context is capped at 2048 tokens to avoid context diluting or prompt truncation.
