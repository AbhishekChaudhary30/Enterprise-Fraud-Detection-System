"""Prediction service and CSV validation tests."""

import pandas as pd
import pytest

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.serving.prediction import PredictionService


def test_csv_validation_removes_target_column() -> None:
    """Prediction input accepts a labeled CSV while removing its target."""
    settings = get_settings()
    frame = pd.DataFrame({"Amount": [10.0], settings.dataset.target_column: [0]})
    clean = PredictionService.validate_csv(frame, settings.dataset.target_column)
    assert settings.dataset.target_column not in clean.columns


def test_invalid_threshold_is_rejected() -> None:
    """Thresholds outside the open probability interval are invalid."""
    settings = get_settings()
    service = PredictionService(settings)
    with pytest.raises(ValueError, match="Threshold"):
        service._predict_frame(None, pd.DataFrame(), 1.0)  # type: ignore[arg-type]
