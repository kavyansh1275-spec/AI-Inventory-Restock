import threading
import time
from collections.abc import Callable


class InventoryMonitor:
    """Simple local polling loop for an inventory check callback.

    The loop is intentionally lightweight and dependency-free. The callback
    decides how inventory is loaded and what to do with the monitoring report.
    """

    def __init__(self, check: Callable[[], object], interval_seconds: int = 3600):
        if interval_seconds < 60:
            raise ValueError("interval_seconds must be at least 60 seconds")
        self.check = check
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def run_once(self):
        return self.check()

    def start(self) -> None:
        if self.running:
            return

        self._stop_event.clear()

        def loop() -> None:
            while not self._stop_event.is_set():
                try:
                    self.check()
                except Exception:
                    # Monitoring must continue after a transient data-source error.
                    pass
                self._stop_event.wait(self.interval_seconds)

        self._thread = threading.Thread(target=loop, name="inventory-monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=2)
        self._thread = None
