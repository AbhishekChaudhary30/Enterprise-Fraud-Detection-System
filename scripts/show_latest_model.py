"""Display metadata for the latest persisted model."""

import json

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.serving.model_loader import ModelLoader

if __name__ == "__main__":
    settings = get_settings()
    bundle = ModelLoader(settings).load()
    print(
        json.dumps({"version": bundle.version, "metadata": bundle.metadata}, indent=2, default=str)
    )
