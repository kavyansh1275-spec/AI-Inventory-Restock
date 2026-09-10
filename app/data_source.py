import csv
from pathlib import Path

from .csv_parser import parse_inventory_csv
from .models import Product


class CSVInventorySource:
    """Dependency-free inventory source for a local CSV file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._last_mtime_ns: int | None = None

    def changed(self) -> bool:
        if not self.path.exists():
            return False
        mtime = self.path.stat().st_mtime_ns
        if mtime != self._last_mtime_ns:
            self._last_mtime_ns = mtime
            return True
        return False

    def load(self) -> list[Product]:
        text = self.path.read_text(encoding="utf-8-sig")
        return parse_inventory_csv(text)

    def load_if_changed(self) -> list[Product] | None:
        if not self.changed():
            return None
        return self.load()
