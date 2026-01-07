"""
Application configuration using Pydantic settings.
Loads environment variables with sensible defaults for development.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql://infohunter:infohunter_dev@localhost:5432/infohunter_db"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Elasticsearch
    elasticsearch_url: str = "http://localhost:9200"
    
    # Application
    environment: str = "development"
    api_title: str = "Info Hunter API"
    api_version: str = "1.0.0"
    
    # GitHub API (optional token for higher rate limits)
    github_token: Optional[str] = None
    
    # Stack Exchange API key (optional, but recommended)
    stackexchange_key: Optional[str] = None
    
    # AI Provider settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ai_provider: str = "openai"  # openai or anthropic
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

