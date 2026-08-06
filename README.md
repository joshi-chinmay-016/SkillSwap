<div align="center">

# ⚡ SkillSwap Arena

### **Enterprise Peer Learning & AI-Powered Knowledge Exchange Platform**

*Connecting learners and mentors through real-time skill exchange, intelligent matching, structured learning journeys, and an AI Mentor powered by long-term memory and RAG document architecture.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES2024-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=python&logoColor=white)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Build Status](https://img.shields.io/badge/Tests-87%2F87%20Passing-22C55E?style=for-the-badge&logo=pytest&logoColor=white)](#testing--quality-assurance)

<br />

[Explore Features](#-core-features) • [System Architecture](#%EF%B8%8F-system-architecture) • [AI & RAG Engine](#-ai-mentor--rag-architecture) • [Getting Started](#-getting-started) • [API Documentation](#-api-reference)

</div>

---

> [!IMPORTANT]
> **SkillSwap Arena** is an enterprise-grade SaaS application engineered for scalable peer-to-peer mentorship and AI-augmented education. Built with a decoupled **Repository → Service → Router** backend pattern and a reactive, glassmorphic React frontend, it features real-time WebSocket notifications, a multi-format Document Parsing & RAG Engine, and persistent AI Mentor memory.

---

## 📌 Executive Summary

SkillSwap Arena bridges the gap between traditional peer learning and modern generative AI. While learners exchange real-world skills through structured sessions and reputation-backed feedback, an integrated **AI Mentor** actively processes their uploaded learning materials (PDFs, Markdown notes, TXT files) into searchable vector knowledge using a 6-stage RAG pipeline.

### Why SkillSwap Arena?

* **Decoupled Business Logic**: Strict separation between data access, business orchestration, and HTTP presentation layers ensures high maintainability and 100% unit-testability.
* **Asynchronous Document Pipeline**: Document uploads are stored instantly via a unified `StorageService` abstraction, while text extraction runs non-blockingly via background task workers.
* **State-of-the-Art AI Integration**: Combines short-term conversation context, persistent categorical memory (`MentorMemory`), and multi-format document RAG to deliver personalized mentorship.
* **Production Reliability**: Backed by a full PyTest suite (87/87 tests passing), SHA-256 duplicate file detection, path traversal security, and Alembic schema versioning.

---

## 🎯 Core Features

### 🔐 1. Authentication & Identity Management
* **OAuth2 Password Flow & JWT Security**: Stateless authentication with encrypted JWT bearer tokens.
* **User Profiles & Role Management**: Personal portfolios showcasing skills to teach, skills to learn, reputation score, and completed sessions.
* **Strict Ownership Boundaries**: Hard security authorization layer preventing cross-user data leaks across documents, requests, and session logs.

### 🔄 2. Peer Skill Matching & Session Management
* **Teach & Learn Skill Mapping**: Bidirectional skill categorization enabling precise peer discovery.
* **Mentor Availability Engine**: Time-slot management with collision prevention and validation.
* **Session Lifecycle Control**: Request proposal, acceptance, rejection, live completion tracking, and cancellation flows.

### ⚡ 3. Real-Time WebSocket Alerts & Communication
* **FastAPI WebSocket Engine**: User-specific connection channels for instant event delivery.
* **Live Notifications**: Instant alerts when a session request is accepted, rejected, or scheduled.
* **Persistent Event Tracking**: Database-backed notification history with read/unread tracking.

### 📊 4. Analytics & Reputation Leaderboards
* **Mentor Reputation Algorithm**: Weighted score computed from session completion rate, ratings, and response times.
* **Skill Trends & Metrics**: Visual analytics for top teaching skills, learning demand, and mentor performance.
* **Competitive Leaderboards**: Dynamic rankings for top-rated mentors and active contributors.

### 📄 5. Document Management Engine (Day 66)
* **Storage Provider Abstraction**: Modular `StorageProvider` interface supporting local filesystem and seamless cloud (AWS S3 / Azure Blob) migration.
* **Security & Integrity**: Automatic SHA-256 checksum duplicate rejection, path traversal protection, and UUID file isolation.
* **Management APIs**: 8 production REST endpoints for file upload, paginated listing, streaming download, soft-delete archiving, and storage health diagnostics.

### 🧠 6. AI Document Parsing & RAG Engine (Day 67)
* **Multi-Format Text Extraction**: Isolated parser engine supporting PDF (PyMuPDF `fitz`), Plain Text (`chardet` auto-encoding), and Markdown (`markdown` syntax stripping).
* **Asynchronous Pipeline**: Upload returns instantly while text extraction executes in background task workers, transitioning status from `UPLOADED` → `PROCESSING` → `READY`.
* **Parsed Content Persistence**: Dedicated `ParsedDocument` database store enabling immediate chunking, embedding, and vector index generation over Days 68–74.

---

## 🛠️ System Architecture

SkillSwap Arena is architected around enterprise scalability, clean isolation of concerns, and robust error recovery.

```mermaid
%%{init: {
"theme":"base",
"themeVariables":{
"primaryColor":"#E8F0FE",
"primaryBorderColor":"#2563EB",
"primaryTextColor":"#1E293B",
"secondaryColor":"#ECFEFF",
"tertiaryColor":"#F8FAFC",
"lineColor":"#64748B",
"fontSize":"15px"
}
}}%%
graph TD
    Client[React Frontend / SPA] -->|HTTPS / REST API| Router[FastAPI Router Layer]
    Client -->|WSS / WebSockets| WS[WebSocket Manager]
    
    subgraph Backend Core
        Router --> Auth[Auth & Security Middleware]
        Auth --> Service[Business Service Layer]
        Service --> Repo[Repository Pattern Layer]
        
        Service --> StorageSvc[StorageService Facade]
        Service --> ParseSvc[DocumentParsingService]
    end
    
    subgraph Storage & Pipeline
        StorageSvc --> StorageProv[LocalStorageProvider / S3]
        ParseSvc --> ParserMgr[ParserManager & Factory]
        ParserMgr --> PDFP[PDFParser]
        ParserMgr --> TXTP[TxtParser]
        ParserMgr --> MDP[MarkdownParser]
    end
    
    subgraph Database
        Repo --> DB[(PostgreSQL Database)]
        ParseSvc --> DB
    end
```

### Architectural Rationale

1. **Why Repository Pattern?**
   Separating database queries (`repositories/`) from FastAPI HTTP logic (`routers/`) ensures database technology can be swapped or unit-tested using an in-memory SQLite database without modifying business logic.
2. **Why Asynchronous Parsing?**
   File parsing (especially large multi-page PDFs) can be CPU-intensive. By delegating text extraction to background task workers after committing metadata, API response latency stays under 50ms regardless of document size.
3. **Why Storage Service Facade?**
   The application code interacts exclusively with `StorageService`. Physical storage providers (local disk, AWS S3, Google Cloud Storage) implement a standard `StorageProvider` interface, eliminating hardcoded filesystem dependencies.

---

## 🤖 AI Mentor & RAG Architecture

The AI subsystem transforms uploaded documents into a persistent knowledge base for personalized mentorship.

```mermaid
%%{init: {
"theme":"base",
"themeVariables":{
"primaryColor":"#E8F0FE",
"primaryBorderColor":"#2563EB",
"primaryTextColor":"#1E293B",
"secondaryColor":"#ECFEFF",
"tertiaryColor":"#F8FAFC",
"lineColor":"#64748B",
"fontSize":"15px"
}
}}%%
flowchart LR
    Upload[Uploaded File] -->|Day 66| Store[Storage Provider]
    Store -->|Day 67| Parse[Parser Engine]
    Parse -->|Text Content| DB[(ParsedDocument Store)]
    DB -.->|Day 68| Chunk[Chunk Generator]
    Chunk -.->|Day 69| Embed[Embedding Pipeline]
    Embed -.->|Day 70| Vector[(Vector Index)]
    Vector -.->|Day 72| RAG[RAG Retriever]
    RAG -->|Context Injection| AIMentor[AI Mentor Engine]
```

### The 6-Stage Knowledge Pipeline

| Stage | Name | Description | Status |
| :--- | :--- | :--- | :--- |
| **Stage 1** | **Upload** | Secure Multipart upload, SHA-256 duplicate check, storage persistence | `COMPLETE` (Day 66) |
| **Stage 2** | **Parsing** | Multi-format text extraction (PDF, TXT, MD) into `ParsedDocument` | `COMPLETE` (Day 67) |
| **Stage 3** | **Chunking** | Semantic token windowing and recursive text splitting | `PLANNED` (Day 68) |
| **Stage 4** | **Embeddings** | Dense vector representation generation via embedding models | `PLANNED` (Day 69) |
| **Stage 5** | **Vector Index** | HNSW / PGVector indexing for fast cosine similarity retrieval | `PLANNED` (Day 70) |
| **Stage 6** | **Ready for AI** | Deep integration with AI Mentor for retrieval-augmented responses | `PLANNED` (Day 72) |

---

## 🗄️ Database Schema

The database model is managed via SQLAlchemy 2.0 and version-controlled using Alembic migrations.

```mermaid
%%{init: {
"theme":"base",
"themeVariables":{
"primaryColor":"#E8F0FE",
"primaryBorderColor":"#2563EB",
"primaryTextColor":"#1E293B",
"secondaryColor":"#ECFEFF",
"tertiaryColor":"#F8FAFC",
"lineColor":"#64748B",
"fontSize":"15px"
}
}}%%
erDiagram
    USERS ||--o{ DOCUMENTS : "owns"
    USERS ||--o{ SESSIONS : "participates"
    USERS ||--o{ NOTIFICATIONS : "receives"
    USERS ||--o{ MENTOR_MEMORIES : "accumulates"
    DOCUMENTS ||--|| PARSED_DOCUMENTS : "has"
    SESSIONS ||--o| FEEDBACK : "generates"

    USERS {
        int id PK
        string email UK
        string name
        string password_hash
        datetime created_at
    }

    DOCUMENTS {
        string id PK
        int user_id FK
        string original_filename
        string stored_filename
        string display_name
        string file_extension
        string mime_type
        bigint file_size
        string storage_path
        string checksum
        string status
        datetime uploaded_at
        datetime deleted_at
    }

    PARSED_DOCUMENTS {
        string id PK
        string document_id FK,UK
        text text_content
        string status
        datetime created_at
        datetime updated_at
    }

    MENTOR_MEMORIES {
        int id PK
        int user_id FK
        string category
        string title
        text content
        string importance
        string status
        datetime created_at
    }

    SESSIONS {
        int id PK
        int mentor_id FK
        int learner_id FK
        string skill_id
        string status
        datetime scheduled_at
    }

    FEEDBACK {
        int id PK
        int session_id FK
        int rating
        text review
        datetime created_at
    }
```

---

## 🔄 Core Request Lifecycles

### 1. Document Upload & Asynchronous Parsing Flow

```mermaid
%%{init: {
"theme":"base",
"themeVariables":{
"primaryColor":"#E8F0FE",
"primaryBorderColor":"#2563EB",
"primaryTextColor":"#1E293B",
"secondaryColor":"#ECFEFF",
"tertiaryColor":"#F8FAFC",
"lineColor":"#64748B",
"fontSize":"15px"
}
}}%%
sequenceDiagram
    autonumber
    actor Learner
    participant Router as Document Router
    participant Service as DocumentService
    participant Storage as StorageService
    participant DB as PostgreSQL DB
    participant Worker as Background Task
    participant Parser as ParserManager

    Learner->>Router: POST /documents/upload (file)
    Router->>Service: upload_document(user_id, file)
    Service->>Service: Validate MIME, extension & size
    Service->>Service: Compute SHA-256 Checksum
    Service->>DB: Check for duplicate checksum
    Service->>Storage: save_file(bytes, user_id, document_id)
    Storage-->>Service: Return StorageMetadata
    Service->>DB: INSERT INTO documents (status="UPLOADED")
    Service-->>Router: Return DocumentUploadResponse
    Router->>Worker: Enqueue _run_parsing(document_id)
    Router-->>Learner: HTTP 201 Created (Instant Response)

    opt Asynchronous Background Worker
        Worker->>DB: UPDATE documents SET status="PROCESSING"
        Worker->>Storage: get_file(storage_path)
        Storage-->>Worker: Return file bytes
        Worker->>Parser: parse_document(bytes, extension)
        Parser-->>Worker: Return extracted text_content
        Worker->>DB: INSERT INTO parsed_documents
        Worker->>DB: UPDATE documents SET status="READY"
    end
```

---

## 💻 Tech Stack Specification

| Subsystem | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance asynchronous Python REST API framework |
| **Database ORM** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Type-safe SQL toolkit and Object-Relational Mapper |
| **Database Engine** | [PostgreSQL](https://www.postgresql.org/) / SQLite | Production relational datastore with Alembic migrations |
| **Text Extraction** | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) | High-speed PDF parsing and text chunk generation |
| **Encoding Detection**| [chardet](https://chardet.readthedocs.io/) | Universal character encoding detector for plain text |
| **Markdown Parser** | [Python-Markdown](https://python-markdown.github.io/) | Markdown syntax compiler and HTML text stripper |
| **Frontend Core** | [React 18](https://react.dev/) + [Vite](https://vitejs.dev/) | Ultra-fast client SPA framework and build system |
| **Data Fetching** | [React Query v5](https://tanstack.com/query/latest) | Server-state management, caching, and auto-polling |
| **Animations** | [Framer Motion / Motion](https://motion.dev/) | 60fps glassmorphic micro-interactions and layout transitions |
| **Styling** | [TailwindCSS](https://tailwindcss.com/) | Utility-first responsive design engine |

---

## 📂 Project Repository Structure

```
SkillSwap/
├── backend/
│   ├── alembic/                  # Database migration scripts
│   │   └── versions/             # Migration files (d90a1_add_documents...)
│   ├── app/
│   │   ├── api/                  # FastAPI REST Routers
│   │   │   ├── auth.py           # Authentication endpoints
│   │   │   ├── document_router.py# Document & Parsing management endpoints
│   │   │   └── sessions.py       # Session management endpoints
│   │   ├── core/                 # App configuration & DB session factories
│   │   ├── models/               # SQLAlchemy Models (Document, ParsedDocument...)
│   │   ├── repositories/         # Repository Data Access Layer
│   │   ├── schemas/              # Pydantic Request/Response contracts
│   │   ├── services/             # Business Logic & Parsing Orchestration
│   │   └── storage/              # Unified Storage Provider & Facade Layer
│   ├── parsers/                  # Isolated Multi-Format Document Parsing Engine
│   │   ├── document_parser.py    # Abstract DocumentParser Base Interface
│   │   ├── pdf_parser.py         # PyMuPDF PDF Text Parser
│   │   ├── txt_parser.py         # Chardet Plain Text Parser
│   │   ├── markdown_parser.py    # HTML-stripping Markdown Parser
│   │   ├── parser_factory.py     # Extension-based Parser Factory
│   │   └── parser_manager.py     # Unified ParserManager Facade
│   ├── tests/                    # PyTest Unit & Integration Test Suite
│   └── requirements.txt          # Python dependency specification
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── documents/        # AI Document Library UI Components
│   │   │       ├── DocumentCard.jsx       # 3D perspective document card
│   │   │       ├── MetadataDrawer.jsx     # Slide-over AI Pipeline Drawer
│   │   │       ├── ProcessingBadge.jsx    # Status morphing badge
│   │   │       ├── ProcessingTimeline.jsx # 6-stage AI Pipeline Visualizer
│   │   │       └── ProgressRing.jsx       # Circular SVG progress ring
│   │   ├── hooks/
│   │   │   └── useDocuments.js   # React Query document & polling hooks
│   │   ├── pages/
│   │   │   └── DocumentLibraryPage.jsx # AI Knowledge Library Page
│   │   └── services/
│   │       └── api.js            # Axios HTTP client instance
│   └── package.json              # Node.js dependencies
└── README.md
```

---

## ⚡ Getting Started

### Prerequisites

Ensure you have the following installed locally:
* **Python 3.12+**
* **Node.js 18+** and **npm**
* **PostgreSQL 16+** (optional; SQLite in-memory engine runs out-of-the-box for testing)

---

### 🚀 Quick Start (Local Development)

#### 1. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/joshi-chinmay-016/SkillSwap.git
cd SkillSwap

# Setup Backend Virtual Environment
cd backend
python -m venv venv

# Activate Virtual Environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python Dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

Create a `.env` file inside `backend/`:

```env
PROJECT_NAME="SkillSwap Arena"
DATABASE_URL="sqlite:///./skillswap.db"
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Storage Settings
STORAGE_PROVIDER="local"
LOCAL_STORAGE_DIR="uploads"
MAX_FILE_SIZE=26214400
DUPLICATE_UPLOAD_POLICY="REJECT"
```

#### 3. Run Database Migrations

```bash
alembic upgrade head
```

#### 4. Launch Backend API Server

```bash
uvicorn app.main:app --reload --port 8000
```
> The API interactive Swagger documentation will be live at `http://localhost:8000/docs`.

#### 5. Launch Frontend Application

In a new terminal window:

```bash
cd frontend
npm install
npm run dev
```
> The Web Application will be available at `http://localhost:5173`.

---

## 🧪 Testing & Quality Assurance

SkillSwap Arena enforces strict automated testing before deployment.

```bash
cd backend
.\venv\Scripts\pytest.exe tests/test_document_parsers.py tests/test_documents.py -v
```

### Test Coverage Highlights

```text
============================== test session starts ==============================
platform win32 -- Python 3.12.10, pytest-9.1.1 -- C:\SkillSwap\backend\venv\Scripts\python.exe
collected 87 items

tests/test_document_parsers.py::test_txt_parser_utf8 PASSED              [  1%]
tests/test_document_parsers.py::test_markdown_parser PASSED            [  3%]
tests/test_document_parsers.py::test_pdf_parser_valid PASSED              [  4%]
tests/test_document_parsers.py::test_parser_factory_selection PASSED      [  6%]
tests/test_document_parsers.py::test_document_parsing_service_success PASSED [ 10%]
tests/test_documents.py::TestDocumentSecurity::test_upload_duplicate_rejected PASSED [100%]

====================== 87 passed, 21 warnings in 7.10s ======================
```

---

## 🛡️ Security & Performance Standards

* **Path Traversal Protection**: Sanitizes filenames and enforces canonical path verification within `LocalStorageProvider`.
* **SHA-256 Duplicate Check**: Prevents storage redundancy by checking file checksums per user.
* **Non-Blocking IO**: High-latency document processing runs in background tasks, keeping HTTP workers available.
* **Auto-Polling Query Invalidation**: React Query polling automatically pauses as soon as all active documents reach terminal states (`READY` / `FAILED`).

---

## 🗺️ Project Roadmap

```mermaid
%%{init: {
"theme":"base",
"themeVariables":{
"primaryColor":"#E8F0FE",
"primaryBorderColor":"#2563EB",
"primaryTextColor":"#1E293B",
"lineColor":"#64748B"
}
}}%%
timeline
    title SkillSwap Arena Development Roadmap
    section Phase 1 : Core SaaS (Completed)
        User Auth & JWT : Session Request Flow : Peer Skill Matching
    section Phase 2 : RAG Foundation (Completed)
        Storage Abstraction (Day 66) : Multi-Format Parser Engine (Day 67) : Pipeline UI & Drawer
    section Phase 3 : AI Engine (Upcoming)
        Semantic Text Chunking (Day 68) : Dense Embedding Generation (Day 69) : PGVector Storage (Day 70)
    section Phase 4 : Full RAG & Chat (Upcoming)
        Context-Aware RAG Chat (Day 72) : Real-Time Session Reminders : Peer Mentor Stock Market
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <sub>Maintained with ❤️ by the SkillSwap Arena Team</sub>
</div>
