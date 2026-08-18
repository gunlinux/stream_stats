from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Database settings
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"

    # Application settings
    app_name: str = "FastAPI App"
    environment: str = "development"
    debug: bool = True

    # API settings
    api_prefix: str = "/api/v1"

    # Static bearer token protecting the API. No default: the app fails to
    # start unless API_TOKEN is set (fail-closed).
    api_token: str

    # CORS: comma-separated list of allowed origins. Credentials are enabled,
    # so a wildcard origin is not valid — set the real origins in production.
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @model_validator(mode="after")
    def _api_token_must_not_be_empty(self) -> Self:
        """Reject a blank API_TOKEN so the API cannot silently start locked out."""
        if not self.api_token:
            raise ValueError("API_TOKEN must be set to a non-empty value")
        return self


# Global settings instance. api_token is bound from the API_TOKEN env var at
# import time; the ignore is scoped to that required field (pydantic-settings
# reads it from the environment, so mypy cannot see the argument).
settings = Settings()  # type: ignore[call-arg]
