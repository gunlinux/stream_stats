from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Input DTO for creating a message."""

    body: str = Field(..., description="Текст сообщения")
    source: int = Field(..., ge=0, le=1, description="0 twitch, 1 youtube")
    message_id: str = Field(..., description="id внешней системы")
    author_id: str = Field(..., description="ID чаттерса")
    stream_id: str = Field(..., description="ID стрима")
    channel_id: str = Field(..., description="Id канала")
