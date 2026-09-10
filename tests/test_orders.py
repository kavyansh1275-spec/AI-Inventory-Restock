import unittest

from app.main import build_order_preview
from app.models import Product
from app.predictor import predict_product


class OrderPreviewTests(unittest.TestCase):
    def test_groups_restock_items_by_supplier(self):
        products = [
            Product(
                name="Protein Powder",
                current_stock=5,
                minimum_stock=10,
                daily_sales=[3, 4, 5],
                lead_time_days=3,
                target_days=7,
                supplier="Supplier A",
            ),
            Product(
                name="Shaker",
                current_stock=2,
                minimum_stock=5,
                daily_sales=[2, 2, 3],
                lead_time_days=3,
                target_days=7,
                supplier="Supplier A",
            ),
        ]

        predictions = [predict_product(product) for product in products]
        result = build_order_preview(predictions)

        self.assertEqual(len(result.orders), 1)
        self.assertEqual(result.orders[0].supplier, "Supplier A")
        self.assertEqual(len(result.orders[0].items), 2)
        self.assertGreater(result.orders[0].total_units, 0)

    def test_flags_restock_without_supplier(self):
        product = Product(
            name="Unknown Supplier Item",
            current_stock=1,
            minimum_stock=10,
            daily_sales=[2, 2, 3],
        )

        result = build_order_preview([predict_product(product)])

        self.assertEqual(result.products_without_supplier, ["Unknown Supplier Item"])
        self.assertEqual(result.orders, [])


if __name__ == "__main__":
    unittest.main()
