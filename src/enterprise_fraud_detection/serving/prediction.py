"""Single-row, batch, CSV prediction, and history services."""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pandas as pd
from loguru import logger

from enterprise_fraud_detection.config.settings import Settings
from enterprise_fraud_detection.serving.model_loader import LoadedModel, ModelLoader


class PredictionService:
    """Run predictions through the persisted pipeline and record prediction history."""

    def __init__(self, settings: Settings, loader: ModelLoader | None = None) -> None:
        """Initialize prediction storage and version-aware model loading."""
        self.settings = settings
        self.loader = loader or ModelLoader(settings)
        self._loaded_models: dict[str, LoadedModel] = {}
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
        """Generate one prediction with probability, confidence, and metadata."""
        started = time.perf_counter()
        bundle = self._load_model(version)
        frame = pd.DataFrame([features])
        result = self._predict_frame(bundle, frame, threshold)
        prediction = result.iloc[0].to_dict()
        prediction_id = str(uuid4())
        response = {
            "prediction_id": prediction_id,
            "prediction_timestamp": datetime.now(UTC).isoformat(),
            "model_version": bundle.version,
            "predicted_label": int(prediction["predicted_label"]),
            "fraud_probability": float(prediction["fraud_probability"]),
            "confidence_score": float(prediction["confidence_score"]),
            "threshold": float(prediction["threshold"]),
            "input_reference": input_reference,
            "execution_time_ms": round((time.perf_counter() - started) * 1000, 3),
        }
        self._record({**response, "features": features})
        logger.info("Prediction completed: {}", prediction_id)
        return response

    def predict_batch(
        self,
        frame: pd.DataFrame,
        version: str | None = None,
        threshold: float | None = None,
        input_reference: str = "batch",
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Generate predictions for a dataframe and record a batch history entry."""
        if frame.empty:
            raise ValueError("Prediction input contains no rows")
        bundle = self._load_model(version)
        result = self._predict_frame(bundle, frame, threshold)
        batch_id = str(uuid4())
        output = frame.reset_index(drop=True).copy()
        output.insert(0, "prediction_id", [str(uuid4()) for _ in range(len(output))])
        output["model_version"] = bundle.version
        output["predicted_label"] = result["predicted_label"].astype(int)
        output["fraud_probability"] = result["fraud_probability"].astype(float)
        output["confidence_score"] = result["confidence_score"].astype(float)
        output["prediction_timestamp"] = datetime.now(UTC).isoformat()
        output_path = self.settings.serving.output_directory / f"{batch_id}.csv"
        output.to_csv(output_path, index=False)
        self._record(
            {
                "prediction_id": batch_id,
                "prediction_timestamp": datetime.now(UTC).isoformat(),
                "model_version": bundle.version,
                "prediction_type": "batch",
                "row_count": len(output),
                "fraud_count": int(output["predicted_label"].sum()),
                "input_reference": input_reference,
                "output_reference": str(output_path),
            }
        )
        logger.info("Batch prediction completed: {} rows, {}", len(output), batch_id)
        return output, {
            "prediction_id": batch_id,
            "output_path": output_path,
            "model_version": bundle.version,
        }

    def _predict_frame(
        self, bundle: LoadedModel, frame: pd.DataFrame, threshold: float | None
    ) -> pd.DataFrame:
        """Apply the persisted pipeline and convert probabilities to labels."""
        probabilities = bundle.pipeline.predict_proba(frame)[:, 1]
        selected_threshold = (
            threshold if threshold is not None else self.settings.serving.default_threshold
        )
        if not 0 < selected_threshold < 1:
            raise ValueError("Threshold must be greater than 0 and less than 1")
        labels = (probabilities >= selected_threshold).astype(int)
        confidence = abs(probabilities - 0.5) * 2
        return pd.DataFrame(
            {
                "predicted_label": labels,
                "fraud_probability": probabilities,
                "confidence_score": confidence,
                "threshold": selected_threshold,
            }
        )

    def _load_model(self, version: str | None) -> LoadedModel:
        """Load a model once per process while preserving version selection."""
        selected_version = version or self.loader.latest_version()
        if selected_version not in self._loaded_models:
            self._loaded_models[selected_version] = self.loader.load(selected_version)
        return self._loaded_models[selected_version]

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
