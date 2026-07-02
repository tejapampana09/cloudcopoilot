import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CloudPilot AI"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI configurations
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Database configurations
    DATABASE_URL: str = ""
    
    # JWT configurations
    JWT_SECRET: str = "a1803b4e3c4265ac29a23d45bf4f6c539fff4ecb33f88628c2f350e988fe0fc4"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
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

def get_chat_llm(api_key: str, model_name: str, **kwargs):
    """
    Helper to instantiate ChatOpenAI, automatically routing to OpenRouter 
    if the API key is an OpenRouter key (starts with 'sk-or-').
    """
    from langchain_openai import ChatOpenAI
    if api_key and api_key.startswith("sk-or-"):
        base_url = "https://openrouter.ai/api/v1"
        if "/" not in model_name:
            model_name = f"openai/{model_name}"
        return ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            **kwargs
        )
    return ChatOpenAI(
        api_key=api_key,
        model_name=model_name,
        **kwargs
    )

