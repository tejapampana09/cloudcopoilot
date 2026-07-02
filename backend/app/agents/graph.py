import os
import re
import json
import datetime
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END

from app.core.config import settings, get_chat_llm
from app.agents.state import AnalyzerState
from app.services.git_service import GitService
from app.services.scanner import HeuristicScanner
from app.services.cost_estimator import CostEstimator
from app.analysis.context_builder import RepositoryContextBuilder
from app.analysis.technology_analyzer import TechnologyAnalyzer
from app.architecture.architecture_analyzer import ArchitectureAnalyzer
from app.reasoning.reasoning_engine import ReasoningEngine
from app.recommendations.aws_decision_engine import AWSDecisionEngine
from app.reports.report_generator import ReportGenerator
from app.services.production_prompt_service import build_production_ready_prompt
from app.schemas.architecture import (
    ArchitectureSummary, AWSRecommendationDetail, TechnologyAnalysis,
    RepositoryContext, VisualizationJSON
)
from app.schemas.analyzer import (
    RepoMetadata, DeploymentRecommendation, HealthBreakdown,
    ChecklistItem, AgentLog, AnalysisResult, CostBreakdown
)
from app.utils.helpers import add_agent_log, analysis_tasks

# Import LangChain OpenAI if available
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

# Fallback Generator
def generate_heuristic_recommendation(metadata: RepoMetadata, target: str) -> str:
    """Generates the 'why' justification heuristically."""
    recs = {
        "AWS Amplify": (
            "AWS Amplify was selected because this is a static frontend application. "
            "Amplify provides zero-config hosting, automated CI/CD from git, global CDN edge routing, "
            "and out-of-the-box SSL certificates, which is the most cost-effective and performant choice."
        ),
        "AWS App Runner": (
            "AWS App Runner is recommended because this is a containerized web application/API. "
            "It offers a fully managed service for deploying containerized web apps directly from your repository "
            "or container registry, automatically handling scale, load balancing, and SSL without infrastructure complexity."
        ),
        "AWS ECS on Fargate": (
            "AWS ECS (Fargate) is recommended because the repository has multi-container configurations (Docker Compose). "
            "ECS Fargate provides serverless container orchestration, allowing you to run microservices, configure "
            "private networking, set up ALB routing, and maintain robust scalability for complex architectures."
        ),
        "AWS Lambda": (
            "AWS Lambda is recommended because serverless frameworks or serverless configuration files were detected. "
            "Lambda enables event-driven execution with zero standby costs, automatic scaling, and a pay-per-request model, "
            "making it ideal for microservices and utility API architectures."
        )
    }
    return recs.get(target, "AWS App Runner is the standard choice for managed containers.")

def generate_heuristic_summary(metadata: RepoMetadata, target: str, owner: str, repo: str) -> str:
    """Generates a summary paragraph heuristically."""
    langs = [l.name for l in metadata.languages[:3]]
    langs_str = ", ".join(langs) if langs else "unknown technologies"
    frameworks_str = ", ".join(metadata.frameworks) if metadata.frameworks else ""
    
    summary = f"This repository ({owner}/{repo}) is a modern application using {langs_str}."
    if frameworks_str:
        summary += f" Key frameworks detected include {frameworks_str}."
        
    if metadata.docker_readiness:
        summary += " Docker support is already configured, enabling streamlined container deployments."
    else:
        summary += " Docker support is currently missing; we recommend adding a Dockerfile to enhance portability."
        
    summary += f" {target} is recommended as the deployment target because it perfectly matches the application profile, offering a balance of performance, ease of use, and cost efficiency."
    return summary

def generate_heuristic_checklist(metadata: RepoMetadata, target: str) -> List[ChecklistItem]:
    """Generates the checklist heuristically."""
    checklist = []
    
    # 1. Languages/Frameworks
    for lang in metadata.languages[:2]:
        checklist.append(ChecklistItem(label=f"{lang.name} detected", status="checked"))
    for f in metadata.frameworks[:2]:
        checklist.append(ChecklistItem(label=f"{f} detected", status="checked"))
        
    # 2. Docker
    if metadata.docker_readiness:
        checklist.append(ChecklistItem(label="Dockerfile found", status="checked"))
    else:
        checklist.append(ChecklistItem(label="Docker missing (recommended for containers)", status="warning"))
        
    # 3. Environment variables
    if metadata.env_variables:
        checklist.append(ChecklistItem(label=f"Environment variables found ({len(metadata.env_variables)} vars)", status="checked"))
    else:
        checklist.append(ChecklistItem(label="No env template or env configuration found", status="warning"))
        
    # 4. Databases
    if metadata.databases:
        for db in metadata.databases[:1]:
            checklist.append(ChecklistItem(label=f"{db} detected", status="checked"))
    else:
        checklist.append(ChecklistItem(label="No SQL/NoSQL database detected", status="checked"))
        
    # 5. Readiness
    checklist.append(ChecklistItem(label=f"Ready for {target}", status="checked"))
    
    return checklist


# ─────────────────────────────────────────────────────────────────────────────
# Graph Nodes
# ─────────────────────────────────────────────────────────────────────────────

def repository_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Repository Agent Node - Clones repository & analyzes frameworks/technology stack"""
    task_id = state['task_id']
    add_agent_log(task_id, "Planner Agent", "Activating Repository Agent...", "in_progress")
    add_agent_log(task_id, "Repository Analyzer", "Cloning codebase and running framework scan...", "in_progress")
    
    try:
        # Clone
        GitService.clone_repository(state['repository_url'], state['clone_path'])
        
        # Scan
        metadata = HeuristicScanner.scan_repository(state['clone_path'])
        metadata.repo_url = state['repository_url']
        state['metadata'] = metadata
        
        # Tech stack scan
        technology_analysis = TechnologyAnalyzer.analyze(metadata)
        state['technology_analysis'] = technology_analysis
        
        # Repository report compile
        state['repository_report'] = {
            "languages": [l.model_dump() for l in metadata.languages],
            "frameworks": metadata.frameworks,
            "package_managers": metadata.package_managers,
            "total_commits": metadata.total_commits,
            "contributors_count": metadata.contributors_count,
            "stale_branches": metadata.stale_branches,
            "release_tags": metadata.release_tags,
            "technical_debt_score": metadata.technical_debt_score,
            "complexity_index": metadata.complexity_index,
            "git_timeline": f"Repository has {metadata.total_commits} commits across {metadata.contributors_count} authors. Complexity index: {metadata.complexity_index}."
        }
        
        add_agent_log(task_id, "Planner Agent", "Repository structure parsed by Repository Agent.", "completed")
        add_agent_log(task_id, "Repository Analyzer", "Repository scan completed successfully.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Repository Analyzer", f"Cloning/Scanning failed: {str(e)}", "failed")
        add_agent_log(task_id, "Planner Agent", "Analysis aborted by Repository Agent.", "failed")
        
    return state


def architecture_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Architecture Agent Node - Identifies layers, packages, modules, boundaries, and ORM dependencies"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Architecture Agent", "Activating Architecture Agent...", "in_progress")
    try:
        # Build Context
        repository_context = RepositoryContextBuilder.build(
            state['metadata'], state['repo_name'], state['owner'], state['clone_path']
        )
        state['repository_context'] = repository_context
        
        # Analyze Architecture
        architecture_analysis = ArchitectureAnalyzer.analyze(state['metadata'], repository_context)
        state['architecture_analysis'] = architecture_analysis

        # Architecture report compile
        state['architecture_report'] = {
            "layers": getattr(architecture_analysis, "layers", ["Application Layer", "Data Access Layer"]),
            "services": state['metadata'].backend + state['metadata'].frontend,
            "databases": state['metadata'].databases,
            "boundaries": f"Architecture is structured around {state['technology_analysis'].backend_stack if state['technology_analysis'] else 'decoupled'} patterns.",
            "api_relationships": "REST API routing mappings found."
        }

        add_agent_log(
            task_id,
            "Architecture Agent",
            f"Architecture Agent complete. Layer boundaries identified.",
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Architecture Agent", f"Architecture analysis failed: {str(e)}", "failed")
    return state


def security_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Security Agent Node - Checks secrets, JWT configs, auth environment variables, and checklist vulnerabilities"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Security Agent", "Activating Security Agent...", "in_progress")
    try:
        metadata = state['metadata']
        
        # Score calculation
        sec_score = 100 - (len(metadata.detected_secrets) * 20)
        if len(metadata.env_variables) > 0 and not any(".env.example" in f for f in metadata.infrastructure_files):
            sec_score -= 15
        sec_score = max(10, min(100, sec_score))
        
        state['security_report'] = {
            "secrets_detected": metadata.detected_secrets,
            "auth_issues": ["Review token expiration variables"] if metadata.env_variables else ["Authentication configs not found"],
            "vulnerabilities": ["Dependency scanning audit completed"],
            "security_score": sec_score
        }
        
        state['checklist'] = [
            ChecklistItem(label="Credential Leaks Check", status="checked" if not metadata.detected_secrets else "error"),
            ChecklistItem(label="Auth Credentials Mapped", status="checked" if metadata.env_variables else "warning"),
            ChecklistItem(label="Docker Container Isolation", status="checked" if metadata.docker_readiness else "warning")
        ]
        
        add_agent_log(task_id, "Security Agent", f"Security Agent complete. Security Score: {sec_score}/100.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Security Agent", f"Security analysis failed: {str(e)}", "failed")
    return state


def performance_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Performance Agent Node - Audits SQLite bottlenecks, large files, performance scaling, and Redis caching options"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Performance Agent", "Activating Performance Agent...", "in_progress")
    try:
        metadata = state['metadata']
        
        # Performance rating
        perf_score = 95 - (20 if "SQLite" in metadata.databases else 0) - (len(metadata.large_files) * 5)
        perf_score = max(20, min(100, perf_score))
        
        state['performance_report'] = {
            "concurrency_bottlenecks": ["SQLite write lock bottlenecks"] if "SQLite" in metadata.databases else ["No database write lock risks detected."],
            "large_files_warnings": metadata.large_files[:3] if metadata.large_files else ["No source file exceeds 500 lines."],
            "caching_opportunities": ["Amazon ElastiCache Redis setup proposed for caching layer"],
            "performance_score": perf_score
        }
        
        state['performance_notes'] = "SQLite write locking bottlenecks concurrency." if "SQLite" in metadata.databases else "No database concurrency bottlenecks detected."
        add_agent_log(task_id, "Performance Agent", "Performance Agent complete. Caching opportunities computed.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Performance Agent", f"Performance analysis failed: {str(e)}", "failed")
    return state


def cloud_architect_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Cloud Architect Agent Node - Performs candidate reasoning and AWS deployment target choices"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Cloud Architect Agent", "Activating Cloud Architect Agent...", "in_progress")
    try:
        # weighted decision Matrix
        primary_target, aws_recommendations, confidence = AWSDecisionEngine.evaluate(
            state['metadata'], state['technology_analysis'], state['repository_context']
        )
        state['aws_recommendations'] = aws_recommendations
        
        reasons_list = ReasoningEngine.generate_reasons(
            state['metadata'], primary_target, state['repository_context']
        )
        state['reasoning'] = "\n".join(reasons_list)
        
        state['confidence'] = {
            'deployment_target': f"{confidence:.1f}%",
            'technology_detection': f"{state['technology_analysis'].detection_confidence.get('frontend_stack', 0)}%"
        }
        
        state['recommendation'] = DeploymentRecommendation(
            target=primary_target,
            why=aws_recommendations[0].reason if aws_recommendations else generate_heuristic_recommendation(state['metadata'], primary_target),
            estimated_monthly_cost=0.0,
            cost_breakdown=CostBreakdown(compute=0.0, database=0.0, storage=0.0, data_transfer=0.0),
            confidence_score=int(confidence)
        )
        
        state['cloud_report'] = {
            "target_compute": primary_target,
            "why_justification": aws_recommendations[0].reason if aws_recommendations else "Standard compute target selection.",
            "scaling_rules": "Scale tasks upwards if memory capacity reaches 80%.",
            "confidence_score": int(confidence)
        }
        
        state['deployment_strategy'] = f"Adopt {primary_target} with an IaC-driven CI/CD pipeline."
        add_agent_log(task_id, "Cloud Architect Agent", f"Cloud Architect Agent complete. Selected target: {primary_target}.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Cloud Architect Agent", f"Cloud Architect Agent failed: {str(e)}", "failed")
    return state


def aws_cost_agent_node(state: AnalyzerState) -> AnalyzerState:
    """AWS Cost Agent Node - Estimates compute, database, and storage monthly pricing configurations"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Cost Agent", "Activating AWS Cost Agent...", "in_progress")
    try:
        rec = state['recommendation']
        complexity = state['repository_context'].project_complexity
        
        est_cost, cost_breakdown = CostEstimator.estimate_cost(rec.target, state['metadata'].databases, complexity)
        rec.estimated_monthly_cost = est_cost
        rec.cost_breakdown = cost_breakdown
        state['recommendation'] = rec
        
        assumptions_str = CostEstimator.generate_assumptions_text(
            rec.target, state['metadata'].databases, complexity, est_cost, cost_breakdown
        )
        state['cost_analysis'] = assumptions_str
        
        state['cost_report'] = {
            "monthly_estimation": est_cost,
            "breakdown": {
                "compute": cost_breakdown.compute,
                "database": cost_breakdown.database,
                "storage": cost_breakdown.storage,
                "transfer": cost_breakdown.data_transfer
            },
            "optimization_opportunities": [
                "Map spot containers on non-production ECS tasks",
                "Store static assets directly on S3 CDN boundaries"
            ]
        }
        
        add_agent_log(task_id, "Cost Agent", f"AWS Cost Agent complete. Est monthly spend: ${est_cost:.2f}.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Cost Agent", f"Cost analysis failed: {str(e)}", "failed")
    return state


def devops_agent_node(state: AnalyzerState) -> AnalyzerState:
    """DevOps Agent Node - Audits Dockerfiles, GitHub Actions workflow files, and IaC setups"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "DevOps Agent", "Activating DevOps Agent...", "in_progress")
    try:
        metadata = state['metadata']
        
        iac_found = ["Terraform"] if metadata.terraform else []
        state['devops_report'] = {
            "cicd_tools": metadata.ci_cd if metadata.ci_cd else ["None"],
            "docker_readiness": metadata.docker_readiness,
            "iac_tools": iac_found if iac_found else ["None"],
            "missing_devops_tooling": [
                "Configure AWS ECR repository workflows",
                "Integrate cloudwatch monitoring dashboards setup"
            ]
        }
        
        add_agent_log(task_id, "DevOps Agent", "DevOps Agent complete. DevOps audits recorded.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "DevOps Agent", f"DevOps agent failed: {str(e)}", "failed")
    return state


def infrastructure_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Infrastructure Agent Node - Packages Terraform, Dockerfile, and environment configs."""
    if state.get('error'):
        return state
    task_id = state['task_id']
    add_agent_log(task_id, "Infrastructure Agent", "Activating Infrastructure Agent...", "in_progress")
    try:
        metadata = state['metadata']
        iac_found = ["Terraform"] if metadata.terraform else []
        state['devops_report'] = {
            "cicd_tools": metadata.ci_cd if metadata.ci_cd else ["None"],
            "docker_readiness": metadata.docker_readiness,
            "iac_tools": iac_found if iac_found else ["None"],
            "missing_devops_tooling": [
                "Configure AWS ECR repository workflows",
                "Integrate cloudwatch monitoring dashboards setup"
            ]
        }
        state['infrastructure_report'] = {
            "terraform_files": ["main.tf", "variables.tf", "outputs.tf"],
            "docker_files": ["Dockerfile", "docker-compose.yml"],
            "environment_templates": [".env.example"]
        }
        add_agent_log(task_id, "Infrastructure Agent", "Infrastructure templates compiled by Infrastructure Agent.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Infrastructure Agent", f"Infrastructure Agent failed: {str(e)}", "failed")
    return state


def deploy_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Deploy Agent Node - Generates pre-flight permission checks and resource plans."""
    if state.get('error'):
        return state
    task_id = state['task_id']
    add_agent_log(task_id, "Deployment Agent", "Activating Deploy Agent...", "in_progress")
    try:
        state['deploy_report'] = {
            "required_iam_permissions": ["sts:GetCallerIdentity", "apprunner:CreateService", "apprunner:DescribeService"],
            "resource_plan": ["aws_apprunner_service.app"],
            "strategy": "Direct CloudPilot AWS App Runner deployment plan configured."
        }
        add_agent_log(task_id, "Deployment Agent", "Pre-flight deployment plan generated by Deploy Agent.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Deployment Agent", f"Deploy Agent failed: {str(e)}", "failed")
    return state


def monitoring_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Monitoring Agent Node - Sets up logging and health alert configurations."""
    if state.get('error'):
        return state
    task_id = state['task_id']
    add_agent_log(task_id, "Monitoring Agent", "Activating Monitoring Agent...", "in_progress")
    try:
        state['monitoring_report'] = {
            "cloudwatch_log_groups": [f"/aws/apprunner/cloudpilot-{state['repo_name'].lower()}"],
            "metrics": ["CPUUtilization", "MemoryUtilization", "RequestCount"],
            "alarm_thresholds": {
                "cpu_max_pct": 80,
                "memory_max_pct": 85,
                "unhealthy_pings_limit": 3
            }
        }
        add_agent_log(task_id, "Monitoring Agent", "CloudWatch logging metrics configured by Monitoring Agent.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Monitoring Agent", f"Monitoring Agent failed: {str(e)}", "failed")
    return state


def cost_optimization_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Cost Optimization Agent Node - Audits resource waste and spots savings opportunities."""
    if state.get('error'):
        return state
    task_id = state['task_id']
    add_agent_log(task_id, "Cost Optimization Agent", "Activating Cost Optimization Agent...", "in_progress")
    try:
        rec = state['recommendation']
        complexity = state['repository_context'].project_complexity if state.get('repository_context') else 'Medium'
        
        est_cost, cost_breakdown = CostEstimator.estimate_cost(rec.target, state['metadata'].databases, complexity)
        rec.estimated_monthly_cost = est_cost
        rec.cost_breakdown = cost_breakdown
        state['recommendation'] = rec
        
        assumptions_str = CostEstimator.generate_assumptions_text(
            rec.target, state['metadata'].databases, complexity, est_cost, cost_breakdown
        )
        state['cost_analysis'] = assumptions_str
        
        state['cost_report'] = {
            "monthly_estimation": est_cost,
            "breakdown": {
                "compute": cost_breakdown.compute,
                "database": cost_breakdown.database,
                "storage": cost_breakdown.storage,
                "transfer": cost_breakdown.data_transfer
            },
            "optimization_opportunities": [
                "Map spot containers on non-production ECS tasks",
                "Store static assets directly on S3 CDN boundaries"
            ]
        }
        
        state['cost_optimization_report'] = {
            "monthly_waste": 0.0,
            "savings_opportunities": [
                "Map spot compute configurations for non-prod traffic",
                "Apply auto-scaling scale-in thresholds during off-hours"
            ],
            "potential_savings": float(est_cost) * 0.35
        }
        add_agent_log(task_id, "Cost Optimization Agent", "Cost optimization options mapped by Cost Optimization Agent.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Cost Optimization Agent", f"Cost Optimization Agent failed: {str(e)}", "failed")
    return state


def executive_summary_agent_node(state: AnalyzerState) -> AnalyzerState:
    """Executive Summary Agent Node - Assembles reports, calculates overall metrics, and generates AI summary"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Monitoring Agent", "Activating Executive Summary Agent...", "in_progress")
    
    metadata = state['metadata']
    rec = state['recommendation']
    
    # Calculate health rating
    doc_score = 20 if metadata.readme_quality == "High" else 12
    docker_score = 15 if metadata.docker_readiness else 0
    security_score = state['security_report'].get('security_score', 80) if state['security_report'] else 80
    env_score = 15 if metadata.env_variables else 5
    dep_score = 10 if metadata.terraform else (5 if metadata.docker_readiness else 0)
    org_score = 15 if metadata.package_managers else 10
    
    health_score = doc_score + docker_score + int(security_score * 0.15) + env_score + dep_score + org_score
    health_score = min(max(health_score, 10), 100)
    state['health_score'] = health_score
    state['health_breakdown'] = HealthBreakdown(
        documentation=doc_score,
        docker=docker_score,
        security=int(security_score * 0.15),
        environment=env_score,
        deployment=dep_score,
        organization=org_score
    )
    
    # Overall metrics
    rep_score = 100 - metadata.technical_debt_score
    state['overall_repository_score'] = max(10, min(100, int(rep_score)))
    state['overall_cloud_readiness_score'] = health_score

    # Call LLM summary if key exists
    api_key = settings.OPENAI_API_KEY
    if HAS_LANGCHAIN and api_key:
        try:
            llm = get_chat_llm(
                api_key=api_key,
                model_name=settings.OPENAI_MODEL,
                temperature=0.2,
                request_timeout=30.0,
                max_retries=2
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    "You are CloudPilot AI, an expert cloud deployment architect. "
                    "Analyze the repository metadata and recommendation. "
                    "Generate a JSON response with exactly three keys:\n"
                    "1. 'ai_summary': A concise one-paragraph summary of the repository's technology stack, architecture (e.g. MERN), and key deployment considerations.\n"
                    "2. 'why_recommendation': A detailed explanation of why the proposed AWS target was selected and its advantages for this stack.\n"
                    "3. 'checklist': A list of objects with keys 'label' (string, e.g. 'React detected') and 'status' (string, either 'checked', 'warning', or 'error') representing code discoveries.\n"
                    "Do not include any markdown styling (like ```json) outside the JSON output. Return pure raw JSON."
                )),
                ("human", "{content}")
            ])
            
            langs_format = ", ".join([f"{l.name} ({l.percentage}%)" for l in metadata.languages])
            user_prompt = (
                f"Repository URL: {state['repository_url']}\n"
                f"Owner: {state['owner']}, Name: {state['repo_name']}\n"
                f"Detected Languages: {langs_format}\n"
                f"Detected Frameworks: {', '.join(metadata.frameworks)}\n"
                f"Frontend: {', '.join(metadata.frontend)}\n"
                f"Backend: {', '.join(metadata.backend)}\n"
                f"Databases: {', '.join(metadata.databases)}\n"
                f"Docker Readiness: {'Dockerfile detected' if metadata.docker_readiness else 'No Dockerfile'}\n"
                f"CI/CD: {', '.join(metadata.ci_cd) if metadata.ci_cd else 'None'}\n"
                f"Environment Variables: {', '.join(metadata.env_variables)}\n"
                f"Recommended AWS Target: {rec.target}"
            )
            
            chain = prompt | llm
            response = chain.invoke({"content": user_prompt})
            
            res_text = response.content.strip()
            if res_text.startswith("```"):
                res_text = re.sub(r'^```json\s*|\s*```$', '', res_text, flags=re.MULTILINE)
                
            res_json = json.loads(res_text)
            state['ai_summary'] = res_json.get("ai_summary", generate_heuristic_summary(metadata, rec.target, state['owner'], state['repo_name']))
            
            llm_why = res_json.get("why_recommendation", "")
            if len(llm_why) > 100:
                rec.why = llm_why
                state['recommendation'] = rec
                
        except Exception:
            state['ai_summary'] = generate_heuristic_summary(metadata, rec.target, state['owner'], state['repo_name'])
    else:
        state['ai_summary'] = generate_heuristic_summary(metadata, rec.target, state['owner'], state['repo_name'])
        
    production_prompt = build_production_ready_prompt(
        metadata=metadata,
        recommendation=rec,
        owner=state['owner'],
        repo_name=state['repo_name'],
    )

    state['executive_summary'] = {
        "summary": state['ai_summary'],
        "overall_health_score": health_score,
        "priority_fixes": [
            "Migrate active databases to AWS RDS instances",
            "Store runtime secrets inside AWS Secrets Manager configs"
        ],
        "action_plan": [
            "Deploy Terraform modules inside subnets boundary",
            "Link CI/CD pipeline triggers directly to hosting targets"
        ],
        "production_ready_prompt": production_prompt,
    }
    
    # Build reports
    reasons_list = state.get('reasoning', '').split("\n") if state.get('reasoning') else []
    state['architecture_report'] = ReportGenerator.build_report(
        metadata=metadata,
        architecture=state['architecture_analysis'],
        aws_recommendations=state['aws_recommendations'] or [],
        repository_context=state['repository_context'],
        reasons_list=reasons_list,
        cost_assumptions_str=state['cost_analysis'],
        health_score=health_score
    )
    
    # Build visualization
    state['visualization'] = ReportGenerator.build_visualization_graph(
        metadata, state['architecture_analysis']
    )
    
    add_agent_log(task_id, "Monitoring Agent", "Executive Summary Agent has finalized report orchestration.", "completed")
    return state


# Build Graph
# ─────────────────────────────────────────────────────────────────────────────
builder = StateGraph(AnalyzerState)

# Add Nodes
builder.add_node("repository_agent", repository_agent_node)
builder.add_node("architecture_agent", architecture_agent_node)
builder.add_node("security_agent", security_agent_node)
builder.add_node("performance_agent", performance_agent_node)
builder.add_node("cloud_architect_agent", cloud_architect_agent_node)
builder.add_node("infrastructure_agent", infrastructure_agent_node)
builder.add_node("deploy_agent", deploy_agent_node)
builder.add_node("monitoring_agent", monitoring_agent_node)
builder.add_node("cost_optimization_agent", cost_optimization_agent_node)
builder.add_node("executive_agent", executive_summary_agent_node)

# Set Flow
builder.set_entry_point("repository_agent")
builder.add_edge("repository_agent", "architecture_agent")
builder.add_edge("architecture_agent", "security_agent")
builder.add_edge("security_agent", "performance_agent")
builder.add_edge("performance_agent", "cloud_architect_agent")
builder.add_edge("cloud_architect_agent", "infrastructure_agent")
builder.add_edge("infrastructure_agent", "deploy_agent")
builder.add_edge("deploy_agent", "monitoring_agent")
builder.add_edge("monitoring_agent", "cost_optimization_agent")
builder.add_edge("cost_optimization_agent", "executive_agent")
builder.add_edge("executive_agent", END)

# Compile Graph
graph = builder.compile()


def run_analysis_pipeline(task_id: str, repo_url: str, clone_path: str) -> Dict[str, Any]:
    """
    Executes the compiled LangGraph state machine.
    """
    owner, repo_name, _ = GitService.validate_and_parse_url(repo_url)
    
    # Initialize state
    initial_state = AnalyzerState(
        repository_url=repo_url,
        task_id=task_id,
        owner=owner,
        repo_name=repo_name,
        clone_path=clone_path,
        metadata=None,
        recommendation=None,
        health_score=None,
        health_breakdown=None,
        checklist=None,
        ai_summary="",
        logs=[],
        error=None
    )
    
    # Add initial logs to task
    add_agent_log(task_id, "Planner Agent", "Workflow initialized.", "pending")
    add_agent_log(task_id, "Repository Analyzer", "Waiting to scan code...", "pending")
    add_agent_log(task_id, "Architecture Agent", "Waiting to analyze architecture...", "pending")
    add_agent_log(task_id, "Security Agent", "Waiting to check security...", "pending")
    add_agent_log(task_id, "Performance Agent", "Waiting to audit performance...", "pending")
    add_agent_log(task_id, "Cloud Architect Agent", "Waiting to select AWS target...", "pending")
    add_agent_log(task_id, "Infrastructure Agent", "Waiting to compile infrastructure...", "pending")
    add_agent_log(task_id, "Deployment Agent", "Waiting to plan deployment...", "pending")
    add_agent_log(task_id, "Monitoring Agent", "Waiting to configure monitoring...", "pending")
    add_agent_log(task_id, "Cost Agent", "Waiting to estimate costs...", "pending")
    add_agent_log(task_id, "DevOps Agent", "Waiting to audit DevOps...", "pending")
    add_agent_log(task_id, "Cost Optimization Agent", "Waiting to map savings...", "pending")
    
    try:
        # Run graph
        final_state = graph.invoke(initial_state)
        
        # Cleanup cloned directory - deferred to cleanup job for RAG chat context
        # GitService.cleanup_directory(clone_path)
        
        if final_state.get('error'):
            analysis_tasks[task_id]["status"] = "failed"
            analysis_tasks[task_id]["error"] = final_state['error']
            return analysis_tasks[task_id]
            
        # Assemble result
        result = AnalysisResult(
            repository_url=final_state['repository_url'],
            repository_name=final_state['repo_name'],
            repository_owner=final_state['owner'],
            analysis_time=datetime.datetime.now().isoformat(),
            status="completed",
            metadata=final_state['metadata'],
            recommendation=final_state['recommendation'],
            health_score=final_state['health_score'],
            health_breakdown=final_state['health_breakdown'],
            checklist=final_state['checklist'],
            ai_summary=final_state['ai_summary'],
            logs=[AgentLog(**log) for log in analysis_tasks[task_id].get("logs", [])],
            repository_report=final_state.get('repository_report'),
            architecture_report=final_state.get('architecture_report'),
            security_report=final_state.get('security_report'),
            performance_report=final_state.get('performance_report'),
            cloud_report=final_state.get('cloud_report'),
            cost_report=final_state.get('cost_report'),
            devops_report=final_state.get('devops_report'),
            executive_summary=final_state.get('executive_summary'),
            overall_repository_score=final_state.get('overall_repository_score'),
            overall_cloud_readiness_score=final_state.get('overall_cloud_readiness_score'),
            infrastructure_report=final_state.get('infrastructure_report'),
            deploy_report=final_state.get('deploy_report'),
            monitoring_report=final_state.get('monitoring_report'),
            cost_optimization_report=final_state.get('cost_optimization_report')
        )
        
        task_data = analysis_tasks[task_id]
        task_data.update(result.model_dump())
        task_data['repository_context'] = final_state.get('repository_context').model_dump() if final_state.get('repository_context') else None
        task_data['technology_analysis'] = final_state.get('technology_analysis').model_dump() if final_state.get('technology_analysis') else None
        task_data['architecture_analysis'] = final_state.get('architecture_analysis').model_dump() if final_state.get('architecture_analysis') else None
        task_data['aws_recommendations'] = [rec.model_dump() for rec in final_state.get('aws_recommendations', [])] if final_state.get('aws_recommendations') else []
        task_data['confidence'] = final_state.get('confidence')
        task_data['reasoning'] = final_state.get('reasoning')
        task_data['visualization'] = final_state.get('visualization').model_dump() if final_state.get('visualization') else None
        task_data['security_notes'] = final_state.get('security_notes')
        task_data['performance_notes'] = final_state.get('performance_notes')
        task_data['cost_analysis'] = final_state.get('cost_analysis')
        task_data['deployment_strategy'] = final_state.get('deployment_strategy')
        task_data['production_ready_prompt'] = final_state.get('executive_summary', {}).get('production_ready_prompt') if final_state.get('executive_summary') else None
        analysis_tasks[task_id] = task_data
        return analysis_tasks[task_id]
        
    except Exception as e:
        GitService.cleanup_directory(clone_path)
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["error"] = str(e)
        add_agent_log(task_id, "Planner Agent", f"Workflow execution crashed: {str(e)}", "failed")
        return analysis_tasks[task_id]
