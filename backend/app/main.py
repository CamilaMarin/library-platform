"""EntreLíneas backend application entry point."""

from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.database import engine

app = FastAPI(
    title="EntreLíneas API",
    version=settings.app_version,
    description="Personal library management platform",
)


@app.get("/health")
def health_check():
    """Health check endpoint. Verifies API is running and database is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    return {
        "status": "ok",
        "database": db_status,
        "version": settings.app_version,
    }
