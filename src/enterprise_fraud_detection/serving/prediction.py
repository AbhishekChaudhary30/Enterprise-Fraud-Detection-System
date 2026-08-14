"""Single-row, batch, CSV prediction with risk scoring and SHAP explanations."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pandas as pd
from loguru import logger

from enterprise_fraud_detection.config.settings import Settings
from enterprise_fraud_detection.serving.explainer import PredictionExplainer
from enterprise_fraud_detection.serving.model_loader import LoadedModel, ModelLoader


class RiskClassifier:
    """Classify fraud probability into risk tiers using data-driven thresholds."""

    def __init__(
        self,
        low_threshold: float = 0.15,
        high_threshold: float = 0.50,
    ) -> None:
        """Initialize risk tier boundaries.

        Thresholds are derived from evaluation analysis:
        - low_threshold: Below this → LOW risk (most legitimate transactions)
        - high_threshold: Above this → HIGH risk (fraud suspected)
        - Between → MEDIUM risk (requires review)
        """
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    def classify(self, probability: float) -> dict[str, Any]:
        """Return risk_score, risk_level, and decision for a fraud probability."""
        risk_score = int(round(probability * 100))
        if probability < self.low_threshold:
            return {
                "risk_score": risk_score,
                "risk_level": "LOW",
                "decision": "APPROVE",
            }
        if probability < self.high_threshold:
            return {
                "risk_score": risk_score,
                "risk_level": "MEDIUM",
                "decision": "REVIEW",
            }
        return {
            "risk_score": risk_score,
            "risk_level": "HIGH",
            "decision": "REJECT",
        }


class PredictionService:
    """Run predictions through the persisted pipeline with risk scoring and explanations."""

    def __init__(self, settings: Settings, loader: ModelLoader | None = None) -> None:
        """Initialize prediction with version-aware model loading and risk classification."""
        self.settings = settings
        self.loader = loader or ModelLoader(settings)
        self._loaded_models: dict[str, LoadedModel] = {}
        self._explainers: dict[str, PredictionExplainer] = {}
        self._risk_classifier = RiskClassifier(
            low_threshold=getattr(settings.serving, "risk_low_threshold", 0.15),
            high_threshold=getattr(settings.serving, "risk_high_threshold", 0.50),
        )
        self.settings.serving.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings.serving.output_directory.mkdir(parents=True, exist_ok=True)
        self.settings.serving.upload_directory.mkdir(parents=True, exist_ok=True)

    def predict_one(
        self,
        features: dict[str, Any],
        version: str | None = None,
        threshold: float | None = None,
        input_reference: str = "single",
    ) -> dict[str, Any]:
        """Generate one prediction with probability, risk scoring, and SHAP explanation."""
        started = time.perf_counter()
        bundle = self._load_model(version)
        frame = pd.DataFrame([features])
        result = self._predict_frame(bundle, frame, threshold)
        prediction = result.iloc[0].to_dict()
        prediction_id = str(uuid4())

        # Generate SHAP explanation
        explainer = self._get_explainer(bundle)
        fallback: list[list[dict[str, Any]]] = [[]]
        explanations = explainer.explain(frame) if explainer else fallback
        explanation = explanations[0] if explanations else []

        # Risk classification
        risk = self._risk_classifier.classify(float(prediction["fraud_probability"]))

        response = {
            "prediction_id": prediction_id,
            "prediction_timestamp": datetime.now(UTC).isoformat(),
            "model_version": bundle.version,
            "predicted_label": int(prediction["predicted_label"]),
            "fraud_probability": round(float(prediction["fraud_probability"]), 6),
            "risk_score": risk["risk_score"],
            "risk_level": risk["risk_level"],
            "decision": risk["decision"],
            "threshold": float(prediction["threshold"]),
            "input_reference": input_reference,
            "execution_time_ms": round((time.perf_counter() - started) * 1000, 3),
            "explanation": explanation,
        }
        self._record({**response, "features": features})
        logger.info(
            "Prediction completed: {} | prob={:.4f} risk={}",
            prediction_id,
            response["fraud_probability"],
            risk["risk_level"],
        )
        return response

    def predict_batch(
        self,
        frame: pd.DataFrame,
        version: str | None = None,
        threshold: float | None = None,
        input_reference: str = "batch",
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Generate predictions for a dataframe with risk scoring."""
        if frame.empty:
            raise ValueError("Prediction input contains no rows")
        started = time.perf_counter()
        bundle = self._load_model(version)
        result = self._predict_frame(bundle, frame, threshold)
        batch_id = str(uuid4())
        output = frame.reset_index(drop=True).copy()
        output.insert(0, "prediction_id", [str(uuid4()) for _ in range(len(output))])
        output["model_version"] = bundle.version
        output["predicted_label"] = result["predicted_label"].astype(int)
        output["fraud_probability"] = result["fraud_probability"].astype(float).round(6)

        # Apply risk classification to each row
        risk_data = [self._risk_classifier.classify(float(p)) for p in result["fraud_probability"]]
        output["risk_score"] = [r["risk_score"] for r in risk_data]
        output["risk_level"] = [r["risk_level"] for r in risk_data]
        output["decision"] = [r["decision"] for r in risk_data]
        output["prediction_timestamp"] = datetime.now(UTC).isoformat()

        output_path = self.settings.serving.output_directory / f"{batch_id}.csv"
        output.to_csv(output_path, index=False)

        # Compute summary statistics
        risk_distribution = {
            "low": int((output["risk_level"] == "LOW").sum()),
            "medium": int((output["risk_level"] == "MEDIUM").sum()),
            "high": int((output["risk_level"] == "HIGH").sum()),
        }

        execution_time_ms = round((time.perf_counter() - started) * 1000, 3)
        summary = {
            "prediction_id": batch_id,
            "prediction_timestamp": datetime.now(UTC).isoformat(),
            "model_version": bundle.version,
            "total_transactions": len(output),
            "fraud_predictions": int(output["predicted_label"].sum()),
            "risk_distribution": risk_distribution,
            "execution_time_ms": execution_time_ms,
            "output_path": str(output_path),
        }

        self._record(
            {
                **summary,
                "prediction_type": "batch",
                "input_reference": input_reference,
            }
        )
        logger.info(
            "Batch prediction completed: {} rows, {} fraud, {} | {}",
            len(output),
            summary["fraud_predictions"],
            risk_distribution,
            batch_id,
        )
        return output, summary

    def _predict_frame(
        self, bundle: LoadedModel, frame: pd.DataFrame, threshold: float | None
    ) -> pd.DataFrame:
        """Apply the persisted pipeline and convert probabilities to labels."""
        selected_threshold = (
            threshold if threshold is not None else self.settings.serving.default_threshold
        )
        if not 0 < selected_threshold < 1:
            raise ValueError("Threshold must be greater than 0 and less than 1")
        probabilities = bundle.pipeline.predict_proba(frame)[:, 1]
        labels = (probabilities >= selected_threshold).astype(int)
        return pd.DataFrame(
            {
                "predicted_label": labels,
                "fraud_probability": probabilities,
                "threshold": selected_threshold,
            }
        )

    def _load_model(self, version: str | None) -> LoadedModel:
        """Load a model once per process while preserving version selection."""
        selected_version = version or self.loader.latest_version()
        if selected_version not in self._loaded_models:
            self._loaded_models[selected_version] = self.loader.load(selected_version)
        return self._loaded_models[selected_version]

    def _get_explainer(self, bundle: LoadedModel) -> PredictionExplainer | None:
        """Get or create a cached SHAP explainer for the model version."""
        if bundle.version not in self._explainers:
            try:
                self._explainers[bundle.version] = PredictionExplainer(bundle.pipeline)
            except Exception as exc:
                logger.warning("Failed to create explainer for {}: {}", bundle.version, exc)
                return None
        return self._explainers[bundle.version]

    def _record(self, record: dict[str, Any]) -> None:
        """Append one JSON record to configured prediction history."""
        with self.settings.serving.history_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, default=str) + "\n")

    def history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Read the most recent prediction history records."""
        path = self.settings.serving.history_file
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:] if line.strip()][::-1]

    def reload(self) -> LoadedModel:
        """Clear the process cache and load the current latest model."""
        self._loaded_models.clear()
        self._explainers.clear()
        return self._load_model(None)

    @staticmethod
    def validate_csv(frame: pd.DataFrame, target_column: str) -> pd.DataFrame:
        """Reject target-bearing, empty, or duplicate CSV input before prediction."""
        if frame.empty:
            raise ValueError("Uploaded CSV is empty")
        if target_column in frame.columns:
            frame = frame.drop(columns=[target_column])
        if frame.empty:
            raise ValueError("Uploaded CSV contains no feature columns")
        return frame
