# 🤝 Contributing Guide — SkillSwap Arena

Thank you for your interest in contributing to **SkillSwap Arena**! This guide provides step-by-step instructions for setting up your local environment, cloning the repository, creating feature branches, adhering to code style standards, and submitting pull requests.

---

## 🚀 Quick Start Workflow Overview

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally.
3. **Create** a descriptive feature branch (`git checkout -b feature/amazing-feature`).
4. **Develop** & test your changes locally.
5. **Commit** using Conventional Commit standards (`git commit -m "feat: add amazing feature"`).
6. **Push** to your fork (`git push origin feature/amazing-feature`).
7. **Open** a Pull Request against `SkillSwap:dev` or `SkillSwap:main`.

---

## 🍴 Step 1: Forking & Cloning the Repository

### 1. Fork the Repository
Navigate to [https://github.com/joshi-chinmay-016/SkillSwap](https://github.com/joshi-chinmay-016/SkillSwap) and click the **Fork** button in the upper-right corner to create your own copy of the repository.

### 2. Clone Your Fork
Open your terminal and clone your forked repository:
```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/SkillSwap.git
cd SkillSwap
```

### 3. Add Upstream Remote
Keep your local clone synchronized with the original repository by adding the upstream remote:
```bash
git remote add upstream https://github.com/joshi-chinmay-016/SkillSwap.git
git fetch upstream
```

---

## 🌿 Step 2: Creating a Feature Branch

Always create a new branch from the latest `dev` branch before starting work:

```bash
git checkout dev
git pull upstream dev
git checkout -b feature/your-feature-name
```

### Branch Naming Conventions
* `feature/feature-name`: New product capabilities or UI components.
* `bugfix/fix-description`: Bug fixes and error resolutions.
* `refactor/subsystem-name`: Code cleanup or architectural refactoring.
* `security/vulnerability-fix`: Security enhancements or auth hardening.
* `docs/documentation-update`: Documentation additions or README revisions.

---

## 🛠️ Step 3: Local Environment Setup

### System Prerequisites
* **Python**: 3.12+
* **Node.js**: 18+ (npm 9+)
* **Database**: PostgreSQL 16+ (or local SQLite for unit testing)

---

### Backend Setup (FastAPI)

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Linux/macOS:
   python3 -m venv venv
   source venv/bin/activate

   # Windows (PowerShell):
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   *Update `.env` with your local PostgreSQL credentials and Gemini API Key if testing AI capabilities.*

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *The interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

---

### Frontend Setup (React + Vite)

1. Open a new terminal window and navigate to `frontend`:
   ```bash
   cd frontend
   ```

2. Install Node package dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *Access the web app at [http://localhost:5173](http://localhost:5173).*

---

## 🧪 Step 4: Testing & Quality Assurance

Run the PyTest backend test suite to verify your changes haven't introduced regressions:

```bash
cd backend
python -m pytest
```

### Running Specific Test Modules
* **WebSocket Security Tests**:
  ```bash
  python -m pytest tests/test_websocket_security.py
  ```
* **Semantic Retrieval Engine Tests**:
  ```bash
  python -m pytest tests/test_retrieval.py
  ```
* **RAG Pipeline Tests**:
  ```bash
  python -m pytest tests/test_rag_hardening.py
  ```

---

## 📐 Step 5: Code Style & Architecture Guidelines

### 1. Router → Service → Repository Isolation
Never execute raw SQL or ORM database calls directly inside router endpoints (`app/api/`).
* **Router**: HTTP request parsing, Pydantic validation, status codes.
* **Service**: Business logic, authorization checks, workflow orchestration.
* **Repository**: SQLAlchemy queries and database persistence.

### 2. Pydantic V2 Modernization
Use modern Pydantic v2 conventions across all schema classes:
```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    id: int
    email: str
    
    model_config = ConfigDict(from_attributes=True)
```

### 3. Security Standards
* Always validate user ownership before mutating or returning user resources.
* Never log JWT tokens, passwords, secrets, or raw vector arrays.

---

## 📝 Step 6: Commit Conventions

We follow the **Conventional Commits** specification:

```bash
git commit -m "type(scope): concise description of changes"
```

### Supported Commit Types
* `feat`: A new user-facing feature.
* `fix`: A bug fix.
* `docs`: Documentation updates.
* `refactor`: Code change that neither fixes a bug nor adds a feature.
* `test`: Adding missing unit or integration tests.
* `chore`: Maintenance, dependencies, build configurations.

*Example*: `git commit -m "feat(auth): enforce JWT validation on websocket endpoint"`

---

## 📤 Step 7: Submitting a Pull Request

1. Push your branch to your GitHub fork:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Navigate to [https://github.com/joshi-chinmay-016/SkillSwap](https://github.com/joshi-chinmay-016/SkillSwap).
3. Click **Compare & pull request**.
4. Fill out the PR template with details of your changes, test evidence, and related issue numbers.

### Pull Request Checklist
- [ ] Code follows project architecture (Router → Service → Repository).
- [ ] All PyTest tests pass (`python -m pytest`).
- [ ] No secret keys or API credentials are committed.
- [ ] Frontend builds without errors (`npm run build`).
- [ ] Documentation has been updated for new endpoints or features.
