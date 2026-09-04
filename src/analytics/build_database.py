"""Build the project's reproducible SQLite analytical database."""

import sqlite3
from pathlib import Path

from src.config import REPORTING_SQL, SCHEMA_SQL, SOURCE_REGISTER_PATH, SQL_DIR
from src.ingestion.source_register import load_source_register


def build_database(database_path: Path | str = ":memory:") -> tuple[sqlite3.Connection, int]:
    """Build all staging, dimensional, fact, QA and reporting objects.

    Returns an open connection and the number of registered source records.
    The caller owns the returned connection.
    """
    if database_path != ":memory:":
        resolved_path = Path(database_path)
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        if resolved_path.exists():
            resolved_path.unlink()
        target = str(resolved_path)
    else:
        target = database_path

    connection = sqlite3.connect(target)
    connection.execute("PRAGMA foreign_keys = ON")
    source_count = load_source_register(connection, SOURCE_REGISTER_PATH)

    for filename in (*SCHEMA_SQL, *REPORTING_SQL):
        sql = (SQL_DIR / filename).read_text(encoding="utf-8")
        try:
            connection.executescript(sql)
        except sqlite3.Error as exc:
            connection.close()
            raise RuntimeError(f"SQL execution failed in {filename}: {exc}") from exc

    connection.commit()
    return connection, source_count
