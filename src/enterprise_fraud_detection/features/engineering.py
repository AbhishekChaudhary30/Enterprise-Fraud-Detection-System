"""Configurable, pipeline-compatible feature engineering."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FeatureEngineer(BaseEstimator, TransformerMixin):  # type: ignore[misc]
    """Select, drop, and derive tabular features without fitting on target data."""

    def __init__(
        self,
        selected_features: tuple[str, ...] = (),
        drop_features: tuple[str, ...] = (),
        derived_features: tuple[str, ...] = (),
    ) -> None:
        """Initialize configurable feature selection and derivation rules."""
        self.selected_features = selected_features
        self.drop_features = drop_features
        self.derived_features = derived_features

    def fit(self, X: pd.DataFrame, y: Any = None) -> FeatureEngineer:
        """Validate configured columns and learn the resulting feature schema."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("FeatureEngineer requires a pandas DataFrame")
        self._validate_source_columns(X)
        transformed = self._transform_frame(X)
        self.feature_names_in_ = list(X.columns)
        self.feature_names_out_ = list(transformed.columns)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Apply configured feature selection, dropping, and derivations."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("FeatureEngineer requires a pandas DataFrame")
        self._validate_source_columns(X)
        transformed = self._transform_frame(X)
        return transformed.reindex(columns=self.feature_names_out_, fill_value=np.nan)

    def get_feature_names_out(self, input_features: Any = None) -> np.ndarray:
        """Return the stable feature names produced by this transformer."""
        return np.asarray(self.feature_names_out_, dtype=object)

    def _validate_source_columns(self, frame: pd.DataFrame) -> None:
        configured = set(self.selected_features) | set(self.drop_features)
        for feature in self.derived_features:
            if feature == "amount_log1p":
                configured.add("Amount")
            elif feature == "time_hour":
                configured.add("Time")
            elif feature == "amount_per_time":
                configured.update({"Amount", "Time"})
            else:
                raise ValueError(f"Unsupported derived feature: {feature}")
        missing = sorted(configured - set(frame.columns))
        if missing:
            raise ValueError(f"Configured feature columns are missing: {missing}")

    def _transform_frame(self, frame: pd.DataFrame) -> pd.DataFrame:
        result = frame.copy()
        if self.selected_features:
            result = result.loc[:, list(self.selected_features)]
        if self.drop_features:
            result = result.drop(columns=list(self.drop_features), errors="ignore")
        for feature in self.derived_features:
            if feature == "amount_log1p":
                result[feature] = np.log1p(result["Amount"].clip(lower=0))
            elif feature == "time_hour":
                result[feature] = (result["Time"] / 3600.0) % 24.0
            elif feature == "amount_per_time":
                result[feature] = result["Amount"] / (result["Time"].abs() + 1.0)
        return result
