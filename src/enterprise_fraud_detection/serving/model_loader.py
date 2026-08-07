"""Version-aware loading of persisted Phase 2 models and pipelines."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
from loguru import logger

from enterprise_fraud_detection.config.settings import Settings


@dataclass(frozen=True)
class LoadedModel:
    """A persisted pipeline and metadata bundle."""

    version: str
    pipeline: Any
    metadata: dict[str, Any]
    model_path: Path
    pipeline_path: Path


class ModelLoader:
    """Load the latest or a requested version from configured model storage."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the loader with centralized paths."""
        self.settings = settings

    def versions(self) -> list[str]:
        """Return available model versions in ascending numeric order."""
        versions = [
            path.name
            for path in self.settings.paths.models.glob("v*")
            if path.is_dir() and path.name[1:].isdigit()
        ]
        return sorted(versions, key=lambda version: int(version[1:]))

    def latest_version(self) -> str:
        """Return the highest available model version."""
        versions = self.versions()
        if not versions:
            raise FileNotFoundError("No trained model versions are available")
        return versions[-1]

    def load(self, version: str | None = None) -> LoadedModel:
        """Load a requested version or the latest version with metadata."""
        selected_version = version or self.latest_version()
        directory = self.settings.paths.models / selected_version
        pipeline_path = directory / "pipeline.joblib"
        model_path = directory / "model.joblib"
        metadata_path = directory / "metadata.json"
        if not all(path.exists() for path in (pipeline_path, model_path, metadata_path)):
            raise FileNotFoundError(f"Incomplete model artifacts for {selected_version}")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        bundle = LoadedModel(
            version=selected_version,
            pipeline=joblib.load(pipeline_path),
            metadata=metadata,
            model_path=model_path,
            pipeline_path=pipeline_path,
        )
        logger.info("Loaded model version {}", selected_version)
        return bundle
