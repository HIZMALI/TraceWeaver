"""A thread-affine, context-managed adapter over the real Relate Python API."""

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import relate


class StorageError(RuntimeError):
    """Application error retaining the engine's reason for terminal diagnostics."""


class DatabaseUnavailable(StorageError):
    """The store cannot be opened, read, or closed."""


class QueryError(StorageError):
    """A query or integrity check failed."""


class GraphStore:
    """Open, use, and close one connection on one thread. Read-only by default."""

    def __init__(self, database: str | Path, *, read_only: bool = True) -> None:
        self.database = str(database)
        self.read_only = read_only
        self._connection: relate.Connection | None = None

    def __enter__(self) -> "GraphStore":
        if self._connection is not None:
            raise QueryError("This store connection is already open")
        try:
            if self.database != ":memory:":
                path = Path(self.database)
                if path.suffix.lower() != ".rl":
                    raise DatabaseUnavailable("The database must be a .rl file")
                if self.read_only and not path.is_file():
                    raise DatabaseUnavailable(
                        f"Database not found: {path}. Run the seed command first"
                    )
                if not self.read_only:
                    path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = relate.connect(self.database, read_only=self.read_only)
        except (relate.Error, OSError) as exc:
            raise DatabaseUnavailable(f"Cannot open Relate store: {exc}") from exc
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except (relate.Error, OSError) as close_error:
                if exc is None:
                    raise DatabaseUnavailable(
                        f"Cannot close Relate store: {close_error}"
                    ) from close_error
                exc.add_note(f"Relate close also failed: {close_error}")

    def _conn(self) -> relate.Connection:
        if self._connection is None:
            raise DatabaseUnavailable("The Relate connection is not open")
        return self._connection

    def execute(self, statement: str, params: dict[str, Any] | None = None) -> list[dict]:
        try:
            return [dict(row) for row in self._conn().execute(statement, params or {}).fetchall()]
        except relate.OperationalError as exc:
            raise DatabaseUnavailable(f"Relate operation failed: {exc}") from exc
        except relate.Error as exc:
            raise QueryError(f"Relate query failed: {exc}") from exc

    @contextmanager
    def transaction(self) -> Iterator["GraphStore"]:
        connection = self._conn()
        if self.read_only:
            raise QueryError("Write transactions require an explicit writable connection")
        if not connection.autocommit:
            raise QueryError("Nested transactions are not supported")
        connection.autocommit = False
        try:
            yield self
            connection.commit()
        except BaseException as exc:
            try:
                connection.rollback()
            except relate.Error as rollback_error:
                exc.add_note(f"Relate rollback also failed: {rollback_error}")
            else:
                connection.autocommit = True
            if isinstance(exc, relate.Error):
                raise QueryError(f"Relate transaction failed: {exc}") from exc
            raise
        else:
            connection.autocommit = True

    def counts(self) -> dict[str, int]:
        nodes = self.execute("MATCH (n) RETURN count(n) AS node_count")[0]["node_count"]
        edges = self.execute("MATCH ()-[r]->() RETURN count(r) AS relationship_count")[0][
            "relationship_count"
        ]
        return {"node_count": nodes, "relationship_count": edges}
