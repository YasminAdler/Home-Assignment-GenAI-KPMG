import os
from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    # API Settings
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT_INFO: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_INFO", "")
    AZURE_OPENAI_DEPLOYMENT_QA: str = os.getenv("AZURE_OPENAI_DEPLOYMENT_QA", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    
    # Knowledge Base Settings
    KNOWLEDGE_BASE_DIR: str = os.getenv("KNOWLEDGE_BASE_DIR", "../data/phase2_data")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = os.getenv("LOG_DIR", "../logs")
    
    # Supported Languages
    SUPPORTED_LANGUAGES: list = ["en", "he"]
    DEFAULT_LANGUAGE: str = "en"
    
    # HMO Options
    HMO_OPTIONS: list = ["מכבי", "מאוחדת", "כללית"]
    TIER_OPTIONS: list = ["זהב", "כסף", "ארד"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()