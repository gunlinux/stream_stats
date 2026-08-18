"""Composition root.

Wires application ports to their infrastructure adapters and exposes FastAPI
dependency providers so routers can request services through ``Depends``.
"""

from secrets import compare_digest
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.ports import HealthRepository, MessageRepository
from src.application.services import HealthService, MessageService
from src.infrastructure.config import settings
from src.infrastructure.database import db_manager
from src.infrastructure.repositories import (
    PostgresHealthRepository,
    PostgresMessageRepository,
)

message_repository: MessageRepository = PostgresMessageRepository(db_manager)
health_repository: HealthRepository = PostgresHealthRepository(db_manager)

message_service = MessageService(message_repository)
health_service = HealthService(health_repository)

# Static bearer-token auth: the token is set via the API_TOKEN env var.
bearer_scheme = HTTPBearer(auto_error=False)


def get_api_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> None:
    """Guard-only dependency: 401 unless the bearer token matches API_TOKEN."""
    if credentials is None or not compare_digest(
        credentials.credentials, settings.api_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_message_service() -> MessageService:
    return message_service


def get_health_service() -> HealthService:
    return health_service
