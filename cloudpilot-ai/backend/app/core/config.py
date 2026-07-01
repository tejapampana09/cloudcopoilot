import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CloudPilot AI"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI configurations
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # CORS Origins
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # Dynamic temp clone directory inside workspace
    @property
    def TEMP_CLONE_DIR(self) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        clone_path = os.path.join(base_dir, "temp_clones")
        os.makedirs(clone_path, exist_ok=True)
        return clone_path

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
