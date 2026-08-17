from datetime import datetime

from src.domain.entities import Message
from src.infrastructure.database import DatabaseManager


class PostgresMessageRepository:
    """asyncpg-backed implementation of the MessageRepository port."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db_manager = db_manager

    async def get_all(self) -> list[Message]:
        async with self._db_manager.get_connection() as conn:
            rows = await conn.fetch(
                """
                SELECT id, body, source, message_id, author_id,
                       stream_id, channel_id, created_at
                FROM messages
                ORDER BY created_at DESC
                """
            )
            return [Message(**row) for row in rows]

    async def get_by_id(self, message_id: int) -> Message | None:
        async with self._db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, body, source, message_id, author_id,
                       stream_id, channel_id, created_at
                FROM messages
                WHERE id = $1
                """,
                message_id,
            )
            return Message(**row) if row else None

    async def create(
        self,
        body: str,
        source: int,
        message_id: str,
        author_id: str,
        stream_id: str,
        channel_id: str,
        created_at: datetime,
    ) -> Message:
        async with self._db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO messages (
                    body, source, message_id,
                    author_id, stream_id, channel_id, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id, body, source, message_id,
                       author_id, stream_id, channel_id, created_at
                """,
                body,
                source,
                message_id,
                author_id,
                stream_id,
                channel_id,
                created_at,
            )
            assert row is not None
            return Message(**row)

    async def delete(self, message_id: int) -> bool:
        async with self._db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                "DELETE FROM messages WHERE id = $1 RETURNING id",
                message_id,
            )
            return row is not None


class PostgresHealthRepository:
    """asyncpg-backed implementation of the HealthRepository port."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db_manager = db_manager

    async def ping(self) -> None:
        async with self._db_manager.get_connection() as conn:
            await conn.fetchval("SELECT 1")
