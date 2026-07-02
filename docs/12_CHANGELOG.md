# CloudPilot AI — Changelog

All notable changes to the CloudPilot platform will be documented in this file.

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
