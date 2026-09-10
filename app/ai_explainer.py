import os
import urllib.error
import urllib.request
import json


def explain_prediction(prediction: dict) -> str:
    """Return a short explanation using local Ollama when available.

    The core predictor never depends on this module or an external paid API.
    """
    host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    prompt = (
        "Explain this inventory prediction to a small business owner in 3 short bullet points. "
        "Mention the risk, why it happened, and the recommended action. Do not invent facts.\n\n"
        + json.dumps(prediction, ensure_ascii=False)
    )
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    request = urllib.request.Request(host + "/api/generate", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data = json.loads(response.read().decode())
        return str(data.get("response", "")).strip() or "Local AI returned no explanation."
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        return "Local AI is unavailable. The deterministic inventory prediction is still valid."
