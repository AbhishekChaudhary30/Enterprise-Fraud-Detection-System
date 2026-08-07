"""Model loader tests."""

from enterprise_fraud_detection.config import get_settings
from enterprise_fraud_detection.serving.model_loader import ModelLoader


def test_latest_model_loads() -> None:
    """The latest persisted model bundle contains a pipeline and metadata."""
    bundle = ModelLoader(get_settings()).load()
    assert bundle.version.startswith("v")
    assert bundle.pipeline is not None
    assert bundle.metadata["selected_model"]


def test_historical_model_versions_are_discoverable() -> None:
    """Version discovery remains numeric and ordered."""
    versions = ModelLoader(get_settings()).versions()
    assert versions == sorted(versions, key=lambda item: int(item[1:]))
    assert versions
