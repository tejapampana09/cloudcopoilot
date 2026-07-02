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
    repo_url: Optional[HttpUrl] = None
    readme_quality: str = "Medium"
    license: str = "Unknown"
    build_commands: List[str] = Field(default_factory=list)
    run_commands: List[str] = Field(default_factory=list)
    test_frameworks: List[str] = Field(default_factory=list)
    total_commits: int = 0
    contributors_count: int = 0
    technical_debt_score: int = 50
    complexity_index: str = "Medium"
    detected_secrets: List[str] = Field(default_factory=list)
    dependency_risks: List[str] = Field(default_factory=list)
    large_files: List[str] = Field(default_factory=list)
    circular_dependencies: List[str] = Field(default_factory=list)
    stale_branches: List[str] = Field(default_factory=list)
    release_tags: List[str] = Field(default_factory=list)

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

class FixSuggestion(BaseModel):
    problem: str
    reason: str
    impact: str
    affected_files: List[str]
    suggested_solution: str
    example_code: str
    confidence_score: int

class SecurityIssue(BaseModel):
    issue_type: str
    severity: str  # Critical, High, Medium, Low
    description: str
    affected_files: List[str]
    suggested_fix: str

class PerformanceIssue(BaseModel):
    issue_type: str
    severity: str
    description: str
    affected_files: List[str]
    suggested_fix: str

class DocumentationSection(BaseModel):
    readme: str
    architecture: str
    folder_guide: str
    api_docs: str
    developer_docs: str
    environment_variables: str
    setup_guide: str

class DeploymentGuide(BaseModel):
    framework_detected: str
    hosting_recommendation: str
    build_commands: List[str]
    environment_variables: List[str]
    required_secrets: List[str]
    troubleshooting_guide: str
    common_deployment_errors: List[str]

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
    repository_report: Optional[Dict[str, Any]] = None
    architecture_report: Optional[Dict[str, Any]] = None
    security_report: Optional[Dict[str, Any]] = None
    performance_report: Optional[Dict[str, Any]] = None
    cloud_report: Optional[Dict[str, Any]] = None
    cost_report: Optional[Dict[str, Any]] = None
    devops_report: Optional[Dict[str, Any]] = None
    executive_summary: Optional[Dict[str, Any]] = None
    overall_repository_score: Optional[int] = None
    overall_cloud_readiness_score: Optional[int] = None
    infrastructure_report: Optional[Dict[str, Any]] = None
    deploy_report: Optional[Dict[str, Any]] = None
    monitoring_report: Optional[Dict[str, Any]] = None
    cost_optimization_report: Optional[Dict[str, Any]] = None
    
    # New AI GitHub Engineer fields
    bugs: List[FixSuggestion] = Field(default_factory=list)
    security_issues: List[SecurityIssue] = Field(default_factory=list)
    performance_issues: List[PerformanceIssue] = Field(default_factory=list)
    documentation: Optional[DocumentationSection] = None
    deployment_guide: Optional[DeploymentGuide] = None

