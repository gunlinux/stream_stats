from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.schemas import MessageCreate
from src.application.services import MessageService
from src.domain.entities import Message
from src.interfaces.dependencies import get_message_service

router = APIRouter()

MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]


@router.get("/messages", response_model=list[Message])
async def get_messages(service: MessageServiceDep) -> list[Message]:
    """Get all messages"""
    return await service.list_messages()


@router.post("/messages", response_model=Message, status_code=201)
async def create_message(message: MessageCreate, service: MessageServiceDep) -> Message:
    """Create a new message"""
    return await service.create_message(message)
