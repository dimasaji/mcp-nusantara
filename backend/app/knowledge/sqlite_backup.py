"""Consistent, standalone backups for the existing SQLite knowledge owners."""

import os
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4


def backup_sqlite_database(source: Path, destination: Path) -> Path:
    """Capture committed WAL state without checkpointing or rewriting source.

    Publish only a closed, integrity-checked snapshot. Existing backups are
    never intentionally replaced; callers supply distinct timestamped names.
    """
    source = Path(source).resolve()
    destination = Path(destination).absolute()
    if not source.is_file():
        raise FileNotFoundError(source)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name("." + destination.name + "." + uuid4().hex + ".tmp")
    try:
        with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=15)) as reader:
            reader.execute("PRAGMA query_only=ON")
            with closing(sqlite3.connect(temporary)) as snapshot_connection:
                reader.backup(snapshot_connection, pages=512, sleep=0.01)
                if snapshot_connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise sqlite3.DatabaseError("SQLite backup integrity check failed")
        with temporary.open("rb+") as stream:
            os.fsync(stream.fileno())
        temporary.rename(destination)
        return destination
    finally:
        temporary.unlink(missing_ok=True)
