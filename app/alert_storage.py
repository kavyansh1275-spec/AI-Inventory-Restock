import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from .storage import _connect


def init_alerts_db() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS inventory_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT NOT NULL UNIQUE,
                product TEXT NOT NULL,
                urgency TEXT NOT NULL,
                current_stock REAL NOT NULL,
                days_remaining REAL,
                suggested_reorder_quantity REAL NOT NULL,
                supplier TEXT,
                action TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                payload_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _fingerprint(alert: dict[str, Any]) -> str:
    stable = {
        "product": alert["product"],
        "urgency": alert["urgency"],
        "current_stock": alert["current_stock"],
        "days_remaining": alert["days_remaining"],
        "suggested_reorder_quantity": alert["suggested_reorder_quantity"],
        "supplier": alert["supplier"],
    }
    return hashlib.sha256(json.dumps(stable, sort_keys=True).encode()).hexdigest()


def get_active_fingerprints() -> set[str]:
    init_alerts_db()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT fingerprint FROM inventory_alerts WHERE active=1"
        ).fetchall()
    return {row["fingerprint"] for row in rows}


def persist_alerts(alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    init_alerts_db()
    now = datetime.now(timezone.utc).isoformat()
    fingerprints = []

    with _connect() as connection:
        for alert in alerts:
            fingerprint = _fingerprint(alert)
            fingerprints.append(fingerprint)
            payload = json.dumps(alert)
            connection.execute(
                """
                INSERT INTO inventory_alerts
                (fingerprint, product, urgency, current_stock, days_remaining,
                 suggested_reorder_quantity, supplier, action, first_seen, last_seen,
                 active, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(fingerprint) DO UPDATE SET
                    last_seen=excluded.last_seen,
                    active=1,
                    payload_json=excluded.payload_json
                """,
                (
                    fingerprint, alert["product"], alert["urgency"],
                    alert["current_stock"], alert["days_remaining"],
                    alert["suggested_reorder_quantity"], alert["supplier"],
                    alert["action"], now, now, payload,
                ),
            )

        if fingerprints:
            placeholders = ",".join("?" for _ in fingerprints)
            connection.execute(
                f"UPDATE inventory_alerts SET active=0 WHERE active=1 AND fingerprint NOT IN ({placeholders})",
                fingerprints,
            )
        else:
            connection.execute("UPDATE inventory_alerts SET active=0 WHERE active=1")
        connection.commit()

    return get_active_alerts()


def get_active_alerts() -> list[dict[str, Any]]:
    init_alerts_db()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM inventory_alerts WHERE active=1 ORDER BY CASE urgency WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, product"
        ).fetchall()
    return [
        json.loads(row["payload_json"]) | {
            "id": row["id"], "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
        }
        for row in rows
    ]


def get_alert_history(limit: int = 50) -> list[dict[str, Any]]:
    init_alerts_db()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM inventory_alerts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [
        json.loads(row["payload_json"]) | {
            "id": row["id"], "first_seen": row["first_seen"],
            "last_seen": row["last_seen"], "active": bool(row["active"]),
        }
        for row in rows
    ]
