# CloudPilot AI — Changelog

All notable changes to the CloudPilot platform will be documented in this file.

---

## [2.0.0-beta] - 2026-07-02
### Added
- **UI/UX Design System & Layout**: Styled [index.css](file:///c:/Users/ss/Desktop/New%20folder/frontend/src/index.css) design tokens, glowing components, and responsive panels.
- **Premium Sidebar Navigation**: Implemented compact collapse mode, project Workspace Switcher dropdown, and a Command+K search bar.
- **Dashboard Redesign Hero**: Added greetings hero panel ("Good Morning, Srikar Reddy"), operational status monitors, repository scanner input, and SaaS metrics insights.
- **Tabbed Reports Panel**: Organized reports page into sub-tabs (Overview, Architecture, Security, Performance, AWS Topology, Cost Analyzer, IaC Deployment).
- **Responsive SVG Charts**: Integrated SVG cost segment donut charts and compute host comparison bar charts.
- **Agent Orchestration Timeline**: Redesigned [DeploymentStepsCard.tsx](file:///c:/Users/ss/Desktop/New%20folder/frontend/src/components/DeploymentStepsCard.tsx) to resolve dynamic execution statuses (Repository Agent, Architecture Agent, Security Agent, Cloud Agent, Executive Report) from streamed logs.
- **Git Analytics Engine**: Sub-process log audits evaluating commit sizes, author count, complexity mapping (Low/Medium/High), and dynamic Technical Debt scores.
- **Ask CloudCopilot RAG Chat**: Implemented [AIConsultantChat.tsx](file:///c:/Users/ss/Desktop/New%20folder/frontend/src/components/AIConsultantChat.tsx) with a left actions column to trigger direct codebase evaluations (explain architecture, reduce cost, analyze database scaling, security scoring, custom Terraform) calling the `/chat` RAG POST endpoint.
- **Directory Cleanups daemon**: Spawns background thread worker on server start that automatically prunes temp_clones directories older than 1 hour.
- **Pytest config**: Added `pytest.ini` ignoring temporary clone folders to ensure clean unit test collections.

### Fixed
- **LangChain ValueError braces crash**: Patched the `call_llm` human prompt in `infra_graph.py` to route contents as variables, preventing parse failures on codebase curly braces.

---

## [1.1.0] - 2026-07-02
### Added
- **Dynamic Weighted Decision Matrix**: Scores compute platforms (Amplify, App Runner, ECS, Lambda) dynamically using weights customized to technology profiles.
- **Explainable Rationale**: Markdown blocks showing why the target was selected, why alternatives were discarded, operational trade-offs, and cost strategies.
- **Deep Dependency Audit**: Scans codebase package lists (`package.json`, `requirements.txt`, `pyproject.toml`, `Cargo.toml`, `go.mod`) to extract databases, ORMs, Auth, Storage, and Caching configurations.
- **Architectural Bottlenecks Parser**: Detects SQLite locks, local uploads constraints, missing environment templates, and missing task queues.
- **Realistic cost simulator**: Estimates RDS sizing, compute instances, data transfer, storage, and load balancers.
- **Granular LangGraph Flow**: Restructured the workflow into 8 single-responsibility nodes.
- **New Test Suite**: Wrote `test_reasoning_engine.py` validating decision, cost, context, and report modules.

### Fixed
- **Visualization Pydantic Crash**: Fixed Pydantic validation error in the report graph generator by replacing `from`/`to` keys with `source`/`target` values.
- **Uvicorn Reload Loop**: Configured uvicorn to ignore git clones in the root workspace, resolving process crashes.

---

## [1.0.0] - 2026-07-01
### Added
- Core React + Vite client dashboard.
- FastAPI backend router endpoints.
- LangGraph execution logic scans.
- SQLite memory database tables.
- Heuristic file code scanner.
- Basic AWS deployment targets.
