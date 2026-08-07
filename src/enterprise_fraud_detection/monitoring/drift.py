"""Reference-versus-current data, prediction, and model drift detection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


@dataclass(frozen=True)
class DriftFinding:
    """Drift result for one feature or signal."""

    name: str
    statistic: float
    p_value: float
    drifted: bool
    threshold: float


class DriftDetector:
    """Detect numerical feature, prediction, and model-output drift."""

    def __init__(self, output_directory: Path, numeric_threshold: float = 0.1) -> None:
        """Initialize output and significance configuration."""
        self.output_directory = output_directory
        self.numeric_threshold = numeric_threshold

    def compare_data(self, reference: pd.DataFrame, current: pd.DataFrame) -> dict[str, Any]:
        """Compare shared numeric feature distributions using two-sample KS tests."""
        findings = []
        for column in sorted(set(reference.columns) & set(current.columns)):
            if not pd.api.types.is_numeric_dtype(reference[column]):
                continue
            result = ks_2samp(reference[column].dropna(), current[column].dropna())
            findings.append(
                DriftFinding(
                    name=column,
                    statistic=float(result.statistic),
                    p_value=float(result.pvalue),
                    drifted=bool(result.pvalue < self.numeric_threshold),
                    threshold=self.numeric_threshold,
                )
            )
        return self._write("data_drift", findings)

    def compare_predictions(
        self,
        reference: np.ndarray | list[float],
        current: np.ndarray | list[float],
        threshold: float | None = None,
    ) -> dict[str, Any]:
        """Compare prediction probability distributions."""
        result = ks_2samp(reference, current)
        findings = [
            DriftFinding(
                name="prediction_probability",
                statistic=float(result.statistic),
                p_value=float(result.pvalue),
                drifted=bool(result.pvalue < (threshold or self.numeric_threshold)),
                threshold=threshold or self.numeric_threshold,
            )
        ]
        return self._write("prediction_drift", findings)

    def compare_model_metrics(
        self,
        reference_metrics: dict[str, float],
        current_metrics: dict[str, float],
        threshold: float = 0.05,
    ) -> dict[str, Any]:
        """Compare current model metrics against a reference model run."""
        findings = []
        for name in sorted(set(reference_metrics) & set(current_metrics)):
            change = abs(float(current_metrics[name]) - float(reference_metrics[name]))
            findings.append(
                DriftFinding(
                    name=name,
                    statistic=change,
                    p_value=0.0,
                    drifted=change > threshold,
                    threshold=threshold,
                )
            )
        return self._write("model_drift", findings)

    def _write(self, name: str, findings: list[DriftFinding]) -> dict[str, Any]:
        self.output_directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(UTC).isoformat(),
            "drift_detected": any(item.drifted for item in findings),
            "findings": [asdict(item) for item in findings],
        }
        (self.output_directory / f"{name}.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8"
        )
        return payload
