from .models import Product, ProductPrediction


def _round(value: float) -> float:
    return round(value, 2)


def predict_product(product: Product) -> ProductPrediction:
    sales = product.daily_sales
    average_daily_sales = sum(sales) / len(sales)

    if average_daily_sales > 0:
        days_remaining = product.current_stock / average_daily_sales
        reorder_point = max(
            product.minimum_stock,
            average_daily_sales * product.lead_time_days,
        )
        target_stock = average_daily_sales * (
            product.lead_time_days + product.target_days
        )
        suggested_quantity = max(0, target_stock - product.current_stock)
    else:
        days_remaining = None
        reorder_point = product.minimum_stock
        suggested_quantity = 0

    needs_restock = (
        product.current_stock <= reorder_point
        or (
            days_remaining is not None
            and days_remaining <= product.lead_time_days
        )
    )

    if average_daily_sales == 0:
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
        days_remaining=None if days_remaining is None else _round(days_remaining),
        reorder_point=_round(reorder_point),
        suggested_reorder_quantity=_round(suggested_quantity),
        needs_restock=needs_restock,
        urgency=urgency,
        supplier=product.supplier,
    )
