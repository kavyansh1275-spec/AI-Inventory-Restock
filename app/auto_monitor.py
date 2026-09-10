import os
from pathlib import Path

from .alert_storage import persist_alerts
from .data_source import CSVInventorySource
from .monitor import build_monitoring_report
from .notifier import notify_alerts
from .predictor import predict_product
from .storage import save_snapshot


class AutomaticInventoryMonitor:
    """Runs prediction and alerting whenever the watched CSV changes."""

    def __init__(self, csv_path: str | Path):
        self.source = CSVInventorySource(csv_path)

    def check(self) -> dict:
        products = self.source.load_if_changed()
        if products is None:
            return {"changed": False, "alerts": [], "notifications_sent": 0}

        predictions = [predict_product(product) for product in products]
        report = build_monitoring_report(predictions)
        active = persist_alerts(report["alerts"])
        report["alerts"] = active
        report["alert_count"] = len(active)
        report["critical_count"] = sum(a["urgency"] == "critical" for a in active)
        save_snapshot({"products": [p.model_dump() for p in predictions], "summary": {
            "total_products": len(predictions),
            "products_needing_restock": sum(p.needs_restock for p in predictions),
            "critical_products": sum(p.urgency == "critical" for p in predictions),
            "products_with_increasing_sales": sum(p.sales_trend == "increasing" for p in predictions),
        }})
        sent = notify_alerts(active)
        return {"changed": True, "alerts": active, "notifications_sent": sent}


def build_auto_monitor() -> AutomaticInventoryMonitor:
    path = os.getenv("INVENTORY_CSV_PATH", "inventory.csv")
    return AutomaticInventoryMonitor(path)
