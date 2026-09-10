import unittest
from pathlib import Path

from app import alert_storage
from app.models import ProductPrediction
from app.monitor import build_alerts


class AlertStorageTests(unittest.TestCase):
    def setUp(self):
        self.original = alert_storage._connect
        self.db = Path("test_alerts.db")
        alert_storage.DB_PATH = self.db

    def tearDown(self):
        if self.db.exists():
            self.db.unlink()

    def make_alert(self, urgency="critical", stock=5):
        prediction = ProductPrediction(
            name="Protein Powder", current_stock=stock, minimum_stock=10,
            average_daily_sales=2, recent_daily_sales=2.5,
            sales_trend="increasing", sales_variability=0.5,
            safety_stock=0.5, days_remaining=2.5, reorder_point=10,
            suggested_reorder_quantity=20, needs_restock=True,
            urgency=urgency, supplier="Fitness Supply Co.",
        )
        return build_alerts([prediction])

    def test_persisted_alert_is_reused_not_duplicated(self):
        first = alert_storage.persist_alerts(self.make_alert())
        second = alert_storage.persist_alerts(self.make_alert())
        history = alert_storage.get_alert_history()
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["active"])

    def test_old_alert_becomes_inactive(self):
        alert_storage.persist_alerts(self.make_alert())
        alert_storage.persist_alerts([])
        active = alert_storage.get_active_alerts()
        history = alert_storage.get_alert_history()
        self.assertEqual(active, [])
        self.assertFalse(history[0]["active"])


if __name__ == "__main__":
    unittest.main()
