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

    # CORS: comma-separated list of allowed origins. Credentials are enabled,
    # so a wildcard origin is not valid — set the real origins in production.
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()
