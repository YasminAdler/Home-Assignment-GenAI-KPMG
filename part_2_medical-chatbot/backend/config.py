from pydantic_settings import BaseSettings
from typing import Literal
from pathlib import Path


class Settings(BaseSettings):
    DEBUG: bool = False
    API_VERSION: str = "v1"

    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str  
    AZURE_OPENAI_DEPLOYMENT_INFO: str
    AZURE_OPENAI_DEPLOYMENT_QA: str
    AZURE_OPENAI_API_VERSION: str = "2023-05-15"

    KNOWLEDGE_BASE_DIR: Path = Path("./data/phase2_data")

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_DIR: Path = Path("./logs")

    API_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
