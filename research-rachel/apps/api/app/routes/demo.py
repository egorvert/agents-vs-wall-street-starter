from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.models.demo import DemoRequest, DemoResponse
from app.services.demo import DemoService
from app.services.dependencies import get_demo_service

router = APIRouter(prefix="/api", tags=["demo"])


@router.post("/demo", response_model=DemoResponse, status_code=status.HTTP_201_CREATED)
def create_demo(
    request: DemoRequest,
    service: Annotated[DemoService, Depends(get_demo_service)],
) -> DemoResponse:
    return service.create(request)
