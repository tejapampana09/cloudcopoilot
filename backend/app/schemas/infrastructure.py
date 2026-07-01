from pydantic import BaseModel, Field
from typing import Dict, List, Optional

class InfrastructureRequest(BaseModel):
    repository_url: str = Field(..., description="The HTTPS or SSH URL of the public GitHub repository")

class InfrastructureResponse(BaseModel):
    generation_id: str = Field(..., description="The unique generation session ID")
    status: str = Field(..., description="The status of the generation process (pending, generating, completed, failed)")
    progress: int = Field(..., description="The percentage progress (0-100)")
    detected_framework: str = Field(..., description="The primary tech stack framework detected")
    generated_files: Dict[str, str] = Field(default_factory=dict, description="A mapping of generated file paths to their content")
    validation_score: int = Field(0, description="The syntax/reference validation score (0-100)")
    next_step: str = Field(..., description="The active or next step in the pipeline")
    error: Optional[str] = None
