"""Start the Phase 4 FastAPI backend."""

import os

import uvicorn

from enterprise_fraud_detection.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("API_PORT", settings.serving.port)))
    uvicorn.run(
        "enterprise_fraud_detection.api.app:app",
        host=host,
        port=port,
        reload=False,
    )
