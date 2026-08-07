"""Unit tests for dataset management using temporary CSV input."""

import pandas as pd
import pytest

from enterprise_fraud_detection.data.dataset import DatasetManager

pytestmark = pytest.mark.unit


def test_dataset_manager_loads_and_validates_temporary_csv(test_settings) -> None:
    """Dataset loading and validation do not require the external fraud dataset."""
    test_settings.paths.raw_data.mkdir(parents=True)
    path = test_settings.paths.raw_data / test_settings.dataset.filename
    pd.DataFrame({"Amount": [10.0, 10.0], "Class": [0, 1]}).to_csv(path, index=False)
    manager = DatasetManager(test_settings)
    report = manager.validate()
    assert report.rows == 2
    assert report.target_present
    assert report.duplicate_rows == 0
