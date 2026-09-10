import math

from .models import Product, ProductPrediction


def _round(value: float) -> float:
    return round(value, 2)


def _sales_std(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _weighted_demand(sales: list[float]) -> float:
    """Give newer sales more influence while retaining the full history."""
    if len(sales) == 1:
        return sales[0]
    window = min(7, len(sales))
    recent = sales[-window:]
    weights = list(range(1, window + 1))
    return sum(value * weight for value, weight in zip(recent, weights)) / sum(weights)


def predict_product(product: Product) -> ProductPrediction:
    sales = product.daily_sales
    average_daily_sales = sum(sales) / len(sales)
    recent_window = min(3, len(sales))
    recent_sales = sales[-recent_window:]
    recent_daily_sales = sum(recent_sales) / recent_window
    forecast_daily_sales = _weighted_demand(sales)
    variability = _sales_std(sales, average_daily_sales)

    if average_daily_sales == 0:
        trend = "stable"
    elif recent_daily_sales > average_daily_sales * 1.10:
        trend = "increasing"
    elif recent_daily_sales < average_daily_sales * 0.90:
        trend = "decreasing"
    else:
        trend = "stable"

    # Blend long-term history with recent weighted demand.
    forecast_daily_sales = (average_daily_sales * 0.4) + (forecast_daily_sales * 0.6)
    safety_stock = variability * math.sqrt(max(product.lead_time_days, 1))

    if forecast_daily_sales > 0:
        days_remaining = product.current_stock / forecast_daily_sales
        reorder_point = max(
            product.minimum_stock,
            forecast_daily_sales * product.lead_time_days + safety_stock,
        )
        target_stock = forecast_daily_sales * (product.lead_time_days + product.target_days) + safety_stock
        suggested_quantity = max(0, target_stock - product.current_stock)
    else:
        days_remaining = None
        reorder_point = product.minimum_stock
        suggested_quantity = 0

    needs_restock = product.current_stock <= reorder_point or (
        days_remaining is not None and days_remaining <= product.lead_time_days
    )

    if forecast_daily_sales == 0:
        urgency = "none"
    elif days_remaining is not None and days_remaining <= product.lead_time_days:
        urgency = "critical"
    elif product.current_stock <= product.minimum_stock:
        urgency = "high"
    elif days_remaining is not None and days_remaining <= product.target_days:
        urgency = "medium"
    else:
        urgency = "low"

    return ProductPrediction(
        name=product.name,
        current_stock=_round(product.current_stock),
        minimum_stock=_round(product.minimum_stock),
        average_daily_sales=_round(average_daily_sales),
        recent_daily_sales=_round(recent_daily_sales),
        sales_trend=trend,
        sales_variability=_round(variability),
        safety_stock=_round(safety_stock),
        days_remaining=None if days_remaining is None else _round(days_remaining),
        reorder_point=_round(reorder_point),
        suggested_reorder_quantity=_round(suggested_quantity),
        needs_restock=needs_restock,
        urgency=urgency,
        supplier=product.supplier,
    )
