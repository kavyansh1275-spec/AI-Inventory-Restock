import logging
import os
from typing import Any

logger = logging.getLogger("inventory.notifications")


class NotificationBackend:
    """Small notification abstraction with a safe local default."""

    def send(self, title: str, message: str, payload: dict[str, Any] | None = None) -> None:
        raise NotImplementedError


class ConsoleNotifier(NotificationBackend):
    def send(self, title: str, message: str, payload: dict[str, Any] | None = None) -> None:
        logger.warning("%s: %s", title, message)


def get_notifier() -> NotificationBackend:
    backend = os.getenv("INVENTORY_NOTIFICATION_BACKEND", "console").lower()
    if backend == "console":
        return ConsoleNotifier()
    raise ValueError(f"Unsupported notification backend: {backend}")


def notify_alerts(alerts: list[dict[str, Any]]) -> int:
    if not alerts:
        return 0
    notifier = get_notifier()
    sent = 0
    for alert in alerts:
        title = f"Inventory {alert['urgency']} alert: {alert['product']}"
        message = alert["action"]
        notifier.send(title, message, alert)
        sent += 1
    return sent
