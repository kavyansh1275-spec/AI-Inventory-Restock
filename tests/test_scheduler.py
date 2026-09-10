import unittest

from app.scheduler import InventoryMonitor


class SchedulerTests(unittest.TestCase):
    def test_run_once_calls_check(self):
        calls = []
        monitor = InventoryMonitor(lambda: calls.append("checked"), interval_seconds=60)
        monitor.run_once()
        self.assertEqual(calls, ["checked"])

    def test_interval_must_be_at_least_one_minute(self):
        with self.assertRaises(ValueError):
            InventoryMonitor(lambda: None, interval_seconds=59)


if __name__ == "__main__":
    unittest.main()
