"""Generate the Phase 1 exploratory analysis report."""

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.data.dataset import DatasetManager
from enterprise_fraud_detection.utils.logging import configure_logging
from enterprise_fraud_detection.visualization.eda import generate_eda_report

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings)
    dataset = DatasetManager(settings)
    generate_eda_report(settings, dataset.load())
