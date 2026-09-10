from fastapi import FastAPI
from .models import InventoryRequest, InventoryResponse
from .predictor import predict_product

app = FastAPI(
    title="AI Inventory Restock Predictor",
    version="0.1.0",
    description="Predicts inventory risk and suggested reorder quantities from recent sales.",
)


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Inventory Restock Predictor",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/predict", response_model=InventoryResponse)
def predict(request: InventoryRequest) -> InventoryResponse:
    predictions = [predict_product(product) for product in request.products]
    restock_count = sum(item.needs_restock for item in predictions)
    critical_count = sum(item.urgency == "critical" for item in predictions)

    return InventoryResponse(
        products=predictions,
        summary={
            "total_products": len(predictions),
            "products_needing_restock": restock_count,
            "critical_products": critical_count,
        },
    )
