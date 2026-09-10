import unittest

from app.models import Product
from app.predictor import predict_product


class PredictorTests(unittest.TestCase):
    def test_restock_needed_when_stock_will_run_out_during_lead_time(self):
        product = Product(
            name="Protein Powder",
            current_stock=18,
            minimum_stock=10,
            daily_sales=[3, 4, 2, 3, 5, 3, 4],
            lead_time_days=5,
            target_days=14,
        )
        result = predict_product(product)
        self.assertTrue(result.needs_restock)
        self.assertEqual(result.urgency, "critical")
        self.assertGreater(result.suggested_reorder_quantity, 0)

    def test_no_sales_does_not_create_fake_reorder_quantity(self):
        product = Product(
            name="Slow Item",
            current_stock=50,
            minimum_stock=10,
            daily_sales=[0, 0, 0],
        )
        result = predict_product(product)
        self.assertFalse(result.needs_restock)
        self.assertIsNone(result.days_remaining)
        self.assertEqual(result.suggested_reorder_quantity, 0)

    def test_minimum_stock_triggers_restock(self):
        product = Product(
            name="Item",
            current_stock=10,
            minimum_stock=10,
            daily_sales=[1, 1, 1],
        )
        result = predict_product(product)
        self.assertTrue(result.needs_restock)
        self.assertEqual(result.urgency, "high")


if __name__ == "__main__":
    unittest.main()
