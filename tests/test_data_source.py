import tempfile
import unittest
from pathlib import Path

from app.data_source import CSVInventorySource


CSV = "name,current_stock,minimum_stock,daily_sales,lead_time_days,target_days,supplier\nProtein Powder,10,20,5|6|5,4,14,Fitness Supply Co.\n"


class DataSourceTests(unittest.TestCase):
    def test_load_if_changed_only_reads_new_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.csv"
            path.write_text(CSV, encoding="utf-8")
            source = CSVInventorySource(path)
            self.assertEqual(len(source.load_if_changed()), 1)
            self.assertIsNone(source.load_if_changed())
            path.write_text(CSV.replace(",10,", ",8,"), encoding="utf-8")
            self.assertEqual(source.load_if_changed()[0].current_stock, 8)


if __name__ == "__main__":
    unittest.main()
