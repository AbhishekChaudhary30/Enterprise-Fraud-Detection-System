"""Run data, prediction, and model drift checks against configured references."""

from __future__ import annotations

import json

import pandas as pd

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.monitoring.drift import DriftDetector
from enterprise_fraud_detection.serving.model_loader import ModelLoader
from enterprise_fraud_detection.utils.logging import configure_logging

if __name__ == "__main__":
    settings = get_settings()
    configure_logging(settings)
    dataset = pd.read_csv(settings.production.reference_data_path)
    split = max(1, len(dataset) // 2)
    reference = dataset.iloc[:split]
    current = dataset.iloc[split:]
    detector = DriftDetector(
        settings.production.drift_output_directory,
        settings.production.drift_numeric_threshold,
    )
    target = settings.dataset.target_column
    data_report = detector.compare_data(
        reference.drop(columns=[target]), current.drop(columns=[target])
    )
    bundle = ModelLoader(settings).load()
    reference_probabilities = bundle.pipeline.predict_proba(reference.drop(columns=[target]))[:, 1]
    current_probabilities = bundle.pipeline.predict_proba(current.drop(columns=[target]))[:, 1]
    prediction_report = detector.compare_predictions(
        reference_probabilities,
        current_probabilities,
        settings.production.drift_prediction_threshold,
    )
    metrics_path = settings.evaluation.output_directory / "metrics.json"
    current_metrics = (
        json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    )
    comparisons = bundle.metadata.get("comparisons", [])
    selected_comparison = next(
        (
            item
            for item in comparisons
            if item.get("model_name") == bundle.metadata.get("selected_model")
        ),
        {},
    )
    reference_metrics = selected_comparison.get("test_metrics", {})
    model_report = detector.compare_model_metrics(reference_metrics, current_metrics)
    print(
        json.dumps(
            {"data": data_report, "prediction": prediction_report, "model": model_report}, indent=2
        )
    )
