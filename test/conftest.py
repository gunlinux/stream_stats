import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import psycopg2
import pytest
from fastapi.testclient import TestClient
from pytest_postgresql import factories
from pytest_postgresql.janitor import DatabaseJanitor

# Settings are read from the environment at import time (pydantic-settings),
# so API_TOKEN must be set before importing the app.
os.environ.setdefault("API_TOKEN", "test-api-token")

from src.infrastructure.config import settings
from src.infrastructure.database import db_manager
from src.main import app


def _find_pg_ctl() -> str:
    """Locate ``pg_ctl``, including Homebrew's keg-only PostgreSQL installs."""
    found = shutil.which("pg_ctl")
    if found:
        return found
    for brew_prefix in (Path("/opt/homebrew"), Path("/usr/local")):
        for candidate in sorted((brew_prefix / "opt").glob("postgresql*/bin/pg_ctl")):
            return str(candidate)
    raise RuntimeError(
        "Could not find pg_ctl. Install PostgreSQL (e.g. `brew install postgresql@15`)."
    )


postgresql_proc = factories.postgresql_proc(executable=_find_pg_ctl())


@pytest.fixture(scope="session")
def database_url(postgresql_proc) -> str:
    """Point the app's db_manager at the ephemeral pytest-postgresql database.

    ``postgresql_proc`` only creates the ``<dbname>_tmpl`` template, so create
    the actual test database from it and apply the project's migrations once.
    """
    proc = postgresql_proc
    auth = f"{proc.user}:{proc.password}@" if proc.password else f"{proc.user}@"
    dsn = f"postgresql://{auth}{proc.host}:{proc.port}/{proc.dbname}"
    janitor = DatabaseJanitor(
        user=proc.user,
        host=proc.host,
        port=proc.port,
        dbname=proc.dbname,
        template_dbname=proc.template_dbname,
        version=proc.version,
        password=proc.password,
    )
    with janitor:
        db_manager.database_url = dsn
        db_manager.apply_migrations()
        yield dsn


@pytest.fixture(autouse=True)
def _clean_messages(database_url: str) -> None:
    """Truncate ``messages`` before each test so tests are order-independent."""
    with psycopg2.connect(database_url) as conn, conn.cursor() as cur:
        cur.execute("TRUNCATE messages RESTART IDENTITY")


@pytest.fixture
def client(database_url: str) -> Iterator[TestClient]:
    """Create a test client for the FastAPI app (authenticated with the test token).

    Runs the app within its lifespan so the asyncpg pool is opened and closed
    per test; a bare TestClient leaks a 10-connection pool per event loop,
    which exhausts the ephemeral PostgreSQL's client limit mid-suite.
    """
    with TestClient(
        app, headers={"Authorization": f"Bearer {settings.api_token}"}
    ) as test_client:
        yield test_client
