# AI Inventory Restock Predictor

A lightweight inventory forecasting MVP for small businesses.

## What it does

Given product stock and recent sales history, the system estimates:

- average daily sales
- days of stock remaining
- reorder point
- suggested reorder quantity
- restock status
- urgency level

The MVP is intentionally deterministic and requires **no paid AI API**. This keeps the first version free to build and easy to validate with real businesses.

## Dashboard

The project includes a simple browser dashboard with:

- inventory summary cards
- product-level restock analysis
- sample data
- CSV import
- responsive layout

Run it locally:

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open `http://127.0.0.1:8000/` for the dashboard or `http://127.0.0.1:8000/docs` for the API.

## CSV format

Use these columns:

```text
name,current_stock,minimum_stock,daily_sales,lead_time_days,target_days,supplier
```

`daily_sales` is a quoted, comma-separated list of recent daily unit sales, for example `"3,4,2,3,5"`.

A ready-to-test file is included as `sample_inventory.csv`.

## API

### JSON prediction

`POST /predict`

```json
{
  "products": [
    {
      "name": "Protein Powder",
      "current_stock": 18,
      "minimum_stock": 10,
      "daily_sales": [3, 4, 2, 3, 5, 3, 4],
      "lead_time_days": 5,
      "target_days": 14,
      "supplier": "Fitness Supply Co."
    }
  ]
}
```

### CSV prediction

`POST /predict/csv` accepts a `.csv` upload and returns the same structured prediction response.

### Health

`GET /health` returns the service health and version.

## Testing

```bash
python -m unittest discover -s tests -v
```

## Design principle

This is a **standalone product**. It does not depend on the `AI-Workflow-Orchestrator` repository at runtime, even though useful engineering patterns can be reused from that project.

## Roadmap

1. Free local MVP dashboard + CSV analysis — current
2. Better forecasting with sales trends and variability
3. Inventory history and saved products
4. Supplier/order workflow
5. Optional AI explanations
6. Business integrations after validation
