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

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()
