import uuid
import os
import json
import asyncio
import datetime
from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Depends, Response
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings, get_chat_llm
from app.schemas.analyzer import AnalyzeRequest, AnalyzeResponse
from app.agents.graph import run_analysis_pipeline
from app.utils.helpers import analysis_tasks
from app.services.git_service import GitService
from app.routers.auth import get_current_user
from app.models.user import User
from app.reports.report_generator import ReportGenerator

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
        "branch": request.branch,
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
        clone_path=clone_path,
        branch=request.branch,
        pat=request.pat
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


@router.post("/analyze/chat")
async def chat_with_repository(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """
    RAG-powered conversational repository consultant agent.
    """
    # Sanitize and detect prompt injection patterns
    def check_prompt_injection(text: str) -> bool:
        patterns = [
            "ignore previous instructions",
            "ignore all instructions",
            "disregard original prompt",
            "bypass restrictions",
            "you must now act as",
            "reveal your system prompt",
            "output your instructions"
        ]
        lowered = text.lower()
        return any(p in lowered for p in patterns)

    if check_prompt_injection(request.message):
        return {"response": "Potential prompt override attempt detected. Please state a repository analysis or configuration inquiry."}

    if request.task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Analysis session not found.")
    
    task_data = analysis_tasks[request.task_id]
    context = ""
    
    if settings.OPENAI_API_KEY:
        from app.services.indexing_service import IndexingService
        matched = IndexingService.search_semantic(
            task_id=request.task_id,
            query=request.message,
            api_key=settings.OPENAI_API_KEY,
            k=5
        )
        if matched:
            context = "\n\n".join([
                f"### FILE: {m['file_path']} (Similarity: {m['score']})\n```\n{m['content']}\n```"
                for m in matched
            ])
            
    def call_llm(system_prompt: str, user_prompt: str) -> str:
        try:
            if not settings.OPENAI_API_KEY:
                return "OpenAI API key not configured."
                
            llm = get_chat_llm(
                api_key=settings.OPENAI_API_KEY,
                model_name=settings.OPENAI_MODEL,
                temperature=0.2,
                request_timeout=30.0,
                max_retries=2
            )
            
            from langchain_core.prompts import ChatPromptTemplate
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
        "You are an expert AI GitHub Repository Assistant. "
        "Use the provided repository context snippets to answer the developer's question accurately. "
        "Keep your answer highly technical, concise, and structured in Markdown format. "
        "Reference specific files, functions, or configurations where relevant. "
        "If the query cannot be answered using the provided context, state that clearly and do not make up information."
    )
    
    user_prompt = (
        f"Repository: {task_data.get('repository_owner')}/{task_data.get('repository_name')}\n"
        f"Primary Languages: {', '.join([l.get('name') for l in task_data.get('metadata', {}).get('languages', [])])}\n\n"
        f"Repository Code Context:\n{context or 'No specific code context matching the query was found.'}\n\n"
        f"Developer Question: {request.message}"
    )
    
    response = call_llm(system_prompt, user_prompt)
    return {"response": response}

@router.get("/analyze/export/json/{task_id}")
def export_report_json(task_id: str, current_user: User = Depends(get_current_user)):
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task ID not found.")
    task_data = analysis_tasks[task_id]
    if task_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    json_data = ReportGenerator.export_json(task_data)
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.json"}
    )

@router.get("/analyze/export/markdown/{task_id}")
def export_report_markdown(task_id: str, current_user: User = Depends(get_current_user)):
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task ID not found.")
    task_data = analysis_tasks[task_id]
    if task_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    markdown_data = ReportGenerator.export_markdown(task_data)
    return Response(
        content=markdown_data,
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.md"}
    )

@router.get("/analyze/export/pdf/{task_id}")
def export_report_pdf(task_id: str, current_user: User = Depends(get_current_user)):
    if task_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Task ID not found.")
    task_data = analysis_tasks[task_id]
    if task_data.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    
    pdf_bytes = ReportGenerator.export_pdf(task_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=report_{task_id}.pdf"}
    )


