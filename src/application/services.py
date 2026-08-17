from datetime import UTC, datetime

from src.application.ports import HealthRepository, MessageRepository
from src.application.schemas import MessageCreate
from src.domain.entities import HealthCheck, Message


class MessageService:
    """Application service (use cases) for message operations."""

    def __init__(self, repository: MessageRepository) -> None:
        self._repository = repository

    async def list_messages(self) -> list[Message]:
        return await self._repository.get_all()

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


class HealthService:
    """Application service for health checks."""

    def __init__(self, repository: HealthRepository) -> None:
        self._repository = repository

    async def check_health(self) -> HealthCheck:
        try:
            await self._repository.ping()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {e!s}"

        return HealthCheck(
            status="healthy",
            timestamp=datetime.now(UTC),
            database=db_status,
        )
