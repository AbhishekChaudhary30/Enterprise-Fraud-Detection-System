"""Configurable model training, comparison, tuning, and version persistence."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from loguru import logger
from sklearn.base import ClassifierMixin
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split

from enterprise_fraud_detection.config.settings import Settings
from enterprise_fraud_detection.features.engineering import FeatureEngineer
from enterprise_fraud_detection.features.preprocessing import build_preprocessor
from enterprise_fraud_detection.modeling.factory import ModelFactory


@dataclass(frozen=True)
class ModelResult:
    """Validation and test metrics for one trained model."""

    model_name: str
    validation_metrics: dict[str, float]
    test_metrics: dict[str, float]
    best_params: dict[str, Any]
    duration_seconds: float


@dataclass(frozen=True)
class TrainingResult:
    """Summary and locations produced by one training run."""

    version: str
    selected_model: str
    model_path: Path
    pipeline_path: Path
    metadata_path: Path
    artifact_directory: Path
    comparisons: tuple[ModelResult, ...]


class TrainingRunner:
    """Train and compare configured fraud classifiers using shared pipelines."""

    def __init__(self, settings: Settings) -> None:
        """Initialize training with centralized project settings."""
        self.settings = settings

    def train(self, frame: pd.DataFrame) -> TrainingResult:
        """Split, tune, compare, select, and save every configured training run."""
        started = time.perf_counter()
        X, y = self._prepare_data(frame)
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.settings.training.test_size,
            stratify=y,
            random_state=self.settings.training.random_state,
        )
        validation_fraction = self.settings.training.validation_size / (
            1.0 - self.settings.training.test_size
        )
        X_train, X_validation, y_train, y_validation = train_test_split(
            X_train,
            y_train,
            test_size=validation_fraction,
            stratify=y_train,
            random_state=self.settings.training.random_state,
        )
        logger.info(
            "Dataset loaded for training: {} rows, {} features, fraud rate {:.4f}",
            len(frame),
            X.shape[1],
            float(y.mean()),
        )

        results: list[ModelResult] = []
        fitted_searches: dict[str, Any] = {}
        for model_name in ModelFactory.enabled_models(self.settings):
            model_started = time.perf_counter()
            logger.info("Training started for model {}", model_name)
            search = self._build_search(model_name)
            search.fit(X_train, y_train)
            validation_metrics = self._metrics(search, X_validation, y_validation)
            fitted_searches[model_name] = search
            duration = time.perf_counter() - model_started
            results.append(
                ModelResult(
                    model_name=model_name,
                    validation_metrics=validation_metrics,
                    test_metrics={},
                    best_params=dict(search.best_params_),
                    duration_seconds=duration,
                )
            )
            logger.info("Training finished for {} in {:.2f}s", model_name, duration)

        metric = self.settings.training.selection_metric
        selected = max(
            results, key=lambda result: result.validation_metrics.get(metric, float("-inf"))
        )
        selected_search = fitted_searches[selected.model_name]
        logger.info("Model selected: {} using {}", selected.model_name, metric)

        X_combined = pd.concat([X_train, X_validation], axis=0)
        y_combined = pd.concat([y_train, y_validation], axis=0)
        selected_search.best_estimator_.fit(X_combined, y_combined)
        test_metrics = self._metrics(selected_search.best_estimator_, X_test, y_test)
        results = [
            ModelResult(
                model_name=result.model_name,
                validation_metrics=result.validation_metrics,
                test_metrics=test_metrics if result.model_name == selected.model_name else {},
                best_params=result.best_params,
                duration_seconds=result.duration_seconds,
            )
            for result in results
        ]
        return self._save_run(
            selected.model_name,
            selected_search.best_estimator_,
            results,
            X.columns.tolist(),
            len(frame),
            time.perf_counter() - started,
        )

    def _prepare_data(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        target = self.settings.dataset.target_column
        if target not in frame.columns:
            raise ValueError(f"Target column '{target}' is missing")
        clean = frame.drop_duplicates().reset_index(drop=True)
        if clean.empty:
            raise ValueError("Dataset is empty after duplicate removal")
        y = clean[target]
        if y.isna().any():
            raise ValueError("Target column contains missing values")
        X = clean.drop(columns=[target])
        if X.shape[1] == 0:
            raise ValueError("Dataset has no features after removing the target")
        return X, y.astype(int)

    def _build_pipeline(self, model: ClassifierMixin) -> Pipeline:
        training = self.settings.training
        sampler: Any = (
            SMOTE(random_state=training.random_state) if training.smote_enabled else "passthrough"
        )
        return Pipeline(
            steps=[
                (
                    "features",
                    FeatureEngineer(
                        selected_features=training.selected_features,
                        drop_features=training.drop_features,
                        derived_features=training.derived_features,
                    ),
                ),
                ("preprocessing", build_preprocessor()),
                ("sampler", sampler),
                ("model", model),
            ]
        )

    def _build_search(self, model_name: str) -> GridSearchCV | RandomizedSearchCV:
        pipeline = self._build_pipeline(ModelFactory.create(model_name, self.settings))
        parameters = ModelFactory.parameter_grid(model_name, self.settings)
        common = {
            "scoring": self.settings.training.selection_metric,
            "cv": self.settings.training.cv_folds,
            "n_jobs": 1,
            "refit": True,
            "error_score": "raise",
        }
        if self.settings.training.search_type.lower() == "grid":
            return GridSearchCV(pipeline, parameters, **common)
        return RandomizedSearchCV(
            pipeline,
            parameters,
            n_iter=self.settings.training.randomized_iterations,
            random_state=self.settings.training.random_state,
            **common,
        )

    @staticmethod
    def _metrics(estimator: Any, X: pd.DataFrame, y: pd.Series) -> dict[str, float]:
        probabilities = estimator.predict_proba(X)[:, 1]
        predictions = estimator.predict(X)
        return {
            "average_precision": float(average_precision_score(y, probabilities)),
            "roc_auc": float(roc_auc_score(y, probabilities)),
            "f1": float(f1_score(y, predictions, zero_division=0)),
            "balanced_accuracy": float(balanced_accuracy_score(y, predictions)),
            "precision": float(precision_score(y, predictions, zero_division=0)),
            "recall": float(recall_score(y, predictions, zero_division=0)),
        }

    def _save_run(
        self,
        selected_model: str,
        pipeline: Pipeline,
        comparisons: list[ModelResult],
        feature_list: list[str],
        row_count: int,
        duration: float,
    ) -> TrainingResult:
        version_number = self._next_version()
        version = f"v{version_number}"
        model_directory = self.settings.paths.models / version
        artifact_directory = self.settings.paths.artifacts / version
        model_directory.mkdir(parents=True, exist_ok=False)
        artifact_directory.mkdir(parents=True, exist_ok=False)
        pipeline_path = model_directory / "pipeline.joblib"
        model_path = model_directory / "model.joblib"
        metadata_path = model_directory / "metadata.json"
        joblib.dump(pipeline, pipeline_path)
        joblib.dump(pipeline.named_steps["model"], model_path)
        joblib.dump(
            pipeline.named_steps["preprocessing"], artifact_directory / "preprocessor.joblib"
        )
        (artifact_directory / "feature_list.json").write_text(
            json.dumps(feature_list, indent=2), encoding="utf-8"
        )
        metadata = {
            "version": version,
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "selected_model": selected_model,
            "row_count": row_count,
            "training_duration_seconds": duration,
            "training_configuration": asdict(self.settings.training),
            "comparisons": [asdict(result) for result in comparisons],
        }
        metadata_path.write_text(json.dumps(metadata, indent=2, default=str), encoding="utf-8")
        (artifact_directory / "metadata.json").write_text(
            json.dumps(metadata, indent=2, default=str), encoding="utf-8"
        )
        logger.info("Model saved to {}", model_path)
        logger.info("Pipeline saved to {}", pipeline_path)
        logger.info("Training metadata saved to {}", metadata_path)
        return TrainingResult(
            version=version,
            selected_model=selected_model,
            model_path=model_path,
            pipeline_path=pipeline_path,
            metadata_path=metadata_path,
            artifact_directory=artifact_directory,
            comparisons=tuple(comparisons),
        )

    def _next_version(self) -> int:
        existing = [
            int(path.name[1:])
            for path in self.settings.paths.models.glob("v*")
            if path.is_dir() and path.name[1:].isdigit()
        ]
        return max(existing, default=0) + 1
