from typing import Protocol
from uuid import UUID

from app.models.demo import DemoRecord


class Repository(Protocol):
    """Small persistence boundary implemented by each database adapter."""

    def initialize(self) -> None: ...

    def save_demo(self, record: DemoRecord) -> DemoRecord: ...

    def get_demo(self, record_id: UUID) -> DemoRecord | None: ...
