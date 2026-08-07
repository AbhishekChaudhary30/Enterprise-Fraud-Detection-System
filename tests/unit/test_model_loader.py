"""Unit tests for temporary model version discovery and loading."""

import pytest

from enterprise_fraud_detection.serving.model_loader import ModelLoader

pytestmark = pytest.mark.unit


def test_latest_and_historical_model_versions_load(artifact_settings) -> None:
    """The loader discovers and loads only temporary test artifacts."""
    loader = ModelLoader(artifact_settings)
    assert loader.versions() == ["v1", "v2"]
    assert loader.latest_version() == "v2"
    assert loader.load("v1").metadata["version"] == "v1"
    assert loader.load().metadata["selected_model"] == "logistic_regression"
