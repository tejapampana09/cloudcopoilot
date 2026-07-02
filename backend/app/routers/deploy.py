from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json

from app.services.deployment_service import DeploymentService
from app.utils.helpers import deployments
from app.routers.auth import get_current_user

router = APIRouter()

# Schemas
class ConnectAWSRequest(BaseModel):
    access_key: str = Field(..., description="AWS IAM Access Key ID")
    secret_key: str = Field(..., description="AWS IAM Secret Access Key")
    region: str = Field(..., description="AWS Region")

class DeployTriggerRequest(BaseModel):
    repository_url: str = Field(..., description="Git repository URL to deploy")
    repository_name: str = Field(..., description="Git repository name")
    access_key: str
    secret_key: str
    region: str
    service_name: str

class DeploymentResponse(BaseModel):
    deployment_id: str
    status: str

# Endpoints
@router.post("/connect", response_model=Dict[str, Any])
def connect_aws(request: ConnectAWSRequest):
    """Validates AWS IAM access credentials."""
    valid = DeploymentService.validate_aws_credentials(
        request.access_key, request.secret_key, request.region
    )
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid AWS IAM credentials or region configuration."
        )
    return {"status": "success", "message": "AWS Account verified successfully."}

@router.post("/trigger", response_model=DeploymentResponse)
def trigger_deployment(request: DeployTriggerRequest, current_user = Depends(get_current_user)):
    """Triggers background AWS App Runner deployment."""
    import uuid
    deployment_id = str(uuid.uuid4())
    
    DeploymentService.start_deployment(
        deployment_id=deployment_id,
        user_id=current_user.id if current_user else None,
        repo_url=request.repository_url,
        repo_name=request.repository_name,
        access_key=request.access_key,
        secret_key=request.secret_key,
        region=request.region,
        service_name=request.service_name
    )
    
    return {"deployment_id": deployment_id, "status": "pending"}

@router.get("/history", response_model=List[Dict[str, Any]])
def get_deployment_history(current_user = Depends(get_current_user)):
    """Retrieves deployment history list for the logged-in user."""
    user_id = current_user.id if current_user else None
    user_deps = []
    for dep_id, dep in deployments.items():
        if dep.get("user_id") == user_id:
            user_deps.append(dep)
            
    # Sort by timestamp descending
    user_deps.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return user_deps

@router.get("/status/{deployment_id}", response_model=Dict[str, Any])
def get_deployment_status(deployment_id: str):
    """Fetches details, status, and logs for a single deployment."""
    dep = deployments.get(deployment_id)
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment task not found."
        )
    return dep

@router.post("/destroy/{deployment_id}", response_model=Dict[str, Any])
def destroy_deployment(deployment_id: str):
    """Decommissions deployed AWS infrastructure resources."""
    dep = deployments.get(deployment_id)
    if not dep:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deployment not found."
        )
        
    DeploymentService.start_destroy(deployment_id)
    return {"status": "success", "message": "Resource destruction triggered."}

@router.get("/stream/{deployment_id}")
async def stream_deployment(deployment_id: str):
    """Streams live deployment logs and state updates using SSE."""
    async def event_generator():
        while True:
            dep = deployments.get(deployment_id)
            if not dep:
                yield f"event: log\ndata: {json.dumps({'error': 'Deployment not found'})}\n\n"
                break
                
            yield f"event: deployment\ndata: {json.dumps(dep)}\n\n"
            
            if dep.get("status") in ["completed", "failed", "destroyed"]:
                break
                
            await asyncio.sleep(1.0)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
