from pydantic import BaseModel, Field

from src.domain.entities import Source


class MessageCreate(BaseModel):
    """Input DTO for creating a message."""

    body: str = Field(..., description="Текст сообщения")
    source: Source = Field(..., description="0 twitch, 1 youtube")
    message_id: str = Field(..., description="id внешней системы")
    author_id: str = Field(..., description="ID чаттерса")
    author: str = Field("", description="Отображаемое имя чаттерса")
    stream_id: str = Field(..., description="ID стрима")
    channel_id: str = Field(..., description="Id канала")
