from pydantic import BaseModel, Field
from typing import List, Optional

class AWSConnectionRequest(BaseModel):
    aws_access_key_id: str = Field(..., min_length=16, description="AWS Access Key ID")
    aws_secret_access_key: str = Field(..., min_length=32, description="AWS Secret Access Key")
    aws_region: str = Field(default="us-east-1", description="Default AWS Region")

class AWSConnectionResponse(BaseModel):
    success: bool
    region: str
    user_arn: Optional[str] = None
    error: Optional[str] = None

class DeployRequest(BaseModel):
    repository_url: str
    target_service: str = Field(default="AWS App Runner")
    aws_region: str = Field(default="us-east-1")
    force_failure: bool = Field(default=False, description="Force a build failure to test AI suggestions")

class DeployResponse(BaseModel):
    deployment_id: str
    repository_url: str
    status: str  # pending, building, deploying, completed, failed, rolling_back
    public_url: Optional[str] = None
    aws_service: str
    region: str
    created_at: str
    monthly_cost: float
    build_duration: str
    deploy_duration: str
    git_commit: str

class SimulatorResponse(BaseModel):
    estimated_cost: str
    estimated_duration: str
    success_probability: int
    warnings: List[str]
    suggestions: List[str]

class RollbackRequest(BaseModel):
    deployment_id: str

class RollbackResponse(BaseModel):
    success: bool
    message: str
    new_deployment_id: str
