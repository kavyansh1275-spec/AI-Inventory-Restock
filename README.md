# AI Inventory Restock Predictor

A lightweight inventory forecasting MVP for small businesses.

## What it does

Given product stock and recent sales history, the system estimates:

- average daily sales
- days of stock remaining
- whether the product needs restocking
- suggested reorder quantity
- a simple urgency level

The first version is intentionally deterministic and does not require a paid AI API. This makes it easy to test locally and validate with real businesses before adding external integrations.

## MVP input

The API accepts products with:

- product name
- current stock
- minimum stock level
- recent daily sales
- optional supplier information

## Run locally

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API.

## Example

```json
{
  "products": [
    {
      "name": "Protein Powder",
      "current_stock": 18,
      "minimum_stock": 10,
      "daily_sales": [3, 4, 2, 3, 5, 3, 4]
    }
  ]
}
```

## Design principle

This is a standalone product. It does not depend on the `AI-Workflow-Orchestrator` repository at runtime, even though useful engineering patterns can be reused from that project.
