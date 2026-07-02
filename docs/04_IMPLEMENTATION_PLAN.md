# CloudPilot AI — Granular Implementation Plan

## Phase 1: Premium UI/UX Redesign
Transform the UI into a premium, state-of-the-art developer platform.

### Sprint 1.1: Design System
- Clean up `tailwind.config.js` and structure common spacing, color variables (emerald, amber, slate, indigo), and global glassmorphism parameters.
- Standardize cards, typography, button sizes, and input borders.

### Sprint 1.2: Sidebar & Layout
- Replace standard header navigation with a collapsible **Premium Left Sidebar** routing.
- Add active indicators, sub-navigation panels, and user status profile at the bottom.

### Sprint 1.3: Dashboard
- Redesign main landing view into a responsive dashboard grid.
- Integrate cards for global status logs, recent repository analyses, and system configurations.

### Sprint 1.4: Repository Analysis
- Create the **AI Execution Timeline** widget.
- Animate streamed agent logs with real-time spinners and status Badge indicators using Framer Motion.

### Sprint 1.5: Reports Tab
- Implement a tabbed panel view: Overview (health scores), AWS Topology (visual graph), Cost Strategy (pricing details), and Setup Blueprint.
- Integrate interactive traffic sliders in the Cost Strategy tab.

### Sprint 1.6: Polish
- Audit responsive layouts on mobile, tablet, and ultra-wide screens.
- Enhance CSS micro-animations for hovered elements.

> **Exit Criteria (Phase 1)**:
> - [ ] Zero TypeScript compile-time errors.
> - [ ] Lighthouse Performance score `>95`.
> - [ ] Responsive layout verified on iOS, Android, and Desktop.
> - [ ] UI elements demo completed successfully.

---

## Phase 2: Deep Repository & Advanced Cloud Intelligence
Extend static scan definitions and add infrastructure blueprint zip exports.

### Sprint 2.1: Git Analytics Engine
- Integrate `git log` sub-process commands in the scanner.
- Map commit counts, contribution velocities, and code complexity scores.

### Sprint 2.2: Terraform Blueprint Exporter
- Build infrastructure templates for primary compute (App Runner, ECS, Lambda), RDS database instances, CloudFront CDNs, and S3 buckets.
- Implement zip download packaging on backend.

> **Exit Criteria (Phase 2)**:
> - [ ] Unit tests for Git log scanning passing.
> - [ ] Downloaded Terraform zip contains valid syntax (.tf files).
> - [ ] No path-traversal vulnerability on git clones.

---

## Phase 3: AI Technical Consultant Chat
Upgrade simple chat capabilities to an advanced RAG repository assistant.

### Sprint 3.1: Codebase Indexer
- Chunk repository code files and index embeddings in pgvector/local database.

### Sprint 3.2: Multi-turn Assistant Q&A
- Support questions regarding file content, function structures, and architectural boundaries.
- Build tools for generating PR diffs, suggesting migrations, and proposing bug fixes directly in the chat panel.

> **Exit Criteria (Phase 3)**:
> - [ ] Q&A system answers repository-specific logic queries correctly.
> - [ ] Code snippets references are clickable and lead to the file.
> - [ ] Context token limits are handled gracefully.

---

## Phase 4: Backend Hardening & Workspaces
Security, optimizations, and team collaboration scopes.

### Sprint 4.1: Security & Rate Limiting
- Add JWT refresh tokens, DB-backed rate limiter, and secure HTTP-only cookies.
- Set up automated directory cleaning for `temp_clones`.

### Sprint 4.2: Team Workspaces
- Implement Workspace schemas, invite roles, and organization management.

> **Exit Criteria (Phase 4)**:
> - [ ] JWT expiry verification tests pass.
> - [ ] Temporary files are pruned automatically after 1 hour.
> - [ ] Workspace invite flow functions.

---

## Phase 5: Documentation & Final Audit
Final polishing, onboarding documentation, and architecture audits.

### Sprint 5.1: Documentation
- Update `README.md` with V2 onboarding steps.
- Write **Developer Guide** (local workspace configurations, database seedings).
- Write **API Reference docs** (Swagger schema verification).

### Sprint 5.2: Final Security Audit
- Run static security analysis on Python and React codebases.
- Verify production deployment configurations.

> **Exit Criteria (Phase 5)**:
> - [ ] Clean build of documentation files.
> - [ ] Final regression and smoke tests pass.
> - [ ] Production deployment demo running.
