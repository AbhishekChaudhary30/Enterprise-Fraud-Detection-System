"""Validate the configured raw dataset."""

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.data.dataset import DatasetManager
from enterprise_fraud_detection.utils.logging import configure_logging

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings)
    DatasetManager(settings).validate()
