from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DemoRequest(BaseModel):
    input: str = Field(min_length=1, max_length=10_000)


class DemoRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID
    input: str
    status: Literal["created"] = "created"
    timestamp: datetime


class DemoResponse(DemoRecord):
    """Public API representation of a persisted demo record."""
