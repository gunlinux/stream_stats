from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.application.schemas import MessageCreate
from src.application.services import MessageService
from src.domain.entities import Message
from src.interfaces.dependencies import get_message_service

router = APIRouter()

MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]


@router.get("/messages", response_model=list[Message])
async def get_messages(
    service: MessageServiceDep,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[Message]:
    """Get messages, newest first, with pagination"""
    return await service.list_messages(limit, offset)


@router.post("/messages", response_model=Message, status_code=201)
async def create_message(message: MessageCreate, service: MessageServiceDep) -> Message:
    """Create a new message"""
    return await service.create_message(message)


@router.get("/messages/{message_id}", response_model=Message)
async def get_message(message_id: int, service: MessageServiceDep) -> Message:
    """Get a message by its ID"""
    return await service.get_message(message_id)


@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(message_id: int, service: MessageServiceDep) -> None:
    """Delete a message by its ID"""
    await service.delete_message(message_id)
