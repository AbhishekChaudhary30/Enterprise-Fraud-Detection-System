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
class TrainingSettings:
    """Machine learning training configuration."""

    random_state: int
    test_size: float
    validation_size: float
    smote_enabled: bool
    selection_metric: str
    search_type: str
    cv_folds: int
    randomized_iterations: int
    selected_features: tuple[str, ...]
    drop_features: tuple[str, ...]
    derived_features: tuple[str, ...]
    models: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class EvaluationSettings:
    """Evaluation, threshold, explainability, and report configuration."""

    output_directory: Path
    plots_directory: Path
    shap_directory: Path
    experiment_history: Path
    threshold_strategy: str
    business_threshold: float
    threshold_grid_size: int
    shap_sample_size: int
    calibration_bins: int


@dataclass(frozen=True)
class ServingSettings:
    """API, authentication, and prediction-serving configuration."""

    host: str
    port: int
    api_prefix: str
    history_file: Path
    upload_directory: Path
    output_directory: Path
    jwt_algorithm: str
    access_token_expire_minutes: int
    admin_username: str
    default_threshold: float
    jwt_secret: str
    admin_password: str


@dataclass(frozen=True)
class ProductionSettings:
    """Production hardening, observability, and drift configuration."""

    environment: str
    rate_limit_requests: int
    rate_limit_window_seconds: int
    request_id_header: str
    metrics_path: Path
    drift_output_directory: Path
    benchmark_output_directory: Path
    reference_data_path: Path
    drift_numeric_threshold: float
    drift_prediction_threshold: float


@dataclass(frozen=True)
class Settings:
    """Immutable application settings used by all project modules."""

    project_root: Path
    project_name: str
    phase: int
    dataset: DatasetSettings
    paths: PathSettings
    logging: LoggingSettings
    training: TrainingSettings
    evaluation: EvaluationSettings
    serving: ServingSettings
    production: ProductionSettings


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
    training_raw = raw.get("training", {})
    evaluation_raw = raw.get("evaluation", {})
    serving_raw = raw.get("serving", {})
    production_raw = raw.get("production", {})

    environment = os.getenv(
        "APP_ENVIRONMENT", str(production_raw.get("environment", "development"))
    )
    jwt_secret = os.getenv("JWT_SECRET", "change-this-secret-in-env")
    admin_password = os.getenv("ADMIN_PASSWORD", "change-this-password-in-env")
    if environment.lower() == "production" and (
        jwt_secret == "change-this-secret-in-env"
        or admin_password == "change-this-password-in-env"
        or len(jwt_secret) < 32
        or len(admin_password) < 12
    ):
        raise ValueError(
            "Production requires a JWT_SECRET of at least 32 characters and "
            "an ADMIN_PASSWORD of at least 12 characters"
        )

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
        training=TrainingSettings(
            random_state=int(training_raw.get("random_state", 42)),
            test_size=float(training_raw.get("test_size", 0.2)),
            validation_size=float(training_raw.get("validation_size", 0.2)),
            smote_enabled=bool(training_raw.get("smote_enabled", False)),
            selection_metric=str(training_raw.get("selection_metric", "average_precision")),
            search_type=str(training_raw.get("search_type", "randomized")),
            cv_folds=int(training_raw.get("cv_folds", 3)),
            randomized_iterations=int(training_raw.get("randomized_iterations", 2)),
            selected_features=tuple(
                str(item) for item in training_raw.get("selected_features", [])
            ),
            drop_features=tuple(str(item) for item in training_raw.get("drop_features", [])),
            derived_features=tuple(str(item) for item in training_raw.get("derived_features", [])),
            models=dict(training_raw.get("models", {})),
        ),
        evaluation=EvaluationSettings(
            output_directory=resolve_path(
                str(evaluation_raw.get("output_directory", "reports/evaluation"))
            ),
            plots_directory=resolve_path(
                str(evaluation_raw.get("plots_directory", "reports/figures/evaluation"))
            ),
            shap_directory=resolve_path(str(evaluation_raw.get("shap_directory", "reports/shap"))),
            experiment_history=resolve_path(
                str(evaluation_raw.get("experiment_history", "reports/experiments.jsonl"))
            ),
            threshold_strategy=str(evaluation_raw.get("threshold_strategy", "maximum_f1")),
            business_threshold=float(evaluation_raw.get("business_threshold", 0.5)),
            threshold_grid_size=int(evaluation_raw.get("threshold_grid_size", 99)),
            shap_sample_size=int(evaluation_raw.get("shap_sample_size", 1000)),
            calibration_bins=int(evaluation_raw.get("calibration_bins", 10)),
        ),
        serving=ServingSettings(
            host=os.getenv("API_HOST", str(serving_raw.get("host", "127.0.0.1"))),
            port=int(os.getenv("API_PORT", str(serving_raw.get("port", 8000)))),
            api_prefix=str(serving_raw.get("api_prefix", "/api/v1")),
            history_file=resolve_path(
                str(serving_raw.get("history_file", "artifacts/prediction_history.jsonl"))
            ),
            upload_directory=resolve_path(
                str(serving_raw.get("upload_directory", "artifacts/uploads"))
            ),
            output_directory=resolve_path(
                str(serving_raw.get("output_directory", "artifacts/predictions"))
            ),
            jwt_algorithm=str(serving_raw.get("jwt_algorithm", "HS256")),
            access_token_expire_minutes=int(serving_raw.get("access_token_expire_minutes", 60)),
            admin_username=os.getenv(
                "ADMIN_USERNAME", str(serving_raw.get("admin_username", "admin"))
            ),
            default_threshold=float(serving_raw.get("default_threshold", 0.5)),
            jwt_secret=jwt_secret,
            admin_password=admin_password,
        ),
        production=ProductionSettings(
            environment=environment,
            rate_limit_requests=int(production_raw.get("rate_limit_requests", 120)),
            rate_limit_window_seconds=int(production_raw.get("rate_limit_window_seconds", 60)),
            request_id_header=str(production_raw.get("request_id_header", "X-Request-ID")),
            metrics_path=resolve_path(
                str(production_raw.get("metrics_path", "artifacts/metrics.json"))
            ),
            drift_output_directory=resolve_path(
                str(production_raw.get("drift_output_directory", "reports/drift"))
            ),
            benchmark_output_directory=resolve_path(
                str(production_raw.get("benchmark_output_directory", "reports/benchmarks"))
            ),
            reference_data_path=resolve_path(
                str(production_raw.get("reference_data_path", "data/raw/creditcard.csv"))
            ),
            drift_numeric_threshold=float(production_raw.get("drift_numeric_threshold", 0.10)),
            drift_prediction_threshold=float(
                production_raw.get("drift_prediction_threshold", 0.10)
            ),
        ),
    )
