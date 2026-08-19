# 🏛️ System Architecture — SkillSwap Arena

SkillSwap Arena is an enterprise-grade peer-learning and mentorship platform built on a decoupled, multi-tiered architecture designed for security, sub-50ms API responsiveness, and horizontal scalability.

---

## 📐 High-Level System Architecture Overview

The system decouples presentation, domain orchestration, vector search, relational storage, and real-time communications.

```mermaid
graph TD
    Client["React 18 Frontend / SPA"] -->|HTTPS / REST API| Router["FastAPI Router Layer"]
    Client -->|WSS / WebSockets| WS["WebSocket Connection Manager"]
    
    subgraph Core ["Backend Core (FastAPI 0.115+)"]
        Router --> Auth["Auth & Security Middleware"]
        Auth --> Service["Business Service Layer"]
        Service --> Repo["Repository Pattern Layer"]
        
        Service --> StorageSvc["StorageService Facade"]
        Service --> ParseSvc["DocumentParsingService"]
        Service --> ChunkingSvc["ChunkingService & ChunkService"]
        Service --> EmbedSvc["EmbeddingService"]
        Service --> RetrievalSvc["RetrievalService"]
        Service --> RAGSvc["RAGService"]
    end
    
    subgraph Storage ["Storage & Vector Processing"]
        StorageSvc --> StorageProv["LocalStorageProvider / AWS S3"]
        ParseSvc --> ParserMgr["ParserManager & Factory"]
        ParserMgr --> PDFP["PDFParser PyMuPDF"]
        ParserMgr --> TXTP["TxtParser chardet"]
        ParserMgr --> MDP["MarkdownParser"]
        ChunkingSvc --> ChunkFactory["ChunkFactory & Strategies"]
        ChunkFactory --> RecursiveStrat["RecursiveChunkStrategy"]
        EmbedSvc --> EmbedProvider["EmbeddingProvider Interface"]
        EmbedProvider --> GeminiEmbed["GeminiEmbeddingProvider"]
        RetrievalSvc --> FAISS["FAISS CPU Vector Store"]
    end
    
    subgraph Database ["Database Layer"]
        Repo --> DB[("PostgreSQL 16 Database")]
        ParseSvc --> DB
        ChunkingSvc --> DB
        EmbedSvc --> DB
    end
```

---

## 🔄 Core Request Lifecycle (Router → Service → Repository)

Every REST HTTP request follows a strict unidirectional data flow ensuring 100% isolation between presentation schemas and data access ORM logic.

```mermaid
sequenceDiagram
    autonumber
    actor User as "Client / SPA"
    participant Router as "FastAPI Router Layer"
    participant Auth as "Auth & Security Middleware"
    participant Service as "Business Service Layer"
    participant Repo as "Repository Layer"
    participant DB as "PostgreSQL Database"

    User->>Router: HTTP Request (e.g. POST /sessions)
    Router->>Auth: Validate JWT Bearer Token
    Auth-->>Router: Authenticated User Principal
    Router->>Service: Call Business Service method (db, user_id, request_data)
    Service->>Service: Validate Business Rules & Authorize Scope
    Service->>Repo: Execute Query / Mutation (db, parameters)
    Repo->>DB: SQLAlchemy ORM / SQL Statement
    DB-->>Repo: Database Result Set
    Repo-->>Service: Return Model / Entity
    Service-->>Router: Return Service DTO / Domain Model
    Router-->>User: Serialize Pydantic V2 Response Schema (200 OK)
```

---

## ⚡ Real-Time WebSocket Communication Architecture

WebSocket connections are authenticated before handshake completion and tracked by an in-memory `ConnectionManager`.

```mermaid
sequenceDiagram
    autonumber
    actor Client as "User Client"
    participant WS as "/ws/{user_id}?token=JWT"
    participant Sec as "Security Engine (decode_access_token)"
    participant Mgr as "ConnectionManager"
    participant Evt as "Event Trigger (Session Request)"

    Client->>WS: Request WebSocket Connection with ?token=<JWT>
    WS->>Sec: Decode & Validate JWT Token
    alt Token Missing, Expired, or Invalid
        Sec-->>WS: Validation Failure
        WS-->>Client: Close Connection (Code 1008 Policy Violation)
    else Subject Mismatch
        Sec-->>WS: Subject Mismatch
        WS-->>Client: Close Connection (Code 1008 Policy Violation)
    else Auth and User ID Validated
        Sec-->>WS: Validated User Principal
        WS->>Mgr: connect(user_id, websocket)
        Mgr-->>Client: Connection Accepted (Code 1000 OK)
        
        Note over Evt, Client: Asynchronous Event Dispatching
        Evt->>Mgr: broadcast_event(target_user_id, event_payload)
        Mgr->>Client: Send JSON Event Notification
    end
```

---

## 📄 Document Ingestion, Parsing & Chunking Subsystem

Document processing is completely asynchronous to ensure file uploads never block main API loop threads.

```mermaid
graph TD
    Upload["User File Upload"] -->|POST /documents| Storage["StorageService Facade"]
    Storage -->|Write File & SHA-256 Checksum| Disk["Local Storage / Cloud Bucket"]
    Storage -->|Save Metadata Status=UPLOADED| DB[("PostgreSQL")]
    
    Storage -->|Trigger Background Task| Worker["Async Processing Worker"]
    
    subgraph Processing ["Background Processing Pipeline"]
        Worker -->|Read Document Stream| Parser["ParserManager Factory"]
        Parser -->|PDF| PyMuPDF["PDFParser fitz"]
        Parser -->|TXT| Chardet["TxtParser chardet"]
        Parser -->|MD| Markdown["MarkdownParser"]
        
        PyMuPDF -->|Extracted Text| ParsedDoc["ParsedDocument Record"]
        Chardet -->|Extracted Text| ParsedDoc
        Markdown -->|Extracted Text| ParsedDoc
        
        ParsedDoc -->|Chunk Strategy| Segmenter["RecursiveChunkStrategy"]
        Segmenter -->|Paragraph & Sentence Boundaries| Chunks["Text Chunks + 150-char Overlaps"]
    end
    
    Chunks -->|Persist Records| DB
    Worker -->|Transition Status=READY| DB
```

---

## 🗄️ Database Schema & Entity-Relationship Diagram (ERD)

The PostgreSQL relational database is version-controlled via Alembic migrations.

```mermaid
erDiagram
    USERS {
        int id PK
        string email UK
        string password_hash
        string name
        int reputation_score
        datetime created_at
    }

    PROFILES {
        int id PK
        int user_id FK
        string bio
        string department
        int year
        string avatar_url
    }

    SKILLS {
        int id PK
        string name UK
        string category
        string description
    }

    USER_SKILLS {
        int id PK
        int user_id FK
        int skill_id FK
        string type
    }

    LEARNING_JOURNEYS {
        int id PK
        int user_id FK
        string title
        string description
        string status
    }

    LEARNING_SESSIONS {
        int id PK
        string uuid UK
        int user_id FK
        int journey_id FK
        string title
        string status
        datetime started_at
        datetime ended_at
    }

    SESSION_SUMMARIES {
        int id PK
        string uuid UK
        int session_id FK UK
        text summary
        json key_takeaways
        json strengths
        json weaknesses
        json follow_up_topics
    }

    FEEDBACK {
        int id PK
        int session_id FK
        int reviewer_id FK
        int reviewee_id FK
        int rating
        string comment
    }

    DOCUMENTS {
        string id PK
        int user_id FK
        string original_filename
        string storage_path
        string checksum
        string status
    }

    PARSED_DOCUMENTS {
        string id PK
        string document_id FK UK
        text text_content
        string status
    }

    CHUNKS {
        string id PK
        string parsed_document_id FK
        int user_id FK
        int chunk_index
        text chunk_text
        string status
    }

    EMBEDDINGS {
        string id PK
        string chunk_id FK
        int user_id FK
        string provider
        string model_name
        int dimension
        string status
    }

    VECTOR_INDEX_ENTRIES {
        int id PK
        string embedding_id FK UK
        int faiss_id UK
        string status
    }

    USERS ||--o| PROFILES : has
    USERS ||--o{ USER_SKILLS : possesses
    SKILLS ||--o{ USER_SKILLS : categorizes
    USERS ||--o{ LEARNING_JOURNEYS : pursues
    LEARNING_JOURNEYS ||--o{ LEARNING_SESSIONS : contains
    LEARNING_SESSIONS ||--o| SESSION_SUMMARIES : generates
    LEARNING_SESSIONS ||--o{ FEEDBACK : receives
    USERS ||--o{ FEEDBACK : reviews
    USERS ||--o{ DOCUMENTS : owns
    DOCUMENTS ||--o| PARSED_DOCUMENTS : parses
    PARSED_DOCUMENTS ||--o{ CHUNKS : splits
    CHUNKS ||--o{ EMBEDDINGS : embeds
    EMBEDDINGS ||--o| VECTOR_INDEX_ENTRIES : indexes
```
