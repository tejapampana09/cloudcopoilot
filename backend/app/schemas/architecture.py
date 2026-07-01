from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class RepositoryContext(BaseModel):
    project_name: str
    project_type: str
    frontend_framework: Optional[str]
    backend_framework: Optional[str]
    programming_languages: List[str]
    package_managers: List[str]
    databases: List[str]
    orm: List[str]
    authentication: List[str]
    storage: List[str]
    caching: List[str]
    queues: List[str]
    third_party_apis: List[str]
    environment_variables: List[str]
    deployment_requirements: List[str]
    docker_availability: bool
    infrastructure_files: List[str]
    build_commands: List[str]
    run_commands: List[str]
    project_complexity: str
    expected_scalability: str
    repository_structure: Dict[str, int]
    dependencies: List[str]

class TechnologyAnalysis(BaseModel):
    frontend_stack: str
    backend_stack: str
    database: Optional[str]
    api_style: str
    authentication: str
    service_architecture: str
    ssr_vs_spa: str
    serverless_readiness: str
    container_readiness: str
    cloud_readiness: str
    detection_confidence: Dict[str, int]

class ArchitectureSummary(BaseModel):
    application_boundaries: str
    frontend: str
    backend: str
    database: str
    storage: str
    networking: str
    authentication_flow: str
    external_integrations: str
    background_jobs: str
    static_assets: str
    media_handling: str
    state_management: str
    deployment_model: str
    bottlenecks: str
    scaling_risks: str
    availability_requirements: str

class AWSRecommendationDetail(BaseModel):
    service: str
    purpose: str
    reason: str
    advantages: List[str]
    trade_offs: List[str]
    alternatives: List[str]
    estimated_monthly_cost_impact: float
    confidence_score: int

class ArchitectureReport(BaseModel):
    repository_summary: str
    technology_stack: str
    architecture_overview: str
    detected_components: List[str]
    aws_architecture_recommendation: List[AWSRecommendationDetail]
    reasons: List[str]
    trade_offs: List[str]
    security_review: str
    performance_review: str
    scalability_review: str
    cost_analysis: str
    deployment_strategy: str
    risk_assessment: str
    future_improvements: str
    overall_architecture_score: int
    cloud_readiness_score: int

class VisualizationNode(BaseModel):
    id: str
    type: str
    label: str
    metadata: Optional[Dict[str, str]]

class VisualizationConnection(BaseModel):
    source: str
    target: str
    label: Optional[str]

class VisualizationJSON(BaseModel):
    nodes: List[VisualizationNode]
    connections: List[VisualizationConnection]

class AnalysisResponsePayload(BaseModel):
    repository_context: RepositoryContext
    technology_analysis: TechnologyAnalysis
    architecture_analysis: ArchitectureSummary
    reasoning: str
    aws_recommendations: List[AWSRecommendationDetail]
    confidence: Dict[str, str]
    security_notes: str
    performance_notes: str
    cost_analysis: str
    deployment_strategy: str
    visualization: VisualizationJSON
    architecture_report: ArchitectureReport
