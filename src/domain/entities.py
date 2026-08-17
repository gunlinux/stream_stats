from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class Source(IntEnum):
    """Message source platform."""

    TWITCH = 0
    YOUTUBE = 1


class Message(BaseModel):
    """Domain entity representing a message."""

    id: int = Field(..., description="message ID")
    body: str = Field(..., description="Текст сообщения")
    source: Source = Field(..., description="0 twitch, 1 youtube")
    message_id: str = Field(..., description="id внешней системы")
    author_id: str = Field(..., description="ID чаттерса")
    stream_id: str = Field(..., description="ID стрима")
    channel_id: str = Field(..., description="Id канала")
    created_at: datetime = Field(..., description="Message creation timestamp")


class HealthCheck(BaseModel):
    """Domain entity representing a health-check result."""

    status: str = Field(..., description='"healthy" or "unhealthy"')
    timestamp: datetime = Field(..., description="Health check timestamp")
    database: str = Field(..., description='"connected" or "disconnected"')
