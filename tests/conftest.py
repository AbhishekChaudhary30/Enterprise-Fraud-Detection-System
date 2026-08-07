"""Deterministic fixtures for unit, integration, and end-to-end tests."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from enterprise_fraud_detection.api.app import app
from enterprise_fraud_detection.auth.security import AuthService
from enterprise_fraud_detection.config.settings import (
    DatasetSettings,
    EvaluationSettings,
    LoggingSettings,
    PathSettings,
    ProductionSettings,
    ServingSettings,
    Settings,
    TrainingSettings,
)
from enterprise_fraud_detection.monitoring.metrics import MetricsRegistry
from enterprise_fraud_detection.serving.model_loader import ModelLoader
from enterprise_fraud_detection.serving.prediction import PredictionService


@pytest.fixture
def synthetic_frame() -> tuple[pd.DataFrame, pd.Series]:
    """Return a small deterministic binary classification dataset."""
    frame = pd.DataFrame(
        {
            "Amount": [10.0, 12.0, 80.0, 95.0, 15.0, 100.0, 20.0, 120.0],
            "V1": [-1.0, -0.8, 1.2, 1.4, -0.5, 1.7, -0.2, 2.0],
        }
    )
    target = pd.Series([0, 0, 1, 1, 0, 1, 0, 1], name="Class")
    return frame, target


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Build fully isolated settings rooted in pytest's temporary directory."""
    paths = PathSettings(
        raw_data=tmp_path / "raw",
        processed_data=tmp_path / "processed",
        external_data=tmp_path / "external",
        models=tmp_path / "models",
        artifacts=tmp_path / "artifacts",
        logs=tmp_path / "logs",
        reports=tmp_path / "reports",
        figures=tmp_path / "figures",
    )
    return Settings(
        project_root=tmp_path,
        project_name="test-project",
        phase=5,
        dataset=DatasetSettings("synthetic.csv", "Class", ""),
        paths=paths,
        logging=LoggingSettings("INFO", "1 day", "1 day"),
        training=TrainingSettings(
            42, 0.2, 0.2, False, "average_precision", "grid", 2, 1, (), (), (), {}
        ),
        evaluation=EvaluationSettings(
            tmp_path / "evaluation",
            tmp_path / "evaluation_figures",
            tmp_path / "shap",
            tmp_path / "experiments.jsonl",
            "maximum_f1",
            0.5,
            9,
            4,
            5,
        ),
        serving=ServingSettings(
            "127.0.0.1",
            8000,
            "/api/v1",
            tmp_path / "history.jsonl",
            tmp_path / "uploads",
            tmp_path / "predictions",
            "HS256",
            60,
            "admin",
            0.5,
            "test-jwt-secret",
            "test-password",
        ),
        production=ProductionSettings(
            "test",
            1000,
            60,
            "X-Request-ID",
            tmp_path / "metrics.json",
            tmp_path / "drift",
            tmp_path / "benchmarks",
            tmp_path / "reference.csv",
            0.1,
            0.1,
        ),
    )


@pytest.fixture
def artifact_settings(test_settings: Settings, synthetic_frame) -> Settings:
    """Create two real temporary versioned pipeline artifacts for tests."""
    frame, target = synthetic_frame
    pipeline = Pipeline(
        [("scale", StandardScaler()), ("model", LogisticRegression(random_state=42))]
    )
    pipeline.fit(frame, target)
    for version in ("v1", "v2"):
        directory = test_settings.paths.models / version
        directory.mkdir(parents=True)
        joblib.dump(pipeline, directory / "pipeline.joblib")
        joblib.dump(pipeline.named_steps["model"], directory / "model.joblib")
        (directory / "metadata.json").write_text(
            json.dumps({"version": version, "selected_model": "logistic_regression"}),
            encoding="utf-8",
        )
    return test_settings


@pytest.fixture
def api_client(artifact_settings: Settings):
    """Return a client using the real API with isolated temporary services."""
    previous = {
        name: getattr(app.state, name, None)
        for name in ("settings", "auth", "loader", "predictions", "metrics")
    }
    loader = ModelLoader(artifact_settings)
    app.state.settings = artifact_settings
    app.state.auth = AuthService(artifact_settings)
    app.state.loader = loader
    app.state.predictions = PredictionService(artifact_settings, loader)
    app.state.metrics = MetricsRegistry(artifact_settings.production.metrics_path)
    with TestClient(app) as client:
        yield client
    for name, value in previous.items():
        setattr(app.state, name, value)
