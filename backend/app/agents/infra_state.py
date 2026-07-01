from typing import TypedDict, List, Dict, Optional, Any
from app.schemas.analyzer import RepoMetadata, AgentLog

class InfrastructureState(TypedDict):
    repository_url: str
    generation_id: str
    clone_path: str
    metadata: RepoMetadata
    plan: List[str]                  # E.g. ["Docker", "Compose", "Environment", "Terraform", "GitHub Actions"]
    generated_files: Dict[str, str]   # Relative path (e.g. 'Dockerfile') -> file content
    validation_report: Dict[str, Any] # {"score": 95, "results": [{"file": "Dockerfile", "status": "valid"}]}
    zip_path: Optional[str]
    status: str                       # pending, generating, completed, failed
    progress: int                     # 0-100
    logs: List[AgentLog]
    error: Optional[str]
