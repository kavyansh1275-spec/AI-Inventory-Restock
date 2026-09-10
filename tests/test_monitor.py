import unittest

from app.models import ProductPrediction
from app.monitor import build_alerts, build_monitoring_report


def prediction(name, urgency, needs_restock=True, supplier=None):
    return ProductPrediction(
        name=name, current_stock=5, minimum_stock=10,
        average_daily_sales=2, recent_daily_sales=2.5,
        sales_trend="increasing", sales_variability=0.5,
        safety_stock=0.5, days_remaining=2.5, reorder_point=10,
        suggested_reorder_quantity=20, needs_restock=needs_restock,
        urgency=urgency, supplier=supplier,
    )


class MonitorTests(unittest.TestCase):
    def test_critical_alert_is_created(self):
        alerts = build_alerts([prediction("Protein Powder", "critical")])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["urgency"], "critical")
        self.assertEqual(alerts[0]["suggested_reorder_quantity"], 20)

    def test_healthy_product_has_no_alert(self):
        alerts = build_alerts([prediction("Yoga Mat", "low", needs_restock=False)])
        self.assertEqual(alerts, [])

    def test_report_counts_critical_alerts(self):
        report = build_monitoring_report([prediction("A", "critical"), prediction("B", "high")])
        self.assertEqual(report["alert_count"], 2)
        self.assertEqual(report["critical_count"], 1)
        self.assertEqual(report["status"], "attention_required")


if __name__ == "__main__":
    unittest.main()
