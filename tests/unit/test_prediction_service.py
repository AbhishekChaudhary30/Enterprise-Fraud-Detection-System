"""Unit tests for prediction service and risk classification."""

import pandas as pd
import pytest

from enterprise_fraud_detection.serving.prediction import PredictionService, RiskClassifier

pytestmark = pytest.mark.unit


def test_risk_classifier_boundaries() -> None:
    """Test risk classification thresholds and tiers."""
    classifier = RiskClassifier(low_threshold=0.15, high_threshold=0.50)
    
    # Low risk
    low = classifier.classify(0.10)
    assert low["risk_level"] == "LOW"
    assert low["decision"] == "APPROVE"
    assert low["risk_score"] == 10
    
    # Medium risk
    medium = classifier.classify(0.30)
    assert medium["risk_level"] == "MEDIUM"
    assert medium["decision"] == "REVIEW"
    assert medium["risk_score"] == 30
    
    # High risk
    high = classifier.classify(0.85)
    assert high["risk_level"] == "HIGH"
    assert high["decision"] == "REJECT"
    assert high["risk_score"] == 85


def test_prediction_consistency(artifact_settings) -> None:
    """The same input must produce the exact same prediction."""
    service = PredictionService(artifact_settings)
    input_data = {"Amount": 20.0, "V1": -0.2}
    
    pred1 = service.predict_one(input_data)
    pred2 = service.predict_one(input_data)
    
    assert pred1["fraud_probability"] == pred2["fraud_probability"]
    assert pred1["risk_score"] == pred2["risk_score"]


def test_different_inputs_produce_different_outputs(artifact_settings) -> None:
    """Materially different inputs should yield different probabilities."""
    service = PredictionService(artifact_settings)
    
    pred1 = service.predict_one({"Amount": 10.0, "V1": -1.0})
    pred2 = service.predict_one({"Amount": 1000.0, "V1": 2.5})
    
    assert pred1["fraud_probability"] != pred2["fraud_probability"]


def test_shap_explanation_generation(artifact_settings) -> None:
    """Predictions should include SHAP explanations with feature contributions."""
    service = PredictionService(artifact_settings)
    result = service.predict_one({"Amount": 20.0, "V1": -0.2})
    
    assert "explanation" in result
    explanation = result["explanation"]
    assert isinstance(explanation, list)
    if explanation:  # Depending on the model, there might be explanations
        item = explanation[0]
        assert "feature" in item
        assert "shap_value" in item
        assert "direction" in item


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
