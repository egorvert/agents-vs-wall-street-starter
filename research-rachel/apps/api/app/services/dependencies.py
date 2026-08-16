from typing import Annotated

from fastapi import Depends

from app.repositories.base import Repository
from app.repositories.dependencies import get_repository
from app.services.demo import DemoService


def get_demo_service(
    repository: Annotated[Repository, Depends(get_repository)],
) -> DemoService:
    return DemoService(repository)
