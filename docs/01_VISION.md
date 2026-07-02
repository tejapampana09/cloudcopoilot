# CloudPilot AI — Core Vision & Objectives

## Core Mission
CloudPilot is an AI-native Cloud Solutions Architect platform. Its goal is to transition manual cloud planning, repository auditing, security assessments, and Terraform IaC generation into an autonomous, explainable reasoning experience.

CloudPilot goes beyond simple static keyword checks, employing a dynamically weighted decision matrix and semantic analysis models to deliver enterprise-grade, technically defensible architectural advice.

---

## Architectural Principles
1. **Explainability First**: Every cloud recommendation must prove its value. No service should be recommended without explaining its advantages, trade-offs, alternative evaluations, and scaling patterns.
2. **Data-Exchange over Text**: LangGraph nodes communicate via well-typed data models rather than loosely structured text prompts, ensuring high reliability and type safety.
3. **Decoupled Architecture**: Separation of presentation UI, service routing APIs, scanning modules, and multi-agent workflows.
4. **Documentation as Code**: Treat documentation as project source code. Update documentation after every single sprint to maintain context for future engineering.

---

## V2 Platform Target Objectives
- **Aesthetic Premium Experience**: Redesign layout with custom navigation sidebar, unified tailwind spacing, and responsive interactive metrics.
- **Deep Repo Auditing**: Analyze commit velocity, author structures, tech debt ratios, and structural bottlenecks.
- **AI Technical Consultant**: Offload standard chat to a semantic RAG indexer that explains codebase syntax, handles AWS migration requests, and generates PR diffs.
- **Production Hardening**: Isolate workspace clones, limit API queries, and encrypt JWT session structures.
