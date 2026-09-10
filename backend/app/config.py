import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "AI Code Review & Refactoring Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API Gateway Config
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # LLM Providers
    GEMINI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""
    
    # Vector Search & Persistence
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "code_pilot"
    
    # Observability
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "code-review-platform"
    
    # Security & Rate Limiting Config
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = SettingsConfigDict(
        env_file=[
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS


settings = Settings()


def sanitize_credentials(text: str) -> str:
    """Scrubs sensitive API keys and connection strings from error messages and log outputs."""
    if not text:
        return text

    sanitized = text
    sensitive_values = [
        settings.GEMINI_API_KEY,
        settings.MISTRAL_API_KEY,
        settings.LANGCHAIN_API_KEY,
        settings.MONGODB_URI
    ]

    for val in sensitive_values:
        if val and len(val.strip()) > 4:
            sanitized = sanitized.replace(val.strip(), "[REDACTED_API_KEY]")

    return sanitized

