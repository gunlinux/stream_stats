from datetime import UTC, datetime

from src.application.ports import HealthRepository, MessageRepository
from src.application.schemas import MessageCreate
from src.domain.entities import HealthCheck, Message
from src.domain.exceptions import MessageNotFoundError


class MessageService:
    """Application service (use cases) for message operations."""

    def __init__(self, repository: MessageRepository) -> None:
        self._repository = repository

    async def list_messages(self, limit: int = 100, offset: int = 0) -> list[Message]:
        return await self._repository.get_all(limit, offset)

    async def get_message(self, message_id: int) -> Message:
        message = await self._repository.get_by_id(message_id)
        if message is None:
            raise MessageNotFoundError(message_id)
        return message

    async def create_message(self, data: MessageCreate) -> Message:
        return await self._repository.create(
            body=data.body,
            source=data.source,
            message_id=data.message_id,
            author_id=data.author_id,
            stream_id=data.stream_id,
            channel_id=data.channel_id,
            created_at=datetime.now(UTC),
        )

    async def delete_message(self, message_id: int) -> None:
        deleted = await self._repository.delete(message_id)
        if not deleted:
            raise MessageNotFoundError(message_id)


class HealthService:
    """Application service for health checks."""

    def __init__(self, repository: HealthRepository) -> None:
        self._repository = repository

    async def check_health(self) -> HealthCheck:
        try:
            await self._repository.ping()
            database = "connected"
        except Exception:
            # No exception details leaked to clients; the status field carries
            # the only signal a load balancer / orchestrator needs.
            database = "disconnected"

        return HealthCheck(
            status="healthy" if database == "connected" else "unhealthy",
            timestamp=datetime.now(UTC),
            database=database,
        )
