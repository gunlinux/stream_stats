import asyncio
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from yoyo import get_backend, read_migrations

from src.infrastructure.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager.

    Runtime database access uses asyncpg (async). Migrations are applied with
    Yoyo, which uses a synchronous psycopg2 backend and runs in a thread.
    """

    def __init__(self) -> None:
        self.database_url = settings.database_url
        self.migrations_path = "resources/migrations"
        self._pool: asyncpg.Pool | None = None
        self._pool_loop: asyncio.AbstractEventLoop | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        loop = asyncio.get_running_loop()
        if self._pool is not None and self._pool_loop is loop:
            return self._pool
        # First use, or the previous pool belongs to a different event loop
        # (e.g. a previous TestClient). Abandon it and create a fresh pool.
        self._pool = await asyncpg.create_pool(self.database_url)
        self._pool_loop = loop
        return self._pool

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._pool_loop = None

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[asyncpg.Connection]:
        """Context manager for an asyncpg connection."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            yield conn

    async def wait_for_database(self, max_retries: int = 30, delay: int = 2) -> None:
        """Wait for the database to be ready."""
        for attempt in range(max_retries):
            try:
                pool = await self._get_pool()
                async with pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                logger.info("Database is ready!")
                return
            except Exception as e:
                logger.warning(
                    "Database not ready (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries,
                    e,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise Exception("Database connection failed after maximum retries")

    def apply_migrations(self) -> None:
        """Apply Yoyo migrations (synchronous psycopg2 backend)."""
        try:
            # Create migrations directory if it doesn't exist
            os.makedirs(self.migrations_path, exist_ok=True)

            # Get the backend
            backend = get_backend(self.database_url)

            # Read migrations
            migrations = read_migrations(self.migrations_path)

            if not migrations:
                logger.info("No migrations found")
                return

            # Apply migrations
            with backend.lock():
                # Get migrations that need to be applied
                to_apply = backend.to_apply(migrations)
                if to_apply:
                    logger.info("Applying %d migrations...", len(to_apply))
                    for migration in to_apply:
                        logger.info("  - Applying: %s", migration.id)
                        try:
                            backend.apply_one(migration)
                            logger.info("    Successfully applied: %s", migration.id)
                        except Exception as e:
                            logger.error("Error applying %s: %s", migration.id, e)
                            raise
                    logger.info("Applied %d migrations successfully", len(to_apply))
                else:
                    logger.info("All migrations are already applied")

        except Exception as e:
            logger.error("Error applying migrations: %s", e)
            raise


# Global database manager instance
db_manager = DatabaseManager()
