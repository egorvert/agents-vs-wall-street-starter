from datetime import UTC, datetime
from uuid import uuid4

from app.models.demo import DemoRecord, DemoRequest, DemoResponse
from app.repositories.base import Repository


class DemoService:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository

    def create(self, request: DemoRequest) -> DemoResponse:
        record = DemoRecord(
            id=uuid4(),
            input=request.input,
            timestamp=datetime.now(UTC),
        )
        saved_record = self.repository.save_demo(record)
        return DemoResponse.model_validate(saved_record.model_dump())
