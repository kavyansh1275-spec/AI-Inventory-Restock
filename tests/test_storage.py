import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.storage import get_latest_snapshot, get_snapshots, init_db, save_snapshot


class StorageTests(unittest.TestCase):
    def test_snapshot_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "inventory.db"
            with patch("app.storage.DB_PATH", db_path):
                init_db()
                snapshot_id = save_snapshot({"products": [], "summary": {"total_products": 0}})
                self.assertGreater(snapshot_id, 0)

                latest = get_latest_snapshot()
                self.assertIsNotNone(latest)
                self.assertEqual(latest["id"], snapshot_id)
                self.assertEqual(latest["products"]["summary"]["total_products"], 0)

    def test_history_is_newest_first(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "inventory.db"
            with patch("app.storage.DB_PATH", db_path):
                init_db()
                first = save_snapshot({"version": 1})
                second = save_snapshot({"version": 2})
                snapshots = get_snapshots(10)

                self.assertEqual(snapshots[0]["id"], second)
                self.assertEqual(snapshots[1]["id"], first)


if __name__ == "__main__":
    unittest.main()
