"""EntreLíneas backend application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.identity.interface.auth_router import router as auth_router
from app.identity.interface.groups_router import router as groups_router
from app.identity.interface.users_router import router as users_router
from app.library.interface.books_router import router as books_router
from app.library.interface.copies_router import router as copies_router
from app.reading_selection.interface.draws_router import router as draws_router
from app.reviews.interface.reviews_router import books_reviews_router
from app.reviews.interface.reviews_router import router as reviews_router

app = FastAPI(
    title="EntreLíneas API",
    version=settings.app_version,
    description="Personal library management platform",
)

# CORS for local development (frontend on port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(users_router)
app.include_router(books_router)
app.include_router(copies_router)
app.include_router(draws_router)
app.include_router(reviews_router)
app.include_router(books_reviews_router)


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
