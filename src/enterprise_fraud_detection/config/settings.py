"""Centralized application settings loaded from YAML and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class DatasetSettings:
    """Dataset-specific configuration."""

    filename: str
    target_column: str
    download_url: str


@dataclass(frozen=True)
class PathSettings:
    """Project paths resolved from project-root-relative YAML values."""

    raw_data: Path
    processed_data: Path
    external_data: Path
    models: Path
    artifacts: Path
    logs: Path
    reports: Path
    figures: Path


@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration."""

    level: str
    rotation: str
    retention: str


@dataclass(frozen=True)
class Settings:
    """Immutable application settings used by all Phase 1 modules."""

    project_root: Path
    project_name: str
    phase: int
    dataset: DatasetSettings
    paths: PathSettings
    logging: LoggingSettings


def _project_root() -> Path:
    """Resolve the project root from the environment or package location."""
    configured_root = os.getenv("PROJECT_ROOT")
    if configured_root:
        root = Path(configured_root).expanduser()
        return root.resolve()
    return Path(__file__).resolve().parents[3]


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping and fail clearly when it is missing or malformed."""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as config_file:
        loaded = yaml.safe_load(config_file) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Configuration root must be a YAML mapping")
    return loaded


def get_settings() -> Settings:
    """Build settings from `.env`, YAML, and supported environment overrides."""
    root = _project_root()
    load_dotenv(root / ".env")
    config_path = Path(os.getenv("CONFIG_FILE", "configs/config.yaml"))
    if not config_path.is_absolute():
        config_path = root / config_path
    raw = _load_yaml(config_path)

    dataset_raw = raw.get("dataset", {})
    paths_raw = raw.get("paths", {})
    logging_raw = raw.get("logging", {})

    def resolve_path(value: str) -> Path:
        path = Path(value).expanduser()
        return path if path.is_absolute() else root / path

    dataset = DatasetSettings(
        filename=str(dataset_raw.get("filename", "creditcard.csv")),
        target_column=str(dataset_raw.get("target_column", "Class")),
        download_url=os.getenv("DATASET_URL", str(dataset_raw.get("download_url", ""))),
    )
    paths = PathSettings(
        raw_data=resolve_path(str(paths_raw["raw_data"])),
        processed_data=resolve_path(str(paths_raw["processed_data"])),
        external_data=resolve_path(str(paths_raw["external_data"])),
        models=resolve_path(str(paths_raw["models"])),
        artifacts=resolve_path(str(paths_raw["artifacts"])),
        logs=resolve_path(str(paths_raw["logs"])),
        reports=resolve_path(str(paths_raw["reports"])),
        figures=resolve_path(str(paths_raw["figures"])),
    )
    return Settings(
        project_root=root,
        project_name=str(raw.get("project", {}).get("name", "enterprise-fraud-detection")),
        phase=int(raw.get("project", {}).get("phase", 1)),
        dataset=dataset,
        paths=paths,
        logging=LoggingSettings(
            level=os.getenv("LOG_LEVEL", str(logging_raw.get("level", "INFO"))),
            rotation=str(logging_raw.get("rotation", "00:00")),
            retention=str(logging_raw.get("retention", "30 days")),
        ),
    )
