"""Reusable schema validation and tabular preprocessing components."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


class FeatureConsistencyError(ValueError):
    """Raised when inference or training data does not match the learned schema."""


class SchemaPreprocessor(BaseEstimator, TransformerMixin):  # type: ignore[misc]
    """Validate columns and apply configurable numeric and categorical preprocessing."""

    def __init__(self, selected_features: tuple[str, ...] = ()) -> None:
        """Initialize optional feature selection for schema preprocessing."""
        self.selected_features = selected_features

    def fit(self, X: pd.DataFrame, y: Any = None) -> SchemaPreprocessor:
        """Detect feature types and learn the expected column schema."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("SchemaPreprocessor requires a pandas DataFrame")
        columns = list(self.selected_features) if self.selected_features else list(X.columns)
        missing = sorted(set(columns) - set(X.columns))
        if missing:
            raise FeatureConsistencyError(f"Missing configured features: {missing}")
        self.feature_names_in_ = columns
        self.numeric_features_ = X[columns].select_dtypes(include="number").columns.tolist()
        self.categorical_features_ = [
            column for column in columns if column not in self.numeric_features_
        ]
        self.transformer_ = ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="median")),
                            ("scaler", StandardScaler()),
                        ]
                    ),
                    self.numeric_features_,
                ),
                (
                    "categorical",
                    Pipeline(
                        steps=[
                            ("imputer", SimpleImputer(strategy="most_frequent")),
                            (
                                "encoder",
                                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                            ),
                        ]
                    ),
                    self.categorical_features_,
                ),
            ],
            remainder="drop",
            verbose_feature_names_out=False,
        )
        self.transformer_.fit(X[columns], y)
        self.feature_names_out_ = self.transformer_.get_feature_names_out().tolist()
        return self

    def transform(self, X: pd.DataFrame) -> Any:
        """Validate columns and transform rows with the fitted preprocessing graph."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("SchemaPreprocessor requires a pandas DataFrame")
        expected = list(self.feature_names_in_)
        missing = sorted(set(expected) - set(X.columns))
        if missing:
            raise FeatureConsistencyError(f"Missing learned features: {missing}")
        return self.transformer_.transform(X[expected])

    def get_feature_names_out(self, input_features: Any = None) -> Any:
        """Return names emitted by the numeric and categorical transformations."""
        return self.feature_names_out_


def build_preprocessor(selected_features: tuple[str, ...] = ()) -> SchemaPreprocessor:
    """Build the shared preprocessing transformer used by every model."""
    return SchemaPreprocessor(selected_features=selected_features)
