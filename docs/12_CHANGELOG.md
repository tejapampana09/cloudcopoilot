# CloudPilot AI — Changelog

All notable changes to the CloudPilot platform will be documented in this file.

---

## [2.0.0-beta] - 2026-07-02
### Added
- **CloudPilot Deploy MVP**: Implemented AWS App Runner live deployments. Exposes IAM key verifiers, service configuration parameters, and live SSE streaming logs. Spawns python background threads executing `terraform init/plan/apply` commands or simulating progress if CLI keys are absent. Includes destruction infrastructure controls and database persistence logging.
- **Phase 2 Repository Intelligence Audit**: Integrated secret detection (AWS Keys, JWT secrets, credentials), large files checks (>500 lines), circular dependencies, and git remote branch release tags checks inside [scanner.py](file:///c:/Users/ss/Desktop/New%20folder/backend/app/services/scanner.py).
- **Autonomous Multi-Agent Orchestrator**: Refactored the LangGraph graph pipeline in [graph.py](file:///c:/Users/ss/Desktop/New%20folder/backend/app/agents/graph.py) to sequence exactly 10 independent sequential agents: Repository Agent -> Architecture Agent -> Security Agent -> Performance Agent -> Cloud Architect Agent -> Infrastructure Agent -> Deploy Agent -> Monitoring Agent -> Cost Optimization Agent -> Executive Agent.
- **Enhanced States Serialization**: Enriched the database task mapping and Pydantic schemas in [analyzer.py](file:///c:/Users/ss/Desktop/New%20folder/backend/app/schemas/analyzer.py) to track and return `infrastructure_report`, `deploy_report`, `monitoring_report`, and `cost_optimization_report`.
- **UI Progress Timeline**: Expanded the frontend [DeploymentStepsCard.tsx](file:///c:/Users/ss/Desktop/New%2520folder/frontend/src/components/DeploymentStepsCard.tsx) component to animate and track all 10 agents sequentially during live scans.
- **UI Tab Integration**: Added DevOps tab and mapped Overall Quality score rings and Priority Fixes / Cloud Action Plan lists inside the Reports Overview panel.
- **UI/UX Design System & Layout**: Styled [index.css](file:///c:/Users/ss/Desktop/New%2520folder/frontend/src/index.css) design tokens, glowing components, and responsive panels.
- **Premium Sidebar Navigation**: Implemented compact collapse mode, project Workspace Switcher dropdown, and a Command+K search bar.
- **Dashboard Redesign Hero**: Added greetings hero panel ("Good Morning, Srikar Reddy"), operational status monitors, repository scanner input, and SaaS metrics insights.
- **Tabbed Reports Panel**: Organized reports page into sub-tabs (Overview, Architecture, Security, Performance, AWS Topology, Cost Analyzer, DevOps, IaC Deployment).
- **Responsive SVG Charts**: Integrated SVG cost segment donut charts and compute host comparison bar charts.
- **Agent Orchestration Timeline**: Redesigned [DeploymentStepsCard.tsx](file:///c:/Users/ss/Desktop/New%2520folder/frontend/src/components/DeploymentStepsCard.tsx) to resolve dynamic execution statuses from streamed logs.
- **Git Analytics Engine**: Sub-process log audits evaluating commit sizes, author count, complexity mapping (Low/Medium/High), and dynamic Technical Debt scores.
- **Ask CloudCopilot RAG Chat**: Implemented [AIConsultantChat.tsx](file:///c:/Users/ss/Desktop/New%2520folder/frontend/src/components/AIConsultantChat.tsx) with a left actions column to trigger direct codebase evaluations (explain architecture, reduce cost, analyze database scaling, security scoring, custom Terraform) calling the `/chat` RAG POST endpoint.
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
