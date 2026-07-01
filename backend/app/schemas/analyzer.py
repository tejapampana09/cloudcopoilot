from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional

class AnalyzeRequest(BaseModel):
    repository_url: str = Field(..., description="The HTTPS or SSH URL of the public GitHub repository")

class AnalyzeResponse(BaseModel):
    task_id: str = Field(..., description="The unique task identifier for the analysis")
    status: str = Field(..., description="The initial status of the analysis task")

class LanguageInfo(BaseModel):
    name: str
    percentage: float

class RepoMetadata(BaseModel):
    languages: List[LanguageInfo] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    frontend: List[str] = Field(default_factory=list)
    backend: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    package_managers: List[str] = Field(default_factory=list)
    docker_readiness: bool = False
    docker_compose: bool = False
    env_variables: List[str] = Field(default_factory=list)
    ci_cd: List[str] = Field(default_factory=list)
    terraform: bool = False
    infrastructure_files: List[str] = Field(default_factory=list)
    readme_quality: str = "Medium"
    license: str = "Unknown"
    build_commands: List[str] = Field(default_factory=list)
    run_commands: List[str] = Field(default_factory=list)
    test_frameworks: List[str] = Field(default_factory=list)

class CostBreakdown(BaseModel):
    compute: float
    database: float
    storage: float
    data_transfer: float

class DeploymentRecommendation(BaseModel):
    target: str = Field(..., description="AWS App Runner | AWS ECS | AWS Lambda | AWS Amplify")
    why: str
    estimated_monthly_cost: float
    cost_breakdown: CostBreakdown
    confidence_score: int

class HealthBreakdown(BaseModel):
    documentation: int
    docker: int
    security: int
    environment: int
    deployment: int
    organization: int

class ChecklistItem(BaseModel):
    label: str
    status: str  # 'checked' | 'warning' | 'error'

class AgentLog(BaseModel):
    agent: str  # 'Planner Agent' | 'Repository Analyzer' | 'Infrastructure Agent' | 'Deployment Agent' | 'Monitoring Agent'
    message: str
    timestamp: str
    status: str  # 'pending' | 'in_progress' | 'completed' | 'failed'

class AnalysisResult(BaseModel):
    repository_url: str
    repository_name: str
    repository_owner: str
    analysis_time: str
    status: str  # 'pending' | 'in_progress' | 'completed' | 'failed'
    metadata: RepoMetadata
    recommendation: DeploymentRecommendation
    health_score: int
    health_breakdown: HealthBreakdown
    checklist: List[ChecklistItem] = Field(default_factory=list)
    ai_summary: str
    logs: List[AgentLog] = Field(default_factory=list)
    error: Optional[str] = None
