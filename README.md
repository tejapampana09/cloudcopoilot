# CloudPilot AI – Phase 1: Repository Analyzer

CloudPilot AI is a repository analysis platform with AI-assisted deployment recommendations and heuristic cloud planning. It inspects any public GitHub repository and designs an optimized deployment target recommendation, monthly AWS cost estimate, cloud readiness score, and a verification checklist.

This repository represents **Phase 1: Repository Analyzer** built using FastAPI, React 19, Tailwind CSS v4, and LangGraph.

---

## Folder Structure

```text
cloudpilot-ai/
├── backend/            # FastAPI Python server
│   ├── app/            # Core backend app package
│   │   ├── core/       # Configuration Settings
│   │   ├── schemas/    # Pydantic schemas (Request/Response contracts)
│   │   ├── services/   # Git cloning, heuristic scanning & cost estimation
│   │   ├── agents/     # LangGraph workflow & states
│   │   └── routers/    # POST/stream endpoints
│   ├── temp_clones/    # Temporary workspace cloning location (auto-purged)
│   ├── requirements.txt
│   └── run.py          # Uvicorn startup entrypoint
├── frontend/           # React 19 / Vite TS frontend SPA
│   ├── src/
│   │   ├── components/ # Premium dashboard widgets
│   │   ├── hooks/      # SSE EventSource hooks
│   │   ├── services/   # API abstraction layer
│   │   └── index.css   # Tailwind v4 imports & Glassmorphism styles
│   ├── vite.config.ts
│   └── package.json
└── shared/
    └── types.ts        # Common TypeScript interfaces
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
# Optional: Add your OpenAI API Key to enrich summary justifications and checklist logs via GPT-4o-mini
OPENAI_API_KEY=your_openai_api_key_here
```

### Running Locally
To launch the backend local dev server on `http://localhost:8000`:
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
3. Paste a public GitHub URL (e.g., `https://github.com/fastapi/fastapi` or `https://github.com/facebook/react`).
4. Click **Analyze Repository** to observe the real-time agent workflow logs and final AWS deployment recommendations.

## Current Limitations
- Phase 1 focuses on repository analysis, heuristics, and deployment recommendations, not on production-grade infrastructure orchestration.
- The AI guidance is based on heuristics and repository metadata; it may not cover every custom build or cloud pattern.
- Authentication, secrets scanning, and public deployment hardening are intentionally limited in this phase.

## Roadmap
- Add robust production deployment tips, integration tests, and CI/CD generation.
- Improve infrastructure recommendations with real AWS service matching and cost profiling.
- Add observability, error tracking, and better user session validation.

## Known Issues
- SSE streams may drop if the backend token is not provided correctly in the query string.
- Some repository scans may miss non-standard project layouts or custom build scripts.
- OpenAI model configuration is optional, and feature quality depends on API availability.

## Architecture
- `backend/` contains the FastAPI service, scan workflow, and SSE streaming endpoints.
- `frontend/` contains the React 19 + Vite SPA, SSE client hooks, and cost/analysis dashboard.
- `shared/` contains common TypeScript interfaces.
