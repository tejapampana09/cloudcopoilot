import uuid
import os
import json
import asyncio
import datetime
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings, get_chat_llm
from app.schemas.analyzer import AnalyzeRequest, AnalyzeResponse
from app.agents.graph import run_analysis_pipeline
from app.utils.helpers import analysis_tasks
from app.services.git_service import GitService
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse, status_code=status.HTTP_202_ACCEPTED)
async def analyze_repository(
    request: AnalyzeRequest, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Triggers an asynchronous code analysis of the provided public GitHub repository.
    """
    try:
        # Validate URL format before launching background task
        GitService.validate_and_parse_url(request.repository_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    # Generate unique task id
    task_id = str(uuid.uuid4())
    clone_path = os.path.join(settings.TEMP_CLONE_DIR, task_id)
    
    # Initialize task data
    analysis_tasks[task_id] = {
        "user_id": current_user.id,
        "repository_url": request.repository_url,
        "repository_name": "",
        "repository_owner": "",
        "analysis_time": "",
        "status": "pending",
        "metadata": {
            "languages": [], "frameworks": [], "frontend": [], "backend": [], 
            "databases": [], "package_managers": [], "docker_readiness": False,
            "docker_compose": False, "env_variables": [], "ci_cd": [],
            "terraform": False, "infrastructure_files": [], "readme_quality": "Medium",
            "license": "Unknown", "build_commands": [], "run_commands": [], "test_frameworks": []
        },
        "recommendation": {
            "target": "AWS App Runner", "why": "", "estimated_monthly_cost": 0.0,
            "cost_breakdown": {"compute": 0.0, "database": 0.0, "storage": 0.0, "data_transfer": 0.0},
            "confidence_score": 0
        },
        "health_score": 0,
        "health_breakdown": {"documentation": 0, "docker": 0, "security": 0, "environment": 0, "deployment": 0, "organization": 0},
        "checklist": [],
        "ai_summary": "",
        "logs": []
    }
    
    # Run pipeline in background
    background_tasks.add_task(
        run_analysis_pipeline,
        task_id=task_id,
        repo_url=request.repository_url,
        clone_path=clone_path
    )
    
    return AnalyzeResponse(task_id=task_id, status="pending")

@router.get("/analyze/stream/{task_id}")
async def stream_analysis(task_id: str, current_user: User = Depends(get_current_user)):
    """
    Streams analysis agent logs and final analysis payload via Server-Sent Events (SSE).
    """
    if task_id not in analysis_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task ID not found."
        )
        
    # Verify owner permission
    task_data = analysis_tasks[task_id]
    if task_data.get("user_id") != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This scan belongs to another user."
        )
        
    async def event_generator():
        last_log_idx = 0
        while True:
            # Check if task was deleted or doesn't exist
            if task_id not in analysis_tasks:
                yield {"event": "error", "data": "Task removed or expired."}
                break
                
            task_data = analysis_tasks[task_id]
            current_logs = task_data.get("logs", [])
            
            # 1. Stream new logs
            if len(current_logs) > last_log_idx:
                for log in current_logs[last_log_idx:]:
                    yield {
                        "event": "log",
                        "data": json.dumps(log)
                    }
                last_log_idx = len(current_logs)
                
            # 2. Check for completion or failure
            if task_data.get("status") in ["completed", "failed"]:
                yield {
                    "event": "result",
                    "data": json.dumps(task_data)
                }
                break
                
            await asyncio.sleep(0.3)
            
    return EventSourceResponse(event_generator())

@router.get("/recent")
async def get_recent_analyses(current_user: User = Depends(get_current_user)):
    """
    Returns the list of recently completed repository analyses for the current user.
    """
    recent = []
    for task_id, task in analysis_tasks.items():
        if task.get("user_id") == current_user.id:
            status = task.get("status")
            if status in ["completed", "failed"]:
                recent.append({
                    "task_id": task_id,
                    "name": task.get("repository_name") or task.get("repository_url").split("/")[-1].replace(".git", ""),
                    "owner": task.get("repository_owner") or "github",
                    "url": task.get("repository_url"),
                    "time": task.get("analysis_time") or datetime.datetime.now().isoformat(),
                    "status": "Completed" if status == "completed" else "Failed",
                    "target": task.get("recommendation", {}).get("target", "AWS App Runner")
                })
    # Sort by time descending
    recent.sort(key=lambda x: x["time"], reverse=True)
    return recent[:10]


class ChatRequest(BaseModel):
    task_id: str
    message: str


@router.post("/chat")
async def chat_with_repository(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    RAG-powered conversational repository consultant agent.
    """
    if request.task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
    
    task_data = analysis_tasks[request.task_id]
    
    # Extract code files context matching query keywords
    clone_path = os.path.join(settings.TEMP_CLONE_DIR, request.task_id)
    context = ""
    
    if os.path.exists(clone_path):
        matched_files = []
        words = [w.lower() for w in request.message.split() if len(w) > 3]
        
        file_count = 0
        for root, dirs, files in os.walk(clone_path):
            if any(ignored in root for ignored in ['.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build']):
                continue
            for file in files:
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, clone_path)
                
                match = False
                if any(w in file.lower() for w in words):
                    match = True
                else:
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            head = f.read(500)
                            if any(w in head.lower() for w in words):
                                match = True
                    except Exception:
                        pass
                
                if match:
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(1500)
                            matched_files.append(f"### FILE: {rel_path}\n```\n{content}\n```")
                            file_count += 1
                    except Exception:
                        pass
                
                if file_count >= 3:
                    break
            if file_count >= 3:
                break
        
        if matched_files:
            context = "\n\n".join(matched_files)
            
    def call_llm(system_prompt: str, user_prompt: str) -> str:
        try:
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            if not settings.OPENAI_API_KEY:
                return "OpenAI API key not configured."
                
            llm = get_chat_llm(
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
        except Exception as e:
            return f"Failed to call LLM: {str(e)}"
            
    system_prompt = (
        "You are a Senior Solutions Architect and Technical Consultant. "
        "Use the provided repository context snippets to answer the developer's question accurately. "
        "Keep your answer highly technical, concise, and structured in Markdown format. "
        "Refer to specific files, functions, or configurations detected in the context where relevant."
    )
    
    user_prompt = (
        f"Repository: {task_data.get('repository_owner')}/{task_data.get('repository_name')}\n"
        f"Primary Compute Target: {task_data.get('recommendation', {}).get('target', 'AWS App Runner')}\n"
        f"Database Detected: {', '.join(task_data.get('metadata', {}).get('databases', []))}\n\n"
        f"Repository Code Context:\n{context or 'No specific code context matching keywords was found.'}\n\n"
        f"Developer Question: {request.message}"
    )
    
    response = call_llm(system_prompt, user_prompt)
        
    return {"response": response}

