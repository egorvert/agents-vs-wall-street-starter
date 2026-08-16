from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """A reusable, source-aware fact for structured AI outputs."""

    id: UUID = Field(default_factory=uuid4)
    type: str
    metric: str
    value: str | int | float | bool | None
    unit: str | None = None
    source: str
    source_date: date | None = None
    confidence: float = Field(ge=0, le=1)
    direction: Literal["positive", "negative", "neutral", "unknown"] = "unknown"
    reasoning: str | None = None


class AgentEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    type: str
    message: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    input: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    events: list[AgentEvent] = Field(default_factory=list)
    output: dict[str, Any] | None = None
    error: str | None = None


class ForecastResult(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    summary: str
    value: str | int | float | None = None
    unit: str | None = None
    confidence: float = Field(ge=0, le=1)
    horizon: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
