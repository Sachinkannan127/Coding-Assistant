import os
from pathlib import Path
from typing import List
import dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Automatically discover and load root .env file regardless of execution CWD
_root_env = Path(__file__).resolve().parent.parent.parent / ".env"
_backend_env = Path(__file__).resolve().parent.parent / ".env"

if _root_env.exists():
    dotenv.load_dotenv(_root_env, override=True)
elif _backend_env.exists():
    dotenv.load_dotenv(_backend_env, override=True)
else:
    dotenv.load_dotenv(override=True)


class Settings(BaseSettings):
    """
    Application Settings Manager powered by Pydantic Settings.
    Loads configurations from environment variables and root .env file.
    """
    # Application Metadata
    APP_NAME: str = "AI Code Review & Refactoring Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # API Gateway Config
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Primary & Secondary LLM Provider Credentials
    GEMINI_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""

    # Database & Vector Persistence
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "code_pilot"

    # Observability (LangSmith Tracing)
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "code-review-platform"

    # Security & Rate Limiting
    ENABLE_RATE_LIMITING: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60

    # Clerk Authentication Config
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_ISSUER_URL: str = ""
    CLERK_JWKS_URL: str = ""
    REQUIRE_AUTH: bool = False


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
        """Parses CORS_ORIGINS string into a list of origins."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS


# Instantiated global settings object
settings = Settings()


def sanitize_credentials(text: str) -> str:
    """
    Scrubs sensitive API keys and connection strings from error messages and log outputs.
    """
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
