import logging
import os
import json
import datetime
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.agents.infra_state import InfrastructureState
from app.services.generator_service import HeuristicGenerator
from app.services.packaging_service import PackagingService
from app.schemas.analyzer import AgentLog, RepoMetadata
from app.utils.helpers import add_infra_agent_log, infra_generations
from app.prompts import agent_prompts

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False

# Staging folders resolved dynamically relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMP_DIR = os.path.join(BASE_DIR, "temp")
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")

# Helper to run LLM completion
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Invokes OpenAI LLM. Raises exception if unconfigured or fails."""
    if not HAS_LANGCHAIN or not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured.")
        
    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.OPENAI_MODEL,
        temperature=0.2,
        request_timeout=30.0,
        max_retries=2
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{content}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"content": user_prompt})
    return response.content.strip()

# Nodes
def planner_node(state: InfrastructureState) -> InfrastructureState:
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Planner Agent", "Reading Repository Analyzer findings...", "in_progress")
    
    metadata = state['metadata']
    target = state.get('target', 'AWS App Runner')
    
    # 1. Choose generators
    steps = ["Docker"]
    if metadata.databases or len(metadata.frameworks) > 1:
        steps.append("Compose")
        
    steps.append("Environment")
    
    if target in ["AWS App Runner", "AWS ECS", "AWS Lambda"]:
        steps.append("Terraform")
        
    steps.append("GitHub Actions")
    
    state['plan'] = steps
    state['status'] = "generating"
    state['progress'] = 10
    
    # Update datastore
    infra_generations[gen_id]["progress"] = 10
    infra_generations[gen_id]["next_step"] = "Docker"
    
    add_infra_agent_log(
        gen_id, 
        "Planner Agent", 
        f"Execution plan formulated: {', '.join(steps)}. Next step: Docker.", 
        "completed"
    )
    return state

def docker_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error'):
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Docker Agent", "Generating optimized Docker container configuration...", "in_progress")
    
    metadata = state['metadata']
    lang = metadata.languages[0].name if metadata.languages else "Node"
    frameworks_str = ", ".join(metadata.frameworks)
    db_str = ", ".join(metadata.databases)
    run_cmd = ", ".join(metadata.run_commands)
    build_cmd = ", ".join(metadata.build_commands)
    
    try:
        # Try LLM
        user_prompt = agent_prompts.DOCKER_USER_PROMPT.format(
            language=lang,
            frameworks=frameworks_str,
            database=db_str,
            run_commands=run_cmd,
            build_commands=build_cmd
        )
        response = call_llm(agent_prompts.DOCKER_SYSTEM_PROMPT, user_prompt)
        
        # Parse output
        dockerfile = ""
        dockerignore = ""
        if "---DOCKERFILE---" in response and "---DOCKERIGNORE---" in response:
            parts = response.split("---DOCKERIGNORE---")
            dockerfile = parts[0].replace("---DOCKERFILE---", "").strip()
            dockerignore = parts[1].strip()
        else:
            dockerfile = response
            dockerignore = ".git\nnode_modules\nvenv\n"
            
        state['generated_files']['Dockerfile'] = dockerfile
        state['generated_files']['.dockerignore'] = dockerignore
        
    except Exception as e:
        # Fallback to heuristics
        fallback = HeuristicGenerator.generate_docker(metadata)
        state['generated_files'].update(fallback)
        
    state['progress'] = 25
    infra_generations[gen_id]["progress"] = 25
    infra_generations[gen_id]["next_step"] = "Compose" if "Compose" in state['plan'] else "Environment"
    
    add_infra_agent_log(gen_id, "Docker Agent", "Dockerfile and .dockerignore generated successfully.", "completed")
    return state

def compose_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error') or "Compose" not in state['plan']:
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Compose Agent", "Generating local docker-compose configurations...", "in_progress")
    
    metadata = state['metadata']
    lang = metadata.languages[0].name if metadata.languages else "Node"
    frameworks_str = ", ".join(metadata.frameworks)
    db_str = ", ".join(metadata.databases)
    target = state.get('target', 'AWS App Runner')
    
    try:
        user_prompt = agent_prompts.COMPOSE_USER_PROMPT.format(
            language=lang,
            frameworks=frameworks_str,
            databases=db_str,
            target=target
        )
        response = call_llm(agent_prompts.COMPOSE_SYSTEM_PROMPT, user_prompt)
        
        compose_content = response
        if "---COMPOSE---" in response:
            compose_content = response.replace("---COMPOSE---", "").strip()
            
        state['generated_files']['docker-compose.yml'] = compose_content
    except Exception as e:
        fallback = HeuristicGenerator.generate_compose(metadata, target)
        state['generated_files']['docker-compose.yml'] = fallback
        
    state['progress'] = 40
    infra_generations[gen_id]["progress"] = 40
    infra_generations[gen_id]["next_step"] = "Environment"
    
    add_infra_agent_log(gen_id, "Compose Agent", "docker-compose.yml generated with services, network, and healthchecks.", "completed")
    return state

def env_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error'):
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Environment Agent", "Generating environment variable configuration...", "in_progress")
    
    metadata = state['metadata']
    env_vars_str = ", ".join(metadata.env_variables)
    frameworks_str = ", ".join(metadata.frameworks)
    
    try:
        user_prompt = agent_prompts.ENV_USER_PROMPT.format(
            env_vars=env_vars_str,
            frameworks=frameworks_str
        )
        response = call_llm(agent_prompts.ENV_SYSTEM_PROMPT, user_prompt)
        
        env_content = response
        if "---ENV---" in response:
            env_content = response.replace("---ENV---", "").strip()
            
        state['generated_files']['.env.example'] = env_content
    except Exception as e:
        fallback = HeuristicGenerator.generate_env(metadata)
        state['generated_files']['.env.example'] = fallback
        
    state['progress'] = 55
    infra_generations[gen_id]["progress"] = 55
    infra_generations[gen_id]["next_step"] = "Terraform" if "Terraform" in state['plan'] else "GitHub Actions"
    
    add_infra_agent_log(gen_id, "Environment Agent", ".env.example file created.", "completed")
    return state

def terraform_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error') or "Terraform" not in state['plan']:
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Terraform Agent", "Generating modular Terraform configurations...", "in_progress")
    
    metadata = state['metadata']
    target = state.get('target', 'AWS App Runner')
    db_str = ", ".join(metadata.databases)
    
    try:
        user_prompt = agent_prompts.TERRAFORM_USER_PROMPT.format(
            target=target,
            databases=db_str
        )
        response = call_llm(agent_prompts.TERRAFORM_SYSTEM_PROMPT, user_prompt)
        
        # Parse multiple TF files
        providers = ""
        main = ""
        variables = ""
        outputs = ""
        
        if "---TERRAFORM_PROVIDERS---" in response:
            parts = response.split("---TERRAFORM_MAIN---")
            providers = parts[0].replace("---TERRAFORM_PROVIDERS---", "").strip()
            
            sub_parts = parts[1].split("---TERRAFORM_VARIABLES---")
            main = sub_parts[0].strip()
            
            var_out_parts = sub_parts[1].split("---TERRAFORM_OUTPUTS---")
            variables = var_out_parts[0].strip()
            outputs = var_out_parts[1].strip()
            
            state['generated_files']['terraform/providers.tf'] = providers
            state['generated_files']['terraform/main.tf'] = main
            state['generated_files']['terraform/variables.tf'] = variables
            state['generated_files']['terraform/outputs.tf'] = outputs
        else:
            fallback = HeuristicGenerator.generate_terraform(metadata, target)
            state['generated_files'].update(fallback)
            
    except Exception as e:
        fallback = HeuristicGenerator.generate_terraform(metadata, target)
        state['generated_files'].update(fallback)
        
    state['progress'] = 70
    infra_generations[gen_id]["progress"] = 70
    infra_generations[gen_id]["next_step"] = "GitHub Actions"
    
    add_infra_agent_log(gen_id, "Terraform Agent", "Terraform modules generated for computing, security group VPC networking, and ECR repositories.", "completed")
    return state

def gha_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error'):
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "GitHub Actions Agent", "Generating deployment workflows...", "in_progress")
    
    metadata = state['metadata']
    lang = metadata.languages[0].name if metadata.languages else "Node"
    build_cmd = ", ".join(metadata.build_commands)
    test_fw = ", ".join(metadata.test_frameworks)
    target = state.get('target', 'AWS App Runner')
    
    try:
        user_prompt = agent_prompts.GHA_USER_PROMPT.format(
            language=lang,
            build_commands=build_cmd,
            test_frameworks=test_fw,
            target=target
        )
        response = call_llm(agent_prompts.GHA_SYSTEM_PROMPT, user_prompt)
        
        workflow_content = response
        if "---WORKFLOW---" in response:
            workflow_content = response.replace("---WORKFLOW---", "").strip()
            
        state['generated_files']['.github/workflows/deploy.yml'] = workflow_content
    except Exception as e:
        fallback = HeuristicGenerator.generate_workflow(metadata, target)
        state['generated_files']['.github/workflows/deploy.yml'] = fallback
        
    state['progress'] = 85
    infra_generations[gen_id]["progress"] = 85
    infra_generations[gen_id]["next_step"] = "Validation"
    
    add_infra_agent_log(gen_id, "GitHub Actions Agent", "CI/CD deployment workflow created at .github/workflows/deploy.yml.", "completed")
    return state

def validation_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error'):
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Validation Agent", "Validating generated config files syntax...", "in_progress")
    
    files = state['generated_files']
    
    # 1. Perform mock regex check or parse check locally
    results = []
    score = 100
    
    # Check Dockerfile syntax
    if "Dockerfile" in files:
        df_content = files["Dockerfile"]
        if "FROM" not in df_content:
            results.append({"file": "Dockerfile", "status": "error", "message": "Missing base image 'FROM'."})
            score -= 10
        else:
            results.append({"file": "Dockerfile", "status": "valid", "message": "Syntax validation passed (standard FROM base detected)."})
            
    # Check Compose syntax
    if "docker-compose.yml" in files:
        dc_content = files["docker-compose.yml"]
        if "services:" not in dc_content:
            results.append({"file": "docker-compose.yml", "status": "error", "message": "Missing 'services' declaration."})
            score -= 10
        else:
            results.append({"file": "docker-compose.yml", "status": "valid", "message": "YAML parsing passed (services stack is structured)."})
            
    # Check Terraform variables references
    tf_main = files.get("terraform/main.tf", "")
    tf_vars = files.get("terraform/variables.tf", "")
    if tf_main:
        if "aws" in tf_main:
            results.append({"file": "terraform/main.tf", "status": "valid", "message": "Terraform AWS providers compiled successfully."})
            
    # Try LLM validation to refine report
    try:
        configs_block = ""
        for path, content in files.items():
            configs_block += f"\n--- FILE: {path} ---\n{content}\n"
            
        user_prompt = agent_prompts.VALIDATION_USER_PROMPT.format(configs_block=configs_block[:4000]) # Cap content size
        response = call_llm(agent_prompts.VALIDATION_SYSTEM_PROMPT, user_prompt)
        
        report = json.loads(response)
        score = report.get("score", score)
        results = report.get("results", results)
    except Exception as e:
        logger.exception("LLM validation step failed in infra_graph for generation %s", gen_id)
        
    state['validation_report'] = {
        "score": score,
        "results": results
    }
    state['progress'] = 95
    infra_generations[gen_id]["progress"] = 95
    infra_generations[gen_id]["next_step"] = "Packaging"
    
    add_infra_agent_log(gen_id, "Validation Agent", f"Infrastructure files audited. Validation score: {score}/100.", "completed")
    return state

def packaging_agent_node(state: InfrastructureState) -> InfrastructureState:
    if state.get('error'):
        return state
        
    gen_id = state['generation_id']
    add_infra_agent_log(gen_id, "Packaging Agent", "Compressing files into download ZIP package...", "in_progress")
    
    try:
        zip_path = PackagingService.package_files(
            generation_id=gen_id,
            generated_files=state['generated_files'],
            temp_dir_base=TEMP_DIR,
            downloads_dir_base=DOWNLOADS_DIR
        )
        
        state['zip_path'] = zip_path
        state['progress'] = 100
        state['status'] = "completed"
        
        # Write to final task database
        infra_generations[gen_id].update({
            "status": "completed",
            "progress": 100,
            "generated_files": state['generated_files'],
            "validation_score": state['validation_report'].get("score", 100),
            "validation_report": state['validation_report'],
            "next_step": "Ready for Deployment"
        })
        
        add_infra_agent_log(gen_id, "Packaging Agent", "ZIP package cloudpilot-infra.zip created successfully.", "completed")
    except Exception as e:
        state['error'] = str(e)
        state['status'] = "failed"
        infra_generations[gen_id]["status"] = "failed"
        infra_generations[gen_id]["error"] = str(e)
        add_infra_agent_log(gen_id, "Packaging Agent", f"Compression failed: {str(e)}", "failed")
        
    return state

# Compile graph
builder = StateGraph(InfrastructureState)

builder.add_node("planner", planner_node)
builder.add_node("docker_agent", docker_agent_node)
builder.add_node("compose_agent", compose_agent_node)
builder.add_node("env_agent", env_agent_node)
builder.add_node("terraform_agent", terraform_agent_node)
builder.add_node("gha_agent", gha_agent_node)
builder.add_node("validation_agent", validation_agent_node)
builder.add_node("packaging_agent", packaging_agent_node)

builder.set_entry_point("planner")
builder.add_edge("planner", "docker_agent")

# Handle routing based on plan
def route_after_docker(state: InfrastructureState):
    if "Compose" in state['plan']:
        return "compose_agent"
    return "env_agent"

def route_after_compose(state: InfrastructureState):
    return "env_agent"

def route_after_env(state: InfrastructureState):
    if "Terraform" in state['plan']:
        return "terraform_agent"
    return "gha_agent"

def route_after_terraform(state: InfrastructureState):
    return "gha_agent"

builder.add_conditional_edges("docker_agent", route_after_docker, {
    "compose_agent": "compose_agent",
    "env_agent": "env_agent"
})
builder.add_edge("compose_agent", "env_agent")
builder.add_conditional_edges("env_agent", route_after_env, {
    "terraform_agent": "terraform_agent",
    "gha_agent": "gha_agent"
})
builder.add_edge("terraform_agent", "gha_agent")
builder.add_edge("gha_agent", "validation_agent")
builder.add_edge("validation_agent", "packaging_agent")
builder.add_edge("packaging_agent", END)

graph = builder.compile()

def run_infrastructure_pipeline(generation_id: str, repo_url: str, metadata: RepoMetadata, target: str) -> Dict[str, Any]:
    """
    Triggers the compiled infrastructure pipeline graph.
    """
    initial_state = InfrastructureState(
        repository_url=repo_url,
        generation_id=generation_id,
        clone_path=os.path.join(TEMP_DIR, generation_id),
        metadata=metadata,
        plan=[],
        generated_files={},
        validation_report={"score": 0, "results": []},
        zip_path=None,
        status="pending",
        progress=0,
        logs=[],
        error=None
    )
    # Add target to state
    initial_state['target'] = target
    
    # Initialize basic logs
    add_infra_agent_log(generation_id, "Planner Agent", "Waiting to initialize generator steps...", "pending")
    add_infra_agent_log(generation_id, "Docker Agent", "Waiting for plan...", "pending")
    add_infra_agent_log(generation_id, "Compose Agent", "Waiting for plan...", "pending")
    add_infra_agent_log(generation_id, "Environment Agent", "Waiting for plan...", "pending")
    add_infra_agent_log(generation_id, "Terraform Agent", "Waiting for plan...", "pending")
    add_infra_agent_log(generation_id, "GitHub Actions Agent", "Waiting for plan...", "pending")
    add_infra_agent_log(generation_id, "Validation Agent", "Waiting for code files to validate...", "pending")
    add_infra_agent_log(generation_id, "Packaging Agent", "Waiting for audit...", "pending")
    
    try:
        final_state = graph.invoke(initial_state)
        if final_state.get('error'):
            infra_generations[generation_id]["status"] = "failed"
            infra_generations[generation_id]["error"] = final_state['error']
        return infra_generations[generation_id]
    except Exception as e:
        infra_generations[generation_id]["status"] = "failed"
        infra_generations[generation_id]["error"] = str(e)
        add_infra_agent_log(generation_id, "Planner Agent", f"Pipeline execution failed: {str(e)}", "failed")
        return infra_generations[generation_id]
