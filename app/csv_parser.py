import csv
import io
from typing import Any


def _number(value: str, field: str) -> float:
    try:
        return float(value.strip())
    except (AttributeError, ValueError):
        raise ValueError(f"Invalid number in {field}: {value!r}")


def parse_inventory_csv(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV must contain a header row")

    required = {"name", "current_stock", "minimum_stock", "daily_sales"}
    missing = required - {name.strip() for name in reader.fieldnames if name}
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    products = []
    for row_number, row in enumerate(reader, start=2):
        raw_sales = (row.get("daily_sales") or "").strip()
        try:
            sales = [float(item.strip()) for item in raw_sales.split(",") if item.strip()]
        except ValueError:
            raise ValueError(f"Row {row_number}: daily_sales must be comma-separated numbers")
        if not sales:
            raise ValueError(f"Row {row_number}: daily_sales cannot be empty")

        product = {
            "name": (row.get("name") or "").strip(),
            "current_stock": _number(row.get("current_stock", ""), "current_stock"),
            "minimum_stock": _number(row.get("minimum_stock", ""), "minimum_stock"),
            "daily_sales": sales,
            "lead_time_days": _number(row.get("lead_time_days", "3") or "3", "lead_time_days"),
            "target_days": _number(row.get("target_days", "14") or "14", "target_days"),
            "supplier": (row.get("supplier") or "").strip() or None,
        }
        products.append(product)

    if not products:
        raise ValueError("CSV contains no product rows")
    return products
