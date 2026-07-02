# CloudCopilot AI – AI GitHub Repository Assistant

CloudCopilot AI is a production-ready **AI GitHub Repository Assistant** (AI GitHub Engineer) that inspects public GitHub repositories, builds a semantic vector index for RAG queries, audits code quality, scans for security and performance vulnerabilities, and auto-generates developer documentations and deployment blueprints.

Built using **FastAPI (Python)**, **React 19 / TypeScript**, **Tailwind CSS v4**, and **LangGraph**.

---

## Core Capabilities

1. **Semantic Codebase Indexing (RAG)**:
   - Clones repositories and parses files using an optimized traversal engine (skips `node_modules`, `.git`, `.venv` directories in place for fast scans).
   - Generates embeddings using `OpenAIEmbeddings` (fully integrated with both standard OpenAI and OpenRouter `sk-or-` APIs).
   - Performs local cosine similarity vector matching in Python, allowing full conversational RAG capabilities over your code context.
2. **Bug Detection & Fix Suggestions**:
   - Audits logic bugs, missing validations, async execution patterns, and duplicate code blocks.
   - Outputs the Problem, Impact, Affected files, Suggested solution, and Syntax-highlighted example fix code.
3. **Security Vulnerability Scanner**:
   - Inspects files for hardcoded secrets/credentials, weak JWT token structures, SQL Injection risks, XSS flaws, and CORS wildcard vulnerabilities.
4. **Performance Auditor**:
   - Identifies oversized components, heavy/bloated dependencies, slow APIs, and concurrency locks (such as SQLite write bottlenecks).
5. **Auto-Generated Technical Documentation**:
   - Generates production-ready markdown templates: `README.md`, System Architecture, Folder Guides, REST API Reference, setup scripts, and dev guidelines.
6. **Deployment Guide Generator**:
   - Detects the project framework, recommends a cloud hosting target (e.g. AWS App Runner, ECS, Lambda, Amplify), details build commands, outlines environment configuration templates, and lists required secrets.

---

## Folder Structure

```text
cloudpilot-ai/
├── backend/            # FastAPI Python Server
│   ├── app/            # Core backend app package
│   │   ├── core/       # Configuration Settings (OpenRouter auto-detection)
│   │   ├── schemas/    # Pydantic schemas (Request/Response contracts)
│   │   ├── models/     # SQLAlchemy schemas (Repository chunks, Users)
│   │   ├── services/   # Semantic indexing, Git helper, Cost estimators
│   │   ├── agents/     # 12-Agent LangGraph Orchestrator pipeline
│   │   └── routers/    # API endpoints (Auth, Analyzer, SSE Streams)
│   ├── requirements.txt
│   └── run.py          # Uvicorn startup entrypoint
├── frontend/           # React 19 / Vite TS Frontend SPA
│   ├── src/
│   │   ├── components/ # Premium light gradient widgets & chats
│   │   ├── hooks/      # SSE EventSource hook
│   │   ├── services/   # API client helper
│   │   └── index.css   # Light Gradient Theme & Glassmorphism styles
│   └── package.json
└── shared/
    └── types.ts        # Shared TypeScript interfaces
```

---

## Backend Setup (FastAPI)

### Prerequisites
- Python 3.10+
- Git CLI (installed and added to PATH)

### Installation
1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows (Command Prompt)
   .\venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
Create a `.env` file in the `backend/` directory:
```env
# Add your OpenAI or OpenRouter key to run indexing and completions
OPENAI_API_KEY=your_key_here
```

### Running Locally
To launch the backend API server on `http://localhost:8000`:
```bash
python run.py
```

---

## Frontend Setup (React 19)

### Prerequisites
- Node.js v18+
- npm v9+

### Installation
1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```

### Running Locally
To launch the Vite development server on `http://localhost:5173`:
```bash
npm run dev
```

---

## Running End-to-End Analysis
1. Ensure both the backend and frontend are running.
2. Open your browser to `http://localhost:5173`.
3. Paste a public GitHub URL (e.g., `https://github.com/fastapi/fastapi` or `https://github.com/expressjs/express`).
4. Click **Scan Repository** to observe the real-time agent activity logs and orchestrator pipeline.
5. Once completed, explore the circular quality scores, Recharts charts, bug fix guides, documentations, and query the **AI Consultant Stream** to chat directly with your codebase.
