from datetime import datetime
from typing import Protocol

from src.domain.entities import Message


class MessageRepository(Protocol):
    """Port (interface) for message persistence, implemented by infrastructure."""

    async def get_all(self, limit: int, offset: int) -> list[Message]: ...

    async def get_by_id(self, message_id: int) -> Message | None: ...

    async def create(
        self,
        body: str,
        source: int,
        message_id: str,
        author_id: str,
        stream_id: str,
        channel_id: str,
        created_at: datetime,
    ) -> Message: ...

    async def delete(self, message_id: int) -> bool: ...


class HealthRepository(Protocol):
    """Port (interface) for infrastructure health checks."""

    async def ping(self) -> None: ...
