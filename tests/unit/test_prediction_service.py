"""Unit tests for prediction behavior using temporary model artifacts."""

import pandas as pd
import pytest

from enterprise_fraud_detection.serving.prediction import PredictionService

pytestmark = pytest.mark.unit


def test_single_prediction_contains_operational_metadata(artifact_settings) -> None:
    """The real prediction service returns ID, score, confidence, and version."""
    service = PredictionService(artifact_settings)
    result = service.predict_one({"Amount": 20.0, "V1": -0.2})
    assert result["model_version"] == "v2"
    assert 0 <= result["fraud_probability"] <= 1
    assert result["prediction_id"]
    assert result["prediction_timestamp"]


def test_csv_validation_removes_target_column(test_settings) -> None:
    """Labeled upload data is converted into feature-only input."""
    frame = pd.DataFrame({"Amount": [10.0], "Class": [0]})
    clean = PredictionService.validate_csv(frame, test_settings.dataset.target_column)
    assert list(clean.columns) == ["Amount"]


def test_invalid_threshold_fails_before_inference(artifact_settings) -> None:
    """Invalid thresholds fail deterministically without invoking the model."""
    service = PredictionService(artifact_settings)
    with pytest.raises(ValueError, match="Threshold"):
        service.predict_one({"Amount": 20.0, "V1": -0.2}, threshold=1.0)
