from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    current_stock: float = Field(ge=0)
    minimum_stock: float = Field(ge=0)
    daily_sales: list[float] = Field(min_length=1, max_length=365)
    lead_time_days: float = Field(default=3, ge=0, le=365)
    target_days: float = Field(default=14, ge=1, le=365)
    supplier: Optional[str] = Field(default=None, max_length=200)

    @field_validator("daily_sales")
    @classmethod
    def validate_sales(cls, values: list[float]) -> list[float]:
        if any(value < 0 for value in values):
            raise ValueError("daily_sales cannot contain negative values")
        return values


class InventoryRequest(BaseModel):
    products: list[Product] = Field(min_length=1, max_length=1000)


class ProductPrediction(BaseModel):
    name: str
    current_stock: float
    minimum_stock: float
    average_daily_sales: float
    recent_daily_sales: float
    sales_trend: str
    sales_variability: float
    safety_stock: float
    days_remaining: Optional[float]
    reorder_point: float
    suggested_reorder_quantity: float
    needs_restock: bool
    urgency: str
    supplier: Optional[str] = None


class InventoryResponse(BaseModel):
    products: list[ProductPrediction]
    summary: dict


class SupplierOrderItem(BaseModel):
    product: str
    supplier: str
    quantity: float
    urgency: str


class SupplierOrderPreview(BaseModel):
    supplier: str
    items: list[SupplierOrderItem]
    total_units: float
    requires_manual_confirmation: bool = True


class OrderPreviewResponse(BaseModel):
    orders: list[SupplierOrderPreview]
    products_without_supplier: list[str]
