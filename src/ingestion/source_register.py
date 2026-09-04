"""Load the governed source register into SQLite staging."""

import csv
import sqlite3
from pathlib import Path


def load_source_register(connection: sqlite3.Connection, csv_path: Path) -> int:
    """Replace ``stg_data_source_register`` with the supplied CSV contents."""
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise ValueError("Source register has no header")
        rows = list(reader)

    if len(fieldnames) != len(set(fieldnames)):
        raise ValueError("Source register contains duplicate column names")
    if any(None in row for row in rows):
        raise ValueError("Source register contains a malformed row")

    quoted_columns = ", ".join(
        f'"{name}" TEXT PRIMARY KEY' if name == "dataset_id" else f'"{name}" TEXT'
        for name in fieldnames
    )
    connection.execute("DROP TABLE IF EXISTS stg_data_source_register")
    connection.execute(f"CREATE TABLE stg_data_source_register ({quoted_columns})")

    placeholders = ", ".join("?" for _ in fieldnames)
    column_list = ", ".join(f'"{name}"' for name in fieldnames)
    values = [[row[name] for name in fieldnames] for row in rows]
    connection.executemany(
        f"INSERT INTO stg_data_source_register ({column_list}) VALUES ({placeholders})",
        values,
    )
    return len(rows)
