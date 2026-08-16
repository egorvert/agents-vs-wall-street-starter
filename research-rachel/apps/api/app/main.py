from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.repositories.base import Repository
from app.repositories.dependencies import get_repository
from app.routes.demo import router as demo_router
from app.routes.health import router as health_router


def create_app(repository: Repository | None = None) -> FastAPI:
    selected_repository = repository or get_repository()
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        selected_repository.initialize()
        yield

    application = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.include_router(health_router)
    application.include_router(demo_router)

    if repository is not None:
        application.dependency_overrides[get_repository] = lambda: selected_repository

    return application


app = create_app()
