import unittest

from app.csv_parser import parse_inventory_csv


class CsvParserTests(unittest.TestCase):
    def test_parses_inventory_csv(self):
        text = '''name,current_stock,minimum_stock,daily_sales,lead_time_days,target_days,supplier
Item A,20,10,"2,3,2",4,14,Supplier A
'''
        products = parse_inventory_csv(text)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["name"], "Item A")
        self.assertEqual(products[0]["daily_sales"], [2.0, 3.0, 2.0])
        self.assertEqual(products[0]["lead_time_days"], 4.0)

    def test_rejects_missing_columns(self):
        with self.assertRaises(ValueError):
            parse_inventory_csv("name,current_stock\nItem,10\n")


if __name__ == "__main__":
    unittest.main()
