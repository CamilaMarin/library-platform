from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg2://entrelineas:entrelineas_dev@localhost:5432/entrelineas"
    async_database_url: str = (
        "postgresql+psycopg2://entrelineas:entrelineas_dev@localhost:5432/entrelineas"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
