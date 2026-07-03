from typing import TypedDict, List, Optional, Dict, Any
from app.schemas.analyzer import RepoMetadata, DeploymentRecommendation, HealthBreakdown, ChecklistItem, AgentLog
from app.schemas.architecture import ArchitectureSummary, TechnologyAnalysis, AWSRecommendationDetail, VisualizationJSON

class AnalyzerState(TypedDict, total=False):
    repository_url: str
    task_id: str
    owner: str
    repo_name: str
    clone_path: str
    branch: Optional[str]
    pat: Optional[str]
    metadata: Optional[RepoMetadata]
    recommendation: Optional[DeploymentRecommendation]
    health_score: Optional[int]
    health_breakdown: Optional[HealthBreakdown]
    checklist: Optional[List[ChecklistItem]]
    ai_summary: Optional[str]
    logs: List[AgentLog]
    error: Optional[str]
    repository_context: Optional[Dict[str, Any]]
    technology_analysis: Optional[TechnologyAnalysis]
    architecture_analysis: Optional[ArchitectureSummary]
    aws_recommendations: Optional[List[AWSRecommendationDetail]]
    confidence: Optional[Dict[str, str]]
    reasoning: Optional[str]
    architecture_report: Optional[Dict[str, Any]]
    visualization: Optional[VisualizationJSON]
    security_notes: Optional[str]
    performance_notes: Optional[str]
    cost_analysis: Optional[str]
    deployment_strategy: Optional[str]
    repository_report: Optional[Dict[str, Any]]
    security_report: Optional[Dict[str, Any]]
    performance_report: Optional[Dict[str, Any]]
    cloud_report: Optional[Dict[str, Any]]
    cost_report: Optional[Dict[str, Any]]
    devops_report: Optional[Dict[str, Any]]
    executive_summary: Optional[Dict[str, Any]]
    overall_repository_score: Optional[int]
    overall_cloud_readiness_score: Optional[int]
    infrastructure_report: Optional[Dict[str, Any]]
    deploy_report: Optional[Dict[str, Any]]
    monitoring_report: Optional[Dict[str, Any]]
    cost_optimization_report: Optional[Dict[str, Any]]
    
    # New AI GitHub Engineer fields
    bugs: Optional[List[Dict[str, Any]]]
    security_issues: Optional[List[Dict[str, Any]]]
    performance_issues: Optional[List[Dict[str, Any]]]
    documentation: Optional[Dict[str, Any]]
    deployment_guide: Optional[Dict[str, Any]]

