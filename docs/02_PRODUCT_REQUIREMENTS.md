# CloudPilot AI — Product Requirements Document (PRD)

## 1. Product Overview
CloudPilot V2 is an enterprise-grade web application that scans public or private GitHub repositories, assesses cloud readiness, generates dynamic cost estimates, recommends AWS services using a weighted decision matrix, and writes Terraform IaC configuration code.

---

## 2. Target Audience
- **DevOps & Solutions Architects**: Seeking rapid, automated baseline architecture layouts and IaC templates.
- **Engineering Leads & CTOs**: Reviewing repository complexity, technical debt, and estimated AWS operational costs.
- **Software Engineers**: Deploying applications without manual AWS console configuration.

---

## 3. Functional Requirements

### 3.1 Premium UI/UX Redesign
- **Design System Consistency**: A curated dark-mode theme utilizing Tailwind configurations, uniform spacings, and glassmorphic card panels.
- **Sidebar & Navigation**: Collapsible left sidebar navigation supporting routing between Dashboard, Deployments, Resources, Cost Analyzer, Security Scanner, and Settings.
- **AI Execution Timeline**: A vertical timeline showing streamed agent logs in real time, with step-by-step progress and status badges.
- **Interactive Reports UI**: A multi-tab dashboard displaying:
  - *Overview*: Repository metrics, readiness score, and summary paragraph.
  - *AWS Topology*: Interactive visualization node graph.
  - *Cost Strategy*: Traffic-tier adjustment sliders and detailed cost breakdowns.
  - *Blueprints*: Downloadable zip package of Terraform files.

### 3.2 AI Technical Consultant (Expanded Repository Chat)
- **Repository Q&A**: Semantic search capabilities allowing users to chat directly with their repository.
- **Code Explanations**: Explain architecture boundaries, individual files, and functions.
- **Refactoring & PRs**: Generate PR diffs, bug fixes, and suggest AWS migration strategies directly in the chat panel.

### 3.3 Deep Repository Intelligence
- **Git Analytics**: Parse git log to map commit count history, author activities, and hot-spot files.
- **Repo Health Card**: Compile technical debt audits and complexity indexes (Low, Medium, High).

### 3.4 Advanced Cloud Intelligence & Exporting
- **Terraform IaC**: Generate production-ready VPC, compute (App Runner/ECS/Lambda), database (RDS), and security configs.
- **Executive PDF Export**: Compile the SOLUTIONS ARCHITECT REPORT into downloadable PDF, DOCX, and Markdown documents.

---

## 4. Non-Functional Requirements
- **Lighthouse Performance**: Target score `>95` on audits by optimizing client asset bundles.
- **Scan Latency**: Complete full scans and decision matrix pipelines in `<45 seconds`.
- **Security Hardening**: Session tokens must expire in 24 hours. Run directory audits safely without shell escaping vulnerability vectors.
- **Responsiveness**: Support fluid grid scaling on Mobile, Tablet, and Desktop layouts.
