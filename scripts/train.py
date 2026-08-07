"""Train, compare, and version the configured Phase 2 models."""

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.data.dataset import DatasetManager
from enterprise_fraud_detection.modeling.trainer import TrainingRunner
from enterprise_fraud_detection.utils.logging import configure_logging

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings)
    dataset = DatasetManager(settings)
    result = TrainingRunner(settings).train(dataset.load())
    print(f"Selected model: {result.selected_model}")
    print(f"Version: {result.version}")
    print(f"Pipeline: {result.pipeline_path}")
    print(f"Metadata: {result.metadata_path}")
