"""Per-prediction SHAP explanation generation using cached tree explainers."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from loguru import logger


class PredictionExplainer:
    """Generate real SHAP-based explanations for individual predictions."""

    def __init__(self, pipeline: Any, max_display: int = 10) -> None:
        """Initialize the explainer with a fitted sklearn-compatible pipeline."""
        self.pipeline = pipeline
        self.max_display = max_display
        self._explainer: Any | None = None
        self._feature_names: list[str] = []
        self._initialize()

    def _initialize(self) -> None:
        """Create the SHAP explainer from the pipeline model."""
        import shap

        model = self.pipeline.named_steps["model"]
        # Get feature names from the preprocessing step
        preprocessor = self.pipeline.named_steps.get("preprocessing")
        if preprocessor is not None and hasattr(preprocessor, "get_feature_names_out"):
            self._feature_names = list(preprocessor.get_feature_names_out())
        else:
            self._feature_names = []

        try:
            self._explainer = shap.TreeExplainer(model)
            logger.info("SHAP TreeExplainer initialized successfully")
        except Exception:
            try:
                self._explainer = shap.LinearExplainer(model, np.zeros((1, 1)))
                logger.info("SHAP LinearExplainer initialized successfully")
            except Exception:
                logger.warning("SHAP explainer initialization failed; explanations unavailable")
                self._explainer = None

    def explain(self, raw_features: pd.DataFrame) -> list[dict[str, Any]]:
        """Generate SHAP explanations for pre-pipeline feature rows.

        Applies the pipeline's feature engineering and preprocessing steps,
        then computes SHAP values using the cached explainer.
        """
        if self._explainer is None:
            return []

        try:
            # Apply feature engineering step
            features_step = self.pipeline.named_steps.get("features")
            if features_step is not None:
                engineered = features_step.transform(raw_features)
            else:
                engineered = raw_features

            # Apply preprocessing step
            preprocessor = self.pipeline.named_steps.get("preprocessing")
            if preprocessor is not None:
                transformed = preprocessor.transform(engineered)
                if hasattr(preprocessor, "get_feature_names_out"):
                    names = list(preprocessor.get_feature_names_out())
                else:
                    names = self._feature_names or [
                        f"feature_{i}" for i in range(transformed.shape[1])
                    ]
            else:
                transformed = engineered.values if hasattr(engineered, "values") else engineered
                names = self._feature_names or [f"feature_{i}" for i in range(transformed.shape[1])]

            shap_values = self._explainer.shap_values(transformed)

            # Handle binary classification (list of arrays for each class)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # fraud class

            explanations = []
            for row_idx in range(len(transformed)):
                row_shap = shap_values[row_idx] if shap_values.ndim > 1 else shap_values
                feature_contributions = []
                indices = np.argsort(np.abs(row_shap))[::-1]
                for idx in indices[: self.max_display]:
                    feature_contributions.append(
                        {
                            "feature": names[idx] if idx < len(names) else f"feature_{idx}",
                            "shap_value": round(float(row_shap[idx]), 6),
                            "direction": (
                                "increases_risk" if row_shap[idx] > 0 else "decreases_risk"
                            ),
                        }
                    )
                explanations.append(feature_contributions)
            return explanations

        except Exception as exc:
            logger.warning("SHAP explanation failed: {}", exc)
            return [[] for _ in range(len(raw_features))]
