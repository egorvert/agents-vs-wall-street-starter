import pytest
from pydantic import ValidationError

from app.models.agent import Evidence


def test_evidence_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        Evidence(
            type="observation",
            metric="example",
            value=42,
            source="demo",
            confidence=1.1,
        )
