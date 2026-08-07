"""Evaluate the latest trained model and generate Phase 3 artifacts."""

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.data.dataset import DatasetManager
from enterprise_fraud_detection.evaluation.evaluator import ModelEvaluator
from enterprise_fraud_detection.utils.logging import configure_logging

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings)
    dataset = DatasetManager(settings)
    result = ModelEvaluator(settings).evaluate(dataset.load())
    print(f"Evaluated model: {result.selected_model}")
    print(f"Version: {result.version}")
    print(f"Threshold: {result.threshold:.4f}")
    print(f"Evaluation report: {result.evaluation_report}")
    print(f"SHAP directory: {result.shap_directory}")
