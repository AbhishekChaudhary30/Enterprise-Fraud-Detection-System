"""Monitoring and drift tests."""

import numpy as np
import pandas as pd

from enterprise_fraud_detection.monitoring.drift import DriftDetector
from enterprise_fraud_detection.monitoring.metrics import MetricsRegistry


def test_metrics_registry_persists(tmp_path) -> None:
    """Metrics counters and latency are persisted as JSON."""
    registry = MetricsRegistry(tmp_path / "metrics.json")
    registry.observe_request(12.5, 200)
    registry.observe_prediction(rows=3, batch=True)
    snapshot = registry.snapshot()
    assert snapshot["request_count"] == 1
    assert snapshot["total_prediction_rows"] == 3
    assert (tmp_path / "metrics.json").exists()


def test_drift_detector_writes_report(tmp_path) -> None:
    """Data drift comparisons produce a structured report."""
    detector = DriftDetector(tmp_path)
    report = detector.compare_data(
        pd.DataFrame({"amount": np.arange(100)}),
        pd.DataFrame({"amount": np.arange(100) + 100}),
    )
    assert report["drift_detected"]
    assert (tmp_path / "data_drift.json").exists()
