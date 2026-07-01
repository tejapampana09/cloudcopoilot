import uuid
import os
import json
import asyncio
import datetime
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
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

