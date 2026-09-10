import os
import secrets

from fastapi import Header, HTTPException


API_KEY = os.getenv("INVENTORY_API_KEY", "").strip()
MAX_BODY_BYTES = int(os.getenv("INVENTORY_MAX_BODY_BYTES", "2000000"))


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Require a key only when INVENTORY_API_KEY is configured."""
    if API_KEY and not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")
    if API_KEY and not secrets.compare_digest(x_api_key or "", API_KEY):
        raise HTTPException(status_code=403, detail="Invalid API key")
