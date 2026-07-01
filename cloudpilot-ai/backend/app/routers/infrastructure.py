import os
import uuid
import json
import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
from app.schemas.infrastructure import InfrastructureRequest, InfrastructureResponse
from app.agents.infra_graph import run_infrastructure_pipeline, DOWNLOADS_DIR, TEMP_DIR
from app.services.git_service import GitService
from app.services.scanner import HeuristicScanner
from app.services.cost_estimator import CostEstimator
from app.utils.helpers import infra_generations

router = APIRouter()

@router.post("/generate", response_model=InfrastructureResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_infrastructure(request: InfrastructureRequest, background_tasks: BackgroundTasks):
    """
    Analyzes the repository and triggers the background infrastructure generation task.
    """
    try:
        # Validate URL format
        owner, repo_name, clean_url = GitService.validate_and_parse_url(request.repository_url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    generation_id = str(uuid.uuid4())
    clone_path = os.path.join(settings.TEMP_CLONE_DIR, f"scan_{generation_id}")
    
    # 1. Run quick scan to get tech profile
    try:
        GitService.clone_repository(request.repository_url, clone_path)
        metadata = HeuristicScanner.scan_repository(clone_path)
        GitService.cleanup_directory(clone_path)
    except Exception as e:
        GitService.cleanup_directory(clone_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to scan repository: {str(e)}"
        )
        
    # Determine deployment target recommendation
    target = "AWS App Runner"
    is_static = len(metadata.frontend) > 0 and len(metadata.backend) == 0
    is_serverless = "serverless" in "".join(metadata.infrastructure_files).lower()
    
    if is_static:
        target = "AWS Amplify"
    elif metadata.docker_compose:
        target = "AWS ECS"
    elif is_serverless:
        target = "AWS Lambda"
        
    detected_framework = metadata.frameworks[0] if metadata.frameworks else "Static Site" if is_static else "Backend Service"
    
    # Initialize session database entry
    infra_generations[generation_id] = {
        "generation_id": generation_id,
        "status": "pending",
        "progress": 0,
        "detected_framework": detected_framework,
        "generated_files": {},
        "validation_score": 0,
        "next_step": "Planner",
        "logs": []
    }
    
    # Dispatch pipeline task in background
    background_tasks.add_task(
        run_infrastructure_pipeline,
        generation_id=generation_id,
        repo_url=request.repository_url,
        metadata=metadata,
        target=target
    )
    
    return InfrastructureResponse(
        generation_id=generation_id,
        status="pending",
        progress=0,
        detected_framework=detected_framework,
        generated_files={},
        validation_score=0,
        next_step="Planner"
    )

@router.get("/stream/{generation_id}")
async def stream_generation(generation_id: str):
    """
    Streams active agent logs and final generated files payload using Server-Sent Events (SSE).
    """
    if generation_id not in infra_generations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation session not found."
        )
        
    async def event_generator():
        last_log_idx = 0
        while True:
            if generation_id not in infra_generations:
                yield {"event": "error", "data": "Session expired."}
                break
                
            gen_data = infra_generations[generation_id]
            current_logs = gen_data.get("logs", [])
            
            # Stream logs
            if len(current_logs) > last_log_idx:
                for log in current_logs[last_log_idx:]:
                    yield {
                        "event": "log",
                        "data": json.dumps(log)
                    }
                last_log_idx = len(current_logs)
                
            # Stream result when finished
            if gen_data.get("status") in ["completed", "failed"]:
                yield {
                    "event": "result",
                    "data": json.dumps(gen_data)
                }
                break
                
            await asyncio.sleep(0.3)
            
    return EventSourceResponse(event_generator())

@router.get("/download/{generation_id}")
async def download_infrastructure(generation_id: str):
    """
    Downloads the packaged ZIP configuration archive containing all generated infrastructure files.
    """
    zip_filename = f"cloudpilot-infra-{generation_id}.zip"
    zip_path = os.path.join(DOWNLOADS_DIR, zip_filename)
    
    if not os.path.exists(zip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated infrastructure package not found."
        )
        
    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename="cloudpilot-infra.zip"
    )
