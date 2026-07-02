import os
import re
import json
import datetime
from typing import List, Dict, Any
from langgraph.graph import StateGraph, END

from app.core.config import settings
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

def clone_and_scan_node(state: AnalyzerState) -> AnalyzerState:
    """Repository Analysis Node"""
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
        metadata.repo_url = state['repository_url']
        
        state['metadata'] = metadata
        
        add_agent_log(task_id, "Planner Agent", "Repository structure parsed.", "completed")
        add_agent_log(task_id, "Repository Analyzer", "Repository scan completed successfully.", "completed")
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Repository Analyzer", f"Cloning/Scanning failed: {str(e)}", "failed")
        add_agent_log(task_id, "Planner Agent", "Analysis aborted due to clone errors.", "failed")
        
    return state


def technology_analysis_node(state: AnalyzerState) -> AnalyzerState:
    """Technology Analysis Node"""
    if state.get('error'):
        return state

    task_id = state['task_id']
    add_agent_log(task_id, "Repository Analyzer", "Analyzing technology stack and frameworks...", "in_progress")
    try:
        technology_analysis = TechnologyAnalyzer.analyze(state['metadata'])
        state['technology_analysis'] = technology_analysis
        
        add_agent_log(
            task_id,
            "Repository Analyzer",
            f"Detected Stack: Frontend={technology_analysis.frontend_stack}, Backend={technology_analysis.backend_stack}, DB={technology_analysis.database or 'None'}.",
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Repository Analyzer", f"Technology analysis failed: {str(e)}", "failed")
    return state


def analyze_architecture_node(state: AnalyzerState) -> AnalyzerState:
    """Architecture Analysis Node"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Infrastructure Agent", "Parsing application layer boundaries and ORM mapping...", "in_progress")
    try:
        # Build Context
        repository_context = RepositoryContextBuilder.build(
            state['metadata'], state['repo_name'], state['owner'], state['clone_path']
        )
        state['repository_context'] = repository_context
        
        # Analyze Architecture
        architecture_analysis = ArchitectureAnalyzer.analyze(state['metadata'], repository_context)
        state['architecture_analysis'] = architecture_analysis

        add_agent_log(
            task_id,
            "Infrastructure Agent",
            f"Architecture analyzed. Complexity: {repository_context.project_complexity}, Scalability: {repository_context.expected_scalability}.",
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Infrastructure Agent", f"Architecture analysis failed: {str(e)}", "failed")
    return state


def reasoning_node(state: AnalyzerState) -> AnalyzerState:
    """Reasoning Node - Infers requirements & trade-offs prior to final selection"""
    if state.get('error'):
        return state

    task_id = state['task_id']
    add_agent_log(task_id, "Infrastructure Agent", "Inferring operational requirements and candidate trade-offs...", "in_progress")
    try:
        # We run the Decision Engine evaluation step to find the primary target
        primary_target, recommendations, confidence = AWSDecisionEngine.evaluate(
            state['metadata'], state['technology_analysis'], state['repository_context']
        )
        
        # Generate reasoning log lists based on target
        reasons_list = ReasoningEngine.generate_reasons(
            state['metadata'], primary_target, state['repository_context']
        )
        state['reasoning'] = "\n".join(reasons_list)
        
        add_agent_log(
            task_id, 
            "Infrastructure Agent", 
            "Operational trade-off reasoning steps computed.", 
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Infrastructure Agent", f"Reasoning node failed: {str(e)}", "failed")
    return state


def decision_engine_node(state: AnalyzerState) -> AnalyzerState:
    """Decision Engine Node - Selects primary service and builds recommendations"""
    if state.get('error'):
        return state

    task_id = state['task_id']
    add_agent_log(task_id, "Infrastructure Agent", "Running weighted decision matrix...", "in_progress")
    try:
        primary_target, aws_recommendations, confidence = AWSDecisionEngine.evaluate(
            state['metadata'], state['technology_analysis'], state['repository_context']
        )
        state['aws_recommendations'] = aws_recommendations
        
        # Set confidence dictionary
        state['confidence'] = {
            'deployment_target': f"{confidence:.1f}%",
            'technology_detection': f"{state['technology_analysis'].detection_confidence.get('frontend_stack', 0)}%"
        }
        
        # Prepare deployment recommendation schema object
        state['recommendation'] = DeploymentRecommendation(
            target=primary_target,
            why=aws_recommendations[0].reason if aws_recommendations else generate_heuristic_recommendation(state['metadata'], primary_target),
            estimated_monthly_cost=0.0, # Will be set in next Cost Analysis node
            cost_breakdown=CostBreakdown(compute=0.0, database=0.0, storage=0.0, data_transfer=0.0),
            confidence_score=int(confidence)
        )
        
        add_agent_log(
            task_id,
            "Infrastructure Agent",
            f"Decision Complete: Recommended {primary_target} with {confidence:.1f}% confidence.",
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Infrastructure Agent", f"Decision Engine node failed: {str(e)}", "failed")
    return state


def cost_analysis_node(state: AnalyzerState) -> AnalyzerState:
    """Cost Analysis Node - Performs realistic pricing estimations and assumptions"""
    if state.get('error'):
        return state

    task_id = state['task_id']
    add_agent_log(task_id, "Deployment Agent", "Estimating architectural cost breakdown...", "in_progress")
    try:
        rec = state['recommendation']
        complexity = state['repository_context'].project_complexity
        
        est_cost, cost_breakdown = CostEstimator.estimate_cost(rec.target, state['metadata'].databases, complexity)
        rec.estimated_monthly_cost = est_cost
        rec.cost_breakdown = cost_breakdown
        state['recommendation'] = rec
        
        # Generate detailed cost assumptions
        assumptions_str = CostEstimator.generate_assumptions_text(
            rec.target, state['metadata'].databases, complexity, est_cost, cost_breakdown
        )
        state['cost_analysis'] = assumptions_str
        
        add_agent_log(
            task_id, 
            "Deployment Agent", 
            f"Cost estimation complete: ${est_cost:.2f}/mo (USD). Assumptions recorded.", 
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Deployment Agent", f"Cost analysis node failed: {str(e)}", "failed")
    return state


def assess_health_node(state: AnalyzerState) -> AnalyzerState:
    """Report Generation & Health Assessment Node"""
    if state.get('error'):
        return state
        
    task_id = state['task_id']
    add_agent_log(task_id, "Deployment Agent", "Assessing repository cloud readiness and generating reports...", "in_progress")
    
    try:
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
        
        # Build solutions architect report
        reasons_list = state['reasoning'].split("\n") if state['reasoning'] else []
        state['architecture_report'] = ReportGenerator.build_report(
            metadata=metadata,
            architecture=state['architecture_analysis'],
            aws_recommendations=state['aws_recommendations'] or [],
            repository_context=state['repository_context'],
            reasons_list=reasons_list,
            cost_assumptions_str=state['cost_analysis'],
            health_score=health_score
        )
        
        # Build visualization graph
        state['visualization'] = ReportGenerator.build_visualization_graph(
            metadata, state['architecture_analysis']
        )
        
        add_agent_log(
            task_id, 
            "Deployment Agent", 
            f"Repository cloud readiness assessed. Score: {health_score}/100. Architectural report compiled.", 
            "completed"
        )
    except Exception as e:
        state['error'] = str(e)
        add_agent_log(task_id, "Deployment Agent", f"Report generation node failed: {str(e)}", "failed")
        
    return state


def generate_ai_summary_node(state: AnalyzerState) -> AnalyzerState:
    """Response Node - AI summary enhancement or heuristic compile"""
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
                temperature=0.2,
                request_timeout=30.0,
                max_retries=2
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
            
            # Overwrite why with our decision details if LLM why is empty or poor
            llm_why = res_json.get("why_recommendation", "")
            if len(llm_why) > 100:
                rec.why = llm_why
                state['recommendation'] = rec
            
            checklist_data = res_json.get("checklist", [])
            checklist_items = []
            for item in checklist_data:
                checklist_items.append(ChecklistItem(
                    label=item.get("label", ""),
                    status=item.get("status", "checked")
                ))
            state['checklist'] = checklist_items if checklist_items else generate_heuristic_checklist(metadata, rec.target)
            
            # Formulate remaining generic notes
            state['security_notes'] = "Review secrets handling and environment variable storage; use AWS Secrets Manager for production credentials."
            state['performance_notes'] = "Use CDN-backed static delivery and managed autoscaling to ensure high availability and low latency."
            state['deployment_strategy'] = f"Adopt {rec.target} with an IaC-driven CI/CD pipeline for repeatable deployments."
            
            add_agent_log(task_id, "Monitoring Agent", "AI deployment summary generated via OpenAI.", "completed")
            return state
        except Exception as e:
            # Fallback to heuristics on LLM error
            pass
            
    # Fallback / Heuristic compile
    state['ai_summary'] = generate_heuristic_summary(metadata, rec.target, state['owner'], state['repo_name'])
    state['checklist'] = generate_heuristic_checklist(metadata, rec.target)
    state['security_notes'] = "Review secrets handling and environment variable storage; use AWS Secrets Manager for production credentials."
    state['performance_notes'] = "Use CDN-backed static delivery and managed autoscaling to ensure high availability and low latency."
    state['deployment_strategy'] = f"Adopt {rec.target} with an IaC-driven CI/CD pipeline for repeatable deployments."

    add_agent_log(task_id, "Monitoring Agent", "AI deployment summary generated via heuristic engine.", "completed")
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────────────────────────────────────
builder = StateGraph(AnalyzerState)

# Add Nodes
builder.add_node("clone_and_scan", clone_and_scan_node)
builder.add_node("run_technology_analysis", technology_analysis_node)
builder.add_node("run_architecture_analysis", analyze_architecture_node)
builder.add_node("run_reasoning", reasoning_node)
builder.add_node("run_decision_engine", decision_engine_node)
builder.add_node("run_cost_analysis", cost_analysis_node)
builder.add_node("run_assess_health", assess_health_node)
builder.add_node("run_generate_ai_summary", generate_ai_summary_node)

# Set Flow
builder.set_entry_point("clone_and_scan")
builder.add_edge("clone_and_scan", "run_technology_analysis")
builder.add_edge("run_technology_analysis", "run_architecture_analysis")
builder.add_edge("run_architecture_analysis", "run_reasoning")
builder.add_edge("run_reasoning", "run_decision_engine")
builder.add_edge("run_decision_engine", "run_cost_analysis")
builder.add_edge("run_cost_analysis", "run_assess_health")
builder.add_edge("run_assess_health", "run_generate_ai_summary")
builder.add_edge("run_generate_ai_summary", END)

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
            logs=[AgentLog(**log) for log in analysis_tasks[task_id].get("logs", [])]
        )
        
        task_data = analysis_tasks[task_id]
        task_data.update(result.model_dump())
        task_data['repository_context'] = final_state.get('repository_context').model_dump() if final_state.get('repository_context') else None
        task_data['technology_analysis'] = final_state.get('technology_analysis').model_dump() if final_state.get('technology_analysis') else None
        task_data['architecture_analysis'] = final_state.get('architecture_analysis').model_dump() if final_state.get('architecture_analysis') else None
        task_data['aws_recommendations'] = [rec.model_dump() for rec in final_state.get('aws_recommendations', [])] if final_state.get('aws_recommendations') else []
        task_data['confidence'] = final_state.get('confidence')
        task_data['reasoning'] = final_state.get('reasoning')
        task_data['architecture_report'] = final_state.get('architecture_report')
        task_data['visualization'] = final_state.get('visualization').model_dump() if final_state.get('visualization') else None
        task_data['security_notes'] = final_state.get('security_notes')
        task_data['performance_notes'] = final_state.get('performance_notes')
        task_data['cost_analysis'] = final_state.get('cost_analysis')
        task_data['deployment_strategy'] = final_state.get('deployment_strategy')
        analysis_tasks[task_id] = task_data
        return analysis_tasks[task_id]
        
    except Exception as e:
        GitService.cleanup_directory(clone_path)
        analysis_tasks[task_id]["status"] = "failed"
        analysis_tasks[task_id]["error"] = str(e)
        add_agent_log(task_id, "Planner Agent", f"Workflow execution crashed: {str(e)}", "failed")
        return analysis_tasks[task_id]
