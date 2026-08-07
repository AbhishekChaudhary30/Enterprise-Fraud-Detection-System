"""Factory for supported classifiers and their configurable search spaces."""

from __future__ import annotations

from typing import Any

from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from enterprise_fraud_detection.config.settings import Settings


class ModelFactory:
    """Create all supported models through one consistent interface."""

    _SUPPORTED = {
        "logistic_regression",
        "random_forest",
        "xgboost",
        "lightgbm",
        "catboost",
    }

    @classmethod
    def create(cls, name: str, settings: Settings) -> ClassifierMixin:
        """Create a configured classifier by registry name."""
        if name not in cls._SUPPORTED:
            raise ValueError(f"Unsupported model '{name}'. Supported: {sorted(cls._SUPPORTED)}")
        config = settings.training.models.get(name, {})
        random_state = settings.training.random_state
        if name == "logistic_regression":
            return LogisticRegression(
                class_weight=config.get("class_weight"),
                max_iter=int(config.get("max_iter", 1000)),
                random_state=random_state,
            )
        if name == "random_forest":
            return RandomForestClassifier(
                class_weight=config.get("class_weight"),
                random_state=random_state,
                n_jobs=-1,
            )
        if name == "xgboost":
            return XGBClassifier(
                objective="binary:logistic",
                eval_metric="logloss",
                random_state=random_state,
                n_jobs=-1,
                tree_method="hist",
            )
        if name == "lightgbm":
            return LGBMClassifier(
                objective="binary",
                random_state=random_state,
                n_jobs=-1,
                verbosity=-1,
            )
        return CatBoostClassifier(
            random_seed=random_state,
            verbose=False,
            thread_count=-1,
            loss_function="Logloss",
        )

    @classmethod
    def parameter_grid(cls, name: str, settings: Settings) -> dict[str, list[Any]]:
        """Translate YAML model parameters into pipeline search parameters."""
        config = settings.training.models.get(name, {})
        mappings = {
            "logistic_regression": {"c": "model__C"},
            "random_forest": {
                "n_estimators": "model__n_estimators",
                "max_depth": "model__max_depth",
                "min_samples_leaf": "model__min_samples_leaf",
            },
            "xgboost": {
                "n_estimators": "model__n_estimators",
                "max_depth": "model__max_depth",
                "learning_rate": "model__learning_rate",
                "subsample": "model__subsample",
                "colsample_bytree": "model__colsample_bytree",
            },
            "lightgbm": {
                "n_estimators": "model__n_estimators",
                "num_leaves": "model__num_leaves",
                "learning_rate": "model__learning_rate",
            },
            "catboost": {
                "iterations": "model__iterations",
                "depth": "model__depth",
                "learning_rate": "model__learning_rate",
            },
        }
        return {
            target: value if isinstance(value, list) else [value]
            for source, target in mappings[name].items()
            if (value := config.get(source)) is not None
        }

    @classmethod
    def enabled_models(cls, settings: Settings) -> list[str]:
        """Return configured enabled models in YAML order."""
        names = []
        for name, config in settings.training.models.items():
            if name not in cls._SUPPORTED:
                raise ValueError(f"Unsupported configured model: {name}")
            if bool(config.get("enabled", True)):
                names.append(name)
        if not names:
            raise ValueError("At least one model must be enabled")
        return names
