"""Composition root.

Wires application ports to their infrastructure adapters and exposes FastAPI
dependency providers so routers can request services through ``Depends``.
"""

from src.application.ports import HealthRepository, MessageRepository
from src.application.services import HealthService, MessageService
from src.infrastructure.database import db_manager
from src.infrastructure.repositories import (
    PostgresHealthRepository,
    PostgresMessageRepository,
)

message_repository: MessageRepository = PostgresMessageRepository(db_manager)
health_repository: HealthRepository = PostgresHealthRepository(db_manager)

message_service = MessageService(message_repository)
health_service = HealthService(health_repository)


def get_message_service() -> MessageService:
    return message_service


def get_health_service() -> HealthService:
    return health_service
