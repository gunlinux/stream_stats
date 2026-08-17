import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import asyncpg
from yoyo import get_backend, read_migrations

from src.infrastructure.config import settings


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
                print("Database is ready!")
                return
            except Exception as e:
                print(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
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
                print("No migrations found")
                return

            # Apply migrations
            with backend.lock():
                # Get migrations that need to be applied
                to_apply = backend.to_apply(migrations)
                if to_apply:
                    print(f"Applying {len(to_apply)} migrations...")
                    for migration in to_apply:
                        print(f"  - Applying: {migration.id}")
                        try:
                            backend.apply_one(migration)
                            print(f"    ✅ Successfully applied: {migration.id}")
                        except Exception as e:
                            print(f"    ❌ Error applying {migration.id}: {e}")
                            raise
                    print(f"Applied {len(to_apply)} migrations successfully")
                else:
                    print("All migrations are already applied")

        except Exception as e:
            print(f"Error applying migrations: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
