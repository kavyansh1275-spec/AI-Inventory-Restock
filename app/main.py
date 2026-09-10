from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .csv_parser import parse_inventory_csv
from .models import InventoryRequest, InventoryResponse
from .predictor import predict_product

APP_VERSION = "0.3.0"

app = FastAPI(
    title="AI Inventory Restock Predictor",
    version=APP_VERSION,
    description="Predicts inventory risk and suggested reorder quantities from recent sales.",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


def analyze_products(products):
    predictions = [predict_product(product) for product in products]
    restock_count = sum(item.needs_restock for item in predictions)
    critical_count = sum(item.urgency == "critical" for item in predictions)
    increasing_count = sum(item.sales_trend == "increasing" for item in predictions)
    return InventoryResponse(
        products=predictions,
        summary={
            "total_products": len(predictions),
            "products_needing_restock": restock_count,
            "critical_products": critical_count,
            "products_with_increasing_sales": increasing_count,
        },
    )


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
