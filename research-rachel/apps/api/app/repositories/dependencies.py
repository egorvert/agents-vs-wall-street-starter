from functools import lru_cache

from app.config.settings import get_settings
from app.repositories.base import Repository
from app.repositories.sqlite import SQLiteRepository


@lru_cache
def get_repository() -> Repository:
    """Select the persistence adapter in one place."""

    settings = get_settings()
    return SQLiteRepository.from_url(settings.resolved_database_url)


# Future adapter selection belongs here, for example:
# if settings.resolved_database_url.startswith("postgresql://"):
#     return PostgresRepository(settings.resolved_database_url)
