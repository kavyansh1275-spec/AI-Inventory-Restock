from collections import defaultdict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .csv_parser import parse_inventory_csv
from .models import (
    InventoryRequest,
    InventoryResponse,
    OrderPreviewResponse,
    SupplierOrderItem,
    SupplierOrderPreview,
)
from .predictor import predict_product
from .storage import get_latest_snapshot, get_snapshots, init_db, save_snapshot

APP_VERSION = "0.6.0"

app = FastAPI(
    title="AI Inventory Restock Predictor",
    version=APP_VERSION,
    description="Predicts inventory risk and suggested reorder quantities from recent sales.",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
def startup() -> None:
    init_db()


def analyze_products(products):
    predictions = [predict_product(product) for product in products]
    restock_count = sum(item.needs_restock for item in predictions)
    critical_count = sum(item.urgency == "critical" for item in predictions)
    increasing_count = sum(item.sales_trend == "increasing" for item in predictions)

    response = InventoryResponse(
        products=predictions,
        summary={
            "total_products": len(predictions),
            "products_needing_restock": restock_count,
            "critical_products": critical_count,
            "products_with_increasing_sales": increasing_count,
        },
    )
    save_snapshot(response.model_dump())
    return response


def build_order_preview(predictions) -> OrderPreviewResponse:
    grouped = defaultdict(list)
    without_supplier = []

    for item in predictions:
        if not item.needs_restock or item.suggested_reorder_quantity <= 0:
            continue
        if not item.supplier:
            without_supplier.append(item.name)
            continue

        grouped[item.supplier].append(
            SupplierOrderItem(
                product=item.name,
                supplier=item.supplier,
                quantity=item.suggested_reorder_quantity,
                urgency=item.urgency,
            )
        )

    orders = [
        SupplierOrderPreview(
            supplier=supplier,
            items=items,
            total_units=round(sum(item.quantity for item in items), 2),
        )
        for supplier, items in sorted(grouped.items())
    ]

    return OrderPreviewResponse(
        orders=orders,
        products_without_supplier=sorted(without_supplier),
    )


def build_alerts(predictions) -> list[dict]:
    alerts = []
    for item in predictions:
        if item.urgency == "critical":
            alerts.append({
                "level": "critical",
                "product": item.name,
                "message": f"{item.name} may run out during supplier lead time.",
                "recommended_action": f"Order {item.suggested_reorder_quantity} units.",
            })
        elif item.urgency == "high":
            alerts.append({
                "level": "high",
                "product": item.name,
                "message": f"{item.name} is at or below its minimum stock.",
                "recommended_action": f"Review an order for {item.suggested_reorder_quantity} units.",
            })
        elif item.sales_trend == "increasing" and item.needs_restock:
            alerts.append({
                "level": "medium",
                "product": item.name,
                "message": f"Sales for {item.name} are increasing while stock needs replenishment.",
                "recommended_action": "Review the suggested reorder quantity soon.",
            })
    return alerts


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "version": APP_VERSION}


@app.post("/predict", response_model=InventoryResponse)
def predict(request: InventoryRequest) -> InventoryResponse:
    return analyze_products(request.products)


@app.post("/predict/csv", response_model=InventoryResponse)
async def predict_csv(file: UploadFile = File(...)) -> InventoryResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    try:
        raw = await file.read()
        text = raw.decode("utf-8-sig")
        products = parse_inventory_csv(text)
        request = InventoryRequest(products=products)
        return analyze_products(request.products)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/orders/preview", response_model=OrderPreviewResponse)
def order_preview(request: InventoryRequest) -> OrderPreviewResponse:
    predictions = [predict_product(product) for product in request.products]
    return build_order_preview(predictions)


@app.post("/alerts")
def alerts(request: InventoryRequest) -> dict:
    predictions = [predict_product(product) for product in request.products]
    return {"alerts": build_alerts(predictions)}


@app.get("/history")
def history(limit: int = 20) -> dict:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    return {"snapshots": get_snapshots(limit)}


@app.get("/history/latest")
def latest_history() -> dict:
    snapshot = get_latest_snapshot()
    return {"snapshot": snapshot}
