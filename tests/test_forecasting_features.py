import unittest

from app.models import Product
from app.predictor import predict_product


class ForecastingFeatureTests(unittest.TestCase):
    def test_increasing_sales_trend_is_detected(self):
        product = Product(
            name="Growing Item",
            current_stock=100,
            minimum_stock=10,
            daily_sales=[2, 2, 2, 3, 4, 5],
        )
        result = predict_product(product)
        self.assertEqual(result.sales_trend, "increasing")
        self.assertGreater(result.recent_daily_sales, result.average_daily_sales)

    def test_variability_creates_safety_stock(self):
        product = Product(
            name="Variable Item",
            current_stock=100,
            minimum_stock=10,
            daily_sales=[1, 8, 1, 8, 1, 8],
            lead_time_days=4,
        )
        result = predict_product(product)
        self.assertGreater(result.sales_variability, 0)
        self.assertGreater(result.safety_stock, 0)
        self.assertGreaterEqual(result.reorder_point, result.minimum_stock)

    def test_zero_sales_remains_stable(self):
        product = Product(
            name="No Sales",
            current_stock=50,
            minimum_stock=10,
            daily_sales=[0, 0, 0],
        )
        result = predict_product(product)
        self.assertEqual(result.sales_trend, "stable")
        self.assertEqual(result.safety_stock, 0)


if __name__ == "__main__":
    unittest.main()
