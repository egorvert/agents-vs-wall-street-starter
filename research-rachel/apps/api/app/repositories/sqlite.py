import sqlite3
from pathlib import Path
from uuid import UUID

from app.models.demo import DemoRecord


class SQLiteRepository:
    """SQLite adapter. A Postgres adapter can implement the same Repository protocol."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    @classmethod
    def from_url(cls, database_url: str) -> "SQLiteRepository":
        prefix = "sqlite:///"
        if not database_url.startswith(prefix):
            raise ValueError(
                "Only SQLite is configured. Add PostgresRepository and select it in "
                "app.repositories.dependencies before using another DATABASE_URL."
            )
        return cls(Path(database_url.removeprefix(prefix)))

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_records (
                    id TEXT PRIMARY KEY,
                    input TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )

    def save_demo(self, record: DemoRecord) -> DemoRecord:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO demo_records (id, input, status, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (str(record.id), record.input, record.status, record.timestamp.isoformat()),
            )
        return record

    def get_demo(self, record_id: UUID) -> DemoRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id, input, status, timestamp FROM demo_records WHERE id = ?",
                (str(record_id),),
            ).fetchone()
        return DemoRecord.model_validate(dict(row)) if row else None
