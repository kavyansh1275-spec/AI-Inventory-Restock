import os
from collections import defaultdict

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .alert_storage import get_active_alerts, get_alert_history, init_alerts_db, persist_alerts
from .auto_monitor import build_auto_monitor
from .csv_parser import parse_inventory_csv
from .models import InventoryRequest, InventoryResponse, OrderPreviewResponse, SupplierOrderItem, SupplierOrderPreview
from .monitor import build_monitoring_report
from .notifier import notify_alerts
from .predictor import predict_product
from .scheduler import InventoryMonitor
from .security import MAX_BODY_BYTES, require_api_key
from .storage import get_latest_snapshot, get_snapshots, init_db, save_snapshot

APP_VERSION = "1.0.2"
app = FastAPI(
    title="AI Inventory Restock Predictor",
    version=APP_VERSION,
    description="Predicts inventory risk and suggested reorder quantities from recent sales.",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
_auto_monitor = None
_scheduler = None


@app.on_event("startup")
def startup() -> None:
    global _auto_monitor, _scheduler
    init_db()
    init_alerts_db()
    if os.getenv("INVENTORY_AUTO_MONITOR", "false").lower() == "true":
        _auto_monitor = build_auto_monitor()
        interval = int(os.getenv("INVENTORY_MONITOR_INTERVAL", "3600"))
        _scheduler = InventoryMonitor(_auto_monitor.check, interval_seconds=interval)
        _scheduler.start()


@app.on_event("shutdown")
def shutdown() -> None:
    if _scheduler:
        _scheduler.stop()


def analyze_products(products, include_inputs: bool = False) -> InventoryResponse:
    predictions = [predict_product(product) for product in products]
    response = InventoryResponse(
        products=predictions,
        summary={
            "total_products": len(predictions),
            "products_needing_restock": sum(item.needs_restock for item in predictions),
            "critical_products": sum(item.urgency == "critical" for item in predictions),
            "products_with_increasing_sales": sum(item.sales_trend == "increasing" for item in predictions),
        },
        input_products=products if include_inputs else None,
    )
    save_snapshot(response.model_dump(exclude_none=True))
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


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "auto_monitor": bool(_scheduler and _scheduler.running),
    }


@app.post("/predict", response_model=InventoryResponse, dependencies=[Depends(require_api_key)])
def predict(request: InventoryRequest) -> InventoryResponse:
    return analyze_products(request.products)


@app.post("/predict/csv", response_model=InventoryResponse, dependencies=[Depends(require_api_key)])
async def predict_csv(file: UploadFile = File(...)) -> InventoryResponse:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")
    try:
        raw = await file.read()
        if len(raw) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="CSV file is too large")
        products = parse_inventory_csv(raw.decode("utf-8-sig"))
        return analyze_products(InventoryRequest(products=products).products, include_inputs=True)
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/orders/preview", response_model=OrderPreviewResponse, dependencies=[Depends(require_api_key)])
def order_preview(request: InventoryRequest) -> OrderPreviewResponse:
    return build_order_preview([predict_product(product) for product in request.products])


@app.post("/alerts", dependencies=[Depends(require_api_key)])
def alerts(request: InventoryRequest) -> dict:
    report = build_monitoring_report([predict_product(product) for product in request.products])
    active = persist_alerts(report["alerts"])
    report["alerts"] = active
    report["alert_count"] = len(active)
    report["critical_count"] = sum(item["urgency"] == "critical" for item in active)
    return {"alerts": report}


@app.post("/notifications/test", dependencies=[Depends(require_api_key)])
def test_notifications() -> dict:
    alerts = get_active_alerts()
    return {"sent": notify_alerts(alerts), "backend": "console"}


@app.post("/monitor/run", dependencies=[Depends(require_api_key)])
def run_monitor_now() -> dict:
    global _auto_monitor
    if _auto_monitor is None:
        _auto_monitor = build_auto_monitor()
    return _auto_monitor.check()


@app.get("/alerts/active", dependencies=[Depends(require_api_key)])
def active_alerts() -> dict:
    return {"alerts": get_active_alerts()}


@app.get("/alerts/history", dependencies=[Depends(require_api_key)])
def alert_history(limit: int = 50) -> dict:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    return {"alerts": get_alert_history(limit)}


@app.get("/history", dependencies=[Depends(require_api_key)])
def history(limit: int = 20) -> dict:
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")
    return {"snapshots": get_snapshots(limit)}


@app.get("/history/latest", dependencies=[Depends(require_api_key)])
def latest_history() -> dict:
    return {"snapshot": get_latest_snapshot()}
