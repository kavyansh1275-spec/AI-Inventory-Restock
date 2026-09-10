from datetime import datetime, timezone
from typing import Any

from .models import ProductPrediction


def build_alerts(predictions: list[ProductPrediction]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []

    for item in predictions:
        if not item.needs_restock:
            continue

        if item.urgency == "critical":
            action = "Restock immediately. Current stock may not cover supplier lead time."
        elif item.urgency == "high":
            action = "Review and confirm a replenishment order soon."
        else:
            action = "Monitor inventory and plan the next replenishment."

        alerts.append(
            {
                "product": item.name,
                "urgency": item.urgency,
                "current_stock": item.current_stock,
                "days_remaining": item.days_remaining,
                "suggested_reorder_quantity": item.suggested_reorder_quantity,
                "supplier": item.supplier,
                "action": action,
            }
        )

    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
    alerts.sort(key=lambda alert: (rank.get(alert["urgency"], 9), alert["product"]))
    return alerts


def build_monitoring_report(predictions: list[ProductPrediction]) -> dict[str, Any]:
    alerts = build_alerts(predictions)
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "attention_required" if alerts else "healthy",
        "alert_count": len(alerts),
        "critical_count": sum(a["urgency"] == "critical" for a in alerts),
        "alerts": alerts,
    }
