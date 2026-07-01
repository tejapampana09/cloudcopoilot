from typing import TypedDict, List, Optional
from app.schemas.analyzer import RepoMetadata, DeploymentRecommendation, HealthBreakdown, ChecklistItem, AgentLog

class AnalyzerState(TypedDict):
    repository_url: str
    task_id: str
    owner: str
    repo_name: str
    clone_path: str
    metadata: Optional[RepoMetadata]
    recommendation: Optional[DeploymentRecommendation]
    health_score: Optional[int]
    health_breakdown: Optional[HealthBreakdown]
    checklist: Optional[List[ChecklistItem]]
    ai_summary: Optional[str]
    logs: List[AgentLog]
    error: Optional[str]
