import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path("inventory.db")


def _connect() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                products_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


def save_snapshot(products: list[dict[str, Any]]) -> int:
    with _connect() as connection:
        cursor = connection.execute(
            "INSERT INTO inventory_snapshots (products_json) VALUES (?)",
            (json.dumps(products),),
        )
        connection.commit()
        return int(cursor.lastrowid)


def get_snapshots(limit: int = 20) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, created_at, products_json FROM inventory_snapshots "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "created_at": row["created_at"],
            "products": json.loads(row["products_json"]),
        }
        for row in rows
    ]


def get_latest_snapshot() -> dict[str, Any] | None:
    snapshots = get_snapshots(limit=1)
    return snapshots[0] if snapshots else None
