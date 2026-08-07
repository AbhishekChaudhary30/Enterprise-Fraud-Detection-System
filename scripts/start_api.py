"""Start the Phase 4 FastAPI backend."""

import uvicorn

from enterprise_fraud_detection.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "enterprise_fraud_detection.api.app:app",
        host=settings.serving.host,
        port=settings.serving.port,
        reload=False,
    )
