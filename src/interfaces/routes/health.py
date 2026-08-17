from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.services import HealthService
from src.domain.entities import HealthCheck
from src.interfaces.dependencies import get_health_service

router = APIRouter()

HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]


@router.get("/health", response_model=HealthCheck)
async def health_check(service: HealthServiceDep) -> HealthCheck:
    """Health check endpoint"""
    return await service.check_health()
