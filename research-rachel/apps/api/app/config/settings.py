from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

API_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = API_ROOT / "data" / "hackathon.db"


class Settings(BaseSettings):
    """Environment-backed configuration with useful local defaults."""

    app_name: str = "Hackathon Starter API"
    openai_api_key: str | None = None
    database_url: str | None = None
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=(API_ROOT / ".env", API_ROOT.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_database_url(self) -> str:
        if self.database_url and self.database_url.strip():
            return self.database_url.strip()
        return f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"

    @property
    def agents_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
