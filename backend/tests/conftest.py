"""Shared test fixtures — PostgreSQL-based test database.

Uses the DATABASE_URL environment variable. In CI this points to the
PostgreSQL service container. Locally, developers should have a running
PostgreSQL instance (see .env.example).

This file is loaded by pytest before any test module, ensuring the
DATABASE_URL environment variable is NOT overridden to SQLite.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL from environment; fall back to local dev PostgreSQL.
# This MUST happen before any app imports that read settings.
TEST_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg2://entrelineas:entrelineas_dev@localhost:5432/entrelineas",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_engine(TEST_DATABASE_URL)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
