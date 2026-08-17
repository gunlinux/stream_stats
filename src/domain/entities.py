from datetime import datetime

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Domain entity representing a message."""

    id: int = Field(..., description="message ID")
    body: str = Field(..., description="Текст сообщения")
    source: int = Field(..., description="0 twitch, 1 youtube")
    message_id: str = Field(..., description="id внешней системы")
    author_id: str = Field(..., description="ID чаттерса")
    stream_id: str = Field(..., description="ID стрима")
    channel_id: str = Field(..., description="Id канала")
    created_at: datetime = Field(..., description="Message creation timestamp")


class HealthCheck(BaseModel):
    """Domain entity representing a health-check result."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    database: str = Field(..., description="Database connection status")
