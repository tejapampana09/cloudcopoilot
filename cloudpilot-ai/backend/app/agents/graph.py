import os
import json
import datetime
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END

from app.core.config import settings
from app.agents.state import AnalyzerState
from app.services.git_service import GitService
from app.services.scanner import HeuristicScanner
from app.services.cost_estimator import CostEstimator
from app.schemas.analyzer import (
    RepoMetadata, DeploymentRecommendation, HealthBreakdown,
    ChecklistItem, AgentLog, AnalysisResult
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
        "AWS ECS": (
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

# Graph Nodes
def clone_and_scan_node(state: AnalyzerState) -> AnalyzerState:
    task_id = state['task_id']
    add_agent_log(task_id, "Planner Agent", "Analyzing repository url...", "in_progress")
    add_agent_log(task_id, "Repository Analyzer", "Cloning and scanning repository...", "pending")
    
    try:
        # Clone
        add_agent_log(task_id, "Planner Agent", f"Initiating shallow clone of {state['repository_url']}...", "in_progress")
        GitService.clone_repository(state['repository_url'], state['clone_path'])
        
        # Scan
        add_agent_log(task_id, "Repository Analyzer", "Repository cloned. Running heuristic file scanner...", "in_progress")
        metadata = HeuristicScanner.scan_repository(state['clone_path'])
        
        state['metadata'] = metadata
        
        add_agent_log(task_id, "Planner Agent", "Repository structure parsed.", "completed")
        add_agent_log(task_id, "Repository Analyzer", "Repository scan completed successfully.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Repository Analyzer", f"Cloning/Scanning failed: {str(e)}", "failed")
        add_agent_log(task_id, "Planner Agent", "Analysis aborted due to clone errors.", "failed")
        
    return state

def analyze_architecture_node(state: AnalyzerState) -> AnalyzerState:
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Infrastructure Agent", "Analyzing application architecture...", "in_progress")
    
    # Simulate architecture mapping
    # (In dynamic run, this analyzes frontend vs backend folder splits, package dependencies)
    metadata = state['metadata']
    
    arch_type = "Monolith"
    if metadata.frontend and metadata.backend:
        arch_type = "Fullstack (Frontend + Backend)"
    elif metadata.frontend:
        arch_type = "Static Frontend"
    elif metadata.backend:
        arch_type = "Backend Service/API"
        
    add_agent_log(task_id, "Infrastructure Agent", f"Architecture layout mapped: {arch_type}.", "completed")
    return state

def generate_recommendations_node(state: AnalyzerState) -> AnalyzerState:
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Infrastructure Agent", "Determining AWS deployment recommendations...", "in_progress")
    
    metadata = state['metadata']
    
    # 1. Determine recommended target
    # - If terraform/cdk only, or serverless: AWS Lambda
    # - If Dockerfile present + docker-compose or multi frameworks: AWS ECS
    # - If static only (React, Vue, Svelte, static Next config without backend): AWS Amplify
    # - Otherwise (Standard backend/frontend dockerized, Python/Node without docker): AWS App Runner
    target = "AWS App Runner"
    confidence = 80
    
    is_static = len(metadata.frontend) > 0 and len(metadata.backend) == 0
    is_serverless = "serverless" in "".join(metadata.infrastructure_files).lower()
    
    if is_static:
        target = "AWS Amplify"
        confidence = 90
    elif metadata.docker_compose:
        target = "AWS ECS"
        confidence = 85
    elif is_serverless:
        target = "AWS Lambda"
        confidence = 88
    else:
        # Default container/managed runtime
        target = "AWS App Runner"
        if metadata.docker_readiness:
            confidence = 95
        else:
            confidence = 80
            
    # 2. Cost Estimate
    est_cost, cost_breakdown = CostEstimator.estimate_cost(target, metadata.databases)
    
    # 3. Write Recommendation placeholder (will enrich in next node or keep if heuristic)
    state['recommendation'] = DeploymentRecommendation(
        target=target,
        why=generate_heuristic_recommendation(metadata, target),
        estimated_monthly_cost=est_cost,
        cost_breakdown=cost_breakdown,
        confidence_score=confidence
    )
    
    add_agent_log(task_id, "Infrastructure Agent", f"Target determined: {target} (Confidence: {confidence}%).", "completed")
    return state

def assess_health_node(state: AnalyzerState) -> AnalyzerState:
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Deployment Agent", "Assessing repository quality and cloud readiness...", "in_progress")
    
    metadata = state['metadata']
    
    # Rubric:
    # 1. Documentation: max 20
    doc_score = 0
    if metadata.readme_quality == "High":
        doc_score = 20
    elif metadata.readme_quality == "Medium":
        doc_score = 15
    else:
        doc_score = 8
        
    # 2. Docker: max 20
    docker_score = 0
    if metadata.docker_readiness:
        docker_score += 15
    if metadata.docker_compose:
        docker_score += 5
        
    # 3. Security: max 15
    security_score = 15
    # Heuristic: subtract if any API keys/secrets are in codebase
    # For Phase 1 we give high score if .env.example exists, subtract if .env file is actually committed
    if not any(".env.example" in f for f in metadata.infrastructure_files) and len(metadata.env_variables) > 0:
        security_score -= 5
        
    # 4. Environment: max 15
    env_score = 5
    if metadata.env_variables:
        env_score = 15
        
    # 5. Deployment: max 15
    dep_score = 0
    if metadata.ci_cd:
        dep_score += 5
    if metadata.terraform:
        dep_score += 10
    elif metadata.docker_readiness:
        dep_score += 5
        
    # 6. Organization: max 15
    org_score = 10
    if metadata.package_managers:
        org_score += 5
        
    health_score = doc_score + docker_score + security_score + env_score + dep_score + org_score
    health_score = min(max(health_score, 0), 100) # Clamp between 0 and 100
    
    state['health_score'] = health_score
    state['health_breakdown'] = HealthBreakdown(
        documentation=doc_score,
        docker=docker_score,
        security=security_score,
        environment=env_score,
        deployment=dep_score,
        organization=org_score
    )
    
    add_agent_log(task_id, "Deployment Agent", f"Repository cloud readiness assessed. Score: {health_score}/100.", "completed")
    return state

def generate_ai_summary_node(state: AnalyzerState) -> AnalyzerState:
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Monitoring Agent", "Generating AI deployment summary...", "in_progress")
    
    metadata = state['metadata']
    rec = state['recommendation']
    
    # 1. Run LLM if API Key is present
    api_key = settings.OPENAI_API_KEY
    if HAS_LANGCHAIN and api_key:
        try:
            llm = ChatOpenAI(
                api_key=api_key,
                model_name=settings.OPENAI_MODEL,
                temperature=0.2
            )
            
            # Formulate the payload data
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
                ("human", (
                    "Repository URL: {repo_url}\n"
                    "Owner: {owner}, Name: {repo_name}\n"
                    "Detected Languages: {languages}\n"
                    "Detected Frameworks: {frameworks}\n"
                    "Frontend: {frontend}\n"
                    "Backend: {backend}\n"
                    "Databases: {databases}\n"
                    "Docker Readiness: {docker}\n"
                    "CI/CD: {ci_cd}\n"
                    "Environment Variables: {env_vars}\n"
                    "Recommended AWS Target: {target}"
                ))
            ])
            
            chain = prompt | llm
            
            # Format inputs
            langs_format = ", ".join([f"{l.name} ({l.percentage}%)" for l in metadata.languages])
            response = chain.invoke({
                "repo_url": state['repository_url'],
                "owner": state['owner'],
                "repo_name": state['repo_name'],
                "languages": langs_format,
                "frameworks": ", ".join(metadata.frameworks),
                "frontend": ", ".join(metadata.frontend),
                "backend": ", ".join(metadata.backend),
                "databases": ", ".join(metadata.databases),
                "docker": "Dockerfile detected" if metadata.docker_readiness else "No Dockerfile",
                "ci_cd": ", ".join(metadata.ci_cd) if metadata.ci_cd else "None",
                "env_vars": ", ".join(metadata.env_variables),
                "target": rec.target
            })
            
            # Parse response
            res_text = response.content.strip()
            # Clean up potential markdown backticks block
            if res_text.startswith("```"):
                res_text = re.sub(r'^```json\s*|\s*```$', '', res_text, flags=re.MULTILINE)
                
            res_json = json.loads(res_text)
            
            state['ai_summary'] = res_json.get("ai_summary", generate_heuristic_summary(metadata, rec.target, state['owner'], state['repo_name']))
            rec.why = res_json.get("why_recommendation", rec.why)
            state['recommendation'] = rec
            
            checklist_data = res_json.get("checklist", [])
            checklist_items = []
            for item in checklist_data:
                checklist_items.append(ChecklistItem(
                    label=item.get("label", ""),
                    status=item.get("status", "checked")
                ))
            state['checklist'] = checklist_items if checklist_items else generate_heuristic_checklist(metadata, rec.target)
            
            add_agent_log(task_id, "Monitoring Agent", "AI deployment summary generated via OpenAI.", "completed")
            return state
        except Exception as e:
            # Fallback to heuristics on LLM error
            pass
            
    # Fallback / No LLM configuration
    state['ai_summary'] = generate_heuristic_summary(metadata, rec.target, state['owner'], state['repo_name'])
    state['checklist'] = generate_heuristic_checklist(metadata, rec.target)
    
    add_agent_log(task_id, "Monitoring Agent", "AI deployment summary generated via heuristic engine.", "completed")
    return state


# Build Graph
builder = StateGraph(AnalyzerState)

# Add Nodes
builder.add_node("clone_and_scan", clone_and_scan_node)
builder.add_node("analyze_architecture", analyze_architecture_node)
builder.add_node("generate_recommendations", generate_recommendations_node)
builder.add_node("assess_health", assess_health_node)
builder.add_node("generate_ai_summary", generate_ai_summary_node)

# Set Flow
builder.set_entry_point("clone_and_scan")
builder.add_edge("clone_and_scan", "analyze_architecture")
builder.add_edge("analyze_architecture", "generate_recommendations")
builder.add_edge("generate_recommendations", "assess_health")
builder.add_edge("assess_health", "generate_ai_summary")
builder.add_edge("generate_ai_summary", END)

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
    add_agent_log(task_id, "Infrastructure Agent", "Waiting to analyze infrastructure...", "pending")
    add_agent_log(task_id, "Deployment Agent", "Waiting to assess deployment readiness...", "pending")
    add_agent_log(task_id, "Monitoring Agent", "Waiting to summarize...", "pending")
    
    try:
        # Run graph
        final_state = graph.invoke(initial_state)
        
        # Cleanup cloned directory
        GitService.cleanup_directory(clone_path)
        
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
            logs=[AgentLog(**log) for log in analysis_tasks[task_id].get("logs", [])]
        )
        
        # Update datastore
        analysis_tasks[task_id].update(result.model_dump())
        return analysis_tasks[task_id]
        
    except Exception as e:
        GitService.cleanup_directory(clone_path)
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["error"] = str(e)
        add_agent_log(task_id, "Planner Agent", f"Workflow execution crashed: {str(e)}", "failed")
        return analysis_tasks[task_id]
