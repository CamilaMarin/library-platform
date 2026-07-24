"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Values loaded from .env file or environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg2://entrelineas:entrelineas_dev@host.docker.internal:5432/entrelineas"

    # JWT settings (ADR-0004)
    jwt_secret_key: str = "entrelineas-dev-secret-replace-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


settings = Settings()
