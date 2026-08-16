from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.sqlite import SQLiteRepository


@pytest.fixture
def repository(tmp_path):
    return SQLiteRepository(tmp_path / "test.db")


@pytest.fixture
def client(repository: SQLiteRepository) -> Iterator[TestClient]:
    with TestClient(create_app(repository)) as test_client:
        yield test_client
